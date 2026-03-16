import os
import requests
import json
from typing import List

class EmbeddingService:
    def __init__(self, provider: str = "ollama", model: str = "mxbai-embed-large"):
        self.provider = provider
        self.model = model
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/embeddings")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_url = "https://api.openai.com/v1/embeddings"
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"

    def get_embedding(self, text: str) -> List[float]:
        # Simple text cleaning before embedding
        text = text.strip()
        if not text:
            return [0.0] * 1536 # Return empty vector for empty strings
            
        if self.provider == "ollama":
            try:
                response = requests.post(
                    self.ollama_url,
                    json={"model": self.model, "prompt": text},
                    timeout=15
                )
                response.raise_for_status()
                return response.json()["embedding"]
            except Exception as e:
                print(f"Ollama embedding failed: {e}. Falling back to mock.")
                return self._mock_embedding()
        
        elif self.provider == "openai":
            if not self.openai_api_key:
                return self._mock_embedding()
            try:
                headers = {"Authorization": f"Bearer {self.openai_api_key}"}
                response = requests.post(
                    self.openai_url,
                    headers=headers,
                    json={"model": "text-embedding-3-small", "input": text},
                    timeout=15
                )
                response.raise_for_status()
                return response.json()["data"][0]["embedding"]
            except Exception as e:
                print(f"OpenAI embedding failed: {e}. Falling back to mock.")
                return self._mock_embedding()

        elif self.provider == "gemini":
            if not self.gemini_api_key:
                return self._mock_embedding()
            try:
                model = self.model or "text-embedding-004"
                url = f"{self.gemini_url.format(model=model)}?key={self.gemini_api_key}"
                response = requests.post(
                    url,
                    json={"content": {"parts": [{"text": text}]}},
                    timeout=15
                )
                response.raise_for_status()
                return response.json()["embedding"]["values"]
            except Exception as e:
                print(f"Gemini embedding failed: {e}. Falling back to mock.")
                return self._mock_embedding()
            
        return self._mock_embedding()

    def _mock_embedding(self, size: int = 1536) -> List[float]:
        return [0.1] * size
