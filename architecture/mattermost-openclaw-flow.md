# Mattermost 與 OpenClaw AI 員工整合設計方案

## 1. 交互流程設計 (Mermaid)

本方案採用 Slash Command 模式，讓核保人員能即時調用 AI 能力。

```mermaid
sequenceDiagram
    participant User as 核保人員
    participant MM as Mattermost
    participant OC as OpenClaw (Main Agent)
    participant SEC as Security Layer (PII Scrub)
    participant KB as Knowledge Base (Wiki.js)

    User->>MM: 輸入 /uw-check [保單內容]
    MM->>OC: 送出 Webhook 請求
    OC->>SEC: 進行個資脫敏 (Scrubbing)
    SEC-->>OC: 返回安全文字
    OC->>KB: 檢索核保規範 (RAG)
    KB-->>OC: 返回相關條款
    OC->>OC: 執行 AI 推論 (業務專家模式)
    OC-->>MM: 回傳結構化建議 (Rich Text)
    MM-->>User: 顯示核保檢查結果
```

## 2. Slash Commands 定義
*   **/uw-manual [關鍵字]**：檢索內部 Wiki.js 中最新的核保手冊內容。
*   **/uw-check [文本]**：對一段保單描述進行規則比對，找出潛在風險點。

## 3. 安全性實作
*   所有通過 `/uw-` 系列指令的輸入輸出，均強制經過 `milk-ai-mcp-insuretech` 模組的 PII 清洗邏輯，確保身分證、電話等資料不外洩。
