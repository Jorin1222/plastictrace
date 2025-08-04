import streamlit as st
import pandas as pd
import qrcode
import io
import base64
from datetime import datetime
import os
import uuid
from PIL import Image

# 頁面配置
st.set_page_config(
    page_title="ELV 廢塑膠產銷履歷示範平台",
    page_icon="♻️",
    layout="wide"
)

# 資料檔案路徑
DATA_FILE = "plastic_trace_data.csv"

# 初始化資料檔案
def init_data_file():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            'qr_id', 'batch_name', 'stage', 'operator', 'timestamp', 
            'weight_kg', 'source', 'destination', 'product_model', 
            'notes', 'location'
        ])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# 載入資料
def load_data():
    init_data_file()
    return pd.read_csv(DATA_FILE, encoding='utf-8-sig')

# 儲存資料
def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# 產生QR碼
def generate_qr_code(qr_id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_id)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 轉換為可下載的格式
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# 產生下載連結
def get_download_link(file_buffer, filename, text):
    b64 = base64.b64encode(file_buffer.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">{text}</a>'
    return href

# 主標題
st.title("♻️ ELV 廢塑膠產銷履歷示範平台")
st.markdown("---")

# 側邊欄選單
st.sidebar.title("功能選單")
menu = st.sidebar.selectbox(
    "選擇功能",
    ["QR碼產生與管理", "掃描登錄資料", "履歷查詢", "資料下載", "系統管理"]
)

# QR碼產生與管理
if menu == "QR碼產生與管理":
    st.header("🏷️ QR碼產生與管理")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("產生新的QR碼")
        batch_name = st.text_input("批次名稱", placeholder="例：廢塑膠批次-001")
        
        if st.button("產生QR碼", type="primary"):
            if batch_name:
                # 產生唯一ID
                qr_id = str(uuid.uuid4())[:8].upper()
                
                # 產生QR碼
                qr_buffer = generate_qr_code(qr_id)
                
                # 顯示QR碼
                st.image(qr_buffer, caption=f"QR碼 ID: {qr_id}", width=200)
                
                # 提供下載連結
                st.markdown(
                    get_download_link(qr_buffer, f"QR_{qr_id}_{batch_name}.png", "📥 下載QR碼"),
                    unsafe_allow_html=True
                )
                
                # 將基本資訊存入資料庫
                df = load_data()
                new_record = {
                    'qr_id': qr_id,
                    'batch_name': batch_name,
                    'stage': '初始建立',
                    'operator': 'QR碼產生系統',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'weight_kg': '',
                    'source': '',
                    'destination': '',
                    'product_model': '',
                    'notes': f'QR碼已建立，批次：{batch_name}',
                    'location': ''
                }
                df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                save_data(df)
                
                st.success(f"✅ QR碼已產生！ID: {qr_id}")
            else:
                st.error("請輸入批次名稱")
    
    with col2:
        st.subheader("已建立的QR碼")
        df = load_data()
        qr_codes = df[df['stage'] == '初始建立'][['qr_id', 'batch_name', 'timestamp']].drop_duplicates()
        
        if not qr_codes.empty:
            st.dataframe(qr_codes, use_container_width=True)
        else:
            st.info("尚未建立任何QR碼")

# 掃描登錄資料
elif menu == "掃描登錄資料":
    st.header("📱 掃描登錄資料")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("輸入QR碼資訊")
        qr_id_input = st.text_input("QR碼 ID", placeholder="輸入或掃描獲得的QR碼ID").upper()
        
        # 驗證QR碼是否存在
        df = load_data()
        valid_qr = qr_id_input in df['qr_id'].values if qr_id_input else False
        
        if qr_id_input and valid_qr:
            st.success(f"✅ QR碼 {qr_id_input} 驗證成功")
            
            # 顯示歷史記錄
            history = df[df['qr_id'] == qr_id_input].sort_values('timestamp', ascending=False)
            st.subheader("歷史記錄")
            if not history.empty:
                st.dataframe(history[['stage', 'timestamp', 'operator', 'weight_kg']], use_container_width=True)
        elif qr_id_input and not valid_qr:
            st.error("❌ QR碼不存在，請檢查輸入")
    
    with col2:
        if qr_id_input and valid_qr:
            st.subheader("登錄新資料")
            
            with st.form("data_entry_form"):
                stage = st.selectbox(
                    "處理階段",
                    ["出廠", "運輸", "後端機構接收", "再生處理", "產品製造", "銷售"]
                )
                
                operator = st.text_input("操作人員", placeholder="輸入操作人員姓名")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    weight_kg = st.number_input("重量 (公斤)", min_value=0.0, step=0.1)
                with col_b:
                    location = st.text_input("地點", placeholder="處理地點")
                
                source = st.text_input("來源", placeholder="例：某某回收廠")
                destination = st.text_input("去向", placeholder="例：某某再生廠")
                product_model = st.text_input("產品型號", placeholder="例：再生塑膠粒 PP-001")
                notes = st.text_area("備註", placeholder="其他相關資訊")
                
                submit_button = st.form_submit_button("🔄 提交資料", type="primary")
                
                if submit_button:
                    if operator:
                        new_record = {
                            'qr_id': qr_id_input,
                            'batch_name': df[df['qr_id'] == qr_id_input]['batch_name'].iloc[0],
                            'stage': stage,
                            'operator': operator,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'weight_kg': weight_kg if weight_kg > 0 else '',
                            'source': source,
                            'destination': destination,
                            'product_model': product_model,
                            'notes': notes,
                            'location': location
                        }
                        
                        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                        save_data(df)
                        
                        st.success("✅ 資料已成功登錄！")
                        st.rerun()
                    else:
                        st.error("請輸入操作人員姓名")

# 履歷查詢
elif menu == "履歷查詢":
    st.header("🔍 履歷查詢")
    
    df = load_data()
    
    if df.empty:
        st.info("目前沒有任何資料")
    else:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("查詢條件")
            
            # 取得所有可用的QR碼
            available_qrs = df['qr_id'].unique()
            selected_qr = st.selectbox("選擇QR碼", ["全部"] + list(available_qrs))
            
            # 階段篩選
            available_stages = df['stage'].unique()
            selected_stages = st.multiselect("選擇階段", available_stages, default=available_stages)
            
            # 日期範圍
            st.subheader("日期範圍")
            date_filter = st.checkbox("啟用日期篩選")
            
            if date_filter:
                start_date = st.date_input("開始日期")
                end_date = st.date_input("結束日期")
        
        with col2:
            st.subheader("查詢結果")
            
            # 篩選資料
            filtered_df = df.copy()
            
            if selected_qr != "全部":
                filtered_df = filtered_df[filtered_df['qr_id'] == selected_qr]
            
            if selected_stages:
                filtered_df = filtered_df[filtered_df['stage'].isin(selected_stages)]
            
            if date_filter and 'start_date' in locals() and 'end_date' in locals():
                filtered_df['date'] = pd.to_datetime(filtered_df['timestamp']).dt.date
                filtered_df = filtered_df[
                    (filtered_df['date'] >= start_date) & 
                    (filtered_df['date'] <= end_date)
                ]
            
            # 顯示結果
            if not filtered_df.empty:
                st.dataframe(
                    filtered_df.sort_values('timestamp', ascending=False),
                    use_container_width=True
                )
                
                # 履歷視覺化
                if selected_qr != "全部":
                    st.subheader(f"QR碼 {selected_qr} 的完整履歷")
                    
                    qr_data = filtered_df[filtered_df['qr_id'] == selected_qr].sort_values('timestamp')
                    
                    for idx, row in qr_data.iterrows():
                        with st.expander(f"📅 {row['timestamp']} - {row['stage']}"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.write(f"**操作人員：** {row['operator']}")
                                st.write(f"**重量：** {row['weight_kg']} 公斤" if row['weight_kg'] else "**重量：** 未記錄")
                                st.write(f"**地點：** {row['location']}" if row['location'] else "**地點：** 未記錄")
                            with col_b:
                                st.write(f"**來源：** {row['source']}" if row['source'] else "**來源：** 未記錄")
                                st.write(f"**去向：** {row['destination']}" if row['destination'] else "**去向：** 未記錄")
                                st.write(f"**產品型號：** {row['product_model']}" if row['product_model'] else "**產品型號：** 未記錄")
                            if row['notes']:
                                st.write(f"**備註：** {row['notes']}")
            else:
                st.info("沒有符合條件的資料")

# 資料下載
elif menu == "資料下載":
    st.header("📥 資料下載")
    
    df = load_data()
    
    if df.empty:
        st.info("目前沒有任何資料可下載")
    else:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("資料統計")
            st.metric("總記錄數", len(df))
            st.metric("唯一QR碼數量", df['qr_id'].nunique())
            st.metric("處理階段數", df['stage'].nunique())
            
            # 各階段統計
            stage_counts = df['stage'].value_counts()
            st.subheader("各階段記錄數")
            for stage, count in stage_counts.items():
                st.write(f"• {stage}: {count} 筆")
        
        with col2:
            st.subheader("下載選項")
            
            # CSV下載
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📄 下載 CSV 檔案",
                data=csv_data,
                file_name=f"plastic_trace_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Excel下載
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='履歷資料', index=False)
                
                # 統計資料
                summary_df = pd.DataFrame({
                    '項目': ['總記錄數', '唯一QR碼數量', '處理階段數'],
                    '數量': [len(df), df['qr_id'].nunique(), df['stage'].nunique()]
                })
                summary_df.to_excel(writer, sheet_name='統計資料', index=False)
            
            st.download_button(
                label="📊 下載 Excel 檔案",
                data=excel_buffer.getvalue(),
                file_name=f"plastic_trace_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.info("💡 建議定期備份資料，保存期限至少五年")

# 系統管理
elif menu == "系統管理":
    st.header("⚙️ 系統管理")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("資料管理")
        
        df = load_data()
        st.write(f"當前資料記錄數：{len(df)}")
        st.write(f"資料檔案大小：{os.path.getsize(DATA_FILE) / 1024:.2f} KB" if os.path.exists(DATA_FILE) else "資料檔案不存在")
        
        # 清除所有資料
        if st.button("🗑️ 清除所有資料", type="secondary"):
            if st.checkbox("我確認要清除所有資料（此操作不可復原）"):
                empty_df = pd.DataFrame(columns=[
                    'qr_id', 'batch_name', 'stage', 'operator', 'timestamp', 
                    'weight_kg', 'source', 'destination', 'product_model', 
                    'notes', 'location'
                ])
                save_data(empty_df)
                st.success("✅ 所有資料已清除")
                st.rerun()
    
    with col2:
        st.subheader("系統資訊")
        st.write("**平台名稱：** ELV 廢塑膠產銷履歷示範平台")
        st.write("**版本：** 1.0.0")
        st.write("**技術架構：** Streamlit + Python")
        st.write("**資料儲存：** 本地 CSV")
        st.write("**建立日期：** 2025-08-04")
        
        st.subheader("使用說明")
        st.write("""
        1. **QR碼產生：** 為每批廢塑膠產生唯一QR碼
        2. **資料登錄：** 各階段人員掃描QR碼並填寫相關資料
        3. **履歷查詢：** 可追蹤完整的產銷履歷
        4. **資料下載：** 支援CSV/Excel格式匯出
        5. **行動支援：** 支援手機、平板、電腦操作
        """)

# 頁尾
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🌱 ELV 廢塑膠產銷履歷示範平台 | 促進循環經濟，提升可追溯性</p>
        <p>💚 為未來歐盟ELV廢塑膠再利用政策接軌做準備</p>
    </div>
    """, 
    unsafe_allow_html=True
)
