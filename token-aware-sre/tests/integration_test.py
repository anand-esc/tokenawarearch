import os
import sys
import logging
import time

# Offline resilience for testing in sandboxed/offline environments
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Add src and token-aware-sre root to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from optimization.pipeline import OptimizationFunnel
from router.dynamic_router import GlobalDynamicRouter
from execution.model_factory import ModelFactory
from action_layer.risk_assessor import RiskAssessor
from evaluation.q_learning import QLearningRouter

# Configure logging for beautiful terminal output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def separator(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

def run_realtime_integration_test():
    separator("INITIALIZING MULTI-AGENT ARCHITECTURE (REAL-TIME TEST)")
    
    # 1. Initialize all components
    print("Loading Phase 1: Optimization Funnel...")
    funnel = OptimizationFunnel()
    
    print("Loading Phase 2: Dynamic Router (with Zero-Shot Classifier)...")
    router = GlobalDynamicRouter()
    
    print("Loading Phase 3: Model Factory...")
    factory = ModelFactory()
    
    print("Loading Phase 4 & Action Layer: Q-Learning & Risk Assessor...")
    q_router = QLearningRouter()
    risk_assessor = RiskAssessor()

    # Create a massive, redundant dummy incident (e.g. from Datadog)
    raw_incident = """
[CRITICAL] Database connection timeout across all production web servers.
java.net.ConnectException: Connection refused (Connection refused)
    at java.net.PlainSocketImpl.socketConnect(Native Method)
    at java.net.AbstractPlainSocketImpl.doConnect(AbstractPlainSocketImpl.java:350)
    at java.net.AbstractPlainSocketImpl.connectToAddress(AbstractPlainSocketImpl.java:206)
java.net.ConnectException: Connection refused (Connection refused)
    at java.net.PlainSocketImpl.socketConnect(Native Method)
java.net.ConnectException: Connection refused (Connection refused)
    at java.net.PlainSocketImpl.socketConnect(Native Method)
    at java.net.AbstractPlainSocketImpl.doConnect(AbstractPlainSocketImpl.java:350)
{"alert_id": "99382", "service": "web-api-prod", "status": "down"}
"""
    chat_history = "User A: Hey, the DB is down again. User B: I think it's the redis cache. User A: Let's restart it."

    separator("PHASE 1: OPTIMIZATION FUNNEL")
    print(f"Original Payload Size: {len(raw_incident) + len(chat_history)} characters")
    start_time = time.time()
    compressed_payload = funnel.process(raw_incident, chat_history)
    print(f"Compressed Payload Size: {len(compressed_payload)} characters")
    print(f"Phase 1 execution time: {time.time() - start_time:.2f} seconds")

    separator("PHASE 2: GLOBAL DYNAMIC ROUTING")
    start_time = time.time()
    routing_decision = router.route_incident(compressed_payload)
    print(f"Severity Score: {routing_decision['severity']}/10")
    print(f"Complexity Score: {routing_decision['complexity']}/10")
    print(f"Target Model: {routing_decision['model_target']}")
    print(f"Allocated Budget: ${routing_decision['budget_usd']}")
    print(f"Reason: {routing_decision['reason']}")
    print(f"Phase 2 execution time: {time.time() - start_time:.2f} seconds")

    separator("PHASE 3: MODEL EXECUTION (DRY RUN)")
    print(f"Attempting to spin up: {routing_decision['model_target']}")
    try:
        model = factory.get_model(routing_decision['model_target'])
        print(f"Successfully loaded LangChain model: {type(model).__name__}")
        # Note: We won't actually invoke the LLM here to prevent hanging if you don't have Ollama running or an API key.
        # We will mock the AI's generated bash script instead.
        print("Mocking LLM Generation step...")
        mock_generated_script = "#!/bin/bash\nsystemctl restart redis\nrm -rf /var/log/redis/*"
    except Exception as e:
        print(f"Model loading failed (expected if API keys/Ollama are missing): {e}")
        mock_generated_script = "#!/bin/bash\nrm -rf /"

    separator("ACTION LAYER: REGEX RISK ASSESSOR")
    print("Scanning AI-generated script for destructive commands...")
    print(f"Generated Script:\n{mock_generated_script}")
    assessment = risk_assessor.assess(mock_generated_script)
    
    print(f"Is Safe? {assessment['is_safe']}")
    print(f"Risk Score: {assessment['risk_score']}/100")
    print(f"Reason: {assessment['reason']}")

    separator("PHASE 4: Q-LEARNING REWARD UPDATE")
    # If the script was safe, we reward. If dangerous, we penalize.
    action_idx = 0 if routing_decision['model_target'] == "LOCAL_SLM" else 1
    reward = 10 if assessment['is_safe'] else -20
    print(f"Applying Reward of {reward} to Q-Table for State({routing_decision['severity']}, {routing_decision['complexity']})...")
    q_router.update(routing_decision['severity'], routing_decision['complexity'], action_idx, reward)
    
    print("\nEND-TO-END INTEGRATION TEST COMPLETE.")

if __name__ == "__main__":
    run_realtime_integration_test()
