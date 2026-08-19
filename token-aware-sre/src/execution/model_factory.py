import os
import logging
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

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
    def __init__(self, local_model_name="qwen", cloud_model_name="gemini-1.5-pro"):
        self.logger = logging.getLogger(__name__)
        self.local_model_name = local_model_name
        self.cloud_model_name = cloud_model_name

    def get_model(self, routing_decision: str):
        """Returns a configured LangChain chat model instance.

        Args:
            routing_decision (str): Either 'LOCAL_SLM' or 'CLOUD_LLM'.

        Returns:
            BaseChatModel: A LangChain chat model object ready for inference.
        """
        if routing_decision == "CLOUD_LLM":
            self.logger.info(f"Instantiating Cloud LLM: {self.cloud_model_name}")
            api_key = os.environ.get("GOOGLE_API_KEY")
            
            if not api_key:
                self.logger.warning("GOOGLE_API_KEY is not set. Falling back to Local SLM to prevent crash.")
                return self._get_local_model()
            
            try:
                return ChatGoogleGenerativeAI(
                    model=self.cloud_model_name,
                    temperature=0.2, # Low temperature for deterministic SRE responses
                    google_api_key=api_key
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize Cloud LLM: {e}. Falling back to Local.")
                return self._get_local_model()
        else:
            return self._get_local_model()

    def _get_local_model(self):
        """Internal helper to instantiate the local Ollama model."""
        self.logger.info(f"Instantiating Local SLM: Ollama ({self.local_model_name})")
        try:
            return ChatOllama(
                model=self.local_model_name,
                temperature=0.2
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Local SLM: {e}")
            raise RuntimeError("Critical Error: Unable to instantiate any model.") from e
