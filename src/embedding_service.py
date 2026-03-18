from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger("wiki-embedding")

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded embedding model: {model_name}")

    def get_embedding(self, text: str):
        """Generates an embedding for the given text."""
        return self.model.encode(text).tolist()

    def chunk_markdown(self, text: str, chunk_size: int = 500, overlap: int = 50):
        """Simplistic Markdown chunking by paragraphs or sentence count."""
        if not text:
            return []
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += p + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = p + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
