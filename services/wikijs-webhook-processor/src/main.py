from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
import httpx
import os
import json
import logging
import hmac
import hashlib
from sentence_transformers import SentenceTransformer
import sys

# Ensure vector_service can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../src"))
from vector_service.lancedb_acl import VectorService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wikijs-processor")

app = FastAPI(title="Wiki.js Webhook Processor")

# Environment variables
WIKIJS_API_URL = os.getenv("WIKIJS_API_URL", "http://wikijs/graphql")
WIKIJS_API_TOKEN = os.getenv("WIKIJS_API_TOKEN", "REPLACE_ME")
WIKIJS_WEBHOOK_SECRET = os.getenv("WIKIJS_WEBHOOK_SECRET", "")
DB_URI = os.getenv("DB_URI", "/tmp/lancedb")

# Initialize models and services
model = SentenceTransformer('all-MiniLM-L6-v2')
vector_service = VectorService(db_uri=DB_URI)

class WikiEvent(BaseModel):
    event: str
    pageId: int
    pageTitle: str
    pagePath: str

@app.get("/")
async def health_check():
    return {"status": "running", "service": "wikijs-webhook-processor"}

from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks
# ... (existing imports)

@app.post("/webhook")
async def handle_wikijs_event(request: Request, background_tasks: BackgroundTasks, x_wikijs_signature: str = Header(None)):
    body = await request.body()
    
    # Verify Signature
    if WIKIJS_WEBHOOK_SECRET:
        if not x_wikijs_signature:
            logger.error("Missing X-Wikijs-Signature header")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        expected_signature = hmac.new(
            WIKIJS_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(x_wikijs_signature, expected_signature):
            logger.error(f"Invalid signature: got {x_wikijs_signature}, expected {expected_signature}")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = event.get("event")
    page_id = event.get("pageId")
    
    if event_type in ["pages:created", "pages:updated"]:
        # Offload heavy processing to background task to respond quickly to Wiki.js
        background_tasks.add_task(process_wiki_page, page_id)
        logger.info(f"Queued background processing for page {page_id}")
        return {"message": "Event queued", "status": "accepted"}
        
    return {"message": "Event ignored", "status": "ignored"}

async def process_wiki_page(page_id: int):
    """
    Background task to handle the full RAG pipeline.
    """
    try:
        page_data = await fetch_wiki_content(page_id)
        if not page_data:
            logger.warning(f"Skipping processing for {page_id}: No data found")
            return

        content = page_data.get("content", "")
        chunks = chunk_markdown(content)
        
        documents = []
        for i, chunk in enumerate(chunks):
            # Optimization: could batch encode if chunks are many
            vector = model.encode(chunk).tolist()
            documents.append({
                "id": f"{page_id}_{i}",
                "vector": vector,
                "text": chunk,
                "roles": ["admin", "staff"], 
                "metadata": {
                    "title": page_data.get("title"),
                    "path": page_data.get("path"),
                    "updatedAt": page_data.get("updatedAt"),
                    "source": "wikijs"
                }
            })
            
        vector_service.add_documents(documents)
        logger.info(f"Successfully indexed {len(documents)} chunks for page {page_id}")
    except Exception as e:
        logger.error(f"Failed to process page {page_id} in background: {str(e)}")

async def fetch_wiki_content(page_id: int):
    """
    Fetches page content from Wiki.js using GraphQL API.
    """
    query = """
    query ($id: Int!) {
      pages {
        single(id: $id) {
          content
          title
          description
          path
          updatedAt
        }
      }
    }
    """
    variables = {"id": page_id}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WIKIJS_API_URL,
                json={"query": query, "variables": variables},
                headers={"Authorization": f"Bearer {WIKIJS_API_TOKEN}"},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            page_data = data.get("data", {}).get("pages", {}).get("single")
            if not page_data:
                logger.error(f"Page {page_id} not found in Wiki.js")
                return None
            return page_data
        except Exception as e:
            logger.error(f"Error fetching content for page {page_id}: {str(e)}")
            return None

def chunk_markdown(content: str, chunk_size: int = 1000):
    """
    Simple markdown chunking by paragraph/length.
    TODO: Use LangChain or similar for smarter semantic chunking.
    """
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
            
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
