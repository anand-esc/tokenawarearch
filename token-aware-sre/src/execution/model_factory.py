import os
import logging
from typing import Optional, Any
try:
    from langchain_ollama import ChatOllama
except ImportError:
    try:
        from langchain_community.chat_models import ChatOllama
    except ImportError:
        ChatOllama = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        ChatOpenAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

from config import Config

class ModelFactory:
    """Instantiates the appropriate Language Model for Phase 3.
    
    Acts as a LangChain factory to seamlessly hot-swap between a local 
    Ollama instance (for SLM) and Cloud LLMs (NVIDIA Nemotron, OpenAI, or Google Gemini)
    based on the Phase 2 routing decision.

    Attributes:
        logger (logging.Logger): Logger for the factory.
        local_model_name (str): The name of the local Ollama model (e.g., 'qwen2.5').
        cloud_model_name (str): The name of the cloud model (e.g., 'nvidia/llama-3.1-nemotron-70b-instruct' or 'gemini-1.5-pro').
    """
    def __init__(self, local_model_name: Optional[str] = None, cloud_model_name: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.local_model_name = local_model_name if local_model_name else Config.LOCAL_SLM_NAME
        self.cloud_model_name = cloud_model_name if cloud_model_name else Config.CLOUD_LLM_NAME
        self.temperature = Config.MODEL_TEMPERATURE

    def get_model(self, routing_decision: str, runtime_config: dict = None) -> Any:
        """Returns a configured LangChain chat model instance.

        Args:
            routing_decision (str): Either 'LOCAL_SLM' or 'CLOUD_LLM'.
            runtime_config (dict): Runtime configurations (api_key, endpoint, etc).

        Returns:
            BaseChatModel: A LangChain chat model object ready for inference.
        """
        runtime_config = runtime_config or {}
        
        if routing_decision == "CLOUD_LLM":
            # Use runtime config first, fallback to class attr
            cloud_model_name = runtime_config.get("llm_name") or self.cloud_model_name
            endpoint = (runtime_config.get("llm_endpoint") or "").strip()
            api_key = runtime_config.get("llm_api_key") or os.environ.get("NVIDIA_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            
            if not api_key:
                self.logger.warning("No Cloud LLM API key provided. Falling back to Local SLM.")
                return self._get_local_model(runtime_config)

            # Check if using NVIDIA Nemotron or OpenAI-compatible endpoint
            is_nvidia = (
                api_key.startswith("nvapi-")
                or "nvidia" in cloud_model_name.lower()
                or "nemotron" in cloud_model_name.lower()
                or "nvidia" in endpoint.lower()
            )
            is_gemini = (
                api_key.startswith("AIza")
                or "gemini" in cloud_model_name.lower()
            )

            if is_nvidia or (ChatOpenAI and not is_gemini):
                self.logger.info(f"Instantiating NVIDIA/OpenAI LLM: {cloud_model_name}")
                base_url = endpoint if endpoint else ("https://integrate.api.nvidia.com/v1" if is_nvidia else None)
                try:
                    return ChatOpenAI(
                        model=cloud_model_name,
                        temperature=self.temperature,
                        api_key=api_key,
                        base_url=base_url,
                        max_tokens=2048
                    )
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenAI/NVIDIA LLM: {e}. Trying Gemini or Local.")

            if is_gemini and ChatGoogleGenerativeAI:
                self.logger.info(f"Instantiating Google Gemini LLM: {cloud_model_name}")
                try:
                    return ChatGoogleGenerativeAI(
                        model=cloud_model_name,
                        temperature=self.temperature,
                        google_api_key=api_key
                    )
                except Exception as e:
                    self.logger.error(f"Failed to initialize Cloud LLM: {e}. Falling back to Local.")
                    return self._get_local_model(runtime_config)

            return self._get_local_model(runtime_config)
        else:
            return self._get_local_model(runtime_config)

    def _get_local_model(self, runtime_config: dict) -> Any:
        """Internal helper to instantiate the local Ollama model."""
        local_model_name = runtime_config.get("slm_name") or self.local_model_name
        base_url = runtime_config.get("slm_endpoint") or "http://localhost:11434"
        
        self.logger.info(f"Instantiating Local SLM: Ollama ({local_model_name}) at {base_url}")
        if not ChatOllama:
            self.logger.warning("ChatOllama not found. Returning Mock Model.")
            return "MOCK_LOCAL_SLM"
            
        try:
            return ChatOllama(
                model=local_model_name,
                temperature=self.temperature,
                base_url=base_url
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Local SLM: {e}")
            raise RuntimeError("Critical Error: Unable to instantiate any model.") from e
