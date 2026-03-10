import os
import hmac
import hashlib
import json
import logging
from fastapi import FastAPI, Request, Header, HTTPException
from .processor import ContentProcessor
from .embedding import EmbeddingService
from ..vector_service.lancedb_acl import VectorService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wiki_webhook")

app = FastAPI()

# Configuration (Prefer environment variables)
WIKI_WEBHOOK_SECRET = os.getenv("WIKI_WEBHOOK_SECRET", "REPLACE_WITH_REAL_SECRET")
VECTOR_DB_URI = os.getenv("VECTOR_DB_URI", "/tmp/lancedb_wiki")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")

# Initialize shared services
vector_service = VectorService(db_uri=VECTOR_DB_URI)
processor = ContentProcessor()
embedding_service = EmbeddingService(provider=EMBEDDING_PROVIDER, model=EMBEDDING_MODEL)

def verify_signature(payload: bytes, signature: str):
    """Wiki.js webhook signature verification (SHA256)"""
    if not signature:
        return False
    # Wiki.js sends signature as "sha256=hash" or just "hash"
    actual_sig = signature.split('=')[-1]
    expected = hmac.new(
        WIKI_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, actual_sig)

@app.post("/webhook/wiki")
async def handle_wiki_event(request: Request, x_wikijs_signature: str = Header(None)):
    payload = await request.body()
    
    # Enable signature verification in production
    if WIKI_WEBHOOK_SECRET != "REPLACE_WITH_REAL_SECRET":
        if not verify_signature(payload, x_wikijs_signature):
            logger.warning("Invalid webhook signature received.")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = data.get("event", "unknown")
    logger.info(f"Received Wiki.js event: {event}")

    # Logic for page:updated or page:created
    if event in ["pages:updated", "pages:created", "page:updated", "page:created"]:
        page_data = data.get("data", {})
        page_content = page_data.get("content", "")
        page_path = page_data.get("path", "unknown")
        
        if page_content:
            chunks = processor.chunk_markdown(page_content)
            documents = []
            for idx, chunk in enumerate(chunks):
                # Call embedding model
                vector = embedding_service.get_embedding(chunk)
                
                documents.append({
                    "id": f"{page_path}_{idx}",
                    "vector": vector,
                    "text": chunk,
                    "metadata": {
                        "path": page_path,
                        "title": page_data.get("title"),
                        "description": page_data.get("description"),
                        "roles": ["public"] # Default ACL
                    }
                })
            
            vector_service.add_documents(documents)
            logger.info(f"Successfully processed and vectorized page: {page_path} ({len(chunks)} chunks)")

    return {"status": "success", "event": event}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
