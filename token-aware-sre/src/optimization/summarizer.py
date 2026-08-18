from transformers import pipeline
import logging
import torch

class ChatHistorySummarizer:
    def __init__(self, model_name="facebook/bart-large-cnn"):
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Loading local summarization model: {model_name}")
        
        # Hardware acceleration check (GPU vs CPU)
        device = 0 if torch.cuda.is_available() else -1
        
        # Load the HuggingFace pipeline for summarization
        self.summarizer = pipeline("summarization", model=model_name, device=device)

    def summarize(self, chat_history: str) -> str:
        """
        Condenses raw chat logs or historical troubleshooting context.
        """
        if not chat_history or len(chat_history.strip()) < 100:
            # If the history is already tiny, don't waste compute/tokens summarizing it.
            return chat_history
            
        try:
            # We strictly limit the output to save downstream tokens (Phase 2 token budgeting)
            summary = self.summarizer(chat_history, max_length=150, min_length=40, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            self.logger.error(f"Summarization failed: {e}")
            return chat_history

if __name__ == "__main__":
    # Quick manual test
    summarizer = ChatHistorySummarizer()
    sample_text = (
        "User: The server just spiked to 100% CPU. What is going on? "
        "Agent: I checked the logs and it seems the redis cache went down. "
        "User: Can we restart it? "
        "Agent: Restarting redis cache now. "
        "User: Still seeing spikes in the web server pods, maybe they are queued up."
    ) * 5  # Make it long enough to trigger summarization
    
    print("Original Length:", len(sample_text))
    print("Summary:", summarizer.summarize(sample_text))
