# 整合多來源知識庫：Notion 與 Confluence 整合方案建議書

## 1. 背景與目標
目前系統已具備基於 LanceDB 的向量搜尋能力 (`VectorService`)，並支持基礎的角色存取控制 (ACL)。為了擴展 RAG (Retrieval-Augmented Generation) 的知識來源，本方案旨在規劃如何將 Notion 與 Confluence 的內容同步至現有的 LanceDB 流程中。

## 2. API 與 Webhook 調研結果

### 2.1 Notion
- **API 類型**: REST API
- **Webhook 支援**: **原生不直接支援向外部 URL 發送 Webhook** (僅提供針對數據庫變更的內部自動化)。
- **同步機制建議**:
    - **輪詢 (Polling)**: 使用 `GET /v1/search` 或列出數據庫/頁面，並過濾 `last_edited_time`。
    - **中間件 (如 Zapier/Make)**: 利用這些工具捕捉 Notion 變更並轉發至我們的 API Gateway。
- **內容獲取**: 使用 `GET /v1/blocks/{block_id}/children` 遞迴獲取頁面內容。

### 2.2 Confluence (Cloud)
- **API 類型**: REST API (v1/v2)
- **Webhook 支援**: **原生支援**。
    - 關鍵事件: `page_created`, `page_updated`, `page_trashed`, `attachment_created`。
- **同步機制建議**:
    - 在 Confluence 設置中配置 Webhook，指向系統的 API Gateway (如 APISIX)。
- **內容獲取**: 使用 `GET /wiki/rest/api/content/{id}?expand=body.storage` 獲取內容。

## 3. 技術方案規劃

### 3.1 架構流程
1. **數據抓取層 (Ingestion Layer)**:
    - **Confluence**: 由 Webhook 觸發 `SyncService`。
    - **Notion**: 由定時任務 (Cron Job) 觸發 `SyncService` 進行增量抓取。
2. **處理層 (Processing Layer)**:
    - 將 HTML (Confluence) 或 Blocks (Notion) 轉換為純文本或 Markdown。
    - 提取元數據 (URL, Author, Space/Database, Roles)。
3. **向量化與存儲 (Embedding & Storage)**:
    - 調用現有的 `VectorService.add_documents`。
    - **重要：** 必須將來源系統的權限標籤 (Roles) 對應到 LanceDB 的 `roles` 字段中。

### 3.2 數據映射表 (Schema)
| 字段 | 來源 | 說明 |
| :--- | :--- | :--- |
| `id` | `notion_id` / `conf_id` | 原始系統的唯一標識 |
| `text` | 頁面內容 | 轉換後的文本內容 |
| `vector` | Embedding | 使用 OpenAI 或本地模型生成的向量 |
| `metadata.source` | `notion` / `confluence` | 來源標識 |
| `metadata.url` | 原始頁面 URL | 用於跳轉參考 |
| `roles` | `space_key` / `db_id` | 用於 ACL 過濾的權限標籤 |

## 4. 集成步驟建議
1. **開發 `IngestionProvider` 介面**: 定義 `fetch_content` 與 `parse_acl` 方法。
2. **實現 `NotionProvider` 與 `ConfluenceProvider`**: 封裝 API 調用與內容清理逻辑。
3. **擴展示 API Gateway (APISIX)**: 
    - 增加 `/ingest/confluence/webhook` 端點。
4. **增強 ACL 同步**: 建立一個權限對應表，將 Notion/Confluence 的群組映射至系統的 Keycloak Roles。

## 5. 安全考量
- **憑證管理**: Notion Token 與 Confluence API Token 應存儲於安全處 (如 Vault 或環境變數)。
- **內容清理**: 確保在向量化前移除敏感信息或無意義的導航組件。
