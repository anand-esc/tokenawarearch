import logging
from .rewriter import LogRewriter
from .summarizer import ChatHistorySummarizer
from .chunker import LogChunker
from .pruner import ContextPruner
from .compressor import LogCompressor

class OptimizationFunnel:
    """Phase 1 Pipeline (The Funnel) for reducing incident payload size.

    This class orchestrates the sequential execution of Rewriting, Summarization, 
    Chunking, Pruning, and Compression to massively reduce the token count of 
    incoming incident logs and chat histories.

    Attributes:
        logger (logging.Logger): Logger for the funnel.
        rewriter (LogRewriter): Component to normalize raw logs.
        summarizer (ChatHistorySummarizer): Component to summarize chat histories.
        chunker (LogChunker): Component to semantically chunk logs.
        pruner (ContextPruner): Component to remove irrelevant chunks.
        compressor (LogCompressor): Component to execute LLMLingua compression.
    """
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("Phase1_Funnel")
        
        self.logger.info("Initializing Phase 1 Funnel components...")
        try:
            self.rewriter = LogRewriter()
            self.summarizer = ChatHistorySummarizer()
            self.chunker = LogChunker()
            self.pruner = ContextPruner()
            self.compressor = LogCompressor()
        except Exception as e:
            self.logger.error(f"Failed to initialize Phase 1 components: {e}")
            raise RuntimeError("Phase 1 initialization failed") from e
            
        self.logger.info("Phase 1 Funnel initialized successfully.")

    def process(self, raw_incident: str, chat_history: str = "") -> str:
        """Main entry point for Phase 1 optimization.

        Condenses raw incident data and chat history into a minimal payload 
        safe for LLM ingestion.

        Args:
            raw_incident (str): The raw incident log, webhook payload, or stack trace.
            chat_history (str, optional): Accompanying Slack/Teams chat history. Defaults to "".

        Returns:
            str: The highly compressed, semantically dense payload string.
        """
        try:
            self.logger.info("--- Step 1 & 2: Rewriting and Summarization ---")
            normalized_log = self.rewriter.rewrite(raw_incident)
            summary = self.summarizer.summarize(chat_history)
            
            # Combine the context
            if summary.strip():
                combined_context = f"CHAT HISTORY SUMMARY:\n{summary}\n\nINCIDENT LOG:\n{normalized_log}"
            else:
                combined_context = f"INCIDENT LOG:\n{normalized_log}"
                
            self.logger.info("--- Step 3: Semantic Chunking ---")
            chunks = self.chunker.chunk_log(combined_context)
            
            self.logger.info("--- Step 4: Context Pruning ---")
            pruned_chunks = self.pruner.prune(chunks)
            
            # Re-assemble pruned chunks
            pruned_text = "\n...\n".join(pruned_chunks)
            
            self.logger.info("--- Step 5: Prompt Compression ---")
            final_payload = self.compressor.compress(pruned_text)
            
            self.logger.info("Phase 1 processing complete.")
            return final_payload
        except Exception as e:
            self.logger.error(f"Critical error during Phase 1 processing: {e}")
            # Fallback gracefully to raw incident if the entire pipeline fails
            return f"PIPELINE_ERROR: {e}\n\nRAW_LOG_FALLBACK:\n{raw_incident}"

if __name__ == "__main__":
    funnel = OptimizationFunnel()
    print("Funnel pipeline ready.")
