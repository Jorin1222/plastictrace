# Google Sheets API 設定指南

## 📋 概述
本指南將協助您設定 Google Sheets API，讓 ELV 廢塑膠產銷履歷示範平台能夠將資料持久化存儲到 Google Sheets。

## 🔧 設定步驟

### 1. 建立 Google Cloud 專案

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 點擊專案選擇器，建立新專案
3. 為專案命名（例如：`plastic-trace-api`）

### 2. 啟用必要的 API

1. 在 Google Cloud Console 中，前往「API 和服務」→「程式庫」
2. 搜尋並啟用以下 API：
   - **Google Sheets API**
   - **Google Drive API**

### 3. 建立服務帳號

1. 前往「IAM 和管理」→「服務帳號」
2. 點擊「建立服務帳號」
3. 填寫服務帳號詳細資訊：
   - 服務帳號名稱：`plastic-trace-service`
   - 服務帳號 ID：自動產生或自訂
   - 說明：用於 ELV 廢塑膠履歷平台的 Google Sheets 存取

4. 點擊「建立並繼續」
5. 角色設定可以跳過（點擊「繼續」）
6. 使用者存取權設定也可以跳過（點擊「完成」）

### 4. 下載服務帳號金鑰

1. 在服務帳號列表中，點擊剛建立的服務帳號
2. 前往「金鑰」頁籤
3. 點擊「新增金鑰」→「建立新的金鑰」
4. 選擇「JSON」格式
5. 下載 JSON 檔案

### 5. 本地開發環境設定

1. 將下載的 JSON 檔案重新命名為 `service_account.json`
2. 將檔案放在專案根目錄（與 `app.py` 同一層）
3. 確認 `.gitignore` 已包含 `service_account.json`（避免上傳到 GitHub）

### 6. Streamlit Cloud 設定

1. 登入 [Streamlit Cloud](https://share.streamlit.io/)
2. 前往您的應用程式設定
3. 點擊「Secrets」
4. 複製 `.secrets_example.toml` 的內容並填入實際的服務帳號資訊：

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-actual-project-id"
private_key_id = "your-actual-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nyour-actual-private-key\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project-id.iam.gserviceaccount.com"
client_id = "your-actual-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
```

### 7. 建立和分享 Google Sheets

1. 前往 [Google Sheets](https://sheets.google.com/)
2. 建立新的試算表
3. 將試算表重新命名為「ELV廢塑膠產銷履歷資料庫」
4. 點擊「分享」按鈕
5. 將服務帳號的電子郵件地址（從 JSON 檔案中的 `client_email`）加入為編輯者

## 🧪 測試設定

1. 啟動應用程式：`streamlit run app.py`
2. 登入系統（使用 admin/admin123）
3. 前往「系統管理」→「Google Sheets」頁籤
4. 點擊「測試 Google Sheets 連接」
5. 確認連接成功

## 📊 功能說明

### 自動備份
- 所有資料會同時儲存到本地 CSV 和 Google Sheets
- 本地 CSV 作為備份，Google Sheets 提供雲端持久化

### 同步功能
- 系統會自動偵測環境並選擇適當的存儲方式
- 可手動同步本地資料到 Google Sheets

### 存取控制
- 只有授權的服務帳號可以存取 Google Sheets
- 資料安全性由 Google Cloud 的 IAM 保護

## 🔒 安全注意事項

1. **絕對不要將 `service_account.json` 上傳到 GitHub**
2. **定期檢查服務帳號的存取權限**
3. **只分享試算表給必要的使用者**
4. **考慮設定 Google Sheets 的檢視權限**

## 🚨 故障排除

### 連接失敗
- 檢查 API 是否已啟用
- 確認服務帳號金鑰正確
- 驗證試算表分享設定

### 權限錯誤
- 確認服務帳號有試算表的編輯權限
- 檢查 Google Drive API 是否已啟用

### 本地開發問題
- 確認 `service_account.json` 檔案路徑正確
- 檢查 JSON 檔案格式是否完整

### Streamlit Cloud 問題
- 確認 Secrets 設定正確
- 檢查私鑰格式（需要包含換行符號 `\n`）
- 驗證所有必要欄位都已設定：`type`, `project_id`, `private_key`, `client_email`
- 確保私鑰包含完整的 BEGIN/END 標記
- 檢查服務帳號是否有足夠權限

### 常見的 Streamlit Cloud Secrets 設定錯誤

1. **私鑰格式錯誤**
   ```toml
   # ❌ 錯誤：缺少換行符號
   private_key = "-----BEGIN PRIVATE KEY-----MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC..."
   
   # ✅ 正確：包含換行符號
   private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n"
   ```

2. **遺漏必要欄位**
   ```toml
   # 確保包含所有必要欄位
   [gcp_service_account]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "key-id"
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "service-account@project.iam.gserviceaccount.com"
   client_id = "client-id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
   ```

3. **服務帳號權限不足**
   - 確認服務帳號已被加入 Google Sheets 的編輯者
   - 檢查 Google Drive API 是否已啟用

### 🔧 線上除錯步驟

1. **前往應用程式的系統管理 → Google Sheets 頁籤**
2. **點擊「環境診斷」按鈕**查看環境變數
3. **點擊「測試 Google Sheets 連接」**查看具體錯誤訊息
4. **根據錯誤訊息調整 Streamlit Cloud Secrets 設定**

## 📈 效益

✅ **資料持久化**：資料不會因應用重啟而遺失  
✅ **即時同步**：多人可同時檢視資料  
✅ **備份機制**：雙重保護（本地 + 雲端）  
✅ **擴展性**：Google Sheets 可處理大量資料  
✅ **協作功能**：團隊成員可共享檢視權限
