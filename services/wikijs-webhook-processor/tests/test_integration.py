import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os
import json
import hmac
import hashlib

# Adjust path to import the service
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from main import app, WIKIJS_WEBHOOK_SECRET
import main

class TestWikiJSProcessorIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.secret = "test-secret"
        # Temporarily override settings
        main.WIKIJS_WEBHOOK_SECRET = self.secret
        main.WIKIJS_API_URL = "http://localhost:8081/graphql"

    @patch("main.process_wiki_page") # Mock background task for response test
    def test_webhook_response_with_signature(self, mock_process):
        payload = {
            "event": "pages:updated",
            "pageId": 123,
            "pageTitle": "Test Page",
            "pagePath": "test/path"
        }
        body = json.dumps(payload).encode()
        
        signature = hmac.new(
            self.secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        response = self.client.post(
            "/webhook", 
            content=body,
            headers={"X-Wikijs-Signature": signature}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "accepted")
        mock_process.assert_called_once_with(123)

    @patch("main.vector_service.add_documents")
    @patch("httpx.AsyncClient.post")
    def test_full_processing_logic(self, mock_post, mock_add_docs):
        # Mocking GraphQL response
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "data": {
                    "pages": {
                        "single": {
                            "id": 123,
                            "title": "Mocked Content",
                            "description": "Desc",
                            "path": "mock/path",
                            "content": "# Mocked Header\n\nContent for RAG.",
                            "updatedAt": "2026-03-10T00:00:00Z"
                        }
                    }
                }
            }
        )

        from main import process_wiki_page
        import asyncio
        
        # Run the background task manually
        asyncio.run(process_wiki_page(123))
        
        # Verify vector service was called
        mock_add_docs.assert_called_once()
        args, _ = mock_add_docs.call_args
        docs = args[0]
        self.assertGreater(len(docs), 0)
        self.assertEqual(docs[0]["metadata"]["title"], "Mocked Content")

if __name__ == "__main__":
    unittest.main()
