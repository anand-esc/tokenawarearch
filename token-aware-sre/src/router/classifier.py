import logging
from transformers import pipeline

class IncidentClassifier:
    """
    Analyzes compressed incident payloads to score Severity and Complexity.
    Uses zero-shot classification to avoid external API costs.
    """
    def __init__(self, model_name="cross-encoder/nli-distilroberta-base"):
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Loading local classification model: {model_name}")
        # Using a fast model for zero-shot classification to evaluate incident text
        try:
            self.classifier = pipeline("zero-shot-classification", model=model_name)
        except Exception as e:
            self.logger.error(f"Failed to load classifier: {e}")
            self.classifier = None

    def classify(self, payload: str) -> dict:
        """
        Returns a dictionary with 'severity' (1-10) and 'complexity' (1-10).
        """
        if not payload or not self.classifier:
            return {"severity": 5, "complexity": 5} # Fallback defaults

        # Define labels to gauge severity
        severity_labels = [
            "critical system failure", 
            "high impact outage", 
            "moderate degradation", 
            "low priority warning", 
            "informational"
        ]
        # Define labels to gauge complexity
        complexity_labels = [
            "requires deep debugging across multiple services", 
            "requires moderate investigation", 
            "simple known issue", 
            "trivial fix"
        ]

        try:
            sev_result = self.classifier(payload, severity_labels)
            comp_result = self.classifier(payload, complexity_labels)

            severity_score = self._map_to_score(sev_result['labels'][0], "severity")
            complexity_score = self._map_to_score(comp_result['labels'][0], "complexity")

            return {
                "severity": severity_score,
                "complexity": complexity_score,
                "primary_severity_label": sev_result['labels'][0],
                "primary_complexity_label": comp_result['labels'][0]
            }

        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            return {"severity": 5, "complexity": 5}

    def _map_to_score(self, label: str, category: str) -> int:
        if category == "severity":
            mapping = {
                "critical system failure": 10,
                "high impact outage": 8,
                "moderate degradation": 5,
                "low priority warning": 3,
                "informational": 1
            }
            return mapping.get(label, 5)
        elif category == "complexity":
            mapping = {
                "requires deep debugging across multiple services": 10,
                "requires moderate investigation": 7,
                "simple known issue": 4,
                "trivial fix": 2
            }
            return mapping.get(label, 5)
        return 5

if __name__ == "__main__":
    classifier = IncidentClassifier()
    sample = "Database connection timeout across all production web servers."
    print(classifier.classify(sample))
