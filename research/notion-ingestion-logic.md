# Notion 知識庫整合與 RAG 注入邏輯研究

## 1. 目標
將 Notion 內部的專案文件、會議記錄及 SOP 自動同步至 LanceDB 向量資料庫，並確保內容在轉換為 Markdown 格式後仍能保持語義完整性，同時繼承基礎的存取控制 (ACL)。

## 2. Notion API 核心機制
- **Authentication**: 使用 `Internal Integration Token`。
- **Entry Points**:
    - **Databases**: 適合結構化資料（如專案清單）。使用 `POST /v1/databases/{database_id}/query` 進行增量抓取。
    - **Pages**: 使用 `GET /v1/pages/{page_id}`。
- **Content Retrieval**: 
    - Notion 內容由 **Blocks** 組成。
    - 需要遞迴調用 `GET /v1/blocks/{block_id}/children` 來獲取完整頁面樹狀結構。

## 3. 內容處理流程 (Ingestion Pipeline)

### 3.1 Block to Markdown 轉換
為了讓 Embedding 模型（如 NVIDIA nv-embed-v1）能精準理解，需將 Notion Blocks 轉換為標準 Markdown：
- `heading_1` -> `# Header`
- `bulleted_list_item` -> `- Item`
- `code` -> ` ```language ... ``` `
- `callout` -> 使用 `> [!INFO]` 或自定義區塊標註。

### 3.2 增量更新策略 (Incremental Sync)
- 記錄上次同步的時間戳 `last_synced_at`。
- 調用 API 時使用 `filter` 過濾 `last_edited_time` 大於上次同步時間的頁面。
- 刪除處理：若頁面在 Notion 被標記為 `archived`，則同步從 LanceDB 中刪除對應的 `id`。

## 4. 權限映射 (ACL Mapping)
由於 Notion 的原生權限 API 較為受限，建議採用以下方案：
- **方案 A (屬性標籤)**：在 Notion Database 中建立一個名為 `AllowedRoles` 的 Multi-select 屬性。
- **方案 B (父層繼承)**：根據頁面所在的父層 Database ID 或 Workspace 區段，自動指派對應的 Keycloak Roles（例如：在 "HR Workspace" 下的所有頁面自動標註 `role:hr`）。

## 5. 資料結構映射 (Schema Mapping)
同步至 `VectorService` 的資料格式：
```python
{
    "id": "notion_page_uuid",
    "text": "# Page Title\n\nContent in markdown...",
    "vector": [0.1, 0.2, ...],
    "metadata": {
        "source": "notion",
        "url": "https://notion.so/...",
        "last_edited_time": "2026-02-23T14:30:00Z",
        "roles": ["engineering", "ai-team"] # 用於 LanceDB .where() 過濾
    }
}
```

## 6. 下一步實作計畫
1. 撰寫 `NotionClient` 封裝類別（基於 `httpx` 或 `notion-client`）。
2. 實作 `RecursiveBlockParser` 處理多層嵌套區塊。
3. 整合至 `enterprise-ai-knowledge-integration/services/wiki-sync-service`。
