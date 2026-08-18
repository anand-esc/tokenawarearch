import logging

class TokenBudgeter:
    """
    Calculates the maximum allowable API spend and token limit based on Incident Severity.
    """
    def __init__(self, cost_per_1k_tokens=0.01): # Default roughly GPT-4 pricing
        self.logger = logging.getLogger(__name__)
        self.cost_per_1k_tokens = cost_per_1k_tokens

    def calculate_budget(self, severity: int) -> dict:
        """
        Takes a severity score (1-10) and returns a budget configuration.
        """
        # Ensure severity is bounded
        severity = max(1, min(10, severity))
        
        # Budget logic:
        # Severity 1-3: $0.00 (Force Local SLM, zero cloud spend)
        # Severity 4-6: Low budget ($0.50 - $1.50)
        # Severity 7-8: Medium budget ($4.00 - $6.50)
        # Severity 9-10: Unlimited/High budget ($11.50 - $16.50+)
        
        if severity <= 3:
            max_spend_usd = 0.0
        elif severity <= 6:
            max_spend_usd = (severity - 3) * 0.5
        elif severity <= 8:
            max_spend_usd = (severity - 6) * 2.5 + 1.5
        else:
            max_spend_usd = (severity - 8) * 5.0 + 6.5

        # Calculate rough token limit based on max spend
        if max_spend_usd == 0.0:
            token_limit = 0
        else:
            token_limit = int((max_spend_usd / self.cost_per_1k_tokens) * 1000)

        budget_config = {
            "max_spend_usd": round(max_spend_usd, 2),
            "max_tokens": token_limit,
            "requires_local_only": max_spend_usd == 0.0
        }
        
        self.logger.info(f"Severity {severity} -> Budget: ${budget_config['max_spend_usd']} ({budget_config['max_tokens']} tokens)")
        return budget_config

if __name__ == "__main__":
    budgeter = TokenBudgeter()
    for s in range(1, 11):
        print(f"Severity {s}:", budgeter.calculate_budget(s))
