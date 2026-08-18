import logging
from .rewriter import LogRewriter
from .summarizer import ChatHistorySummarizer
from .chunker import LogChunker
from .pruner import ContextPruner
from .compressor import LogCompressor

class OptimizationFunnel:
    """
    Phase 1 Pipeline (The Funnel).
    Executes Rewriting, Summarization, Chunking, Pruning, and Compression sequentially.
    """
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("Phase1_Funnel")
        
        self.logger.info("Initializing Phase 1 Funnel components...")
        self.rewriter = LogRewriter()
        self.summarizer = ChatHistorySummarizer()
        self.chunker = LogChunker()
        self.pruner = ContextPruner()
        self.compressor = LogCompressor()
        self.logger.info("Phase 1 Funnel initialized successfully.")

    def process(self, raw_incident: str, chat_history: str = "") -> str:
        """
        Main entry point for Phase 1. Condenses raw incident data and chat history into a minimal payload.
        """
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

if __name__ == "__main__":
    funnel = OptimizationFunnel()
    print("Funnel pipeline ready.")
