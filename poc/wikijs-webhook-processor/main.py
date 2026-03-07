from fastapi import FastAPI, Request, BackgroundTasks
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

async def vectorize_content(page_id, title, content, metadata):
    # Placeholder for vectorization logic (e.g., call Ollama/OpenAI then store in pgvector)
    logging.info(f"Vectorizing Page ID {page_id}: {title}")
    # TODO: Implement connection to vector DB

@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    event = data.get("event")
    logging.info(f"Received Wiki.js Event: {event}")

    if event in ["pageCreated", "pageUpdated"]:
        page_data = data.get("page", {})
        page_id = page_data.get("id")
        title = page_data.get("title")
        content = page_data.get("content")
        metadata = {
            "path": page_data.get("path"),
            "tags": page_data.get("tags"),
            "author": data.get("author", {}).get("name")
        }
        
        background_tasks.add_task(vectorize_content, page_id, title, content, metadata)
        return {"status": "processing", "page_id": page_id}
    
    return {"status": "ignored", "event": event}

@app.get("/health")
def health_check():
    return {"status": "ok"}
