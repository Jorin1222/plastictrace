# ELV 廢塑膠產銷履歷示範平台

## 專案說明
這是一個基於 Streamlit 的 ELV（End-of-Life Vehicle）廢塑膠產銷履歷追蹤平台，用於追蹤廢塑膠從回收到再生產品的完整流程。

## 功能特色
- 🏷️ **QR碼產生與管理** - 為每批廢塑膠產生唯一識別碼
- 📱 **掃描登錄資料** - 各階段人員掃描QR碼並記錄相關資訊
- 🔍 **履歷查詢** - 完整追蹤產銷履歷
- 📥 **資料下載** - 支援CSV/Excel格式匯出
- ⚙️ **系統管理** - 資料管理與系統維護

## 安裝與執行

### 1. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 2. 執行應用程式
```bash
streamlit run app.py
```

### 3. 開啟瀏覽器
應用程式將在 `http://localhost:8501` 啟動

## 檔案結構
```
Plastictrace/
├── app.py                    # 主要應用程式
├── requirements.txt          # Python 依賴套件
├── README.md                # 專案說明文件
├── plastic_trace_data.csv   # 資料檔案（執行後自動生成）
└── deploy_guide.md          # 部署指南
```

## 部署至 Streamlit Cloud

### 準備工作
1. 將專案上傳至 GitHub
2. 註冊 [Streamlit Cloud](https://streamlit.io/cloud)

### 部署步驟
1. 登入 Streamlit Cloud
2. 點擊 "New app"
3. 選擇 GitHub repository
4. 設定以下參數：
   - **Repository:** 您的 GitHub 儲存庫
   - **Branch:** main
   - **Main file path:** app.py
5. 點擊 "Deploy"

## 使用流程

### 1. QR碼產生
- 稽核團體登入系統
- 輸入批次名稱
- 系統產生唯一QR碼
- 下載並列印QR碼標籤

### 2. 各階段登錄
各處理階段人員：
- **出廠階段** - 記錄出廠資訊
- **運輸階段** - 記錄運輸過程
- **後端機構** - 記錄接收處理
- **再生處理** - 記錄再生加工
- **產品製造** - 記錄產品生產
- **銷售階段** - 記錄銷售資訊

### 3. 履歷查詢
- 輸入QR碼ID或選擇批次
- 查看完整處理履歷
- 匯出特定時段資料

### 4. 資料管理
- 定期下載備份資料
- 資料保存至少五年
- 支援CSV/Excel格式

## 技術規格
- **前端框架:** Streamlit
- **程式語言:** Python 3.8+
- **資料儲存:** CSV檔案
- **QR碼生成:** qrcode 套件
- **資料處理:** pandas
- **部署平台:** Streamlit Cloud

## 示範資料
平台預設支援5筆測試資料，用於驗證：
- 流程完整性
- 查詢功能
- 履歷建立
- 資料匯出

## 注意事項
- 此為示範版本，實際部署時需考慮資料安全性
- 建議定期備份資料檔案
- 手機掃描QR碼需使用相機應用程式或QR碼掃描器
- 支援多種裝置：手機、平板、電腦

## 未來擴展
- 用戶權限管理
- 資料庫整合
- 多語系支援
- 法規合規性強化
- 批次混合管理

## 聯絡資訊
如有任何問題或建議，請聯絡開發團隊。
