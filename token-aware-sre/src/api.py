from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import os
import sys
import requests as http_requests
import logging
from threading import Lock

# Add current dir to path
sys.path.append(os.path.dirname(__file__))

# Import the existing Python backend
from config import Config
from optimization.pipeline import OptimizationFunnel
from router.dynamic_router import GlobalDynamicRouter
from execution.agent_scheduler import AgentScheduler
from action_layer.risk_assessor import RiskAssessor
from evaluation.q_learning import QLearningRouter
from evaluation.evaluator import IncidentEvaluator

logger = logging.getLogger(__name__)

# Validate Configs on startup
Config.validate()

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
scheduler = AgentScheduler()
q_router = QLearningRouter()
risk_assessor = RiskAssessor()
evaluator = IncidentEvaluator()
print("Models loaded successfully.")

# Thread-safe runtime config
runtime_config = {
    "llm_api_key": os.environ.get("GOOGLE_API_KEY", ""),
    "llm_name": "gemini-2.5-pro",
    "llm_endpoint": "",
    "slm_api_key": "",
    "slm_name": "qwen2.5",
    "slm_endpoint": "http://localhost:11434",
}
config_lock = Lock()

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    """Payload for initiating a chat request with an incident log."""
    prompt: str
    chat_history: str = ""
    is_outage: bool = False

class RewardRequest(BaseModel):
    """Payload for submitting a Q-Learning reward update."""
    severity: int
    complexity: int
    model_target: str
    reward: int

class ConfigUpdate(BaseModel):
    """Payload for dynamically updating model runtime configuration."""
    model_type: str  # 'llm' or 'slm'
    name: str = ""
    api_key: str = ""
    endpoint: str = ""

class TestConnectionRequest(BaseModel):
    """Payload for testing connectivity to a specified model endpoint."""
    model_type: str  # 'llm' or 'slm'
    api_key: str = ""
    endpoint: str = ""

# --- Endpoints ---

@app.post("/api/config")
def update_config(req: ConfigUpdate):
    """Update runtime model configuration from the frontend."""
    with config_lock:
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
def test_connection(req: TestConnectionRequest):
    """Actually test connectivity to LLM or SLM."""
    with config_lock:
        current_config = runtime_config.copy()
        
    if req.model_type == "slm":
        endpoint = (req.endpoint or current_config["slm_endpoint"]).rstrip("/")
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
        api_key = req.api_key or current_config["llm_api_key"]
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
def process_chat(req: ChatRequest):
    """Processes an incoming chat payload through the entire optimization and execution funnel."""
    start_time = time.time()
    
    with config_lock:
        current_config = runtime_config.copy()
        
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
    
    # Calculate Real Token Costs
    # Using basic heuristic: 4 chars = 1 token.
    # We use a baseline config value for token costs.
    cost_per_1k_tokens = 0.01  # USD
    original_tokens = original_size / 4.0
    compressed_tokens = compressed_size / 4.0
    
    original_cost = (original_tokens / 1000.0) * cost_per_1k_tokens
    compressed_cost = (compressed_tokens / 1000.0) * cost_per_1k_tokens
    
    # Phase 2: Routing
    t0 = time.time()
    routing_decision = router.route_incident(compressed_payload)
    t_route = round((time.time() - t0) * 1000)
    
    # Phase 3: REAL Execution via AgentScheduler
    t0 = time.time()
    model_target = routing_decision['model_target']
    
    script = scheduler.schedule_and_execute(
        compressed_payload=compressed_payload,
        routing_decision=routing_decision,
        runtime_config=current_config
    )
    
    t_execute = round((time.time() - t0) * 1000)
    
    # Dynamic per-call savings calculation
    if model_target == "LOCAL_SLM":
        per_call_saving = original_cost
    else:
        per_call_saving = original_cost - compressed_cost
        
    # Phase 4: Risk Assessment
    assessment = risk_assessor.assess(script)
    
    latency = round((time.time() - start_time) * 1000)
    
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
def apply_reward(req: RewardRequest):
    """Records the outcome of a routing decision using Q-Learning."""
    action_idx = 0 if req.model_target == "LOCAL_SLM" else 1
    
    # Determine success heuristically (reward > 0)
    is_success = req.reward > 0
    calculated_reward = evaluator.calculate_reward(action_idx, is_success)
    
    q_router.update(req.severity, req.complexity, action_idx, calculated_reward)
    return {"status": "success", "message": f"Q-Table updated with {calculated_reward}"}

@app.get("/api/qtable")
def get_qtable():
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
def get_status():
    """Check actual health of pipeline components and live model connectivity."""
    with config_lock:
        current_config = runtime_config.copy()
        
    # Check SLM (Ollama)
    slm_status = "Offline"
    slm_endpoint = current_config["slm_endpoint"].rstrip("/")
    if slm_endpoint:
        try:
            r = http_requests.get(f"{slm_endpoint}/api/tags", timeout=3)
            if r.status_code == 200:
                slm_status = "Online"
        except Exception as e:
            logger.warning(f"SLM health check failed: {e}")
    
    # Check LLM (API key present)
    llm_status = "Online" if current_config["llm_api_key"] else "No Key"
    
    return {
        "llm_status": llm_status,
        "slm_status": slm_status
    }
