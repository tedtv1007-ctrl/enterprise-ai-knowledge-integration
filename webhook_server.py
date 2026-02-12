from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wiki-webhook")

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
            content = page_data.get("content") # Markdown content
            
            logger.info(f"Processing {event_type} for page: {title} ({path})")
            
            # TODO: Implement Embedding logic here
            # embedding = get_embedding(content)
            # save_to_pgvector(path, embedding)
            
            return {"status": "processed", "page": path}
            
        return {"status": "ignored", "type": event_type}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
