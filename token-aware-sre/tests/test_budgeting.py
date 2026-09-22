import pytest
from src.router.budgeting import TokenBudgeter

def test_budgeter_initialization():
    budgeter = TokenBudgeter()
    assert budgeter.cost_per_1k_tokens > 0

def test_calculate_budget_critical_severity():
    budgeter = TokenBudgeter()
    result = budgeter.calculate_budget(10)
    assert result["max_spend_usd"] > 0.0
    assert result["requires_local_only"] is False

def test_calculate_budget_low_severity():
    budgeter = TokenBudgeter()
    result = budgeter.calculate_budget(2)
    assert result["max_spend_usd"] == 0.0
    assert result["requires_local_only"] is True
