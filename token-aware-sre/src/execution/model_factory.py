import os
import logging
from typing import Optional, Any
try:
    from langchain_community.chat_models import ChatOllama
except ImportError:
    ChatOllama = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

from config import Config

class ModelFactory:
    """Instantiates the appropriate Language Model for Phase 3.
    
    Acts as a LangChain factory to seamlessly hot-swap between a local 
    Ollama instance (for SLM) and Google Gemini (for Cloud LLM) based 
    on the Phase 2 routing decision.

    Attributes:
        logger (logging.Logger): Logger for the factory.
        local_model_name (str): The name of the local Ollama model (e.g., 'qwen').
        cloud_model_name (str): The name of the cloud Gemini model.
    """
    def __init__(self, local_model_name: Optional[str] = None, cloud_model_name: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.local_model_name = local_model_name if local_model_name else Config.LOCAL_SLM_NAME
        self.cloud_model_name = cloud_model_name if cloud_model_name else Config.CLOUD_LLM_NAME
        self.temperature = Config.MODEL_TEMPERATURE

    def get_model(self, routing_decision: str) -> Any:
        """Returns a configured LangChain chat model instance.

        Args:
            routing_decision (str): Either 'LOCAL_SLM' or 'CLOUD_LLM'.

        Returns:
            BaseChatModel: A LangChain chat model object ready for inference.
        """
        if routing_decision == "CLOUD_LLM":
            self.logger.info(f"Instantiating Cloud LLM: {self.cloud_model_name}")
            api_key = os.environ.get("GOOGLE_API_KEY")
            
            if not api_key or not ChatGoogleGenerativeAI:
                self.logger.warning("GOOGLE_API_KEY is not set or SDK missing. Falling back to Local SLM.")
                return self._get_local_model()
            
            try:
                return ChatGoogleGenerativeAI(
                    model=self.cloud_model_name,
                    temperature=self.temperature, # Low temperature for deterministic SRE responses
                    google_api_key=api_key
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize Cloud LLM: {e}. Falling back to Local.")
                return self._get_local_model()
        else:
            return self._get_local_model()

    def _get_local_model(self) -> Any:
        """Internal helper to instantiate the local Ollama model."""
        self.logger.info(f"Instantiating Local SLM: Ollama ({self.local_model_name})")
        if not ChatOllama:
            self.logger.warning("ChatOllama not found. Returning Mock Model.")
            return "MOCK_LOCAL_SLM"
            
        try:
            return ChatOllama(
                model=self.local_model_name,
                temperature=self.temperature
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Local SLM: {e}")
            raise RuntimeError("Critical Error: Unable to instantiate any model.") from e
