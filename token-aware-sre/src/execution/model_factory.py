import os
import logging
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

class ModelFactory:
    """
    Instantiates the appropriate Language Model based on the Phase 2 routing decision.
    """
    def __init__(self, local_model_name="qwen", cloud_model_name="gemini-1.5-pro"):
        self.logger = logging.getLogger(__name__)
        self.local_model_name = local_model_name
        self.cloud_model_name = cloud_model_name

    def get_model(self, routing_decision: str):
        """
        Returns a LangChain chat model instance.
        routing_decision: either 'LOCAL_SLM' or 'CLOUD_LLM'
        """
        if routing_decision == "CLOUD_LLM":
            self.logger.info(f"Instantiating Cloud LLM: {self.cloud_model_name}")
            # Requires GOOGLE_API_KEY environment variable to be set
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                self.logger.warning("GOOGLE_API_KEY is not set. Falling back to Local SLM.")
                return self._get_local_model()
            
            return ChatGoogleGenerativeAI(
                model=self.cloud_model_name,
                temperature=0.2, # Low temperature for deterministic SRE responses
                google_api_key=api_key
            )
        else:
            return self._get_local_model()

    def _get_local_model(self):
        self.logger.info(f"Instantiating Local SLM: Ollama ({self.local_model_name})")
        # Ensure Ollama is running locally (e.g., http://localhost:11434)
        return ChatOllama(
            model=self.local_model_name,
            temperature=0.2
        )
