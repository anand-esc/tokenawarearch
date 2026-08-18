import logging
try:
    from llmlingua import PromptCompressor
except ImportError:
    PromptCompressor = None

class LogCompressor:
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing LLMLingua prompt compressor...")
        # We use TinyLlama for fast, local compression. It requires minimal VRAM.
        try:
            if PromptCompressor:
                self.compressor = PromptCompressor(
                    model_name=model_name,
                    device_map="auto"
                )
            else:
                self.compressor = None
                self.logger.warning("llmlingua not installed. Compressor will bypass.")
        except Exception as e:
            self.logger.error(f"Failed to load LLMLingua: {e}")
            self.compressor = None

    def compress(self, context: str) -> str:
        """
        Compresses the final context payload before sending to Phase 2 (Router).
        Removes stopwords and irrelevant tokens while preserving semantics.
        """
        if not context or len(context) < 200:
            return context
            
        if self.compressor is None:
            self.logger.warning("Compressor not loaded. Returning uncompressed text.")
            return context
            
        try:
            # We target a 2x-3x compression ratio to save API budget
            results = self.compressor.compress_prompt(
                context,
                instruction="Extract the critical error details and context.",
                question="What is the root cause of this incident?",
                target_token=500,
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
            self.logger.error(f"Compression failed: {e}")
            return context

if __name__ == "__main__":
    compressor = LogCompressor()
    print("Compressor initialized.")
