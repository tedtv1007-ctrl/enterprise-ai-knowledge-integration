import os
import hmac
import hashlib
import json
import logging
from fastapi import FastAPI, Request, Header, HTTPException
try:
    from .processor import ContentProcessor
    from .embedding import EmbeddingService
    from ..vector_service.lancedb_acl import VectorService
except ImportError:
    from processor import ContentProcessor
    from embedding import EmbeddingService
    import sys
    import os
    # Add parent dir for vector_service
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from vector_service.lancedb_acl import VectorService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wiki_webhook")

app = FastAPI()

# Configuration (Prefer environment variables)
WIKI_WEBHOOK_SECRET = os.getenv("WIKI_WEBHOOK_SECRET", "REPLACE_WITH_REAL_SECRET")
WIKI_API_URL = os.getenv("WIKI_API_URL", "https://wiki.example.com/graphql")
WIKI_API_TOKEN = os.getenv("WIKI_API_TOKEN", "")
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

async def get_wiki_page_details(page_id: int):
    """Fetch page details including roles from Wiki.js GraphQL API"""
    if not WIKI_API_TOKEN:
        return None
        
    query = """
    query ($id: Int!) {
      pages {
        single(id: $id) {
          content
          title
          description
          path
          tags
          # ACL / Permission info if available in Wiki.js Schema
          # groups { id, name } 
        }
      }
    }
    """
    try:
        import requests
        headers = {"Authorization": f"Bearer {WIKI_API_TOKEN}"}
        response = requests.post(
            WIKI_API_URL,
            json={"query": query, "variables": {"id": page_id}},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("data", {}).get("pages", {}).get("single")
    except Exception as e:
        logger.error(f"Failed to fetch page details from Wiki.js: {e}")
        return None

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
        page_id = data.get("data", {}).get("id")
        
        # Proactive fetch from GraphQL to get official content and potentially roles
        wiki_page = await get_wiki_page_details(page_id) if page_id else None
        
        if wiki_page:
            page_content = wiki_page.get("content", "")
            page_path = wiki_page.get("path", "unknown")
            page_title = wiki_page.get("title")
            page_tags = wiki_page.get("tags", [])
        else:
            # Fallback to payload data if API call fails or is not configured
            page_data = data.get("data", {})
            page_content = page_data.get("content", "")
            page_path = page_data.get("path", "unknown")
            page_title = page_data.get("title")
            page_tags = page_data.get("tags", [])
        
        if page_content:
            # First, delete existing entries for this path to avoid duplicates
            vector_service.delete_by_path(page_path)
            
            chunks = processor.chunk_markdown(page_content)
            documents = []
            
            # Role mapping logic: Default to "public"
            # In a real enterprise setup, we would query the groups assigned to this page
            allowed_roles = ["public"]
            
            # Simple heuristic based on tags
            if "private" in page_tags or "internal" in page_tags:
                allowed_roles = ["authenticated"]
            if "admin" in page_tags:
                allowed_roles = ["admin"]
            
            for idx, chunk in enumerate(chunks):
                vector = embedding_service.get_embedding(chunk)
                
                documents.append({
                    "id": f"{page_path}_{idx}",
                    "vector": vector,
                    "text": chunk,
                    "metadata": {
                        "path": page_path,
                        "title": page_title,
                        "description": wiki_page.get("description") if wiki_page else None,
                        "roles": allowed_roles
                    }
                })
            
            vector_service.add_documents(documents)
            logger.info(f"Successfully re-indexed page: {page_path} ({len(chunks)} chunks) with roles: {allowed_roles}")

    return {"status": "success", "event": event}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
