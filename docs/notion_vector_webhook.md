# Notion → Vectorization Webhook

目標
- 建立一個可接收 Notion 頁面更新通知的 webhook，將變更內容擷取、預處理，並送入向量化服務（例如 OpenAI embeddings、Ollama 或本地向量化器），最終儲存到向量資料庫（e.g., Pinecone / Milvus / PGVector）。

設計要點
1. 接收事件
   - 使用 Notion integration 與 webhook 設定（Notion 的 event types 與 pages/blocks endpoints）。
   - Webhook 驗證：使用 Notion 提供的簽名或 HMAC 驗證 header。
2. 工作流
   - 接收 event → 拉取 Notion page content via Notion API → 抽取純文本並做簡潔化處理（去掉程式碼區、長清單切分）→ 對段落或區塊進行向量化 → 存入 vector DB。
3. 錯誤與重試
   - 使用持久化 queue（RabbitMQ / Redis Streams / SQS）以保證 at-least-once delivery 與重試。
   - 失敗時回退策略：log + DLQ。
4. 安全
   - Notion token 與向量化 API keys 保存在 secrets manager（已配置 ExternalSecrets / Vault 範例）。

快速啟動步驟
1. 建立 webhook endpoint（services/notion_webhook.py）並在 Notion integration 中註冊回呼 URL。
2. 實作 content extractor（services/notion_extractor.py），以 Notion API 抓頁面並合併 block text。
3. 實作 vectorizer adapter（services/vectorizer.py），支援多種 provider（OpenAI, Ollama）。
4. 實作存取 vector DB 的 repository（services/vector_repo.py）。
5. 測試：建立 mock Notion webhook payload 在 tests/ 下跑整合測試。

Roadmap
- v0.1: Basic pull-based webhook handling + OpenAI embeddings + PGVector storage.
- v0.2: Support for incremental updates, chunking strategies, multi-language normalization.
- v1.0: High-throughput streaming ingestion with Redis Streams + batching.
