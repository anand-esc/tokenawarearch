import sys
import os

# Ensure offline deterministic execution in sandboxed / offline environments
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Ensure src is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.optimization.pipeline import OptimizationFunnel

def test_funnel_compression():
    funnel = OptimizationFunnel()
    
    chat_history = "User: Server is down.\nAgent: Looking into it. I see spikes." * 10
    
    raw_log = """
    {"event_title": "Database Connection Refused", "alert_transition": "Triggered", "body": "Timeout trying to reach 10.0.0.1"}
    """
    
    print("Testing Funnel Pipeline...")
    compressed_payload = funnel.process(raw_incident=raw_log, chat_history=chat_history)
    
    print("=== FINAL PAYLOAD ===")
    print(compressed_payload)
    print("=====================")
    print(f"Original length roughly: {len(chat_history) + len(raw_log)} characters")
    print(f"Compressed length roughly: {len(compressed_payload)} characters")
    
if __name__ == "__main__":
    test_funnel_compression()
