import numpy as np
import logging
import pickle
import os
from typing import Optional
from config import Config

class QLearningRouter:
    """Tabular Q-Learning agent for dynamic SLM vs LLM routing.
    
    Maintains a Q-Table mapping (Severity, Complexity) states to the optimal
    action (Local SLM vs Cloud LLM). It learns over time to maximize token 
    efficiency based on the rewards from the Evaluator.

    Attributes:
        q_table (np.ndarray): The Q-value matrix.
        alpha (float): Learning rate.
        gamma (float): Discount factor.
        epsilon (float): Exploration rate for epsilon-greedy strategy.
    """
    def __init__(self, states_severity: int = 10, states_complexity: int = 10, actions: int = 2, 
                 alpha: Optional[float] = None, gamma: Optional[float] = None, epsilon: Optional[float] = None):
        self.logger = logging.getLogger(__name__)
        # State space: Severity (0-10) x Complexity (0-10) x Actions (0=SLM, 1=LLM)
        self.q_table = np.zeros((states_severity + 1, states_complexity + 1, actions))
        self.alpha = alpha if alpha is not None else Config.Q_LEARNING_ALPHA
        self.gamma = gamma if gamma is not None else Config.Q_LEARNING_GAMMA
        self.epsilon = epsilon if epsilon is not None else Config.Q_LEARNING_EPSILON
        
        # Path to persist the "Brain"
        self.save_path = os.path.join(os.path.dirname(__file__), "q_table.pkl")
        self._load_table()

    def choose_action(self, severity: int, complexity: int) -> int:
        """Selects the best routing action using an epsilon-greedy policy.

        Args:
            severity (int): Incident severity (1-10).
            complexity (int): Incident complexity (1-10).

        Returns:
            int: 0 for Local SLM, 1 for Cloud LLM.
        """
        try:
            # Exploration: Try a random model to discover new strategies
            if np.random.uniform(0, 1) < self.epsilon:
                return np.random.choice([0, 1])
            # Exploitation: Pick the model with the highest historical success/reward
            else:
                return int(np.argmax(self.q_table[severity, complexity]))
        except IndexError as e:
            self.logger.error(f"State out of bounds: {e}. Defaulting to SLM.")
            return 0

    def update(self, severity: int, complexity: int, action: int, reward: float):
        """Updates the Q-Table based on the Bellman equation.

        Args:
            severity (int): The state severity.
            complexity (int): The state complexity.
            action (int): The action taken (0 or 1).
            reward (float): The reward received from the Evaluator.
        """
        try:
            current_q = self.q_table[severity, complexity, action]
            # Max future Q is simplified since episodes are 1-step (contextual bandit style formulation)
            # Max future Q is simplified since episodes are 1-step (contextual bandit style formulation),
            # but we explicitly incorporate gamma to satisfy RL formulations and future-proof for Phase 5 multi-step.
            max_future_q = 0.0
            new_q = current_q + self.alpha * (reward + self.gamma * max_future_q - current_q)
            self.q_table[severity, complexity, action] = new_q
            self._save_table()
            self.logger.debug(f"Updated Q-Table for state ({severity}, {complexity}), action {action} -> {new_q:.2f}")
        except Exception as e:
            self.logger.error(f"Failed to update Q-Table: {e}")

    def _save_table(self):
        """Persists the Q-Table to disk."""
        try:
            with open(self.save_path, 'wb') as f:
                pickle.dump(self.q_table, f)
        except Exception as e:
            self.logger.error(f"Could not save Q-table: {e}")

    def _load_table(self):
        """Loads the Q-Table from disk if it exists."""
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'rb') as f:
                    self.q_table = pickle.load(f)
                self.logger.info("Loaded existing Q-Table.")
            except Exception as e:
                self.logger.error(f"Could not load Q-table: {e}. Starting fresh.")
