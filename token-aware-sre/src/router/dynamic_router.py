import logging
from .classifier import IncidentClassifier
from .budgeting import TokenBudgeter

class GlobalDynamicRouter:
    """
    The main ingress point for Phase 2.
    Evaluates the compressed incident payload, consults the Classifier and Budgeter,
    and returns a routing decision.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Global Dynamic Router...")
        self.classifier = IncidentClassifier()
        self.budgeter = TokenBudgeter()

    def route_incident(self, compressed_payload: str) -> dict:
        """
        Determines the optimal execution model (Local SLM vs Cloud LLM).
        """
        self.logger.info("Evaluating incoming incident payload for routing.")

        # 1. Classify Severity and Complexity
        classification = self.classifier.classify(compressed_payload)
        severity = classification.get("severity", 5)
        complexity = classification.get("complexity", 5)

        # 2. Determine Budget based on Severity
        budget = self.budgeter.calculate_budget(severity)

        # 3. Routing Logic: Match Complexity vs Budget
        # If budget requires local only, force SLM.
        # If complexity is high AND we have budget, use Cloud LLM.
        # Otherwise, default to Local SLM to save costs.

        if budget["requires_local_only"]:
            model_target = "LOCAL_SLM"
            reason = "Budget restricted to $0.00 due to low severity."
        elif complexity >= 7 and budget["max_spend_usd"] > 0.0:
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
            "budget_usd": budget["max_spend_usd"],
            "token_limit": budget["max_tokens"],
            "primary_severity_label": classification.get("primary_severity_label"),
            "primary_complexity_label": classification.get("primary_complexity_label")
        }

        self.logger.info(f"Routing Decision: {model_target} - {reason}")
        return routing_decision

if __name__ == "__main__":
    router = GlobalDynamicRouter()
    sample_low = "Minor warning on dev server."
    sample_high = "CRITICAL: Multiple databases down, out of memory, network timeout across all regions."
    
    print("\n--- Low Severity Test ---")
    print(router.route_incident(sample_low))
    
    print("\n--- High Severity Test ---")
    print(router.route_incident(sample_high))
