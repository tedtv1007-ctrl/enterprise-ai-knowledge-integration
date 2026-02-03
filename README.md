# 企業內部 AI 知識整合平台 (Enterprise AI Knowledge Integration)

本專案致力於研究與實作企業內部的知識整合與協作系統，核心技術採用 Container 部署。

## 🏗️ 系統架構 (Architecture)

```mermaid
graph TD
    subgraph "Identity & Security (AD/SSO)"
        AD["Active Directory<br/>(企業使用者目錄)"]
        KC["Keycloak<br/>(SSO 認證中心)"]
    end

    subgraph "Enterprise AI Workspace (Docker Containers)"
        Wiki["Wiki.js / Outline<br/>(知識庫)"]
        Chat["Mattermost<br/>(協作通訊)"]
        OC["OpenClaw Agent<br/>(AI 核心總控)"]
        RAG["AnythingLLM<br/>(知識檢索)"]
        Ollama["Ollama<br/>(本地大模型)"]
        MCP["MCP Server<br/>(連動協議層)"]
    end

    AD -->|LDAP 同步| KC
    KC -->|OIDC / SAML| Wiki
    KC -->|OIDC / SAML| Chat
    
    User((使用者)) -->|身份登入| KC
    User -->|搜尋與編輯| Wiki
    User -->|指令與對談| Chat
    
    Chat <-->|提供助理服務| OC
    OC <-->|連動協議| MCP
    MCP <-->|上下文檢索| RAG
    RAG <-->|內容索引| Wiki
    RAG <-->|推理計算| Ollama
```

## 整合工具鏈
- **身份驗證 (Auth)**: Keycloak + Active Directory
- **知識庫 (Wiki)**: Wiki.js / Outline
- **協作通訊 (Chat)**: Mattermost
- **AI 代理 (Agent)**: OpenClaw
- **本機腦 (Local LLM)**: Ollama
- **知識檢索與 RAG**: AnythingLLM
- **連動協議**: MCP (Model Context Protocol)

## 技術架構 (Technical Architecture)
所有系統環境變數、Docker Compose 配置與連線設定將記錄於此 GitHub 專案。

## 應用與研究 (Applications)
實際的業務流程應用、使用者情境與功能測試進度將記錄於 [Notion](https://www.notion.so/fdjyclaw-2f9d0ca2817080ae989eff5f9efbd8bf)。
