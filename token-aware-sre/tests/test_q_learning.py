try:
    import pytest
except ImportError:
    pytest = None
import numpy as np
from unittest.mock import patch
from src.evaluation.q_learning import QLearningRouter

@patch('os.path.exists')
def test_q_learning_initialization(mock_exists):
    mock_exists.return_value = False # Force fresh init
    router = QLearningRouter()
    assert router.q_table.shape == (11, 11, 3) # 10 states + 1 (1-indexed), 3 actions

def test_choose_action_bounds():
    router = QLearningRouter()
    action = router.choose_action(5, 5)
    assert action in [0, 1, 2]

def test_q_table_update():
    router = QLearningRouter(epsilon=0.0) # Disable exploration for test
    initial_q = router.q_table[9, 9, 1]
    router.update(9, 9, 1, 15.0)
    new_q = router.q_table[9, 9, 1]
    assert new_q > initial_q # Q-value should increase with positive reward
