import os

class Config:
    """Centralized configuration for the Token-Aware Multi-Agent Architecture."""
    
    # ---------------------------------------------------------
    # Optimization Funnel (Phase 1)
    # ---------------------------------------------------------
    COMPRESSOR_MODEL = os.getenv("COMPRESSOR_MODEL", "none")
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
    COMPRESSION_TARGET_TOKENS = int(os.getenv("COMPRESSION_TARGET_TOKENS", "500"))
    
    # ---------------------------------------------------------
    # Classifier & Router (Phase 2)
    # ---------------------------------------------------------
    CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", "none")
    MAX_API_BUDGET = float(os.getenv("MAX_API_BUDGET", "0.05"))  # Max USD per incident
    
    # ---------------------------------------------------------
    # Model Factory (Phase 3)
    # ---------------------------------------------------------
    LOCAL_SLM_NAME = os.getenv("LOCAL_SLM_NAME", "qwen")
    CLOUD_LLM_NAME = os.getenv("CLOUD_LLM_NAME", "gemini-1.5-pro")
    MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
    
    # ---------------------------------------------------------
    # Q-Learning (Phase 4)
    # ---------------------------------------------------------
    Q_LEARNING_ALPHA = float(os.getenv("Q_LEARNING_ALPHA", "0.1"))
    Q_LEARNING_GAMMA = float(os.getenv("Q_LEARNING_GAMMA", "0.9"))
    Q_LEARNING_EPSILON = float(os.getenv("Q_LEARNING_EPSILON", "0.2"))
    
    # ---------------------------------------------------------
    # Risk Assessor
    # ---------------------------------------------------------
    SAFE_RISK_THRESHOLD = int(os.getenv("SAFE_RISK_THRESHOLD", "30"))

    @classmethod
    def validate(cls):
        """Validates critical configurations at startup."""
        if cls.SIMILARITY_THRESHOLD <= 0 or cls.SIMILARITY_THRESHOLD > 1:
            raise ValueError("SIMILARITY_THRESHOLD must be between 0 and 1.")
        if cls.SAFE_RISK_THRESHOLD < 0 or cls.SAFE_RISK_THRESHOLD > 100:
            raise ValueError("SAFE_RISK_THRESHOLD must be between 0 and 100.")
