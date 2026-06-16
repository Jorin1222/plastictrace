# CLAUDE.md — Plastictrace（ELV 廢塑膠產銷履歷示範平台）

> 給在本資料夾工作的 Claude Code agent（以下稱「**實作方**」）的專案指令。
> **回應一律用繁體中文。**

---

## 0. 最重要：雙 agent 協作方式

本任務由兩個 agent 接力：

- **規劃方**（在 `C:\Users\yltsai0597\OneDrive\桌面\114-115創新作法執行` 工作）：握有業務脈絡、wiki 知識庫、9.2.2 報告與三方分工設計。**負責出規格、審查、拍板。**
- **實作方**（你，在 `D:\程式庫\Plastictrace`）：負責實際改 code、跑測試、commit。

**溝通靠本資料夾的 `chat.md`**：
1. 你開始前，**先 Read `chat.md`**，看規劃方留的最新訊息與規格。
2. 你做完一個段落、有疑問、或要請規劃方拍板時，**append 一則訊息到 `chat.md`**（不要改別人的舊訊息，只在檔尾追加）。
3. 格式：`### [實作方 YYYY-MM-DD HH:MM] 標題` + 內容。問題請編號,方便對方逐條回。
4. 然後**停下來等**，由使用者把你的訊息轉達規劃方、再把規劃方的回覆貼回來（或請使用者說「去看 chat.md」）。
5. 重大決策（資料模型、破壞性變更、刪檔）一定先在 chat.md 問過再做。

---

## 1. 專案現況

- **是什麼**：Streamlit + Google Sheets + QR Code 的廢塑膠（來源＝報廢車輛）全程溯源**示範平台**。
- **技術棧**：Streamlit / pandas / qrcode / openpyxl / gspread / Google 服務帳號。
- **主要檔案**：
  - `app.py`（主流程：登入→路由→QR 產生/掃描登錄/查詢/匯出，約 1000 行）
  - `data_manager.py`（CSV ↔ Google Sheets 抽象，含資料 schema）
  - `google_sheets_manager.py`（gspread 包裝）
  - `modern_ui.py`（CSS/元件）
- **git**：本資料夾就是 GitHub repo `Jorin1222/plastictrace` 的本地端，`origin/main` 與本機 main 同步。**動手前先 `git fetch` 確認沒落後**（家裡備援機也可能推過）。改完 commit + push。
- **安全鐵則（既有設計，務必維持）**：程式碼公開、**真實資料留本地**；`service_account.json`、真實 CSV 不進 git；雲端/Streamlit Cloud 只跑示範資料。見 `SECURITY.md`。

---

## 2. 本次任務目標

把這個示範平台升級成能**完整支援「9.2.2 再生料溯源試辦」三方分工**的工具，讓使用者能拿著它去跟處理業、後端收受對象（如大豐）談試辦。

### 業務背景（一句話）
歐盟新版 ELV 法規要求新車塑膠含一定比例再生料、且部分須來自報廢車閉環並全程溯源；現行 GRS 認證只認到「再生料」段，回收/處理段是斷的。本平台要能**補上這段斷點、並記錄歐盟新規關心的關鍵欄位**。

### 三方分工要對方填的欄位（系統必須有對應格子）
- 處理業出廠：重量 ✅、**再生料添加比率 %（缺）**、去向 ✅、照片（缺）、RRMS 單號（缺結構化欄）
- 後端收料：收料重量 ✅、用途/產品 ✅、**再生含量 %（缺）**、照片（缺）

---

## 3. 規格：要改什麼（依優先序）

> 工程偏好：DRY（目前 schema 在 `data_manager.py` 重複 3 次，請收斂成單一 `COLUMNS` 常數）、explicit 勝於 clever、邊界處理要足、改動用最小但乾淨的 diff。

### P0 必做（否則對不上 9.2.2 與分工表）
1. **資料模型加 5 欄**（在 `data_manager.py` 統一定義，並讓 `app.py` 登錄表單、歷程顯示、查詢篩選、統計都跟上）：
   - `recycled_ratio`：再生料添加比率／再生含量（%），數值 0–100，可空。
   - `data_tier`：資料可信度分級，選單「實測（初級）／推估（二級）」。
   - `is_elv_closedloop`：是否報廢車閉環來源，選單「是／否／未知」。
   - `rrms_doc_id`：RRMS／報廢系統申報單號（字串）。
   - `material_type`：物料類別，選單「PP／PE／PS／PVC／ABS／其他」。
2. **DRY 收斂**：`data_manager.py` 內 `_load_csv()` 兩處、`load_data` 等重複的欄位清單，抽成一個 `COLUMNS` 常數，單一來源。

### P1 試辦實務
3. **角色化簡化表單**：登錄表單依角色只顯示該角色要填的少數欄位（處理業：重量/添加比率/去向/物料/RRMS單號/照片；後端：收料重量/用途產品/再生含量/照片）。對方動作越少越好。
4. **質量平衡檢視**：依 batch 顯示「進料↔產出↔損耗」與可回收率/再生含量彙整（試辦成功指標要用）。
5. **照片上傳**：登錄表單加 `st.file_uploader`，存檔到本地（雲端示範模式不存真圖），schema 記 `photo_path` 或檔名引用。若評估太重可在 chat.md 提出降級為 P2。

### P2 上線真實業者前必處理
6. **預設帳號**：`admin/admin123` 等明碼目前寫在 README/程式裡 → 移出明碼（改讀 `st.secrets`／環境變數），README 不再寫死密碼。
7. **清理**：repo 有多個 0-byte 未追蹤殘檔（`app_new.py`、`demo_data.py`、`generate_demo_data.py`、`safe_demo_init.py`、數個空 .md）→ 刪除或 archive；`README.md` 開頭有亂碼字元 `## �` → 修掉。

### 測試（不可省）
8. 補 `data_manager` 的 round-trip 測試（append→load 欄位一致）、`recycled_ratio` 邊界（0/100/空/超界）、質量平衡計算 helper 的單元測試。Streamlit UI 不易測，至少把可測的計算邏輯抽成純函式再測。

---

## 4. 驗收（完成定義）
- [ ] 三方分工表要填的每個欄位，系統都有對應格子且能存取查詢。
- [ ] 角色化表單可用，處理業/後端各只看到自己要填的少數欄位。
- [ ] 質量平衡檢視能依 batch 算出再生含量並對照歐盟 15%/25%。
- [ ] 既有 demo 流程（QR 產生/掃描/查詢/匯出）不被破壞。
- [ ] 測試綠燈；安全鐵則維持；空檔清理完成。
- [ ] 規格上的疑問都在 `chat.md` 跟規劃方確認過。

---

## 5. 風格
- 回應與 commit message 用繁體中文。
- 優先用 Read/Edit/Write/Grep，少用 shell。
- 動大刀前先在 chat.md 說一句你的做法，讓規劃方/使用者能便宜地踩煞車。

---

## 6. 開發指令與架構速查（給快速上手用）

### 常用指令
```bash
pip install -r requirements.txt   # 安裝依賴
streamlit run app.py              # 啟動（預設 http://localhost:8501）
./start.sh                        # 等同上述，附環境檢查（Windows 用 start.bat）
```
- **目前沒有測試套件**——CI（`.github/workflows/streamlit.yml`，Python 3.11）只在 push/PR 時 smoke-test 套件能否 import，不跑單元測試。第 3.8 節要新增的測試是從零開始，沒有現成 `pytest` 設定可沿用。

### 架構大圖（需跨檔閱讀才看得懂的部分）

1. **儲存抽象是三層**：`app.py` 全程只呼叫相容函式 `load_data()` / `save_data(df)`（`data_manager.py` 尾端）→ 走 `get_data_manager()` 回傳的 **`DataManager` 單例** → 由它決定後端。**`save_data` 一律先寫本地 CSV 當備份，再視情況寫 Google Sheets**。改任何讀寫邏輯都應走這層，不要在 `app.py` 直接碰 CSV / gspread。

2. **後端選擇是自動的**：`DataManager.initialize()` 嘗試取得 `GoogleSheetsManager`；本地看有沒有 `service_account.json`、雲端看 `st.secrets["gcp_service_account"]`，**兩者皆無就退回本地 CSV**（`plastic_trace_data.csv`）。Sheets 的 `save_data` 是 **clear + 整表重寫**（非 append），資料量大時每次存檔都是 O(n) 全量上傳。

3. **資料是 append-only 事件流**：產生 QR 碼會寫一筆 `stage='初始建立'` 的列；之後每次掃描登錄都 **append 一筆新列**（同一 `qr_id` 多列）。某 QR 的「履歷」＝該 `qr_id` 所有列依 `timestamp` 排序，沒有 update-in-place。

4. **路由與權限都在 `app.py` `main()`**：`page=scan` + `qr_id` query param ⇒ **掃描登錄頁是公開的、不需登入**（這是手機掃 QR 的入口）；其餘功能一律要登入。角色（admin/operator/viewer）只在 `modern_ui.create_navigation_sidebar()` 決定側邊欄看得到哪些選單——**不是真正的後端權限控管**，只是 UI 隱藏。

5. **兩個已知的重複（也是第 3 節要收斂的目標）**：
   - **11 欄 schema 在 `app.py` / `data_manager.py` / `google_sheets_manager.py` 各自硬寫**（共 6+ 處）。改欄位要同時改全部，極易漏 → P0 要收斂成單一 `COLUMNS` 常數。
   - **`is_streamlit_cloud()` 重複 3 處**（`app.py` ×2、`google_sheets_manager.py` ×1），靠 `COMPUTERNAME` 等環境變數判斷雲端/本地，連帶決定 QR 碼 base_url（`plastictracetest.streamlit.app` vs `localhost:8501`）與認證來源。改部署判斷邏輯時三處要一起改。

### 安全邊界（修改前務必確認）
- `.gitignore` 已擋掉 `service_account.json`、`.streamlit/secrets.toml`、**所有 `*.csv` / `*.json` / `*.xlsx`**。真實資料與憑證**絕不可進 git**；任何新增的資料/憑證檔請確認落在既有 ignore 規則內。詳見 `SECURITY.md`。
