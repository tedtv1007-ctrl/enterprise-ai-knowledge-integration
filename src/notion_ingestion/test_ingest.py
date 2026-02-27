import unittest
from unittest.mock import MagicMock, patch
from ingest import NotionIngester
from notion_client import APIResponseError

class TestNotionIngester(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_key"
        self.db_id = "test_db_id"
        self.ingester = NotionIngester(self.api_key, self.db_id)

    @patch("ingest.Client")
    def test_fetch_changed_pages_success(self, MockClient):
        """Test fetch_changed_pages returns expected results when API call succeeds."""
        # Setup mock client behavior
        mock_client_instance = MockClient.return_value
        self.ingester.notion = mock_client_instance # Override the instance created in setUp
        
        # Simulate a database query response
        fake_page = {"id": "page_123", "properties": {"Name": "Test Page"}}
        mock_client_instance.databases.query.return_value = {
            "results": [fake_page],
            "has_more": False,
            "next_cursor": None
        }

        # Call the method
        pages = self.ingester.fetch_changed_pages()

        # Verify results
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["id"], "page_123")
        mock_client_instance.databases.query.assert_called_once()

    @patch("ingest.Client")
    def test_fetch_changed_pages_error(self, MockClient):
        """Test fetch_changed_pages handles API errors gracefully."""
        mock_client_instance = MockClient.return_value
        self.ingester.notion = mock_client_instance

        # Simulate an API error
        # APIResponseError requires a response object.
        mock_response = MagicMock()
        mock_response.status_code = 400
        
        mock_client_instance.databases.query.side_effect = APIResponseError(
            mock_response, message="Bad Request", code=400
        )

        # Call the method
        pages = self.ingester.fetch_changed_pages()

        # Verify empty list returned on error
        self.assertEqual(pages, [])

    @patch("ingest.Client")
    def test_get_page_content_parsing(self, MockClient):
        """Test parsing of different block types."""
        mock_client_instance = MockClient.return_value
        self.ingester.notion = mock_client_instance

        # Mock block data
        mock_blocks = {
            "results": [
                {
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"plain_text": "Hello World"}]}
                },
                {
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"plain_text": "Header 1"}]}
                },
                {
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"plain_text": "Item 1"}]}
                },
                {
                    "type": "code",
                    "code": {
                        "language": "python",
                        "rich_text": [{"plain_text": "print('hi')"}]
                    }
                },
                {
                    "type": "image",
                    "image": {
                        "caption": [{"plain_text": "My Image"}],
                        "file": {"url": "http://example.com/img.png"}
                    }
                }
            ]
        }
        mock_client_instance.blocks.children.list.return_value = mock_blocks

        # Call method
        content = self.ingester.get_page_content("page_123")

        # Verify output
        self.assertIn("Hello World", content)
        self.assertIn("# Header 1", content)
        self.assertIn("- Item 1", content)
        self.assertIn("```python\nprint('hi')\n```", content)
        self.assertIn("![My Image](http://example.com/img.png)", content)

    @patch("ingest.Client")
    def test_intentional_failure_for_lobster_reflex(self, MockClient):
        """A test case designed to fail to trigger the Lobster Architecture reflex arc."""
        self.assertEqual(True, False, "Intentional failure to test Lobster Reflex Arc")

if __name__ == "__main__":
    unittest.main()
