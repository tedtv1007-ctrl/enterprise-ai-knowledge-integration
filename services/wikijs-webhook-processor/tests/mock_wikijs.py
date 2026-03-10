from fastapi import FastAPI, Request, HTTPException
import json
import logging

app = FastAPI(title="Wiki.js Mock GraphQL Server")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-wikijs")

@app.post("/graphql")
async def mock_graphql(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    query = payload.get("query", "")
    variables = payload.get("variables", {})
    page_id = variables.get("id")
    
    logger.info(f"Received GraphQL query for page {page_id}")
    
    if "pages" in query and "single" in query:
        # Mock successful page content
        return {
            "data": {
                "pages": {
                    "single": {
                        "id": page_id,
                        "title": f"Mock Page {page_id}",
                        "description": "This is a mock description",
                        "path": f"path/to/page/{page_id}",
                        "content": f"# Mock Content for {page_id}\n\nThis is a paragraph for RAG testing.\n\nAnother paragraph to ensure chunking works correctly for page {page_id}.",
                        "updatedAt": "2026-03-10T00:00:00Z"
                    }
                }
            }
        }
    
    return {"errors": [{"message": "Invalid query"}]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
