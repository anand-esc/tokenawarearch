import logging
from .classifier import IncidentClassifier
from .budgeting import TokenBudgeter

class GlobalDynamicRouter:
    """The central intelligence node for Phase 2.
    
    Evaluates the highly compressed incident payload, queries the Classifier 
    and Budgeter, and makes the definitive decision on whether to route the 
    remediation task to a free Local SLM or a paid Cloud LLM.

    Attributes:
        logger (logging.Logger): Logger for the router.
        classifier (IncidentClassifier): Component to score severity and complexity.
        budgeter (TokenBudgeter): Component to allocate a token budget.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Global Dynamic Router...")
        try:
            self.classifier = IncidentClassifier()
            self.budgeter = TokenBudgeter()
        except Exception as e:
            self.logger.error(f"Failed to initialize router components: {e}")
            raise RuntimeError("Router initialization failed") from e

    def route_incident(self, compressed_payload: str) -> dict:
        """Determines the optimal execution model (Local SLM vs Cloud LLM).

        Args:
            compressed_payload (str): The optimized incident text from Phase 1.

        Returns:
            dict: The routing decision including the target model and reasoning.
        """
        self.logger.info("Evaluating incoming incident payload for routing.")

        try:
            # 1. Classify Severity and Complexity
            classification = self.classifier.classify(compressed_payload)
            severity = classification.get("severity", 5)
            complexity = classification.get("complexity", 5)

            # 2. Determine Budget based on Severity
            budget = self.budgeter.calculate_budget(severity)

            # 3. Routing Logic: Match Complexity vs Budget
            if budget.get("requires_local_only", False):
                model_target = "LOCAL_SLM"
                reason = "Budget restricted to $0.00 due to low severity."
            elif complexity >= 7 and budget.get("max_spend_usd", 0) > 0.0:
                model_target = "CLOUD_LLM"
                reason = "High complexity requires frontier model. Budget is available."
            else:
                model_target = "LOCAL_SLM"
                reason = "Low to moderate complexity. Local SLM is sufficient and saves budget."

            routing_decision = {
                "model_target": model_target,
                "reason": reason,
                "severity": severity,
                "complexity": complexity,
                "budget_usd": budget.get("max_spend_usd", 0.0),
                "token_limit": budget.get("max_tokens", 0),
                "primary_severity_label": classification.get("primary_severity_label"),
                "primary_complexity_label": classification.get("primary_complexity_label")
            }

            self.logger.info(f"Routing Decision: {model_target} - {reason}")
            return routing_decision
            
        except Exception as e:
            self.logger.error(f"Routing decision failed: {e}")
            # Failsafe: ALWAYS route local if something crashes to prevent runaway cloud spend
            return {
                "model_target": "LOCAL_SLM",
                "reason": f"Failsafe triggered due to error: {e}",
                "severity": 5,
                "complexity": 5,
                "budget_usd": 0.0,
                "token_limit": 0
            }

if __name__ == "__main__":
    router = GlobalDynamicRouter()
    print("Router ready.")
