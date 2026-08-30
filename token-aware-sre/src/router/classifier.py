import logging
from typing import Dict, Optional, Any
from transformers import pipeline
from config import Config

class IncidentClassifier:
    """Evaluates incident payloads to score Severity and Complexity locally.
    
    Uses zero-shot classification via a fast local model (`cross-encoder/nli-distilroberta-base`) 
    to triage the incident without spending any external API budget.

    Attributes:
        logger (logging.Logger): Logger for the classifier.
        classifier (pipeline): HuggingFace zero-shot classification pipeline.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name if model_name else Config.CLASSIFIER_MODEL
        self.logger.info(f"Loading local classification model: {self.model_name}")
        try:
            self.classifier = pipeline("zero-shot-classification", model=self.model_name)
        except Exception as e:
            self.logger.error(f"Failed to load classifier: {e}")
            self.classifier = None

    def classify(self, payload: str) -> Dict[str, Any]:
        """Classifies the compressed incident payload.

        Args:
            payload (str): The compressed incident text from Phase 1.

        Returns:
            dict: A dictionary containing integer scores (1-10) for 'severity' and 'complexity', 
                  as well as the primary labels that matched.
        """
        if not payload or not self.classifier:
            self.logger.warning("Classifier not loaded or payload empty. Returning defaults.")
            return {"severity": 5, "complexity": 5}

        severity_labels = [
            "critical system failure", 
            "high impact outage", 
            "moderate degradation", 
            "low priority warning", 
            "informational"
        ]
        
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
            self.logger.error(f"Classification failed during inference: {e}")
            return {"severity": 5, "complexity": 5}

    def _map_to_score(self, label: str, category: str) -> int:
        """Maps a textual classification label to a numerical score (1-10)."""
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
