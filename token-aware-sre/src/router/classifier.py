import os
import logging
from typing import Dict, Optional, Any
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from config import Config

class IncidentClassifier:
    """Evaluates incident payloads to score Severity and Complexity locally.
    
    Uses our fine-tuned DistilRoBERTa regression model to predict the optimal 
    1-10 scores based on raw token patterns.
    """
    def __init__(self, model_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.model_path = model_path or (Config.CLASSIFIER_MODEL if Config.CLASSIFIER_MODEL != "none" else None)
        self.tokenizer = None
        self.model = None

        if self.model_path and self.model_path.lower() != "none":
            self.logger.info(f"Loading proprietary fine-tuned classifier from: {self.model_path}")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
                self.model.eval() # Set to evaluation mode
            except Exception as e:
                self.logger.error(f"Failed to load fine-tuned model: {e}")
                self.tokenizer = None
                self.model = None
        else:
            self.logger.info("No local fine-tuned model path provided; using zero-shot/heuristic fallback.")

    def classify(self, payload: str) -> Dict[str, Any]:
        """Classifies the incident payload to predict Severity and Complexity."""
        if not payload or not self.model or not self.tokenizer:
            self.logger.warning("Classifier not loaded or payload empty. Falling back to heuristic.")
            return {"severity": 5, "complexity": 5}

        try:
            # Tokenize input
            inputs = self.tokenizer(payload, return_tensors="pt", truncation=True, padding=True, max_length=512)
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Extract the two regression logits [Severity, Complexity]
            predictions = outputs.logits.squeeze().tolist()
            
            # Ensure predictions are bounds-checked between 1 and 10
            severity = max(1, min(10, int(round(predictions[0]))))
            complexity = max(1, min(10, int(round(predictions[1]))))

            return {
                "severity": severity,
                "complexity": complexity
            }

        except Exception as e:
            self.logger.error(f"Classification failed during inference: {e}")
            return {"severity": 5, "complexity": 5}

if __name__ == "__main__":
    classifier = IncidentClassifier()
    sample = "@@@ Node worker-pool-3 transitioned to NotReady. Kubelet logs show 'PLEG is not healthy' @@@"
    print(classifier.classify(sample))
