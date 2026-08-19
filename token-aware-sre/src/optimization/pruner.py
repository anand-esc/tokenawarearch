from sentence_transformers import SentenceTransformer, util
import logging

class ContextPruner:
    """Removes semantically redundant log chunks to save token space.
    
    Uses a fast local embedding model (`all-MiniLM-L6-v2`) to convert text chunks 
    into vectors. If a chunk's cosine similarity exceeds the threshold compared 
    to already kept chunks, it is discarded (e.g., pruning 100 identical Java NullPointerExceptions).

    Attributes:
        logger (logging.Logger): Logger for the pruner.
        model (SentenceTransformer): The local embedding model.
        similarity_threshold (float): Threshold above which chunks are considered redundant (0.0 to 1.0).
    """
    def __init__(self, model_name='all-MiniLM-L6-v2', similarity_threshold=0.85):
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Loading local embedding model: {model_name}")
        self.similarity_threshold = similarity_threshold
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            self.model = None

    def prune(self, chunks: list) -> list:
        """Embeds and filters out semantically identical text chunks.

        Args:
            chunks (list): A list of text strings representing the log blocks.

        Returns:
            list: A pruned list of text strings containing only novel information.
        """
        if not chunks or len(chunks) <= 1:
            return chunks

        if not self.model:
            self.logger.warning("Embedding model not loaded. Skipping pruning.")
            return chunks

        try:
            # Compute embeddings for all chunks in one batch
            embeddings = self.model.encode(chunks, convert_to_tensor=True)
            
            kept_indices = [0] # We always keep the very first chunk (usually contains the error header)
            
            for i in range(1, len(chunks)):
                current_emb = embeddings[i].unsqueeze(0)
                kept_embs = embeddings[kept_indices]
                
                # Calculate cosine similarities against all chunks we've decided to keep so far
                cos_scores = util.cos_sim(current_emb, kept_embs)[0]
                
                # If the maximum similarity is below our threshold, it contains novel information. Keep it.
                if cos_scores.max().item() < self.similarity_threshold:
                    kept_indices.append(i)
                else:
                    self.logger.debug(f"Dropped chunk {i} due to high similarity.")
                    
            # Return only the chunks that survived the pruning
            return [chunks[idx] for idx in kept_indices]
            
        except Exception as e:
            self.logger.error(f"Pruning failed during embedding calculation: {e}")
            return chunks # Safe fallback: return everything

if __name__ == "__main__":
    pruner = ContextPruner()
    sample_chunks = [
        "Connection refused to database 10.0.0.1",
        "Connection refused to database 10.0.0.1", # Exact duplicate
        "Timeout while trying to reach redis server", # Novel
        "Failed to connect to database at 10.0.0.1" # Semantic duplicate
    ]
    print("Original count:", len(sample_chunks))
    pruned = pruner.prune(sample_chunks)
    print("Pruned count:", len(pruned))
    print("Pruned:", pruned)
