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
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    creds = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=[
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"
                        ]
                    )
                else:
                    st.error("❌ 請在 Streamlit Cloud 設定 Google Sheets 認證")
                    return False
            else:
                # 本地開發環境：從檔案讀取
                if os.path.exists("service_account.json"):
                    creds = Credentials.from_service_account_file(
                        "service_account.json",
                        scopes=[
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive"
                        ]
                    )
                else:
                    st.warning("⚠️ 本地環境找不到 Google Sheets 認證檔案，將使用本地 CSV")
                    return False
            
            self.gc = gspread.authorize(creds)
            self.setup_spreadsheet()
            return True
            
        except Exception as e:
            st.error(f"❌ Google Sheets 認證失敗：{str(e)}")
            return False
    
    def is_streamlit_cloud(self):
        """檢查是否在 Streamlit Cloud 環境"""
        return (
            os.getenv('STREAMLIT_SHARING_MODE') is not None or
            os.getenv('HOSTNAME', '').endswith('.streamlit.app') or
            'streamlit.app' in os.getenv('SERVER_NAME', '') or
            not os.getenv('COMPUTERNAME')  # Windows 本地環境會有這個變數
        )
    
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
                # 設置標題行
                headers = [
                    'qr_id', 'batch_name', 'stage', 'operator', 'timestamp', 
                    'weight_kg', 'source', 'destination', 'product_model', 
                    'notes', 'location'
                ]
                self.worksheet.append_row(headers)
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
                return pd.DataFrame(columns=[
                    'qr_id', 'batch_name', 'stage', 'operator', 'timestamp', 
                    'weight_kg', 'source', 'destination', 'product_model', 
                    'notes', 'location'
                ])
            
            df = pd.DataFrame(data)
            return df
            
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
            
            # 設置標題行
            headers = [
                'qr_id', 'batch_name', 'stage', 'operator', 'timestamp', 
                'weight_kg', 'source', 'destination', 'product_model', 
                'notes', 'location'
            ]
            
            # 準備資料（包含標題行）
            data_to_upload = [headers]
            
            if not df.empty:
                # 確保 DataFrame 有正確的欄位順序
                df_ordered = df.reindex(columns=headers, fill_value='')
                
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
            
            # 準備記錄資料
            headers = [
                'qr_id', 'batch_name', 'stage', 'operator', 'timestamp', 
                'weight_kg', 'source', 'destination', 'product_model', 
                'notes', 'location'
            ]
            
            record_values = [str(record_dict.get(header, '')) for header in headers]
            
            # 新增記錄
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
