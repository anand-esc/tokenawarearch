try:
    import pytest
except ImportError:
    pytest = None
from unittest.mock import patch
from src.router.dynamic_router import GlobalDynamicRouter

@patch('src.router.dynamic_router.QLearningRouter')
@patch('src.router.dynamic_router.TokenBudgeter')
@patch('src.router.dynamic_router.IncidentClassifier')
def test_dynamic_router_hybrid_trigger(MockClassifier, MockBudgeter, MockQLearning):
    # Setup Mocks
    mock_classifier = MockClassifier.return_value
    mock_classifier.classify.return_value = {"severity": 6, "complexity": 6}
    
    mock_budgeter = MockBudgeter.return_value
    mock_budgeter.calculate_budget.return_value = {"requires_local_only": False, "max_spend_usd": 0.05, "max_tokens": 1000}
    
    mock_q = MockQLearning.return_value
    mock_q.choose_action.return_value = 2 # 2 = Hybrid
    
    router = GlobalDynamicRouter()
    router.classifier = mock_classifier
    router.budgeter = mock_budgeter
    router.q_router = mock_q
    
    decision = router.route_incident("mock payload")
    
    assert decision["model_target"] == "HYBRID_ORCHESTRATOR"
    assert decision["severity"] == 6
    assert decision["complexity"] == 6

@patch('src.router.dynamic_router.QLearningRouter')
@patch('src.router.dynamic_router.TokenBudgeter')
@patch('src.router.dynamic_router.IncidentClassifier')
def test_dynamic_router_local_fallback(MockClassifier, MockBudgeter, MockQLearning):
    mock_budgeter = MockBudgeter.return_value
    mock_budgeter.calculate_budget.return_value = {"requires_local_only": True} # Forces SLM
    
    router = GlobalDynamicRouter()
    router.budgeter = mock_budgeter
    decision = router.route_incident("mock payload")
    
    assert decision["model_target"] == "LOCAL_SLM"
