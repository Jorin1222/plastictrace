# 🔒 資料安全與隱私保護說明

## ⚠️ 重要安全提醒

### 目前的安全狀況
- **GitHub 倉庫**：公開可見（任何人都能查看程式碼）
- **資料檔案**：已設定保護，不會上傳到 GitHub
- **Streamlit Cloud**：只執行程式，不儲存真實資料

---

## 🔑 Google Sheets 連線原理、金鑰位置與必補風險（2026-06 釐清，以本節為準）

> 本節為最新釐清。若與下方較舊內容出入，**以本節為準**。

### 一、為什麼程式碼公開、Sheet 仍讀得到？（程式碼 ≠ 鑰匙）

程式碼只是**指令**：「去找一張身分證，用它證明我是服務帳號，再打開那張試算表」。
**程式碼本身不含私鑰**，私鑰是在程式**執行當下**才從「跑它的那台機器」上讀進來的。

當初的設定其實是這三步：

```
①  Google Cloud 建「服務帳號」(機器人)
    → email:plastic-trace-service@plastic-trace-api.iam.gserviceaccount.com
    → 下載它的身分證 = service_account.json（內含私鑰）
②  打開 Google Sheet →「共用」→ 把機器人 email 加成「編輯者」
    → Google 從此認得這機器人可改這張表
③  把身分證放到「會執行程式的地方」：
    ├─ 本機:service_account.json 放專案資料夾（被 .gitignore 擋住，不進 git）
    └─ 雲端:貼到 Streamlit Cloud → Settings → Secrets 的 [gcp_service_account]
```

執行時：讀身分證 → 向 Google 證明「我是這機器人」→ Google 查機器人有沒有被加進這張表
→ ✅ 准許讀寫。**「鑰匙在本地」也能讀，是因為鑰匙在「正在跑程式的機器」上，不在 repo。**

### 二、私鑰放在哪（兩份副本、兩個環境、互不依賴）

| 執行環境 | 私鑰位置 | 用途 |
|----------|----------|------|
| 本機 `streamlit run` | 專案資料夾 `service_account.json`（gitignore 擋住） | 本機跑時連 Sheet |
| 雲端 plastictracetest.streamlit.app | Streamlit Cloud → Settings → Secrets `[gcp_service_account]` | 部署版連 Sheet |
| 別人 clone 公開 repo | **兩個都沒有** | 連不到你的 Sheet，退回本地空 CSV |

→ **公開 repo 只洩漏「怎麼敲門」，沒洩漏「鑰匙」。** 這就是「程式碼公開、真實資料留本地」設計成立的原因。

### 三、三條資料外洩路徑與現況

| 路徑 | 機制 | 狀態 |
|------|------|------|
| 私鑰直連 Sheet | 從 repo 撈到私鑰直接呼叫 API | ✅ 不成立（私鑰不在 git，已驗證 `git ls-files` 無憑證） |
| Sheet 自身公開分享 | Google Drive「知道連結的人都能看」 | ✅ 已關閉（一般存取權＝**限制**，只你＋服務帳號） |
| **demo 密碼 + 展示模式 + 匯出** | 公開 repo 含 demo 密碼，未設正式帳號時任何人可登入 app 匯出全部資料 | ⚠️ **未設 `[auth]` 前持續存在** |

> 注意第三條：攻擊者不是直連 Sheet，而是**借你的 app 當代理**——app 有私鑰，登入者借 app 的手讀資料。
> 對外試辦前**務必設定 `[auth]`** 才能關閉。

### 四、設定 `[auth]` 正式帳號（關閉路徑三）

到 Streamlit Cloud → 你的 app → **Settings → Secrets**，在**現有 `[gcp_service_account]` 之外、不要刪它**，加上：

```toml
[gcp_service_account]      # 已存在，別動（刪了雲端就連不上 Sheet）
# ... 原有內容 ...

[auth]                     # 新增這段
admin = "你的強密碼"
operator = "你的強密碼"
viewer = "你的強密碼"
```

存檔 → app 自動重啟 →「🧪 展示模式」橫幅消失、改用你的密碼。
（本機則放在 `.streamlit/secrets.toml`，或用環境變數 `APP_ADMIN_PW` / `APP_OPERATOR_PW` / `APP_VIEWER_PW`。範本見 `.secrets_example.toml`。）

未設定 `[auth]` 時，app 會自動進入**展示模式**並使用展示帳號（`admin/demo-admin` 等），
UI 明確標示——**不會把自己鎖在外面，但也代表資料未受密碼保護**。

### 五、私鑰萬一外洩，怎麼換（金鑰輪換）

1. Google Cloud Console → IAM 與管理 → 服務帳號 → `plastic-trace-service` → 金鑰 → **建立新金鑰**（下載新的 JSON）。
2. 更新兩處副本：本機 `service_account.json`、Streamlit Cloud Secrets 的 `[gcp_service_account]`。
3. 回服務帳號 → **刪除舊金鑰**（舊的立刻失效）。
4. 服務帳號 email 不變，Sheet 共用設定**不必重設**。

### 六、驗證指令（確認沒有憑證/資料進 git）

```bash
git ls-files | grep -iE 'service_account|secrets\.toml|\.csv|\.json$'   # 應為空
```

### 七、上線前安全檢查清單

- [ ] Streamlit Cloud 設好 `[auth]` 正式密碼（關閉 demo 匯出路徑）
- [ ] Google Sheet 一般存取權＝**限制**，只分享給你＋服務帳號 email
- [ ] `git ls-files` 確認無任何憑證/資料檔
- [ ] （P3，正式上線前）補掃描頁**寫入端驗證**（token/簽章），防外人亂寫
- [ ] 登入後到「系統管理 → 系統資訊」核對 git commit ＝ GitHub 最新

---

## 🛡️ 已實施的保護措施

### 1. Git 忽略設定
```
# .gitignore 已加入以下保護
*.csv
*.xlsx  
*.xls
*.json
service_account.json
.secrets.toml
plastic_trace_data.csv
data/
records/
backup/
archive/
```

### 2. 資料分離架構
- **程式碼**：放在 GitHub（公開）
- **資料**：只存在本地電腦（私人）
- **雲端**：只有示範功能（無真實資料）

### 3. 安全流程
1. 本地開發：真實資料在您的電腦
2. GitHub：只上傳程式碼
3. Streamlit Cloud：自動建立示範環境

### 4. Google Sheets 服務帳號安全
⚠️ **service_account.json 檔案包含敏感的Google Cloud認證資訊**

#### 立即安全措施：
- ✅ 檔案已加入 `.gitignore` 保護
- ✅ 絕不上傳到 GitHub 或任何公開平台
- ✅ 線上版本使用 Streamlit Secrets 機制

#### 建議處理方式：
1. **保留但移動到安全位置**：
   ```bash
   # 移到用戶配置目錄
   mkdir -p ~/.config/plastic-trace/
   mv service_account.json ~/.config/plastic-trace/
   ```

2. **完全刪除（如已設定 Streamlit Secrets）**：
   ```bash
   rm service_account.json
   ```

3. **定期輪換金鑰**：
   - 在 Google Cloud Console 中重新生成服務帳號金鑰
   - 刪除舊金鑰以提升安全性

## 🔧 如何確保資料安全

### 立即執行的安全檢查
```bash
# 檢查哪些檔案被 Git 追蹤
git ls-files

# 確認敏感檔案不在列表中
git ls-files | grep -E "(\.csv|\.json|service_account)"

# 檢查 .gitignore 設定
cat .gitignore | grep -E "(service_account|\.json|\.csv)"

# 確認目前狀態
git status
```

### 移除已上傳的敏感檔案
```bash
# 從 Git 追蹤中移除（但保留本地檔案）
git rm --cached plastic_trace_data.csv
git rm --cached service_account.json

# 提交變更
git commit -m "移除敏感資料檔案，加強安全防護"
git push
```

### 安全處理 service_account.json
```bash
# 選項1：移動到安全位置（推薦）
mkdir -p ~/.config/plastic-trace/
mv service_account.json ~/.config/plastic-trace/

# 選項2：完全刪除（如已設定Streamlit Secrets）
rm service_account.json

# 確認檔案已被忽略
echo "service_account.json" >> .gitignore
git add .gitignore
git commit -m "更新.gitignore保護服務帳號檔案"
```

## 🌐 部署安全性

### Streamlit Cloud 特性
- **暫存環境**：每次重新部署會清除所有資料
- **無持久儲存**：無法永久保存用戶資料
- **隔離執行**：每個應用獨立運行

### 建議的使用方式
1. **示範展示**：使用 Streamlit Cloud 版本展示功能
2. **實際使用**：在自己電腦上運行處理真實資料
3. **資料備份**：定期匯出 CSV/Excel 到安全位置

## 🚨 進一步安全建議

### 選項 1：私人倉庫（可選，非必要）
> 註：本專案採「程式碼公開、真實資料留本地」設計，**公開 repo 在已設 `[auth]` 且 Sheet 為限制存取時是安全的**（見上方釐清節）。設為 Private 是額外保險，非必要。
- 將 GitHub 倉庫設為 Private
- 只有您能存取程式碼
- 仍可部署到 Streamlit Cloud

### 選項 2：完全本地化
- 只在本地電腦使用
- 不上傳任何程式碼到網路
- 最高安全性但無法遠端存取

### 選項 3：企業版部署
- 使用私人伺服器
- 加入使用者驗證
- 資料加密儲存

## 🔄 立即行動清單

### ✅ 已完成
- [x] 更新 .gitignore 保護資料檔案
- [x] 從 Git 移除已上傳的 CSV 檔案
- [x] 建立安全的示範資料初始化機制
- [x] 加入 service_account.json 保護設定
- [x] 設定 Streamlit Secrets 機制

### 🔲 建議執行
- [ ] 安全處理 service_account.json 檔案（移動或刪除）
- [ ] 考慮將 GitHub 倉庫設為 Private
- [ ] 定期檢查 `git ls-files` 確保無敏感檔案
- [ ] 建立資料備份計畫
- [ ] 設定存取權限控制（如需要）
- [ ] 定期輪換 Google Cloud 服務帳號金鑰

## 📞 如有疑慮

如果您擔心資料已經洩露：
1. **立即檢查**：前往 https://github.com/Jorin1222/plastictrace 查看是否有敏感資料
2. **緊急移除**：如發現敏感檔案，立即使用 `git rm` 移除
3. **變更倉庫**：考慮將倉庫設為 Private 或刪除重建

**記住：安全第一，功能第二！** 🔐
