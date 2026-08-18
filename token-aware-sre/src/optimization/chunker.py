from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

class LogChunker:
    def __init__(self, chunk_size=1000, chunk_overlap=150):
        self.logger = logging.getLogger(__name__)
        # The Recursive text splitter is ideal for logs. It tries to split on double newlines, 
        # then single newlines, then spaces, keeping stack traces together as much as possible.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_log(self, text: str) -> list:
        """
        Breaks massive stack traces into safely overlapping blocks.
        """
        if not text:
            return []
            
        chunks = self.splitter.split_text(text)
        self.logger.info(f"Split raw log into {len(chunks)} chunks.")
        return chunks

if __name__ == "__main__":
    chunker = LogChunker(chunk_size=50, chunk_overlap=10)
    sample = "Traceback (most recent call last):\n  File 'main.py', line 1\n    print(x)\nNameError: name 'x' is not defined"
    print(chunker.chunk_log(sample))
