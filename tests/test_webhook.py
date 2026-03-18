import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def mock_services():
    # Patch the classes in the source modules BEFORE they are imported by webhook_server
    with patch("src.embedding_service.EmbeddingService") as mock_emb_cls, \
         patch("src.vector_store.VectorStore") as mock_vec_cls:
        
        mock_emb_instance = mock_emb_cls.return_value
        mock_vec_instance = mock_vec_cls.return_value
        
        # Setup common mock behavior
        mock_emb_instance.chunk_markdown.return_value = ["chunk 1", "chunk 2"]
        mock_emb_instance.get_embedding.return_value = [0.1] * 384
        
        yield {
            "embedding": mock_emb_instance,
            "vector_store": mock_vec_instance
        }

def test_webhook_page_updated(mock_services):
    # Import app INSIDE the test to ensure it picks up the patched classes
    from webhook_server import app
    client = TestClient(app)
    
    payload = {
        "type": "page.updated",
        "data": {
            "title": "Test Page",
            "path": "test-page",
            "content": "This is test content.\n\nMore content."
        }
    }
    
    response = client.post("/webhook", json=payload)
    
    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert response.json()["page"] == "test-page"
    assert response.json()["chunks"] == 2

def test_webhook_ignored_event():
    from webhook_server import app
    client = TestClient(app)
    
    payload = {
        "type": "comment.created",
        "data": {"foo": "bar"}
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
