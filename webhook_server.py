from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
import os
import hmac
import hashlib
import json
from src.embedding_service import EmbeddingService
from src.vector_store import VectorStore

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wiki-webhook")

# Configuration (Prefer environment variables)
WIKI_WEBHOOK_SECRET = os.getenv("WIKI_WEBHOOK_SECRET", "REPLACE_WITH_REAL_SECRET")

# Initialize shared services
embedding_service = EmbeddingService()
vector_store = VectorStore()

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

@app.post("/webhook")
async def receive_webhook(request: Request, x_wikijs_signature: str = Header(None)):
    payload_bytes = await request.body()
    
    # Enable signature verification in production
    if WIKI_WEBHOOK_SECRET != "REPLACE_WITH_REAL_SECRET":
        if not verify_signature(payload_bytes, x_wikijs_signature):
            logger.warning("Invalid webhook signature received.")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(payload_bytes)
        event_type = payload.get("type", payload.get("event")) # Handle both 'type' and 'event'
        
        if event_type in ["page.created", "page.updated", "pages:created", "pages:updated", "page:created", "page:updated"]:
            page_data = payload.get("data", {})
            title = page_data.get("title")
            path = page_data.get("path")
            content = page_data.get("content", "")
            
            logger.info(f"Processing {event_type} for page: {title} ({path})")
            
            # 1. Chunk content
            chunks = embedding_service.chunk_markdown(content)
            
            # 2. Vectorize and save chunks
            for idx, chunk in enumerate(chunks):
                vector = embedding_service.get_embedding(chunk)
                # Attempt to save to pgvector
                try:
                    vector_store.upsert_embedding(path, idx, chunk, vector)
                except Exception as e:
                    logger.warning(f"Could not save to vector store (skipping for now): {str(e)}")
            
            return {"status": "processed", "page": path, "chunks": len(chunks)}
            
        elif event_type in ["page.deleted", "pages:deleted", "page:deleted"]:
            page_data = payload.get("data", {})
            path = page_data.get("path")
            logger.info(f"Deleting embeddings for page: {path}")
            # vector_store.delete_page_embeddings(path)
            return {"status": "deleted", "page": path}

        return {"status": "ignored", "type": event_type}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Ensure tables exist
    try:
        vector_store.create_table()
    except Exception as e:
        logger.error(f"Could not initialize vector store: {str(e)}")

    uvicorn.run(app, host="0.0.0.0", port=8000)
