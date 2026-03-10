import os
import requests
from typing import List

class EmbeddingService:
    def __init__(self, provider: str = "ollama", model: str = "mxbai-embed-large"):
        self.provider = provider
        self.model = model
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def get_embedding(self, text: str) -> List[float]:
        if self.provider == "ollama":
            try:
                response = requests.post(
                    self.ollama_url,
                    json={"model": self.model, "prompt": text},
                    timeout=10
                )
                response.raise_for_status()
                return response.json()["embedding"]
            except Exception as e:
                print(f"Ollama embedding failed: {e}. Falling back to mock.")
                return [0.1] * 1536 # Mock fallback
        
        elif self.provider == "openai":
            # Placeholder for OpenAI embedding call
            return [0.1] * 1536
            
        return [0.1] * 1536
