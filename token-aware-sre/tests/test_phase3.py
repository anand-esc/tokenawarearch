import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.action_layer.risk_assessor import RiskAssessor
from src.action_layer.executor import MockExecutor

def test_action_layer():
    assessor = RiskAssessor()
    executor = MockExecutor()

    print("Test 1: Safe script")
    safe_script = "systemctl restart nginx\npython health_check.py"
    assessment = assessor.assess(safe_script)
    executor.execute(safe_script, assessment)
    assert assessment["is_safe"] == True

    print("\nTest 2: Destructive script")
    dangerous_script = "sudo rm -rf /var/lib/mysql\ndrop table users;"
    assessment = assessor.assess(dangerous_script)
    executor.execute(dangerous_script, assessment)
    assert assessment["is_safe"] == False
    
    print("\nAction Layer tests completed.")

if __name__ == "__main__":
    test_action_layer()
