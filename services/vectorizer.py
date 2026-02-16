
class VectorizerBase:
    def embed(self, texts):
        raise NotImplementedError()

class OpenAIEmbedding(VectorizerBase):
    def __init__(self, client):
        self.client = client
    def embed(self, texts):
        # placeholder: client call to OpenAI embeddings
        return [[0.0]]*len(texts)

class OllamaEmbedding(VectorizerBase):
    def __init__(self, client):
        self.client = client
    def embed(self, texts):
        # placeholder: call to Ollama local model
        return [[0.0]]*len(texts)
