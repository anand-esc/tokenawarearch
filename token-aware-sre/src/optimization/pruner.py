from sentence_transformers import SentenceTransformer, util
import logging

class ContextPruner:
    def __init__(self, model_name='all-MiniLM-L6-v2', similarity_threshold=0.85):
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Loading local embedding model: {model_name}")
        # This is a super fast, small embedding model that converts sentences into numerical vectors
        self.model = SentenceTransformer(model_name)
        
        # If a chunk is >= 85% similar to an existing chunk, we drop it to save tokens
        self.similarity_threshold = similarity_threshold

    def prune(self, chunks: list) -> list:
        """
        Takes a list of text chunks, embeds them, and drops highly similar/redundant ones.
        (e.g. repeated Java NullPointerExceptions that flooded the logs)
        """
        if not chunks or len(chunks) <= 1:
            return chunks

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
