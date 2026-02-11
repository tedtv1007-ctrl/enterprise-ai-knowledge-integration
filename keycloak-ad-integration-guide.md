# Keycloak 與 Active Directory (AD) 整合最佳實踐指南

## 1. 簡介
本指南旨在提供 Keycloak 與 Microsoft Active Directory (AD) 進行 User Federation (使用者聯合) 的整合步驟與最佳實踐。透過整合，企業可以使用現有的 AD 帳號登入 Keycloak 保護的應用程式。

## 2. 前置準備 (Prerequisites)

在開始 Keycloak 設定之前，請確保以下項目已準備就緒：

*   **AD 服務帳號 (Service Account)**: 建立一個專用的 AD 帳號供 Keycloak 連線使用 (Bind DN)。
    *   *權限*: 至少需要讀取使用者和群組的權限。若需要讓 Keycloak 修改 AD 密碼或屬性，則需要寫入權限。
    *   *最佳實踐*: 密碼設定為永不過期，並限制該帳號的登入權限。
*   **網路連線**: Keycloak 伺服器必須能連線至 AD 網域控制站 (Domain Controller)。
    *   *Port*: 389 (LDAP) 或 636 (LDAPS, 推薦)。
*   **LDAPS 憑證 (推薦)**: 若使用 LDAPS (SSL/TLS)，需將 AD 的 CA 憑證匯入 Keycloak 的 Truststore (Java KeyStore)。

## 3. User Federation 設定步驟

### 步驟 1: 新增 LDAP Provider
1. 登入 Keycloak Admin Console。
2. 在左側選單選擇目標 Realm。
3. 點擊 **User Federation**。
4. 點擊 **Add provider...** 並選擇 **ldap**。

### 步驟 2: 基本設定 (Required Settings)
*   **UI display name**: `Active Directory` (或容易識別的名稱)
*   **Vendor**: 選擇 `Active Directory`
    *   *注意*: 選擇此選項會自動填入部分預設值 (如 username LDAP attribute 為 `sAMAccountName`)。

### 步驟 3: 連線與認證設定 (Connection & Authentication)
*   **Connection URL**: `ldaps://dc01.example.com:636` (建議使用 LDAPS)
*   **Users DN**: `OU=Users,DC=example,DC=com` (指定搜尋使用者的 Base DN，範圍越精確效能越好)
*   **Bind DN**: `CN=Keycloak Service,OU=ServiceAccounts,DC=example,DC=com` (AD 服務帳號的完整 DN)
*   **Bind Credential**: 輸入服務帳號密碼。
*   **Test Connection** & **Test Authentication**: 設定完成後，務必點擊這兩個按鈕確認連線成功。

### 步驟 4: 搜尋與同步設定 (LDAP Searching and Updating)
*   **Edit Mode**:
    *   `READ_ONLY`: Keycloak 不會修改 AD 資料 (最安全，推薦)。
    *   `WRITABLE`: Keycloak 可修改 AD 資料。
    *   `UNSYNCED`: 資料不匯入 Keycloak DB，僅代理認證 (不推薦，會限制 Keycloak 功能)。
*   **Username LDAP attribute**: `sAMAccountName` (AD 預設)。
*   **RDN LDAP attribute**: `cn` (AD 預設)。
*   **UUID LDAP attribute**: `objectGUID` (AD 預設，重要！這是使用者的唯一識別碼)。
*   **User Object Classes**: `person, organizationalPerson, user` (預設即可)。
*   **User LDAP Filter**:
    *   建議加入過濾器以排除停用帳號或電腦帳號。
    *   範例: `(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))`
*   **Search Scope**: `Subtree` (搜尋 Users DN 下的所有子 OU)。

### 步驟 5: 同步策略 (Synchronization Settings)
*   **Periodic Full Sync**: 開啟。建議每天或每週執行一次 (例如: `86400` 秒)。
*   **Periodic Changed Users Sync**: 開啟。建議頻率較高，例如每 15 分鐘 (`900` 秒) 或更短，以確保 Keycloak 能快速感知 AD 的變更。

## 4. Mapper 設定 (屬性映射)

Mapper 定義了 AD 屬性如何對應到 Keycloak 的使用者屬性。設定完 Vendor 為 Active Directory 後，Keycloak 會自動建立一些預設 Mapper。

### 檢查與新增 Mappers
切換到 **Mappers** 頁籤。

#### 1. 基本屬性 (預設通常已建立)
確保以下映射存在且正確：
*   **username**:
    *   *Mapper Type*: `user-attribute-ldap-mapper`
    *   *LDAP Attribute*: `sAMAccountName`
    *   *User Model Attribute*: `username`
*   **email**:
    *   *Mapper Type*: `user-attribute-ldap-mapper`
    *   *LDAP Attribute*: `mail`
    *   *User Model Attribute*: `email`
*   **first name / last name**:
    *   *LDAP Attribute*: `givenName` / `sn`
*   **CN 映射 (Full Name)**:
    *   *Mapper Type*: `full-name-ldap-mapper`
    *   *LDAP Attribute*: `cn`
    *   *Write Only*: `true` (如果 Edit Mode 是 READ_ONLY，此項無影響，但在寫入模式下用於回寫 CN)。

#### 2. MSAD User Account Control (重要)
*   **mapper**: `MSAD User Account Control`
*   **描述**: 這是一個特殊的 Mapper，用於將 AD 的 `userAccountControl` 屬性映射到 Keycloak 的使用者狀態 (Enabled/Disabled)。
*   **設定**: 確保已加入此 Mapper，否則 AD 停用的帳號在 Keycloak 中可能仍顯示為啟用。

#### 3. 群組映射 (Group Mapper) - 選用
若需將 AD 群組同步到 Keycloak：
*   點擊 **Create**。
*   **Mapper Type**: `group-ldap-mapper`
*   **LDAP Groups DN**: `OU=Groups,DC=example,DC=com`
*   **Group Name LDAP Attribute**: `cn`
*   **Mode**:
    *   `READ_ONLY`: 只從 AD 讀取群組。
    *   `LDAP_ONLY`: 群組結構保留在 LDAP，不匯入 Keycloak DB (較少用)。
    *   `IMPORT`: 將群組匯入 Keycloak (推薦)。
*   **User Groups Retrieve Strategy**:
    *   `LOAD_GROUPS_BY_MEMBER_ATTRIBUTE`: 使用群組的 `member` 屬性查詢 (AD 預設推薦)。
*   **Member Attribute**: `member`

## 5. 驗證與測試流程

在開放給終端使用者之前，請執行以下測試：

### 1. 連線測試
*   在 Provider 設定頁面，再次確認 **Test Connection** 和 **Test Authentication** 顯示 `Success`。

### 2. 同步測試 (Synchronize)
*   在 **Action** 選單 (右上角) 選擇 **Synchronize all users**。
*   觀察畫面上方的提示訊息，確認匯入 (Imported) 與更新 (Updated) 的使用者數量是否符合預期。
*   查看 Keycloak Server Log (`server.log`) 是否有錯誤訊息 (如 timeout, 權限不足)。

### 3. 使用者資料驗證
*   至左側 **Users** 選單，點擊 **View all users**。
*   隨機挑選一名 AD 使用者，檢查：
    *   **Username**: 是否正確 (sAMAccountName)。
    *   **Email**: 是否正確。
    *   **Attributes**: 檢查是否有多餘或遺失的屬性。
    *   **Details**: 確認 `Enabled` 狀態是否與 AD 一致。

### 4. 登入測試
*   開啟無痕視窗 (Incognito Mode)。
*   前往 Keycloak Account Console (`/realms/{realm-name}/account`)。
*   使用 AD 帳號與密碼嘗試登入。
*   **測試案例**:
    *   **正常登入**: 輸入正確帳密 -> 成功。
    *   **密碼錯誤**: 輸入錯誤密碼 -> 失敗 (Invalid username or password)。
    *   **停用帳號**: 使用 AD 中已停用的帳號 -> 失敗 (Account is disabled)。
    *   **密碼過期**: (若有設定) 使用 AD 中密碼過期的帳號 -> Keycloak 應提示更新密碼。

### 5. 群組同步測試 (若有設定)
*   在 AD 中將某使用者加入某群組。
*   在 Keycloak 執行 **Synchronize changed users** (或等待週期同步)。
*   檢查 Keycloak 該使用者的 **Groups** 頁籤，確認群組已出現。

## 6. 常見問題排查 (Troubleshooting)

*   **無法登入，Log 顯示 "Invalid Credentials"**:
    *   檢查 AD 帳號是否鎖定。
    *   檢查 Bind DN 帳號密碼是否正確。
*   **使用者無法匯入**:
    *   檢查 Users DN 範圍是否正確。
    *   檢查 User LDAP Filter 是否太嚴格。
*   **連線 Timeout**:
    *   檢查防火牆是否開放 TCP 389 或 636。
    *   若使用 LDAPS，檢查 Keycloak 是否信任 AD 的憑證 (Truststore)。
