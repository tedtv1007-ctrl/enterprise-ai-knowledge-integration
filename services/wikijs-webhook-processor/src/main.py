import os
import hmac
import hashlib
import json
import logging
import httpx
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

# Try relative imports for modules
try:
    from .modules.processor import ContentProcessor
    from .modules.embedding import EmbeddingService
    from .modules.vector_service import VectorService
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
    from processor import ContentProcessor
    from embedding import EmbeddingService
    from vector_service import VectorService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wikijs-processor")

app = FastAPI(title="Wiki.js Webhook Processor (Refactored)")

# Configuration (Prefer environment variables)
WIKI_WEBHOOK_SECRET = os.getenv("WIKI_WEBHOOK_SECRET", "")
WIKIJS_API_URL = os.getenv("WIKIJS_API_URL", "http://wikijs/graphql")
WIKIJS_API_TOKEN = os.getenv("WIKIJS_API_TOKEN", "")
DB_URI = os.getenv("DB_URI", "/tmp/lancedb_wiki")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")

# Initialize shared services
vector_service = VectorService(db_uri=DB_URI)
processor = ContentProcessor()
embedding_service = EmbeddingService(provider=EMBEDDING_PROVIDER, model=EMBEDDING_MODEL)

@app.get("/")
async def health_check():
    return {"status": "running", "service": "wikijs-webhook-processor", "version": "2.0.0"}

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

async def fetch_wiki_content(page_id: int):
    """Fetches page content from Wiki.js using GraphQL API."""
    query = """
    query ($id: Int!) {
      pages {
        single(id: $id) {
          content
          title
          description
          path
          tags
          updatedAt
        }
      }
    }
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WIKIJS_API_URL,
                json={"query": query, "variables": {"id": page_id}},
                headers={"Authorization": f"Bearer {WIKIJS_API_TOKEN}"},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("pages", {}).get("single")
        except Exception as e:
            logger.error(f"Error fetching content for page {page_id}: {str(e)}")
            return None

async def process_wiki_page(page_id: int):
    """Background task to handle the full RAG pipeline."""
    try:
        page_data = await fetch_wiki_content(page_id)
        if not page_data:
            logger.warning(f"Skipping processing for {page_id}: No data found")
            return

        content = page_data.get("content", "")
        path = page_data.get("path", "unknown")
        tags = page_data.get("tags", [])
        
        # Delete existing entries for this path to avoid duplicates
        vector_service.delete_by_path(path)
        
        chunks = processor.chunk_markdown(content)
        documents = []
        
        # Simple heuristic for roles based on tags
        allowed_roles = ["public"]
        if any(t in tags for t in ["private", "internal", "confidential"]):
            allowed_roles = ["authenticated"]
        if "admin" in tags:
            allowed_roles = ["admin"]

        for i, chunk in enumerate(chunks):
            vector = embedding_service.get_embedding(chunk)
            documents.append({
                "id": f"{page_id}_{i}",
                "vector": vector,
                "text": chunk,
                "metadata": {
                    "title": page_data.get("title"),
                    "path": path,
                    "roles": allowed_roles,
                    "updatedAt": page_data.get("updatedAt"),
                    "source": "wikijs"
                }
            })
            
        vector_service.add_documents(documents)
        logger.info(f"Successfully indexed {len(documents)} chunks for page {page_id} (path: {path})")
    except Exception as e:
        logger.error(f"Failed to process page {page_id} in background: {str(e)}")

@app.post("/webhook")
async def handle_wikijs_event(request: Request, background_tasks: BackgroundTasks, x_wikijs_signature: str = Header(None)):
    body = await request.body()
    
    # Verify Signature
    if WIKI_WEBHOOK_SECRET:
        if not verify_signature(body, x_wikijs_signature):
            logger.warning("Invalid webhook signature received.")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event_data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event_data.get("event")
    # Wiki.js payload structure can vary; checking both common patterns
    page_id = event_data.get("pageId") or event_data.get("data", {}).get("id")
    
    if event_type in ["pages:created", "pages:updated"]:
        if page_id:
            background_tasks.add_task(process_wiki_page, int(page_id))
            logger.info(f"Queued background processing for page {page_id}")
            return {"message": "Event queued", "status": "accepted"}
        
    return {"message": "Event ignored", "status": "ignored"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
