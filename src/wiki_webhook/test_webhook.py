import unittest
from fastapi.testclient import TestClient
try:
    from .main import app, WIKI_WEBHOOK_SECRET
except ImportError:
    from main import app, WIKI_WEBHOOK_SECRET
import hmac
import hashlib
import json

client = TestClient(app)

class TestWikiWebhook(unittest.TestCase):
    def test_webhook_invalid_signature(self):
        payload = {"event": "test"}
        response = client.post(
            "/webhook/wiki",
            json=payload,
            headers={"x-wikijs-signature": "invalid"}
        )
        # Should fail if secret is configured
        if WIKI_WEBHOOK_SECRET != "REPLACE_WITH_REAL_SECRET":
            self.assertEqual(response.status_code, 401)
        else:
            self.assertEqual(response.status_code, 200)

    def test_webhook_valid_page_update(self):
        payload = {
            "event": "page:updated",
            "data": {
                "path": "test-page",
                "title": "Test Page",
                "content": "This is a test content. # Header\nMore text here.",
                "description": "Just a test"
            }
        }
        payload_bytes = json.dumps(payload).encode()
        
        signature = hmac.new(
            WIKI_WEBHOOK_SECRET.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        response = client.post(
            "/webhook/wiki",
            content=payload_bytes,
            headers={"x-wikijs-signature": signature}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["event"], "page:updated")

if __name__ == "__main__":
    unittest.main()
