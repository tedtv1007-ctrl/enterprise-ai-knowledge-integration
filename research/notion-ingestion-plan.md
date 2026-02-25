# Notion API Ingestion Service Plan

## Objective
Build a service to ingest Notion pages into a vector database (AnythingLLM / Chroma / PGVector) for RAG.

## Technical Challenges
1.  **Rate Limiting**: Notion API has strict rate limits (3 requests/sec average).
2.  **Incremental Sync**: Only fetch pages updated since `last_edited_time`.
3.  **Content Parsing**: Convert Notion blocks (Paragraph, Heading, Code, Image) into clean Markdown.
4.  **Metadata Preservation**: Keep tags, page hierarchy, and URLs for citations.

## Architecture (PoC)
-   **Language**: Python 3.11+
-   **Libraries**: `notion-client`, `langchain`, `chromadb` (or `pgvector`)
-   **Flow**:
    1.  **Scanner**: Query Notion Search API for pages modified > `LAST_SYNC_TIME`.
    2.  **Fetcher**: Retrieve block children recursively.
    3.  **Parser**: Transform blocks to Markdown text.
    4.  **Chunker**: Split text into semantic chunks (overlap 200 chars).
    5.  **Embedder**: Generate embeddings (nomic-embed-text / openai).
    6.  **Indexer**: Upsert to Vector DB.

## Development Steps
1.  [ ] **Step 1**: Create `notion_client_wrapper.py` (Handle Auth & Rate Limits).
2.  [ ] **Step 2**: Create `block_parser.py` (Block-to-Markdown logic).
3.  [ ] **Step 3**: Integration test with a sample "Knowledge Base" page.
