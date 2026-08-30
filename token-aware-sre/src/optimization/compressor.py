import logging
try:
    from llmlingua import PromptCompressor
except ImportError:
    PromptCompressor = None

from config import Config

class LogCompressor:
    """Uses LLMLingua to compress the final context payload before routing.
    
    This component removes stopwords and semantically irrelevant tokens while 
    preserving the core meaning of the incident, often achieving 2x-3x 
    compression ratios to drastically save on API costs.

    Attributes:
        logger (logging.Logger): Logger for the compressor.
        compressor (PromptCompressor): LLMLingua compressor instance.
    """
    def __init__(self, model_name: str = None):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name if model_name else Config.COMPRESSOR_MODEL
        self.target_tokens = Config.COMPRESSION_TARGET_TOKENS
        self.logger.info("Initializing LLMLingua prompt compressor...")
        
        try:
            if PromptCompressor:
                # We use TinyLlama for fast, local compression. It requires minimal VRAM.
                self.compressor = PromptCompressor(
                    model_name=self.model_name,
                    device_map="auto"
                )
            else:
                self.compressor = None
                self.logger.warning("llmlingua not installed. Compressor will bypass.")
        except Exception as e:
            self.logger.error(f"Failed to load LLMLingua: {e}")
            self.compressor = None

    def compress(self, context: str) -> str:
        """Compresses the context payload.

        Args:
            context (str): The pruned, assembled log and chat history string.

        Returns:
            str: The highly compressed text prompt ready for the Phase 2 router.
        """
        if not context or len(context) < 200:
            return context
            
        if self.compressor is None:
            self.logger.warning("Compressor not loaded. Returning uncompressed text.")
            return context
            
        try:
            results = self.compressor.compress_prompt(
                context,
                instruction="Extract the critical error details and context.",
                question="What is the root cause of this incident?",
                target_token=self.target_tokens,
                condition_compare=True,
                condition_in_question='after',
                rank_method='longllmlingua'
            )
            compressed_prompt = results.get('compressed_prompt', context)
            
            # Log metrics for debugging
            origin_tokens = results.get('origin_tokens', 0)
            compressed_tokens = results.get('compressed_tokens', 0)
            self.logger.info(f"Compressed from {origin_tokens} to {compressed_tokens} tokens.")
            
            return compressed_prompt
        except Exception as e:
            self.logger.error(f"Compression failed during inference: {e}")
            return context # Graceful fallback

if __name__ == "__main__":
    compressor = LogCompressor()
    print("Compressor initialized.")
