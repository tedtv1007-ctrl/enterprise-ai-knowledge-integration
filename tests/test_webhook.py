import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from webhook_server import app

# Create client within a fixture or after the app is initialized
def get_client():
    return TestClient(app)

@patch("webhook_server.VectorStore")
@patch("webhook_server.EmbeddingService")
def test_webhook_page_updated(mock_embedding, mock_vector_store):
    client = get_client()
    # Setup mocks
    mock_embedding.return_value.chunk_markdown.return_value = ["chunk 1", "chunk 2"]
    mock_embedding.return_value.get_embedding.return_value = [0.1] * 384
    
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
    client = get_client()
    payload = {
        "type": "comment.created",
        "data": {"foo": "bar"}
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
