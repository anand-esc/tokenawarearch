import sys
import os
import random
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.evaluation.q_learning import QLearningRouter
from src.evaluation.evaluator import IncidentEvaluator

logging.basicConfig(level=logging.INFO)

def pre_train_agent(episodes=1000):
    """
    Simulates 1,000 incident resolutions to 'pre-train' the Q-Table.
    This answers: "How do we initially train the model?"
    By feeding it simulated historical data, it learns the baseline rules 
    before ever touching a live production environment.
    """
    print(f"Starting Pre-Training Simulation with {episodes} episodes...")
    router = QLearningRouter(epsilon=0.8) # High exploration for training
    evaluator = IncidentEvaluator()
    
    slm_successes = 0
    llm_successes = 0

    for i in range(episodes):
        # 1. Randomly generate an incident state
        severity = random.randint(1, 10)
        complexity = random.randint(1, 10)
        
        # 2. Agent chooses an action (0=SLM, 1=LLM)
        action = router.choose_action(severity, complexity)
        
        # 3. Simulate the outcome (Environment response)
        # Assume SLM is good at low complexity (<=5), fails at high complexity (>5)
        # Assume LLM is good at everything (succeeds 95% of the time)
        if action == 0:
            is_success = random.random() < 0.9 if complexity <= 5 else random.random() < 0.2
            if is_success: slm_successes += 1
        else:
            is_success = random.random() < 0.95
            if is_success: llm_successes += 1
            
        # 4. Calculate reward and update Q-Table
        reward = evaluator.calculate_reward(action, is_success)
        router.update(severity, complexity, action, reward)
        
    print("\nPre-Training Complete!")
    print(f"SLM Simulated Successes: {slm_successes}")
    print(f"LLM Simulated Successes: {llm_successes}")
    print("\nLet's test the trained agent's decisions (Exploitation Mode):")
    
    # Turn off exploration to see what it learned
    router.epsilon = 0.0 
    
    # Test a simple issue
    simple_action = router.choose_action(severity=2, complexity=2)
    print(f"Low Sev/Comp (2,2) -> Routed to: {'SLM' if simple_action == 0 else 'Cloud LLM'}")
    
    # Test a complex issue
    complex_action = router.choose_action(severity=9, complexity=9)
    print(f"High Sev/Comp (9,9) -> Routed to: {'SLM' if complex_action == 0 else 'Cloud LLM'}")

if __name__ == "__main__":
    pre_train_agent()
