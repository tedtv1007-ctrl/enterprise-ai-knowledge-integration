# Wiki.js 知識庫自動化同步與向量化研究報告

## 1. Webhook 自動化觸發機制
本研究實作了基於事件驅動的知識庫同步路徑：
*   **即時同步**：配置 Wiki.js Webhook 監聽 `pages:created` 與 `pages:updated` 事件，確保頁面存檔時立即觸發流程。
*   **安全校驗**：支援 Webhook Secret 簽章驗證，確保僅有來自內部 Wiki.js 的更新請求會被處理。

## 2. 向量化處理器設計 (Python + FastAPI)
*   **內容清洗與切片**：實作自動 Markdown 解析，將長篇條款切割為 500 字元的語義塊 (Semantic Chunks)，提升檢索精準度。
*   **Embedding 轉換**：整合本地化模型 (如 all-MiniLM-L6-v2) 進行向量轉值，確保數據處理不離開企業內部網路。

## 3. PostgreSQL pgvector 儲存架構
*   **高效檢索**：設計了 `wiki_embeddings` 資料表結構，並配置 **HNSW 索引** 以達成毫秒級的向量相似度搜尋。
*   **版本控制**：實作「先刪後寫」機制，確保當 Wiki 頁面更新時，舊的過期向量會自動被最新內容取代。

---
產出時間: 2026-02-07
研究員: OpenClaw ETL & Vector Specialist
