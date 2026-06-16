"""
統一的資料管理器
自動選擇使用 Google Sheets 或本地 CSV，提供無縫的資料存取
"""

import pandas as pd
import os
import streamlit as st
from google_sheets_manager import get_sheets_manager, is_sheets_available
from schema import COLUMNS, ensure_schema, empty_frame

class DataManager:
    def __init__(self):
        self.csv_file = "plastic_trace_data.csv"
        self.use_sheets = False
        self.sheets_manager = None
        self.initialize()
    
    def initialize(self):
        """初始化資料管理器"""
        # 嘗試使用 Google Sheets
        try:
            self.sheets_manager = get_sheets_manager()
            self.use_sheets = is_sheets_available()
            
            if self.use_sheets:
                st.sidebar.success("🌐 使用 Google Sheets 存儲")
                # 顯示 Google Sheets 連結
                if hasattr(self.sheets_manager, 'get_sheet_url'):
                    sheet_url = self.sheets_manager.get_sheet_url()
                    if sheet_url:
                        st.sidebar.markdown(f"📊 [查看資料表]({sheet_url})")
            else:
                st.sidebar.info("💾 使用本地 CSV 存儲")
                
        except Exception as e:
            st.sidebar.warning(f"⚠️ Google Sheets 不可用，使用本地存儲: {str(e)}")
            self.use_sheets = False
    
    def load_data(self):
        """載入資料。所有 return 出口都過 ensure_schema(),保證舊資料補齊新欄、
        欄位順序一致(修 review C2:避免某條路徑漏接 migration → KeyError)。"""
        try:
            if self.use_sheets and self.sheets_manager:
                # 從 Google Sheets 載入
                df = self.sheets_manager.load_data()
                if not df.empty:
                    return ensure_schema(df)
                else:
                    # 如果 Google Sheets 為空，嘗試從本地 CSV 載入並同步
                    if os.path.exists(self.csv_file):
                        df_csv = ensure_schema(pd.read_csv(self.csv_file, encoding='utf-8-sig'))
                        if not df_csv.empty:
                            st.info("📤 正在將本地資料同步到 Google Sheets...")
                            self.sheets_manager.save_data(df_csv)
                            return df_csv

            # 使用本地 CSV
            return self._load_csv()

        except Exception as e:
            st.warning(f"⚠️ 載入資料時發生錯誤，使用本地備份: {str(e)}")
            return self._load_csv()
    
    def save_data(self, df):
        """儲存資料"""
        try:
            # 總是先儲存到本地作為備份
            self._save_csv(df)
            
            # 如果可用，也儲存到 Google Sheets
            if self.use_sheets and self.sheets_manager:
                success = self.sheets_manager.save_data(df)
                if success:
                    return True
                else:
                    st.warning("⚠️ Google Sheets 儲存失敗，已儲存到本地")
            
            return True
            
        except Exception as e:
            st.error(f"❌ 儲存資料失敗: {str(e)}")
            return False
    
    def append_record(self, record_dict):
        """新增單筆記錄——以「單列 append」而非「load 整表→覆寫」寫入。

        修 review A1(P0 critical):整表覆寫在多人同時掃碼時會後寫覆蓋前寫、掉資料,
        且每筆 O(n)。改用單列 append:Sheets 走 worksheet.append_row(原子)、本地 CSV
        走檔尾 append,兩者都不重寫既有列。試辦多方手機並行掃碼的常態下不再掉資料。
        """
        # 只取 schema 內欄位、補齊缺欄,順序固定
        record = {col: record_dict.get(col, '') for col in COLUMNS}
        ok = True
        # 1) 本地 CSV 備份(單列 append)
        try:
            self._append_csv(record)
        except Exception as e:
            st.error(f"❌ 寫入本地備份失敗: {str(e)}")
            ok = False
        # 2) Google Sheets 單列 append
        if self.use_sheets and self.sheets_manager:
            try:
                if not self.sheets_manager.append_record(record):
                    st.warning("⚠️ Google Sheets 寫入失敗，已存本地備份")
            except Exception as e:
                st.warning(f"⚠️ Google Sheets 寫入失敗，已存本地備份: {str(e)}")
        return ok

    def _append_csv(self, record):
        """把單列 append 到本地 CSV。若既有檔仍是舊欄位,先一次性 migration 補欄重寫。"""
        row_df = pd.DataFrame([record], columns=COLUMNS)
        if not os.path.exists(self.csv_file):
            row_df.to_csv(self.csv_file, header=True, index=False, encoding='utf-8-sig')
            return
        existing_cols = pd.read_csv(self.csv_file, nrows=0, encoding='utf-8-sig').columns.tolist()
        if existing_cols != COLUMNS:
            # 舊檔欄位不符 → 一次性補欄重寫後再含新列
            migrated = ensure_schema(pd.read_csv(self.csv_file, encoding='utf-8-sig'))
            pd.concat([migrated, row_df], ignore_index=True).to_csv(
                self.csv_file, header=True, index=False, encoding='utf-8-sig')
        else:
            row_df.to_csv(self.csv_file, mode='a', header=False, index=False, encoding='utf-8-sig')
    
    def _load_csv(self):
        """從本地 CSV 載入資料(出口統一過 ensure_schema)"""
        if not os.path.exists(self.csv_file):
            return empty_frame()

        try:
            return ensure_schema(pd.read_csv(self.csv_file, encoding='utf-8-sig'))
        except Exception as e:
            st.error(f"❌ 讀取本地 CSV 失敗: {str(e)}")
            return empty_frame()
    
    def _save_csv(self, df):
        """儲存到本地 CSV(整表;統一過 ensure_schema 保證 16 欄)"""
        try:
            ensure_schema(df).to_csv(self.csv_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            st.error(f"❌ 儲存本地 CSV 失敗: {str(e)}")
            return False
    
    def get_storage_info(self):
        """獲取存儲資訊"""
        info = {
            "storage_type": "Google Sheets" if self.use_sheets else "本地 CSV",
            "backup_available": os.path.exists(self.csv_file),
            "sheets_available": self.use_sheets
        }
        
        if self.use_sheets and self.sheets_manager:
            info["sheet_url"] = self.sheets_manager.get_sheet_url()
        
        return info
    
    def sync_to_sheets(self):
        """手動同步本地資料到 Google Sheets"""
        if not self.use_sheets:
            st.error("❌ Google Sheets 不可用")
            return False
        
        try:
            df = self._load_csv()
            if not df.empty:
                success = self.sheets_manager.save_data(df)
                if success:
                    st.success("✅ 資料已成功同步到 Google Sheets")
                    return True
                else:
                    st.error("❌ 同步到 Google Sheets 失敗")
                    return False
            else:
                st.info("ℹ️ 沒有本地資料需要同步")
                return True
                
        except Exception as e:
            st.error(f"❌ 同步失敗: {str(e)}")
            return False

# 全域資料管理器實例
data_manager = None

def get_data_manager():
    """獲取資料管理器實例"""
    global data_manager
    if data_manager is None:
        data_manager = DataManager()
    return data_manager

# 相容性函數（保持與原有程式碼的相容性）
def load_data():
    """載入資料 - 相容性函數"""
    return get_data_manager().load_data()

def save_data(df):
    """儲存資料 - 相容性函數"""
    return get_data_manager().save_data(df)
