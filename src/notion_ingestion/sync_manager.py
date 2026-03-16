import os
import logging
from typing import List, Dict, Any
from .ingest import NotionIngester
from ..wiki_webhook.processor import ContentProcessor
from ..wiki_webhook.embedding import EmbeddingService
from ..vector_service.lancedb_acl import VectorService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notion_sync")

class NotionSyncManager:
    """
    Orchestrates the synchronization of Notion pages into the VectorService.
    """
    def __init__(self, api_key: str, database_id: str, vector_db_uri: str = "/tmp/lancedb_wiki"):
        self.ingester = NotionIngester(api_key, database_id)
        self.processor = ContentProcessor()
        self.embedding_service = EmbeddingService(
            provider=os.getenv("EMBEDDING_PROVIDER", "ollama"),
            model=os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
        )
        self.vector_service = VectorService(db_uri=vector_db_uri)

    def sync_database(self, last_sync_time: str = None):
        """
        Fetches modified pages from Notion and updates the vector database.
        """
        logger.info(f"Starting Notion sync for database: {self.ingester.database_id}")
        pages = self.ingester.fetch_changed_pages(last_sync_time=last_sync_time)
        
        for page in pages:
            page_id = page["id"]
            page_title = self._get_title(page)
            page_url = page.get("url")
            
            logger.info(f"Syncing page: {page_title} ({page_id})")
            
            # 1. Fetch full content
            content = self.ingester.get_page_content(page_id)
            if not content:
                logger.warning(f"No content found for page: {page_id}")
                continue
                
            # 2. Delete existing entries to prevent duplicates
            self.vector_service.delete_by_path(page_id)
            
            # 3. Chunk the content
            chunks = self.processor.chunk_markdown(content)
            
            # 4. Determine roles/ACL (Example: Check for 'Private' property or database-level tags)
            # Default to public, can be customized based on Notion properties
            allowed_roles = ["public"]
            
            documents = []
            for idx, chunk in enumerate(chunks):
                # 5. Get Embeddings
                vector = self.embedding_service.get_embedding(chunk)
                
                documents.append({
                    "id": f"notion_{page_id}_{idx}",
                    "vector": vector,
                    "text": chunk,
                    "metadata": {
                        "path": page_id,
                        "title": page_title,
                        "description": f"Notion page: {page_url}",
                        "roles": allowed_roles,
                        "source": "notion"
                    }
                })
            
            # 6. Add to Vector DB
            if documents:
                self.vector_service.add_documents(documents)
                logger.info(f"Successfully indexed Notion page: {page_title} with {len(documents)} chunks.")

    def _get_title(self, page: Dict[str, Any]) -> str:
        """Extracts the title from a Notion page object."""
        properties = page.get("properties", {})
        # Common title property names in Notion
        for prop_name in ["Name", "Title", "title", "name"]:
            prop = properties.get(prop_name, {})
            if prop.get("type") == "title":
                title_list = prop.get("title", [])
                return "".join([t.get("plain_text", "") for t in title_list])
        return "Untitled Page"

if __name__ == "__main__":
    API_KEY = os.getenv("NOTION_API_KEY")
    DB_ID = os.getenv("NOTION_DB_ID")
    
    if API_KEY and DB_ID:
        sync_manager = NotionSyncManager(API_KEY, DB_ID)
        sync_manager.sync_database()
    else:
        print("Please set NOTION_API_KEY and NOTION_DB_ID")
