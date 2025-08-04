import streamlit as st
import pandas as pd
import qrcode
import io
import base64
from datetime import datetime
import os
import uuid
from PIL import Image
import hashlib
import zipfile
from io import BytesIO

# 頁面配置
st.set_page_config(
    page_title="ELV 廢塑膠產銷履歷示範平台",
    page_icon="♻️",
    layout="wide"
)

# 預設帳號密碼 (實際使用時應存放在安全的地方)
DEFAULT_USERS = {
    "admin": "admin123",
    "operator": "op2024",
    "viewer": "view2024"
}

# 資料檔案路徑
DATA_FILE = "plastic_trace_data.csv"

# 登入檢查函數
def check_login():
    """檢查是否已登入"""
    return st.session_state.get('logged_in', False)

def get_user_role():
    """獲取當前使用者角色"""
    return st.session_state.get('user_role', 'guest')

def login_user(username, password):
    """使用者登入"""
    if username in DEFAULT_USERS and DEFAULT_USERS[username] == password:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        # 設定角色
        if username == "admin":
            st.session_state['user_role'] = 'admin'
        elif username == "operator":
            st.session_state['user_role'] = 'operator'
        else:
            st.session_state['user_role'] = 'viewer'
        return True
    return False

def logout_user():
    """使用者登出"""
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['user_role'] = 'guest'

def is_scan_page():
    """檢查是否為掃描登錄頁面"""
    try:
        qr_id_from_url = st.query_params.get("qr_id", "")
        page_from_url = st.query_params.get("page", "")
        return qr_id_from_url and page_from_url == "scan"
    except:
        return False

def show_login_form():
    """顯示登入表單"""
    st.title("🔐 系統登入")
    st.markdown("### 請輸入帳號密碼以使用系統功能")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("帳號", placeholder="請輸入帳號")
            password = st.text_input("密碼", type="password", placeholder="請輸入密碼")
            login_button = st.form_submit_button("登入", type="primary")
            
            if login_button:
                if login_user(username, password):
                    st.success(f"✅ 歡迎 {username} 登入系統！")
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤")
        
        st.markdown("---")
        st.info("""
        **📋 測試帳號：**
        - 管理員：admin / admin123
        - 操作員：operator / op2024  
        - 查看者：viewer / view2024
        
        **ℹ️ 說明：**
        - 只有掃描QR碼進行資料登錄不需要登入
        - 其他功能需要登入後才能使用
        """)

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
def generate_qr_code(qr_id, base_url=None):
    """產生可掃描的QR碼，包含直接跳轉到登錄頁面的網址"""
    # 自動偵測部署環境並使用對應的網址
    if base_url is None:
        def is_streamlit_cloud():
            """檢查是否在 Streamlit Cloud 環境"""
            return (
                os.getenv('STREAMLIT_SHARING_MODE') is not None or
                os.getenv('HOSTNAME', '').endswith('.streamlit.app') or
                'streamlit.app' in os.getenv('SERVER_NAME', '') or
                not os.getenv('COMPUTERNAME')  # Windows 本地環境會有這個變數
            )
        
        if is_streamlit_cloud():
            base_url = "https://plastictracetest.streamlit.app"
        else:
            base_url = "http://localhost:8501"
    
    # 構建完整的網址，包含QR碼ID參數
    full_url = f"{base_url}/?qr_id={qr_id}&page=scan"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(full_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 轉換為可下載的格式
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf, full_url

# 產生下載連結
def get_download_link(file_buffer, filename, text):
    b64 = base64.b64encode(file_buffer.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">{text}</a>'
    return href

def show_scan_interface():
    """顯示掃描登錄介面（公開功能）"""
    # 如果不是掃描頁面，顯示標題
    if not is_scan_page():
        st.title("♻️ ELV 廢塑膠產銷履歷示範平台")
        st.markdown("---")
    
    st.header("📱 掃描登錄資料")
    
    # 檢查是否透過QR碼掃描進入
    qr_id_from_url = ""
    try:
        qr_id_from_url = st.query_params.get("qr_id", "")
        if qr_id_from_url:
            st.success(f"🔍 已掃描QR碼: {qr_id_from_url}")
            st.info("請在下方填寫此批次的詳細資料")
    except:
        pass
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("輸入QR碼資訊")
        
        # 檢查是否從QR碼掃描進入
        try:
            default_qr_id = st.query_params.get("qr_id", "").upper()
        except:
            default_qr_id = ""
        
        qr_id_input = st.text_input(
            "QR碼 ID", 
            value=default_qr_id,
            placeholder="輸入或掃描獲得的QR碼ID"
        ).upper()
        
        if default_qr_id:
            st.success(f"🔍 已從QR碼掃描自動填入: {default_qr_id}")
        
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

def show_main_interface():
    """顯示主要功能介面（需要登入）"""
    # 主標題和使用者資訊
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("♻️ ELV 廢塑膠產銷履歷示範平台")
    with col2:
        st.success(f"👤 {st.session_state.get('username', 'User')} ({get_user_role()})")
        if st.button("登出"):
            logout_user()
            st.rerun()

    # 🔒 資料安全提醒 + 部署狀態
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        if os.path.exists(DATA_FILE):
            st.success("🔐 使用本地資料（安全模式）")
        else:
            st.info("🧪 首次使用，將建立示範資料")

    with col2:
        # 檢查部署環境
        def is_streamlit_cloud():
            """檢查是否在 Streamlit Cloud 環境"""
            return (
                os.getenv('STREAMLIT_SHARING_MODE') is not None or
                os.getenv('HOSTNAME', '').endswith('.streamlit.app') or
                'streamlit.app' in os.getenv('SERVER_NAME', '') or
                not os.getenv('COMPUTERNAME')  # Windows 本地環境會有這個變數
            )
        
        if is_streamlit_cloud():
            st.success("🌐 線上版本 (Streamlit Cloud)")
            st.caption("QR碼可全球掃描使用")
        else:
            st.warning("🏠 本地版本")
            st.caption("QR碼僅限區網使用")
            
    with col3:
        if st.button("🔍 狀態"):
            try:
                if 'STREAMLIT_SERVER_PORT' in os.environ:
                    st.info("""
                    **🌐 線上部署狀態：**
                    - ✅ 全球存取
                    - ✅ 手機可掃描QR碼
                    - ✅ 即時資料同步
                    - 🔗 網址：plastictracetest.streamlit.app
                    """)
                else:
                    st.info("""
                    **🏠 本地開發狀態：**
                    - ✅ 區網內可用
                    - ⚠️ 需部署才能手機展示
                    - 💡 建議部署到 Streamlit Cloud
                    """)
            except:
                st.info("開發環境狀態檢查")

    st.markdown("---")

    # 側邊欄選單
    st.sidebar.title("功能選單")
    
    # 根據角色顯示不同功能
    user_role = get_user_role()
    
    if user_role == 'admin':
        menu_options = ["QR碼產生與管理", "掃描登錄資料", "履歷查詢", "資料下載", "系統管理"]
    elif user_role == 'operator':
        menu_options = ["QR碼產生與管理", "掃描登錄資料", "履歷查詢", "資料下載"]
    else:  # viewer
        menu_options = ["履歷查詢", "資料下載"]
    
    menu = st.sidebar.selectbox("選擇功能", menu_options)
    
    # 功能路由
    if menu == "QR碼產生與管理":
        show_qr_management()
    elif menu == "掃描登錄資料":
        show_scan_interface()
    elif menu == "履歷查詢":
        show_query_interface()
    elif menu == "資料下載":
        show_download_interface()
    elif menu == "系統管理":
        show_admin_interface()

def show_qr_management():
    """QR碼產生與管理功能"""
    st.header("🏷️ QR碼產生與管理")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("產生新的QR碼")
        batch_name = st.text_input("批次名稱", placeholder="例：廢塑膠批次-001")
        
        if st.button("產生QR碼", type="primary"):
            if batch_name:
                # 產生唯一ID
                qr_id = str(uuid.uuid4())[:8].upper()
                
                # 產生包含自動偵測網址的QR碼
                qr_buffer, qr_url = generate_qr_code(qr_id)
                
                # 顯示QR碼
                st.image(qr_buffer, caption=f"QR碼 ID: {qr_id}", width=200)
                
                # 顯示QR碼包含的網址
                st.code(qr_url, language="text")
                
                # 根據環境顯示不同的說明
                if "streamlit.app" in qr_url:
                    st.success("🌐 **線上版本QR碼** - 任何地方都可掃描使用！")
                    st.caption("📱 用手機掃描此QR碼可直接跳轉到資料登錄頁面")
                else:
                    st.info("🏠 **本地版本QR碼** - 僅限此電腦網路環境使用")
                    st.caption("📡 部署到 Streamlit Cloud 後將自動產生公開版本")
                
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
                    'operator': f'{st.session_state.get("username", "系統")} (QR碼產生)',
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
            
            # 添加QR碼下載功能
            st.subheader("下載已建立的QR碼")
            
            # 選擇要下載的QR碼
            selected_qr = st.selectbox(
                "選擇要下載的QR碼", 
                options=qr_codes['qr_id'].tolist(),
                format_func=lambda x: f"{x} - {qr_codes[qr_codes['qr_id']==x]['batch_name'].iloc[0]}"
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("📥 下載單個QR碼", type="secondary"):
                    if selected_qr:
                        # 產生選中的QR碼
                        qr_buffer, qr_url = generate_qr_code(selected_qr)
                        batch_name = qr_codes[qr_codes['qr_id']==selected_qr]['batch_name'].iloc[0]
                        
                        # 顯示QR碼
                        st.image(qr_buffer, caption=f"QR碼: {selected_qr}", width=150)
                        
                        # 提供下載連結
                        st.markdown(
                            get_download_link(qr_buffer, f"QR_{selected_qr}_{batch_name}.png", "📥 點擊下載"),
                            unsafe_allow_html=True
                        )
                        
                        st.info(f"🔗 QR碼網址：{qr_url}")
            
            with col_b:
                if st.button("📦 批量下載所有QR碼", type="secondary"):
                    # 建立一個臨時的zip檔案來包含所有QR碼
                    import zipfile
                    from io import BytesIO
                    
                    zip_buffer = BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for _, row in qr_codes.iterrows():
                            qr_id = row['qr_id']
                            batch_name = row['batch_name']
                            
                            # 產生QR碼
                            qr_buffer, qr_url = generate_qr_code(qr_id)
                            
                            # 將QR碼圖片加入zip檔案
                            filename = f"QR_{qr_id}_{batch_name}.png"
                            zip_file.writestr(filename, qr_buffer.getvalue())
                            
                            # 建立包含QR碼資訊的文字檔
                            info_content = f"""QR碼資訊
ID: {qr_id}
批次名稱: {batch_name}
建立時間: {row['timestamp']}
網址: {qr_url}
"""
                            info_filename = f"QR_{qr_id}_{batch_name}_info.txt"
                            zip_file.writestr(info_filename, info_content.encode('utf-8'))
                    
                    zip_buffer.seek(0)
                    
                    # 提供zip檔案下載
                    st.download_button(
                        label="📦 下載所有QR碼 (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"所有QR碼_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )
                    
                    st.success(f"✅ 已準備 {len(qr_codes)} 個QR碼的ZIP檔案")
        else:
            st.info("尚未建立任何QR碼")

def show_query_interface():
    """履歷查詢功能"""
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

def show_download_interface():
    """資料下載功能"""
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
            st.subheader("各階段統計")
            for stage, count in stage_counts.items():
                st.write(f"**{stage}：** {count} 筆")
        
        with col2:
            st.subheader("下載選項")
            
            # 選擇下載格式
            download_format = st.selectbox("選擇下載格式", ["CSV", "Excel"])
            
            # 選擇下載範圍
            download_scope = st.selectbox("選擇下載範圍", ["全部資料", "指定QR碼"])
            
            if download_scope == "指定QR碼":
                available_qrs = df['qr_id'].unique()
                selected_qrs = st.multiselect("選擇QR碼", available_qrs)
                if selected_qrs:
                    df = df[df['qr_id'].isin(selected_qrs)]
            
            # 下載按鈕
            if st.button("📥 準備下載", type="primary"):
                if download_format == "CSV":
                    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="下載 CSV 檔案",
                        data=csv_data,
                        file_name=f"plastic_trace_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:  # Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='履歷資料')
                    
                    st.download_button(
                        label="下載 Excel 檔案",
                        data=output.getvalue(),
                        file_name=f"plastic_trace_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

def show_admin_interface():
    """系統管理功能（僅管理員可用）"""
    if get_user_role() != 'admin':
        st.error("❌ 此功能僅限管理員使用")
        return
    
    st.header("⚙️ 系統管理")
    
    tab1, tab2, tab3 = st.tabs(["使用者管理", "資料管理", "系統資訊"])
    
    with tab1:
        st.subheader("使用者帳號")
        st.info("目前使用預設帳號系統，可在此查看帳號資訊")
        
        users_df = pd.DataFrame([
            {"帳號": "admin", "角色": "管理員", "權限": "完整存取"},
            {"帳號": "operator", "角色": "操作員", "權限": "QR碼管理、資料登錄、查詢、下載"},
            {"帳號": "viewer", "角色": "查看者", "權限": "僅查詢與下載"}
        ])
        st.dataframe(users_df, use_container_width=True)
    
    with tab2:
        st.subheader("資料庫管理")
        
        df = load_data()
        st.metric("總資料筆數", len(df))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 清空所有資料", type="secondary"):
                if st.checkbox("確認清空（此操作無法復原）"):
                    # 清空資料檔案
                    empty_df = pd.DataFrame(columns=[
                        'qr_id', 'batch_name', 'stage', 'operator', 'timestamp', 
                        'weight_kg', 'source', 'destination', 'product_model', 
                        'notes', 'location'
                    ])
                    save_data(empty_df)
                    st.success("✅ 資料已清空")
                    st.rerun()
        
        with col2:
            if st.button("📊 匯出備份"):
                backup_data = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下載備份檔案",
                    data=backup_data,
                    file_name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with tab3:
        st.subheader("系統資訊")
        
        # 檢查部署環境
        def is_streamlit_cloud():
            """檢查是否在 Streamlit Cloud 環境"""
            return (
                os.getenv('STREAMLIT_SHARING_MODE') is not None or
                os.getenv('HOSTNAME', '').endswith('.streamlit.app') or
                'streamlit.app' in os.getenv('SERVER_NAME', '') or
                not os.getenv('COMPUTERNAME')  # Windows 本地環境會有這個變數
            )
        
        env_status = "Streamlit Cloud" if is_streamlit_cloud() else "本地環境"
        st.info(f"部署環境：{env_status}")
        
        # 系統狀態
        st.write("**版本資訊：**")
        st.write("- 平台版本：v1.0.0")
        st.write("- 最後更新：2024-08-04")
        st.write("- 版權：財團法人台灣產業服務基金會")

# 主程式邏輯 - 權限控制
def main():
    # 檢查是否為掃描頁面（不需要登入）
    if is_scan_page():
        show_scan_interface()
        return
    
    # 檢查登入狀態
    if not check_login():
        show_login_form()
        return
    
    # 已登入，顯示完整功能介面
    show_main_interface()

# 版權聲明
st.markdown("---")
st.markdown("**© 2024 財團法人台灣產業服務基金會 Taiwan Industry Service Foundation**")

# 主程式執行
if __name__ == "__main__":
    main()
