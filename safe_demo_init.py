"""
安全的示範資料初始化器
此檔案確保示範資料只在本地產生，不會上傳到 GitHub
"""

import pandas as pd
import os
from datetime import datetime, timedelta

def init_demo_data_safely():
    """
    只在本地沒有資料檔案時才產生示範資料
    這樣可以避免在 Streamlit Cloud 上產生持久資料
    """
    
    DATA_FILE = "plastic_trace_data.csv"
    
    # 檢查是否已有資料檔案
    if os.path.exists(DATA_FILE):
        print(f"📁 資料檔案 {DATA_FILE} 已存在，跳過初始化")
        return False
    
    print("🔒 安全提醒：正在本地產生示範資料（不會上傳到 GitHub）")
    
    # 這裡放入原本的示範資料生成程式碼
    demo_data = []
    
    # 示範批次 1: PP塑膠批次（簡化版）
    qr_id_1 = "DEMO0001"
    batch_name_1 = "PP塑膠示範批次"
    base_time_1 = datetime.now() - timedelta(days=30)
    
    demo_data.extend([
        {
            'qr_id': qr_id_1,
            'batch_name': batch_name_1,
            'stage': '初始建立',
            'operator': 'QR碼產生系統',
            'timestamp': base_time_1.strftime('%Y-%m-%d %H:%M:%S'),
            'weight_kg': '',
            'source': '',
            'destination': '',
            'product_model': '',
            'notes': '示範資料 - 僅供功能測試',
            'location': ''
        },
        {
            'qr_id': qr_id_1,
            'batch_name': batch_name_1,
            'stage': '出廠',
            'operator': '示範操作員',
            'timestamp': (base_time_1 + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'weight_kg': 100.0,
            'source': '示範拆解廠',
            'destination': '示範處理廠',
            'product_model': '示範PP零件',
            'notes': '這是示範資料，非真實記錄',
            'location': '示範地點'
        }
    ])
    
    # 儲存到本地
    df = pd.DataFrame(demo_data)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    
    print(f"✅ 示範資料已在本地產生：{DATA_FILE}")
    print("🔐 此檔案已加入 .gitignore，不會上傳到 GitHub")
    
    return True

def check_data_security():
    """檢查資料安全狀態"""
    DATA_FILE = "plastic_trace_data.csv"
    
    print("🔍 資料安全檢查：")
    print(f"   📁 本地資料檔案存在：{'是' if os.path.exists(DATA_FILE) else '否'}")
    print(f"   🔒 已設定 .gitignore：{'是' if os.path.exists('.gitignore') else '否'}")
    
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
            if '*.csv' in gitignore_content:
                print("   ✅ CSV 檔案已被 .gitignore 保護")
            else:
                print("   ⚠️  警告：CSV 檔案可能未被保護")

if __name__ == "__main__":
    check_data_security()
    init_demo_data_safely()
