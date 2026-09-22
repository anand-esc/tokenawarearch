import pytest
from unittest.mock import patch, MagicMock
from src.router.classifier import IncidentClassifier

@patch('src.router.classifier.AutoModelForSequenceClassification.from_pretrained')
@patch('src.router.classifier.AutoTokenizer.from_pretrained')
def test_classifier_mocked_inference(mock_tokenizer, mock_model):
    # Setup Mocks
    mock_model_instance = MagicMock()
    mock_outputs = MagicMock()
    mock_outputs.logits.squeeze.return_value.tolist.return_value = [8.2, 5.7] # Mock predictions
    mock_model_instance.return_value = mock_outputs
    mock_model.return_value = mock_model_instance
    
    classifier = IncidentClassifier(model_path="dummy_path")
    result = classifier.classify("mock payload")
    
    assert result["severity"] == 8
    assert result["complexity"] == 6

def test_classifier_empty_payload_fallback():
    classifier = IncidentClassifier(model_path="dummy_path")
    classifier.model = None # Force fallback
    result = classifier.classify("")
    
    assert result["severity"] == 5
    assert result["complexity"] == 5
