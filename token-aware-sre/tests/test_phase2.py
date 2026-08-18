import sys
import os

# Ensure src is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.router.dynamic_router import GlobalDynamicRouter

def test_router():
    print("Initializing Global Dynamic Router (this may take a few seconds to load the local BERT model)...")
    router = GlobalDynamicRouter()
    
    print("\n" + "="*50)
    print("Test 1: Low Complexity / Low Severity (Informational)")
    print("="*50)
    sample_low = "User login took 50ms longer than usual but succeeded. Trivial fix, informational only."
    result_low = router.route_incident(sample_low)
    print(result_low)
    
    print("\n" + "="*50)
    print("Test 2: High Complexity / High Severity (Critical Failure)")
    print("="*50)
    sample_high = "critical system failure: Kubernetes cluster in us-east-1 went down. 503 errors across all payment gateways. requires deep debugging across multiple services."
    result_high = router.route_incident(sample_high)
    print(result_high)
    
    print("\nRouting tests completed.")

if __name__ == "__main__":
    test_router()
