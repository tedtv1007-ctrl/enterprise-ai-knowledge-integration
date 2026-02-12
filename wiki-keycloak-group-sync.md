# Wiki.js 與 Keycloak 權限群組 (Group) 同步機制研究

**專案**: enterprise-ai-knowledge-integration
**日期**: 2026-02-12
**標籤**: research, security, iam

## 1. 原理概述
Wiki.js 支援透過 OIDC (OpenID Connect) 登入時，讀取 ID Token 或 Access Token 中的 Claim 來自動分配使用者群組。這使得我們可以在 Keycloak (或 AD) 統一管理人員權限，無需在 Wiki.js 手動開通。

**核心機制**: **名稱匹配 (Name Matching)**
Wiki.js 會讀取 Token 中的群組列表 (例如 `["dev-team", "marketing"]`)，並嘗試尋找 Wiki.js 內部 **名稱完全相同** 的群組。如果找到，使用者登入後就會自動獲得該群組的權限。

---

## 2. Keycloak 端設定 (Client Scope & Mapper)
目標：確保 Keycloak 發出的 Token 包含 `groups` Claim。

1.  **建立 Client Scope**:
    *   進入 **Client Scopes** > **Create client scope**。
    *   Name: `wiki-groups`。
    *   Type: `Default` 或 `Optional`。

2.  **設定 Mapper**:
    *   進入剛建立的 `wiki-groups` > **Mappers** > **Configure a new mapper** > **Group Membership**。
    *   **Name**: `group-mapper`
    *   **Token Claim Name**: `groups` (這是 Wiki.js 預設讀取的欄位)
    *   **Full group path**: `OFF` (建議關閉。若開啟，群組名會變成 `/dev-team`；若關閉則為 `dev-team`。Wiki.js 匹配名稱時不包含斜線通常較直觀)。
    *   **Add to ID token**: `ON`。
    *   **Add to access token**: `ON`。

3.  **綁定 Client**:
    *   進入 **Clients** > 選擇您的 Wiki.js Client (e.g., `wiki-client`)。
    *   **Client scopes** > **Add client scope** > 選擇 `wiki-groups` > Add as **Default**。

---

## 3. Wiki.js 端設定
目標：告知 Wiki.js 讀取哪個 Claim 來決定群組。

1.  **進入後台**: Administration > **Authentication** > **Keycloak** (或 Generic OIDC)。
2.  **Configuration 設定**:
    *   找到 **Group Mapping** 或 **Self-registration** 區塊。
    *   **Groups Claim**: 輸入 `groups` (需與 Keycloak Mapper 設定一致)。
    *   **Map groups**: 確保此選項已啟用。

---

## 4. 驗證流程
1.  **Keycloak**: 建立一個群組 `knowledge-editors`，並將使用者 `alice` 加入。
2.  **Wiki.js**: 建立一個群組 `knowledge-editors`，並賦予 "寫入/編輯" 權限。
3.  **登入**: 使用 `alice` 登入 Wiki.js。
4.  **檢查**:
    *   進入 Wiki.js 後台 > Users > 點擊 `alice`。
    *   確認 `knowledge-editors` 群組已被 **自動勾選**。

## 5. 注意事項
*   **大小寫敏感**: Keycloak 的 `Dev-Team` 與 Wiki.js 的 `dev-team` 被視為不同群組，無法匹配。建議統一全小寫。
*   **權限移除**: 當使用者在 Keycloak 被移除群組，下次登入 Wiki.js 時，該權限通常會被同步移除 (取決於 Wiki.js 版本與設定，建議測試驗證)。
