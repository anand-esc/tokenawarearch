import logging
from .classifier import IncidentClassifier
from .budgeting import TokenBudgeter
try:
    from src.evaluation.q_learning import QLearningRouter
except ImportError:
    from evaluation.q_learning import QLearningRouter

class GlobalDynamicRouter:
    """The central intelligence node for Phase 2.
    
    Evaluates the highly compressed incident payload, queries the Classifier 
    and Budgeter, and makes the definitive decision on whether to route the 
    remediation task to a Local SLM, Cloud LLM, or Hybrid Orchestrator.

    Attributes:
        logger (logging.Logger): Logger for the router.
        classifier (IncidentClassifier): Component to score severity and complexity.
        budgeter (TokenBudgeter): Component to allocate a token budget.
        q_router (QLearningRouter): Tabular RL agent for cost/token optimization.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Global Dynamic Router...")
        try:
            self.classifier = IncidentClassifier()
            self.budgeter = TokenBudgeter()
            self.q_router = QLearningRouter()
        except Exception as e:
            self.logger.error(f"Failed to initialize router components: {e}")
            raise RuntimeError("Router initialization failed") from e

    def route_incident(self, compressed_payload: str) -> dict:
        """Determines the optimal execution model (Local SLM vs Cloud LLM vs Hybrid)."""
        self.logger.info("Evaluating incoming incident payload for routing.")

        try:
            # 1. Classify Severity and Complexity using our fine-tuned RoBERTa model
            classification = self.classifier.classify(compressed_payload)
            severity = classification.get("severity", 5)
            complexity = classification.get("complexity", 5)

            # 2. Determine Budget based on Severity
            budget = self.budgeter.calculate_budget(severity)

            # 3. Routing Logic: Match Complexity vs Budget via Q-Learning!
            if budget.get("requires_local_only", False):
                model_target = "LOCAL_SLM"
                reason = "Budget restricted to $0.00 due to low severity."
            else:
                # Query the RL Brain! (0 = SLM, 1 = LLM, 2 = Hybrid)
                action = self.q_router.choose_action(severity, complexity)
                
                if action == 2:
                    model_target = "HYBRID_ORCHESTRATOR"
                    reason = "Q-Learning Brain chose Hybrid (0-Token Breakdown) for max efficiency."
                elif action == 1 and budget.get("max_spend_usd", 0) > 0.0:
                    model_target = "CLOUD_LLM"
                    reason = "Q-Learning Brain chose Cloud LLM. Budget is available."
                else:
                    model_target = "LOCAL_SLM"
                    reason = "Q-Learning Brain chose Local SLM (or insufficient budget for Cloud override)."

            routing_decision = {
                "model_target": model_target,
                "reason": reason,
                "severity": severity,
                "complexity": complexity,
                "budget_usd": budget.get("max_spend_usd", 0.0),
                "token_limit": budget.get("max_tokens", 0)
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
