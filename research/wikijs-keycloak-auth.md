# Wiki.js 與 Keycloak (OIDC) 權限對接流程

## 1. Keycloak 側設定
- **Client 建立**:
    - Client ID: `wikijs`
    - Protocol: `openid-connect`
    - Access Type: `confidential`
    - Valid Redirect URIs: `https://wiki.example.com/login/callback`
- **Mappers 設定**:
    - 建立一個名為 `groups` 的 Token Mapper。
    - Mapper Type: `Group Membership`
    - Token Claim Name: `groups`
    - Full group path: `OFF` (建議關閉以簡化對應)

## 2. Wiki.js 側設定
- **啟用策略**: 進入 Admin > Authentication > 加入 `Keycloak / Generic OpenID Connect`。
- **組態參數**:
    - Issuer: `https://keycloak.example.com/auth/realms/YOUR_REALM`
    - Client ID: `wikijs`
    - Client Secret: (從 Keycloak 取得)
- **Role Mapping (關鍵)**:
    - 在 Wiki.js 的 Keycloak 設定頁面中，找到 **Group Mapping** 或 **Role Assignment** 區段。
    - **Self-registration**: 啟用 (才能讓 Keycloak 用戶自動建立 Wiki.js 帳號)。
    - **Default Group**: 設定為 `Guests` 或 `Regular Users`。
    - **Mapping Rule**: 
        - 當 Keycloak Claim `groups` 包含 `/Engineering` -> 映射至 Wiki.js Group `Engineers`。
        - 當 Keycloak Claim `groups` 包含 `/Management` -> 映射至 Wiki.js Group `Managers`。

## 3. 權限隔離設計
- **Wiki.js Groups**: 建立與業務職能對應的群組。
- **Page Rules**:
    - 針對 `/engineering/*` 路徑，設定僅 `Engineers` 群組具備 Read/Write 權限。
    - 針對 `/hr/*` 路徑，設定僅 `HR` 群組具備存取權限。
