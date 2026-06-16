"""
Google Sheets API 管理器
用於將資料持久化到 Google Sheets，支援本地和雲端環境
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json
import os
from datetime import datetime
from schema import COLUMNS, ensure_schema

class GoogleSheetsManager:
    def __init__(self, spreadsheet_name="ELV廢塑膠產銷履歷資料庫"):
        self.gc = None
        self.sheet = None
        self.worksheet = None
        self.spreadsheet_name = spreadsheet_name
        self.worksheet_name = "履歷資料"
        self.setup_credentials()
    
    def setup_credentials(self):
        """設置 Google Sheets 認證"""
        try:
            # 檢查是否在 Streamlit Cloud 環境
            if self.is_streamlit_cloud():
                # 從 Streamlit secrets 獲取認證資訊
                if "gcp_service_account" in st.secrets:
                    st.info("🔍 正在使用 Streamlit Cloud Secrets 進行認證...")
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    
                    # 驗證必要的欄位
                    required_fields = ["type", "project_id", "private_key", "client_email"]
                    missing_fields = [field for field in required_fields if field not in creds_dict]
                    
                    if missing_fields:
                        st.error(f"❌ Streamlit Secrets 缺少必要欄位: {', '.join(missing_fields)}")
                        return False
                    
                    # 檢查私鑰格式
                    private_key = creds_dict.get("private_key", "")
                    if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
                        st.error("❌ 私鑰格式錯誤，請確認包含完整的 BEGIN/END 標記")
                        return False
                    
                    creds = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=[
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"
                        ]
                    )
                    st.success("✅ Streamlit Cloud 認證成功")
                else:
                    st.error("❌ 在 Streamlit Cloud Secrets 中找不到 'gcp_service_account' 設定")
                    st.info("""
                    請在 Streamlit Cloud 設定中添加 Google Sheets 認證：
                    1. 前往應用程式設定頁面
                    2. 點擊 'Secrets' 頁籤
                    3. 添加 gcp_service_account 設定
                    """)
                    return False
            else:
                # 本地開發環境：從檔案讀取
                if os.path.exists("service_account.json"):
                    st.info("🔍 正在使用本地 service_account.json 進行認證...")
                    creds = Credentials.from_service_account_file(
                        "service_account.json",
                        scopes=[
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"
                        ]
                    )
                    st.success("✅ 本地認證檔案讀取成功")
                else:
                    st.warning("⚠️ 本地環境找不到 service_account.json，將使用本地 CSV")
                    st.info("""
                    如要使用 Google Sheets，請：
                    1. 下載服務帳號 JSON 檔案
                    2. 重新命名為 service_account.json
                    3. 放置在專案根目錄
                    """)
                    return False
            
            self.gc = gspread.authorize(creds)
            self.setup_spreadsheet()
            return True
            
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Google Sheets 認證失敗：{error_msg}")
            
            # 提供具體的錯誤診斷
            if "No such file or directory" in error_msg:
                st.info("💡 檔案不存在，請檢查認證檔案路徑")
            elif "invalid_grant" in error_msg:
                st.info("💡 認證金鑰無效，請重新下載服務帳號金鑰")
            elif "insufficient authentication scopes" in error_msg:
                st.info("💡 權限範圍不足，請檢查 API 範圍設定")
            elif "API has not been used" in error_msg:
                st.info("💡 請確認已啟用 Google Sheets API 和 Google Drive API")
            elif "private_key" in error_msg:
                st.info("💡 私鑰格式問題，請檢查換行符號是否正確")
            
            return False
    
    def is_streamlit_cloud(self):
        """檢查是否在 Streamlit Cloud 環境"""
        # 詳細的環境檢測
        env_indicators = {
            'STREAMLIT_SHARING_MODE': os.getenv('STREAMLIT_SHARING_MODE'),
            'HOSTNAME': os.getenv('HOSTNAME', ''),
            'SERVER_NAME': os.getenv('SERVER_NAME', ''),
            'COMPUTERNAME': os.getenv('COMPUTERNAME'),
            'HOME': os.getenv('HOME', ''),
            'USER': os.getenv('USER', ''),
        }
        
        # 判斷是否為 Streamlit Cloud
        is_cloud = (
            env_indicators['STREAMLIT_SHARING_MODE'] is not None or
            env_indicators['HOSTNAME'].endswith('.streamlit.app') or
            'streamlit.app' in env_indicators['SERVER_NAME'] or
            env_indicators['COMPUTERNAME'] is None or  # 非 Windows 環境
            '/app' in env_indicators['HOME']  # 容器環境
        )
        
        # 調試資訊（僅在測試時顯示）
        if st.session_state.get('show_env_debug', False):
            st.write("🔍 環境變數診斷:")
            for key, value in env_indicators.items():
                st.write(f"   {key}: {value}")
            st.write(f"   判斷結果: {'Streamlit Cloud' if is_cloud else '本地環境'}")
        
        return is_cloud
    
    def setup_spreadsheet(self):
        """設置或創建 Google Sheets"""
        try:
            # 嘗試開啟現有的試算表
            try:
                self.sheet = self.gc.open(self.spreadsheet_name)
                st.success(f"✅ 已連接到現有的 Google Sheets: {self.spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                # 創建新的試算表
                self.sheet = self.gc.create(self.spreadsheet_name)
                st.success(f"✅ 已創建新的 Google Sheets: {self.spreadsheet_name}")
            
            # 設置工作表
            try:
                self.worksheet = self.sheet.worksheet(self.worksheet_name)
            except gspread.WorksheetNotFound:
                # 創建新的工作表
                self.worksheet = self.sheet.add_worksheet(
                    title=self.worksheet_name, 
                    rows=1000, 
                    cols=20
                )
                # 設置標題行(單一來源,含 9.2.2 新增欄位)
                self.worksheet.append_row(COLUMNS)
                st.info(f"🆕 已創建新的工作表: {self.worksheet_name}")
            
            return True
            
        except Exception as e:
            st.error(f"❌ 設置 Google Sheets 失敗：{str(e)}")
            return False
    
    def load_data(self):
        """從 Google Sheets 載入資料"""
        try:
            if not self.worksheet:
                return pd.DataFrame()
            
            # 獲取所有資料
            data = self.worksheet.get_all_records()
            
            if not data:
                # 如果沒有資料，返回空的 DataFrame 但有正確的欄位
                return pd.DataFrame(columns=COLUMNS)
            
            return ensure_schema(pd.DataFrame(data))

        except Exception as e:
            st.error(f"❌ 從 Google Sheets 載入資料失敗：{str(e)}")
            return pd.DataFrame()
    
    def save_data(self, df):
        """將資料儲存到 Google Sheets"""
        try:
            if not self.worksheet:
                st.error("❌ Google Sheets 工作表未初始化")
                return False
            
            # 清空現有資料（保留標題行）
            self.worksheet.clear()

            # 設置標題行(單一來源,含新欄位 → 修「save 默默丟新欄」的 A2 critical gap)
            headers = COLUMNS

            # 準備資料（包含標題行）
            data_to_upload = [headers]

            if not df.empty:
                # 確保 DataFrame 有正確的欄位(補齊缺欄、依 COLUMNS 排序)
                df_ordered = ensure_schema(df)

                # 轉換為列表格式
                for _, row in df_ordered.iterrows():
                    data_to_upload.append([str(val) if pd.notna(val) else '' for val in row])
            
            # 批次上傳資料
            self.worksheet.update('A1', data_to_upload)
            
            st.success(f"✅ 資料已成功儲存到 Google Sheets ({len(df)} 筆記錄)")
            return True
            
        except Exception as e:
            st.error(f"❌ 儲存資料到 Google Sheets 失敗：{str(e)}")
            return False
    
    def append_record(self, record_dict):
        """新增單筆記錄到 Google Sheets"""
        try:
            if not self.worksheet:
                st.error("❌ Google Sheets 工作表未初始化")
                return False
            
            # 準備記錄資料(單一來源,含新欄位)
            record_values = [str(record_dict.get(header, '')) for header in COLUMNS]

            # 新增記錄(單列 append,並發安全)
            self.worksheet.append_row(record_values)
            
            return True
            
        except Exception as e:
            st.error(f"❌ 新增記錄到 Google Sheets 失敗：{str(e)}")
            return False
    
    def get_sheet_url(self):
        """獲取 Google Sheets 的網址"""
        if self.sheet:
            return self.sheet.url
        return None
    
    def test_connection(self):
        """測試 Google Sheets 連接"""
        try:
            if self.worksheet:
                # 嘗試讀取一個儲存格
                test_value = self.worksheet.acell('A1').value
                st.success("✅ Google Sheets 連接測試成功")
                return True
            else:
                st.error("❌ Google Sheets 工作表未初始化")
                return False
        except Exception as e:
            st.error(f"❌ Google Sheets 連接測試失敗：{str(e)}")
            return False

# 全域實例
sheets_manager = None

def get_sheets_manager():
    """獲取 Google Sheets 管理器實例"""
    global sheets_manager
    if sheets_manager is None:
        sheets_manager = GoogleSheetsManager()
    return sheets_manager

def is_sheets_available():
    """檢查 Google Sheets 是否可用"""
    manager = get_sheets_manager()
    return manager.gc is not None and manager.worksheet is not None
