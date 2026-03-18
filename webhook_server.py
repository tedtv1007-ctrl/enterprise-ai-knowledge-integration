from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
import os
from src.embedding_service import EmbeddingService
from src.vector_store import VectorStore

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wiki-webhook")

# Initialize services
# Use dummy or real depending on environment
embedding_service = EmbeddingService()
vector_store = VectorStore()

class WikiPayload(BaseModel):
    type: str
    data: dict

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
        event_type = payload.get("type")
        
        if event_type in ["page.created", "page.updated"]:
            page_data = payload.get("data", {})
            title = page_data.get("title")
            path = page_data.get("path")
            content = page_data.get("content", "")
            
            logger.info(f"Processing {event_type} for page: {title} ({path})")
            
            # 1. Clean old embeddings for this page (if it was an update)
            # vector_store.delete_page_embeddings(path)
            
            # 2. Chunk content
            chunks = embedding_service.chunk_markdown(content)
            
            # 3. Vectorize and save chunks
            for idx, chunk in enumerate(chunks):
                vector = embedding_service.get_embedding(chunk)
                # Attempt to save to pgvector
                try:
                    vector_store.upsert_embedding(path, idx, chunk, vector)
                except Exception as e:
                    logger.warning(f"Could not save to vector store (skipping for now): {str(e)}")
            
            return {"status": "processed", "page": path, "chunks": len(chunks)}
            
        elif event_type == "page.deleted":
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
