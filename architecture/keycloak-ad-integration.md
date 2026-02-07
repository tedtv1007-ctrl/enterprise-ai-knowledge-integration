# Keycloak 與 Windows AD 身分整合實作方案

## 1. 認證架構圖 (Mermaid)

```mermaid
graph LR
    User([使用者]) --> MM[Mattermost / Wiki.js]
    MM -->|OIDC Redirect| KC[Keycloak SSO]
    KC -->|LDAP Query| AD[(Windows Active Directory)]
    KC -.->|MFA Check| OTP[TOTP / MFA]
    AD -->> KC: 身分驗證成功
    KC -->> MM: 簽發 JWT Token
    MM -->> User: 完成單一登入
```

## 2. 整合配置清單
*   **User Federation**：建立 LDAP Provider 連接 Windows AD，設定 `LDAP Filter` 過濾特定 OU 中的保險業員工。
*   **Mapper 設定**：將 AD 的 `memberOf` 屬性映射為 Keycloak 的 `Roles`，實現 Wiki.js 的權限自動化。
*   **MFA 強制執行**：在 `Authentication Flow` 中設定，當來源為外部網路時，強制啟用 Google Authenticator 二次驗證。

## 3. 下一步實作
*   建立 `mattermost-oidc-client`。
*   建立 `wikijs-oidc-client`。
