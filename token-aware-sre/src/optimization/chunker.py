try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    class RecursiveCharacterTextSplitter:
        """Fallback character text splitter when langchain is unavailable."""
        def __init__(self, chunk_size=1000, chunk_overlap=150, length_function=len, is_separator_regex=False):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text: str) -> list:
            if not text:
                return []
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                chunks.append(text[start:end])
                if end == len(text):
                    break
                start += max(1, self.chunk_size - self.chunk_overlap)
            return chunks
import logging

class LogChunker:
    """Semantically chunks massive raw logs into safely overlapping blocks.
    
    This prevents contextual tearing (e.g., splitting a stack trace in half) 
    by prioritizing double newlines, then single newlines, then spaces.

    Attributes:
        logger (logging.Logger): Logger for the chunker.
        splitter (RecursiveCharacterTextSplitter): The LangChain text splitter instance.
    """
    def __init__(self, chunk_size=1000, chunk_overlap=150):
        self.logger = logging.getLogger(__name__)
        try:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize LogChunker: {e}")
            self.splitter = None

    def chunk_log(self, text: str) -> list:
        """Splits a large string into a list of smaller strings.

        Args:
            text (str): The massive raw log string.

        Returns:
            list: A list of string chunks. Returns a list with the original text if chunking fails.
        """
        if not text:
            return []
            
        if not self.splitter:
            self.logger.warning("Splitter not initialized. Returning raw text as single chunk.")
            return [text]
            
        try:
            chunks = self.splitter.split_text(text)
            self.logger.info(f"Split raw log into {len(chunks)} chunks.")
            return chunks
        except Exception as e:
            self.logger.error(f"Chunking failed: {e}")
            return [text]

if __name__ == "__main__":
    chunker = LogChunker(chunk_size=50, chunk_overlap=10)
    sample = "Traceback (most recent call last):\n  File 'main.py', line 1\n    print(x)\nNameError: name 'x' is not defined"
    print(chunker.chunk_log(sample))
