import logging

class IncidentEvaluator:
    """Evaluates the outcome of an AI-generated fix and calculates a reward.
    
    This acts as the "LLM-as-a-Judge" feedback mechanism. It determines the financial
    and operational success of the execution layer to train the Reinforcement Learning agent.

    Attributes:
        logger (logging.Logger): Logger for the evaluator.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_reward(self, action: int, is_success: bool) -> float:
        """Calculates the reinforcement learning reward based on success and cost.

        Args:
            action (int): 0 for Local SLM, 1 for Cloud LLM.
            is_success (bool): True if the incident was successfully resolved.

        Returns:
            float: The calculated reward score.
        """
        try:
            if action == 0 and is_success:
                reward = 10.0  # Perfect outcome: Fixed the issue for $0.00
            elif action == 1 and is_success:
                reward = 4.0   # Good outcome: Fixed the issue, but cost API budget
            elif action == 0 and not is_success:
                reward = -5.0  # Bad outcome: Failed to fix, wasted time (but free)
            else:
                reward = -10.0 # Terrible outcome: Failed to fix AND wasted paid API budget
                
            action_name = "Local SLM" if action == 0 else "Cloud LLM"
            status = "SUCCESS" if is_success else "FAILURE"
            self.logger.info(f"Evaluated {action_name} ({status}) -> Reward: {reward}")
            
            return reward
        except Exception as e:
            self.logger.error(f"Failed to calculate reward: {e}")
            return 0.0 # Neutral fallback
