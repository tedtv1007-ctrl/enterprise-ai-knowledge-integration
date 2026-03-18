import os
import logging
from typing import List, Dict, Optional, Any
from notion_client import Client, APIResponseError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notion_ingester")

class NotionIngester:
    """
    Handles ingestion of content from Notion databases.
    """
    def __init__(self, api_key: str, database_id: str):
        """
        Initialize the NotionIngester.

        Args:
            api_key (str): The Notion API integration key.
            database_id (str): The ID of the database to ingest from.
        """
        self.notion = Client(auth=api_key)
        self.database_id = database_id

    def fetch_changed_pages(self, last_sync_time: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query database for pages modified since last_sync_time.

        Args:
            last_sync_time (str, optional): ISO 8601 date string to filter pages modified after this time.

        Returns:
            List[Dict[str, Any]]: A list of Notion page objects.
        """
        query_filter = {}
        if last_sync_time:
            query_filter = {
                "property": "Last edited time",
                "date": {
                    "after": last_sync_time
                }
            }
        
        logger.info(f"Querying Notion DB: {self.database_id}")
        results = []
        has_more = True
        start_cursor = None

        try:
            while has_more:
                # API call wrapped in try-except
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    filter=query_filter if last_sync_time else None,
                    start_cursor=start_cursor
                )
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                
            logger.info(f"Found {len(results)} pages to process.")
            return results

        except APIResponseError as error:
            logger.error(f"Notion API Error: {error}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return []

    def _extract_text(self, block: Dict[str, Any], block_type: str) -> str:
        """Helper to extract plain text from rich_text array."""
        rich_text = block.get(block_type, {}).get("rich_text", [])
        return "".join([t.get("plain_text", "") for t in rich_text])

    def get_page_content(self, page_id: str) -> str:
        """
        Recursively fetch blocks and convert to Markdown.
        Supports: paragraph, heading_1..3, lists, code, image.

        Args:
            page_id (str): The ID of the page to fetch content for.

        Returns:
            str: The page content formatted as Markdown.
        """
        try:
            blocks = self.notion.blocks.children.list(block_id=page_id)
            markdown_content = []
            
            for block in blocks.get("results", []):
                b_type = block.get("type")
                
                if b_type == "paragraph":
                    text = self._extract_text(block, "paragraph")
                    markdown_content.append(text)
                
                elif b_type == "heading_1":
                    text = "# " + self._extract_text(block, "heading_1")
                    markdown_content.append(text)
                
                elif b_type == "heading_2":
                    text = "## " + self._extract_text(block, "heading_2")
                    markdown_content.append(text)
                
                elif b_type == "heading_3":
                    text = "### " + self._extract_text(block, "heading_3")
                    markdown_content.append(text)
                
                elif b_type == "bulleted_list_item":
                    text = "- " + self._extract_text(block, "bulleted_list_item")
                    markdown_content.append(text)
                
                elif b_type == "numbered_list_item":
                    text = "1. " + self._extract_text(block, "numbered_list_item")
                    markdown_content.append(text)
                
                elif b_type == "code":
                    code_block = block.get("code", {})
                    language = code_block.get("language", "")
                    text = self._extract_text(block, "code")
                    markdown_content.append(f"```{language}\n{text}\n```")
                
                elif b_type == "image":
                    image_block = block.get("image", {})
                    caption_list = image_block.get("caption", [])
                    caption = "".join([t.get("plain_text", "") for t in caption_list])
                    
                    # Handle both 'file' (temporary AWS S3) and 'external' (public URL)
                    url = ""
                    if "file" in image_block:
                        url = image_block["file"].get("url", "")
                    elif "external" in image_block:
                        url = image_block["external"].get("url", "")
                        
                    markdown_content.append(f"![{caption}]({url})")

                # Add more block types as needed...

            return "\n\n".join(markdown_content)
        except APIResponseError as error:
            logger.error(f"Notion API Error fetching blocks for {page_id}: {error}")
            return ""

if __name__ == "__main__":
    # Example Usage
    API_KEY = os.getenv("NOTION_API_KEY")
    DB_ID = os.getenv("NOTION_DB_ID")
    
    if API_KEY and DB_ID:
        ingester = NotionIngester(API_KEY, DB_ID)
        pages = ingester.fetch_changed_pages()
        for page in pages[:5]: # Process first 5 for test
            print(f"Processing {page['id']}...")
            content = ingester.get_page_content(page['id'])
            print(content[:100] + "...")
    else:
        print("Please set NOTION_API_KEY and NOTION_DB_ID")
