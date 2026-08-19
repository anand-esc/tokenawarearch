from transformers import pipeline
import logging
import torch

class ChatHistorySummarizer:
    """Condenses raw chat logs or historical context using a local summarization model.
    
    This component uses a lightweight HuggingFace model to summarize noisy Slack 
    or Microsoft Teams incident chat histories into concise paragraphs, saving 
    downstream token budget.

    Attributes:
        logger (logging.Logger): Logger for the summarizer.
        summarizer (pipeline): HuggingFace summarization pipeline.
    """
    def __init__(self, model_name="facebook/bart-large-cnn"):
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Loading local summarization model: {model_name}")
        
        # Hardware acceleration check (GPU vs CPU)
        device = 0 if torch.cuda.is_available() else -1
        
        try:
            # Load the HuggingFace pipeline for summarization
            self.summarizer = pipeline("summarization", model=model_name, device=device)
        except Exception as e:
            self.logger.error(f"Failed to load summarizer model: {e}")
            self.summarizer = None

    def summarize(self, chat_history: str) -> str:
        """Summarizes the input chat history string.

        Args:
            chat_history (str): The raw incident chat history.

        Returns:
            str: The summarized text, or the original text if it was too short or if an error occurred.
        """
        if not chat_history or len(chat_history.strip()) < 100:
            # If the history is already tiny, don't waste compute/tokens summarizing it.
            return chat_history
            
        if not self.summarizer:
            self.logger.warning("Summarizer pipeline not initialized. Returning raw text.")
            return chat_history

        try:
            # We strictly limit the output to save downstream tokens
            summary = self.summarizer(chat_history, max_length=150, min_length=40, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            self.logger.error(f"Summarization failed during inference: {e}")
            # Safe fallback
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
