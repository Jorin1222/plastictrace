# 實作計畫 — 9.2.2 再生料溯源試辦欄位升級

> 給 `/plan-eng-review` 與 `/plan-design-review` 審查用。對應 CLAUDE.md §3 規格。

## 範圍與優先序
P0 資料模型 + DRY 收斂 → P1 角色化表單 + 質量平衡 + 照片 → P2 帳號/清理 → 測試。

## P0-1 單一 schema 來源(DRY 收斂)
在 `data_manager.py` 頂層定義唯一常數:
```python
COLUMNS = [
    'qr_id', 'batch_name', 'stage', 'operator', 'timestamp',
    'weight_kg', 'source', 'destination', 'product_model', 'notes', 'location',
    # 新增 5 欄
    'recycled_ratio', 'data_tier', 'is_elv_closedloop', 'rrms_doc_id', 'material_type',
]
```
改寫所有重複處引用 `COLUMNS`:
- `data_manager.py`:`_load_csv()` 兩處空 DataFrame
- `google_sheets_manager.py`:headers ×3(setup_spreadsheet / save_data / append_record)
- `app.py`:`init_data_file()`、QR 產生 new_record、掃描登錄 new_record 的 key 集合

## P0-2 向後相容 / migration(單一進入點)
新增 helper:
```python
def _ensure_schema(df):
    # 缺欄補空、依 COLUMNS 排序;不丟棄未知欄(保守)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ''
    return df[COLUMNS + [c for c in df.columns if c not in COLUMNS]]
```
- 放在 `DataManager.load_data()` 的**所有 return 出口**統一套用 → CSV 與 Google Sheets 兩條路都自動補齊新欄。
- **Google Sheets 加欄安全性**:`save_data` 是 clear+整表重寫且用欄名對齊(`reindex`),非位置對齊;`load_data` 用 `get_all_records` 以表頭為 key。舊表頭仍是 11 欄時,load 後由 `_ensure_schema` 補欄,下次 save 表頭自動升為 16 欄,既有列舊值不受影響。
- **動 Sheets 前先請使用者匯出一份備份**(防呆)。

## P0-3 app.py 欄位跟上
新 5 欄接進:登錄表單輸入、QR 產生 new_record、歷程 expander 顯示、查詢篩選、統計概覽。
新欄型別:
- `recycled_ratio`:`st.number_input` 0–100、可空。
- `data_tier`:selectbox「實測(初級)/推估(二級)」
- `is_elv_closedloop`:selectbox「是/否/未知」
- `rrms_doc_id`:text_input
- `material_type`:selectbox「PP/PE/PS/PVC/ABS/其他」

## P1-3 角色化簡化表單 — 採設計合成解(規劃方已拍板 2026-06-16 15:10)
**stage 驅動表單**(不靠登入角色,掃描頁本就公開):依登錄者選的 `stage` 只顯示該節點必填欄位,其餘收進「▸ 更多欄位(選填)」expander,**16 欄全部仍存資料層**。
- `出廠`(處理業):重量 / 再生料來源純度 / 去向 / 物料類別 / RRMS單號 / data_tier
- `後端機構接收／再生處理`(後端):收料重量 / 用途產品 / 成品再生含量 / data_tier
- 加分(便宜才做):同一 QR 已登過 `出廠` → 表單預設 stage 跳 `後端機構接收`,減少選錯。
手機掃碼即填,欄位最少化、觸控目標 ≥44px、數值欄用 number_input。

## P1-4 質量平衡(抽純函式以利測試)— 規劃方已定義業務語意(2026-06-16 15:10)
```python
def compute_mass_balance(df, batch):  # 純函式,不碰 st
    # 回傳 {進料, 收料, 產出, 損耗, 回收率, 再生含量, 來源純度, data_tier}
```
**重量加總:禁止 SUM 全 stage,改節點取值**(同一 stage 多筆取時間最新一筆,不加總):
- 進料 = `出廠` 重量;收料 = `後端機構接收` 重量(**僅供對帳,不進加總**)
- 產出 = `再生處理／產品製造` 成品重量(取最終一筆);損耗 = 進料 − 產出;回收率 = 產出 ÷ 進料
- `運輸` 不計入(在途會重複計)
**再生含量(`recycled_ratio`)分兩種語意,不可混用**:
- headline「成品再生含量 %」(對歐盟 15%/25%)= batch 中 stage ∈ {再生處理,產品製造,銷售} 時間最新非空那筆(後端填的)
- 「再生料來源純度」= `出廠` 那筆,分開顯示,**不對門檻**
- headline 數字旁**必標 `data_tier`(實測初級／推估二級)**——推估數據的綠燈可信度不等同實測。
UI 端:水平流向(進料→產出・損耗)+ 放大主數字 + 顏色門檻(<15%紅 / 15–25%琥珀 / ≥25%綠)+ tier 標記。

## P1-5 照片上傳 — 建議本期降級 P2
理由:Streamlit Cloud 容器檔案系統 ephemeral(重啟即失)、雲端示範本就不存真圖;本地存圖牽涉路徑/容量/隱私(廠區/車牌照可能含個資)。
過渡:schema 留 `photo_ref` 字串欄,表單提供「照片另存後填檔名或雲端連結」。待試辦流程驗證後再做真正 file_uploader。**請規劃方拍板。**

## P2
- 預設帳號 `admin/admin123` 等明碼移出 → 讀 `st.secrets`/環境變數;README 不再寫死。
- 清理 0-byte 殘檔(app_new.py / demo_data.py / generate_demo_data.py / safe_demo_init.py / 數個空 .md);修 README 開頭亂碼 `## �`。

## P3 TODO(規劃方指示記下,正式上線前必補)
- **寫入端驗證**:掃描頁公開可寫(任何拿到 QR 網址者皆可寫入 Sheet),試辦期接受為可接受風險(參與者已知、量小 5–10 批、資料留本地、qr_id 不易猜)。**正式上線前必補 token/簽章驗證**,別讓它隨試辦結束被遺忘。
- Sheets 1000×20 容量上限搬遷(試辦量級內不會撞到)。

## 測試(pytest,新建)
- `COLUMNS` append→load round-trip 欄位一致
- `_ensure_schema` migration:舊 11 欄 df 補齊為 16 欄
- `recycled_ratio` 邊界:0 / 100 / 空 / 超界
- `compute_mass_balance` 單元測試
- 環境註記:測試以 Python 3.13(已裝依賴)執行。

## 不破壞既有
QR 產生/掃描/查詢/匯出 demo 流程維持;~~append-only 事件流不變~~(見下方審查:目前其實是 clear+整表重寫,非 append-only);安全鐵則(真實資料/憑證不進 git)維持。

---

## GSTACK REVIEW REPORT

`/plan-eng-review` — 2026-06-16,branch `main`。Eng review 自審 + 獨立子代理 outside-voice(codex 因 token 401 改用 Claude subagent)。

### Step 0 範圍挑戰
- 動 4–5 檔、0 新類別/服務 → **不觸發複雜度煞車**,範圍合理、無 scope creep。
- 已存在可重用:`DataManager` 抽象、`GoogleSheetsManager.append_record()`(單列 append,目前未被使用)、save_data 的 `reindex`。
- 範圍缺漏:規劃方點名的 `is_streamlit_cloud()` ×3 去重**未寫進本計畫任務**;見 C1。

### 四節審查結論

| # | 嚴重度 | 信心 | 位置 | 發現 |
|---|---|---|---|---|
| A1 | **P0** | 9/10 | `data_manager.py` save_data → `google_sheets_manager.py:207,228` | **多人同時掃碼會掉資料**。所有寫入都是 `load → concat → save_data(整表)`,save_data 對 Sheets 是 `clear()`+`update('A1', 全表)`。兩人並行各自 load→append→save = 後寫覆蓋前寫(last-write-wins),前者那筆消失。無鎖、無樂觀並發檢查。試辦正是多方手機並行掃碼 → **試辦殺手**。`append_record()`(`:237` 單列 append)早已寫好卻沒被用。 |
| A2 | **P0** | 8/10 | `google_sheets_manager.py:210-221,245-251` | **「下次 save 自動升 16 欄」是錯的**。save_data 與 append_record 都**硬寫 11 欄 headers** 並 `df.reindex(columns=headers)` → 每次存檔**默默丟掉新 5 欄**。`_ensure_schema` 在 load 補回、表單填入、save 又丟 = 資料流失,且**只驗 load 的 round-trip 測試抓不到**。⇒ P0-1 對這幾行的 COLUMNS 收斂必須**先於/同時於** P0-2 落地,否則開一個資料流失窗。 |
| C1 | P2 | 9/10 | `app.py:157,1004` + `google_sheets_manager.py:108`;URL 硬寫 `app.py:167` | `is_streamlit_cloud()` 重複 3 處且 QR base_url 硬寫。若誤判,QR 全指向 localhost → **整個試辦 QR 掃不動**。風險高於 schema 重複,應一併納入 DRY。 |
| C2 | P1 | 8/10 | `data_manager.py:42-54` | `_ensure_schema` 掛在 load 出口,但 **CSV-sync 那條 return(`:54`)與 Sheets-空 fallback 會繞過**。漏一條 → 11 欄 df 進 16 欄程式 → `df['material_type']` KeyError。「所有 return 出口」要逐條點名。另:`df[c]=''` 原地改 caller 的 df,潛在測試 flakiness。 |
| C3 | P1 | 7/10 | `app.py:284` + `google_sheets_manager.py:225` | `weight_kg` 空值存 `''`、整表經 `str(val)` round-trip → 數值欄變字串。`compute_mass_balance` 求和會遇 `''`/str/float 混型。需明定**強制轉型+驗證契約**。 |
| T1 | P1 | 8/10 | `data_manager.py:8` import streamlit | `_ensure_schema` 住在 import streamlit 的模組,headless 測試會被 `st` 拖累。**把純邏輯(`_ensure_schema`、`compute_mass_balance`)抽到一個不 import streamlit 的模組**(如 `schema.py`),才測得乾淨。 |

### 測試覆蓋(在 §3.8 基礎上補)
- A1 並發 lost-update:單元難測,由「改走 append_record」修正吸收;補一條「append 不重寫既有列」的測試。
- A2 **完整 round-trip 測試**:append→save→**重新 load**→欄位值一致(不能只驗 load 端,否則漏掉 save 丟欄)。
- C2 `_ensure_schema`:11 欄舊 df→16 欄;未知欄處理(保留 or 丟棄,要明確);欄序。
- C3 `compute_mass_balance`:混型 `''`/字串/數值的強制轉型。

### NOT in scope(本期明確不做)
- 照片真圖上傳(P1-5)→ 降級 P2,先用 `photo_ref` 字串欄頂著。理由:Cloud 檔案系統 ephemeral、隱私。
- 多人並發的完整交易鎖/外部 DB → 本期用 append_record 緩解即可,不引入 DB。
- 1000×20 Sheets 容量上限的搬遷 → 試辦量級內不會撞到,記為 P3 TODO。

### What already exists(避免重造)
- `GoogleSheetsManager.append_record()` 已實作但未使用 → A1 的修法是**啟用它**,非新寫。
- save_data 的 `reindex(fill_value='')` 已是 migration 雛形 → 收斂進 `_ensure_schema` 即可。
- `stage` 已是 selectbox、單一表單已有全部欄位 → 見 cross-model tension(角色化表單)。

### Failure modes(新 codepath 的生產故障)
1. 並發寫入掉資料(A1)— 無測試、無錯誤處理、**靜默** → **critical gap**,P0 必修。
2. 新欄 save 被 reindex 丟棄(A2)— 靜默資料流失 → **critical gap**,P0 必修。
3. QR 環境誤判指向 localhost(C1)— 使用者掃不出反應,半靜默。

### CROSS-MODEL TENSION(eng review 提出)
- **角色化簡化表單(P1-3)**:規劃方要(CLAUDE.md §3「對方動作越少越好」);eng outside-voice 主張**試辦期反而該讓欄位全開**,先觀察各方實際會填什麼,角色化留到 post-pilot。→ 由下方設計審查裁決。

---

## 設計審查(/plan-design-review)

設計完整度初評 **4/10**(欄位與角色拆分意圖有寫,但缺:手機優先版面、欄位順序、輸入型別與驗證回饋、掃描流程的空/錯/成功狀態、質量平衡的視覺呈現)。補上以下決策後可達 ~8/10。

### 設計裁決:角色化 tension 的解法(回答 eng cross-model tension)
**設計師判斷站規劃方這邊,但用一個合成解化解 eng 的疑慮:**
- 現場情境 = 拆車廠、單手持手機、要最短路徑。對「現場資料蒐集 app」而言**欄位越少 → 填寫完成率越高、資料品質越好**(「omit, then omit again」)。eng「全開以觀察」違反這個現場現實。
- **合成解(兩全)**:**資料層保留全部 16 欄**(回應 eng「想知道大家會填什麼」),但**表單只顯示該節點必要的少數欄位**(回應現場「動作越少越好」),其餘收進一個「▸ 更多欄位(選填)」expander。想填的人填得到,不想填的人不被擋路。
- **由 `stage` 選擇驅動表單**,不靠登入角色:掃描頁本就公開(現場人員不該被迫登入),使用者選「出廠」→ 顯示處理業欄位;選「後端接收」→ 顯示後端欄位。比「角色化」乾淨,且不需要帳號。

### 設計發現
| # | 維度 | 評分 | 發現與修法 |
|---|---|---|---|
| DZ1 | 表單精簡 | 4→9 | 見上方合成解:stage 驅動的條件欄位 + 「更多欄位」expander。 |
| DZ2 | 質量平衡呈現 | 3→8 | 別丟一張表。用**水平流向**(進料 X kg → 產出 Y kg・損耗 Z kg)+ **一個放大的「再生含量 %」主數字**,並用顏色對照歐盟門檻:< 15% 紅、15–25% 琥珀、≥ 25% 綠。試辦在賣的就是「這個數字達不達標」,要讓它一眼可見。 |
| DZ3 | 缺漏狀態 | 4→8 | 掃描表單補:送出中、剛存了什麼的確認回顯;質量平衡補空狀態「此批次尚無足夠資料計算」。 |
| DZ4 | 手機優先 | 5→8 | 明定單欄版面、觸控目標 ≥ 44px;重量/比率用 `st.number_input`(叫出數字鍵盤);比率欄標 `%` 單位、限 0–100。 |
| DZ5 | 輸入驗證回饋 | 4→8 | `recycled_ratio` 超界即時提示;必填欄(操作人員/重量)缺漏時明確標示,不要靜默擋送出。 |

**設計審查 VERDICT:** 角色化簡化表單**該做**,但用「stage 驅動 + 全欄存於資料層 + expander」的合成解,而非二選一;質量平衡要做成「一個達標數字 + 顏色門檻」而非表格。

### Implementation Tasks(由發現合成)
- [ ] **T1 (P0, CC ~20min)** — 寫入路徑改走 `append_record`(新單列 append),停用熱路徑的整表重寫 — 修 A1 並發掉資料 + O(n)→O(1)。
- [ ] **T2 (P0, CC ~10min)** — `google_sheets_manager.py` 三處 headers 改引用 `COLUMNS`,確保 save 不再 reindex 丟新欄 — 修 A2;**排程必須 ≥ schema 加欄之前/同時**。
- [ ] **T3 (P1, CC ~15min)** — 純邏輯抽到無 streamlit 的 `schema.py`(`COLUMNS`/`_ensure_schema`/`compute_mass_balance`)— 修 T1 可測性。
- [ ] **T4 (P1, CC ~10min)** — `load_data` 全 return 出口逐條套 `_ensure_schema`(含 `:54` CSV-sync、Sheets-空 fallback)— 修 C2。
- [ ] **T5 (P1, CC ~10min)** — `compute_mass_balance` 明定強制轉型+空值契約 — 修 C3。
- [ ] **T6 (P2, CC ~10min)** — `is_streamlit_cloud()` 收斂為單一來源、QR base_url 集中 — 修 C1。
- [ ] **T7 (P0 測試)** — 完整 append→save→reload round-trip(抓 A2 類 save 丟欄)。

### 並行化
多數任務集中在 `data_manager.py`/`google_sheets_manager.py`,彼此相依(T2、T4 動同檔),**建議循序實作**,無顯著 worktree 並行收益。

### 報告總表
| Review | 觸發 | Runs | 狀態 | 發現 |
|--------|------|------|------|------|
| Eng Review | `/plan-eng-review` | 1 | issues_open | 2 P0 critical gap + 4 P1/P2;範圍合理需補正 |
| Outside Voice | Claude subagent(codex token 401) | 1 | issues_found | 與 eng 高度一致,A1/A2 兩模型獨立都點名 |
| Design Review | `/plan-design-review` | 1 | issues_open | 完整度 4→8,化解角色化 tension,質量平衡呈現需重做 |

**VERDICT:** ENG + DESIGN review 完成。Eng 發現 **2 個 P0 critical gap(A1 並發掉資料、A2 save 丟欄)**,落地前必修;cross-model 高度一致。Design 把完整度從 4/10 補到 8/10,並裁定角色化表單**該做**(用 stage 驅動 + 全欄存資料層 + expander 的合成解)。**落地前需規劃方就下列三點拍板。**

**UNRESOLVED DECISIONS:**
- 寫入路徑是否改走 `append_record`(A1/T1)— 牽涉試辦並發量(同時幾個現場人員掃碼),交規劃方確認。
- 質量平衡語意(同 batch 多筆中哪筆 `recycled_ratio` 為準、跨階段重量如何加總不重複計)— 需規劃方給業務定義,否則 `compute_mass_balance` 無法寫對。
- 角色化合成解(stage 驅動表單 + 全欄存層 + 更多欄位 expander)是否符合試辦想要的填寫體驗 — 設計已裁定方向,仍請規劃方確認沒牴觸三方分工實務。
