from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import os
import sys
import requests as http_requests
import logging

# Add current dir to path
sys.path.append(os.path.dirname(__file__))

# Import the existing Python backend
from optimization.pipeline import OptimizationFunnel
from router.dynamic_router import GlobalDynamicRouter
from execution.model_factory import ModelFactory
from action_layer.risk_assessor import RiskAssessor
from evaluation.q_learning import QLearningRouter

logger = logging.getLogger(__name__)

app = FastAPI(title="Token-Aware Multi-Agent API")

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (Load models once)
print("Initializing Models (This will download HF models if not cached)...")
funnel = OptimizationFunnel()
router = GlobalDynamicRouter()
factory = ModelFactory()
q_router = QLearningRouter()
risk_assessor = RiskAssessor()
print("Models loaded successfully.")

# Runtime config -- updated from frontend
runtime_config = {
    "llm_api_key": os.environ.get("GOOGLE_API_KEY", ""),
    "llm_name": "gemini-2.5-pro",
    "llm_endpoint": "",
    "slm_api_key": "",
    "slm_name": "qwen2.5",
    "slm_endpoint": "http://localhost:11434",
}

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    prompt: str
    chat_history: str = ""
    is_outage: bool = False

class RewardRequest(BaseModel):
    severity: int
    complexity: int
    model_target: str
    reward: int

class ConfigUpdate(BaseModel):
    model_type: str  # 'llm' or 'slm'
    name: str = ""
    api_key: str = ""
    endpoint: str = ""

class TestConnectionRequest(BaseModel):
    model_type: str  # 'llm' or 'slm'
    api_key: str = ""
    endpoint: str = ""

# --- Helpers ---

SRE_SYSTEM_PROMPT = """You are an expert Site Reliability Engineer. Given an infrastructure incident description, generate a concise bash remediation script. Output ONLY the script starting with #!/bin/bash. No explanations, no markdown fences."""

def call_llm(prompt: str) -> str:
    """Call Cloud LLM (Google Gemini) with the real API key."""
    api_key = runtime_config["llm_api_key"]
    model_name = runtime_config["llm_name"]
    
    if not api_key:
        return "#!/bin/bash\n# ERROR: No LLM API key configured.\n# Please set your Gemini API key in the LLM Configuration panel.\necho 'No API key set'"
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, SystemMessage
        
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.2,
            google_api_key=api_key
        )
        response = llm.invoke([
            SystemMessage(content=SRE_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        result = response.content.strip()
        # Strip markdown fences if LLM wraps them
        if result.startswith("```"):
            lines = result.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            result = "\n".join(lines)
        if not result.startswith("#!"):
            result = "#!/bin/bash\n" + result
        return result
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return f"#!/bin/bash\n# ERROR: LLM call failed\n# {str(e)[:200]}\necho 'LLM Error'"

def call_slm(prompt: str) -> str:
    """Call Local SLM (Ollama) at the configured endpoint."""
    endpoint = runtime_config["slm_endpoint"].rstrip("/")
    model_name = runtime_config["slm_name"]
    
    if not endpoint:
        return "#!/bin/bash\n# ERROR: No SLM endpoint configured.\necho 'No endpoint set'"
    
    try:
        resp = http_requests.post(
            f"{endpoint}/api/generate",
            json={
                "model": model_name,
                "prompt": f"{SRE_SYSTEM_PROMPT}\n\nIncident:\n{prompt}",
                "stream": False,
                "options": {"temperature": 0.2}
            },
            timeout=60
        )
        resp.raise_for_status()
        result = resp.json().get("response", "").strip()
        # Strip markdown fences if SLM wraps them
        if result.startswith("```"):
            lines = result.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            result = "\n".join(lines)
        if not result.startswith("#!"):
            result = "#!/bin/bash\n" + result
        return result
    except http_requests.exceptions.ConnectionError:
        return f"#!/bin/bash\n# ERROR: Cannot connect to Ollama at {endpoint}\n# Make sure Ollama is running: ollama serve\necho 'SLM Offline'"
    except Exception as e:
        logger.error(f"SLM call failed: {e}")
        return f"#!/bin/bash\n# ERROR: SLM call failed\n# {str(e)[:200]}\necho 'SLM Error'"

# --- Endpoints ---

@app.post("/api/config")
async def update_config(req: ConfigUpdate):
    """Update runtime model configuration from the frontend."""
    if req.model_type == "llm":
        if req.api_key:
            runtime_config["llm_api_key"] = req.api_key
        if req.name:
            runtime_config["llm_name"] = req.name
        if req.endpoint:
            runtime_config["llm_endpoint"] = req.endpoint
    elif req.model_type == "slm":
        if req.api_key:
            runtime_config["slm_api_key"] = req.api_key
        if req.name:
            runtime_config["slm_name"] = req.name
        if req.endpoint:
            runtime_config["slm_endpoint"] = req.endpoint
    return {"status": "ok", "config": runtime_config}

@app.post("/api/test-connection")
async def test_connection(req: TestConnectionRequest):
    """Actually test connectivity to LLM or SLM."""
    if req.model_type == "slm":
        endpoint = (req.endpoint or runtime_config["slm_endpoint"]).rstrip("/")
        try:
            resp = http_requests.get(f"{endpoint}/api/tags", timeout=5)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            return {
                "status": "online",
                "message": f"Ollama running. Available models: {', '.join(models) if models else 'none'}",
                "models": models
            }
        except http_requests.exceptions.ConnectionError:
            return {"status": "offline", "message": f"Cannot reach Ollama at {endpoint}. Run: ollama serve"}
        except Exception as e:
            return {"status": "error", "message": str(e)[:300]}
    
    elif req.model_type == "llm":
        api_key = req.api_key or runtime_config["llm_api_key"]
        if not api_key:
            return {"status": "error", "message": "No API key provided. Enter your Gemini API key."}
        try:
            # Use the Gemini REST API to list models as a lightweight health check
            resp = http_requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=10
            )
            if resp.status_code == 200:
                models = [m["name"].split("/")[-1] for m in resp.json().get("models", [])[:5]]
                return {"status": "online", "message": f"Gemini API valid. Models: {', '.join(models)}"}
            elif resp.status_code == 400 or resp.status_code == 403:
                return {"status": "error", "message": "Invalid API key. Check your Gemini key."}
            else:
                return {"status": "error", "message": f"Unexpected response: {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)[:300]}
    
    return {"status": "error", "message": "Unknown model_type"}

@app.post("/api/chat")
async def process_chat(req: ChatRequest):
    start_time = time.time()
    
    original_size = len(req.prompt) + len(req.chat_history)
    
    # Phase 1: Optimization
    t0 = time.time()
    compressed_payload = funnel.process(req.prompt, req.chat_history)
    t_optimize = round((time.time() - t0) * 1000)
    
    compressed_size = len(compressed_payload)
    if compressed_size > original_size:
        compressed_payload = req.prompt + "\n" + req.chat_history
        compressed_size = original_size
        
    reduction = int((1 - (compressed_size / max(original_size, 1))) * 100)
    reduction = max(0, reduction)
    
    # Phase 2: Routing
    t0 = time.time()
    routing_decision = router.route_incident(compressed_payload)
    t_route = round((time.time() - t0) * 1000)
    
    # Phase 3: REAL Execution
    t0 = time.time()
    model_target = routing_decision['model_target']
    
    if model_target == "CLOUD_LLM":
        script = call_llm(compressed_payload)
    else:
        script = call_slm(compressed_payload)
    
    t_execute = round((time.time() - t0) * 1000)
    
    # Phase 4: Risk Assessment
    assessment = risk_assessor.assess(script)
    
    latency = round((time.time() - start_time) * 1000)
    per_call_saving = 0.14 if model_target == "LOCAL_SLM" else 0.00
    
    return {
        "response": script,
        "transparency": {
            "original_prompt": req.prompt,
            "compressed_prompt": compressed_payload,
            "original_chars": original_size,
            "compressed_chars": compressed_size,
            "reduction_percent": reduction,
            "severity": routing_decision['severity'],
            "complexity": routing_decision['complexity'],
            "model_target": model_target,
            "budget_usd": routing_decision['budget_usd'],
            "routing_reason": routing_decision['reason'],
            "is_safe": assessment['is_safe'],
            "risk_score": assessment['risk_score'],
            "risk_reason": assessment['reason'],
            "latency_ms": latency,
            "t_optimize_ms": t_optimize,
            "t_route_ms": t_route,
            "t_execute_ms": t_execute,
            "estimated_savings_usd": per_call_saving
        }
    }

@app.post("/api/reward")
async def apply_reward(req: RewardRequest):
    action_idx = 0 if req.model_target == "LOCAL_SLM" else 1
    q_router.update(req.severity, req.complexity, action_idx, req.reward)
    return {"status": "success", "message": f"Q-Table updated with {req.reward}"}

@app.get("/api/qtable")
async def get_qtable():
    """Return the Q-Table as a JSON-safe dictionary."""
    try:
        table = q_router.q_table
        json_table = {}
        for sev in range(table.shape[0]):
            comp_dict = {}
            for comp in range(table.shape[1]):
                values = table[sev, comp].tolist()
                if values[0] != 0.0 or values[1] != 0.0:
                    comp_dict[str(comp)] = values
            if comp_dict:
                json_table[str(sev)] = comp_dict
        return {"q_table": json_table}
    except Exception as e:
        return {"q_table": {}, "error": str(e)}

@app.get("/api/status")
async def get_status():
    """Check actual health of pipeline components and live model connectivity."""
    # Check SLM (Ollama)
    slm_status = "Offline"
    slm_endpoint = runtime_config["slm_endpoint"].rstrip("/")
    if slm_endpoint:
        try:
            r = http_requests.get(f"{slm_endpoint}/api/tags", timeout=3)
            if r.status_code == 200:
                slm_status = "Online"
        except Exception:
            pass
    
    # Check LLM (API key present)
    llm_status = "Online" if runtime_config["llm_api_key"] else "No Key"
    
    return {
        "llm_status": llm_status,
        "slm_status": slm_status
    }
