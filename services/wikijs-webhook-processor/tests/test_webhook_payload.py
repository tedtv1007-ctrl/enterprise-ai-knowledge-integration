import httpx
import json
import asyncio

async def test_webhook():
    url = "http://localhost:8000/webhook"
    payload = {
        "event": "pages:updated",
        "pageId": 123,
        "pageTitle": "Test Page",
        "pagePath": "test/page"
    }
    
    print(f"Sending test payload to {url}...")
    async with httpx.AsyncClient() as client:
        try:
            # Note: This expects the server to be running. 
            # In a CI/CD context, we would start the server first.
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}. (Make sure the FastAPI server is running on port 8000)")

if __name__ == "__main__":
    asyncio.run(test_webhook())
