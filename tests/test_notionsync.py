import os
from enterprise_ai_knowledge_integration.services.notion_extractor import fetch_page_text


def test_fetch_page_text_no_key(monkeypatch):
    monkeypatch.delenv('NOTION_KEY', raising=False)
    text = fetch_page_text('nonexistent')
    assert text == ''
