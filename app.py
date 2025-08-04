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
# 匯入新的資料管理器
from data_manager import get_data_manager, load_data, save_data
# 匯入現代化 UI 元件
from modern_ui import apply_modern_css, create_header, create_status_bar, create_navigation_sidebar, create_quick_actions

# 頁面配置
st.set_page_config(
    page_title="ELV 廢塑膠產銷履歷示範平台",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 應用現代化樣式
apply_modern_css()

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
    """顯示現代化登入表單"""
    # 應用樣式
    apply_modern_css()
    
    # 頁首
    create_header()
    
    st.markdown("""
    <div class="custom-card" style="max-width: 400px; margin: 2rem auto;">
        <h3 style="text-align: center; color: #1f2937; margin-bottom: 1.5rem;">🔐 系統登入</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### 請輸入帳號密碼")
            username = st.text_input("帳號", placeholder="請輸入帳號")
            password = st.text_input("密碼", type="password", placeholder="請輸入密碼")
            login_button = st.form_submit_button("登入", type="primary", use_container_width=True)
            
            if login_button:
                if login_user(username, password):
                    st.success(f"✅ 歡迎 {username} 登入系統！")
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 測試帳號資訊卡片
        st.markdown("""
        <div class="feature-card" style="margin-top: 2rem;">
            <h4 style="margin: 0 0 1rem 0; color: #1f2937;">📋 測試帳號</h4>
            <div style="display: grid; gap: 0.5rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>管理員：</strong></span>
                    <span>admin / admin123</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>操作員：</strong></span>
                    <span>operator / op2024</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>查看者：</strong></span>
                    <span>viewer / view2024</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="custom-card" style="margin-top: 1rem; background: #f0f9ff;">
            <p style="margin: 0; color: #0369a1; text-align: center;">
                <strong>ℹ️ 說明：</strong><br>
                只有掃描QR碼進行資料登錄不需要登入<br>
                其他功能需要登入後才能使用
            </p>
        </div>
        """, unsafe_allow_html=True)

# 初始化資料檔案
def init_data_file():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            'qr_id', 'batch_name', 'stage', 'operator', 'timestamp', 
            'weight_kg', 'source', 'destination', 'product_model', 
            'notes', 'location'
        ])
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
    """顯示現代化主要功能介面"""
    # 應用現代化樣式
    apply_modern_css()
    
    # 創建頁首
    create_header()
    
    # 用戶資訊和登出按鈕
    col1, col2 = st.columns([4, 1])
    with col2:
        username = st.session_state.get('username', 'User')
        user_role = st.session_state.get('user_role', 'guest')
        role_colors = {'admin': '🔴', 'operator': '🔵', 'viewer': '⚪'}
        role_icon = role_colors.get(user_role, '⚫')
        
        st.markdown(f"""
        <div class="custom-card" style="text-align: center; padding: 1rem;">
            <div style="color: #1f2937; font-weight: 600;">{role_icon} {username}</div>
            <div style="color: #6b7280; font-size: 0.875rem;">{user_role}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("登出", type="secondary", use_container_width=True):
            logout_user()
            st.rerun()

    # 系統狀態卡片
    st.markdown("### 📊 系統狀態")
    create_status_bar()
    
    st.markdown("---")

    # 側邊欄導航
    selected_menu = create_navigation_sidebar()
    
    # 如果沒有選擇功能，顯示歡迎頁面
    if not selected_menu and not st.session_state.get('current_page'):
        show_welcome_dashboard()
    else:
        # 更新當前頁面
        if selected_menu:
            st.session_state['current_page'] = selected_menu
        
        # 根據選擇的功能顯示對應介面
        current_page = st.session_state.get('current_page', '歡迎頁面')
        
        if current_page == "QR碼產生與管理":
            show_qr_management()
        elif current_page == "掃描登錄資料":
            show_scan_interface()
        elif current_page == "履歷查詢":
            show_query_interface()
        elif current_page == "資料下載":
            show_download_interface()
        elif current_page == "系統管理":
            show_admin_interface()

def show_welcome_dashboard():
    """顯示歡迎儀表板"""
    st.markdown("### 🏠 歡迎使用 ELV 廢塑膠產銷履歷示範平台")
    
    # 快速操作
    create_quick_actions()
    
    # 處理快速操作
    if st.session_state.get('quick_action'):
        action = st.session_state['quick_action']
        if action == 'new_qr':
            st.session_state['current_page'] = "QR碼產生與管理"
            st.rerun()
        elif action == 'view_stats':
            show_system_overview()
        elif action == 'sync_data':
            dm = get_data_manager()
            if dm.use_sheets:
                dm.sync_to_sheets()
            else:
                st.info("📁 本地模式不需要同步")
        del st.session_state['quick_action']
    
    st.markdown("---")
    
    # 系統概覽
    show_system_overview()
    
    # 最近活動
    show_recent_activities()

def show_system_overview():
    """顯示系統概覽"""
    st.markdown("### � 系統概覽")
    
    df = load_data()
    
    if df.empty:
        st.markdown("""
        <div class="custom-card" style="text-align: center; padding: 3rem;">
            <h3 style="color: #6b7280; margin: 0;">📊 尚無資料</h3>
            <p style="color: #9ca3af; margin: 1rem 0;">開始建立您的第一個 QR 碼吧！</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 階段統計
        st.markdown("#### 🔄 處理階段統計")
        stage_counts = df['stage'].value_counts()
        
        for stage, count in stage_counts.items():
            percentage = (count / len(df)) * 100
            st.markdown(f"""
            <div class="custom-card" style="margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 500;">{stage}</span>
                    <span style="color: #3b82f6; font-weight: 600;">{count} 筆 ({percentage:.1f}%)</span>
                </div>
                <div style="background: #e5e7eb; border-radius: 4px; height: 6px; margin-top: 0.5rem;">
                    <div style="background: #3b82f6; height: 100%; border-radius: 4px; width: {percentage}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # QR 碼狀態
        st.markdown("#### 🏷️ QR 碼狀態")
        qr_codes = df[df['stage'] == '初始建立']['qr_id'].nunique()
        active_qrs = df[df['stage'] != '初始建立']['qr_id'].nunique()
        
        st.markdown(f"""
        <div class="custom-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <span>總 QR 碼數量</span>
                <span style="font-weight: 600; color: #1f2937;">{qr_codes}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <span>活躍 QR 碼</span>
                <span style="font-weight: 600; color: #059669;">{active_qrs}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>使用率</span>
                <span style="font-weight: 600; color: #3b82f6;">{(active_qrs/qr_codes*100) if qr_codes > 0 else 0:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_recent_activities():
    """顯示最近活動"""
    st.markdown("### 📱 最近活動")
    
    df = load_data()
    
    if df.empty:
        st.info("📭 暫無活動記錄")
        return
    
    # 取最近 5 筆記錄
    recent_df = df.sort_values('timestamp', ascending=False).head(5)
    
    for _, row in recent_df.iterrows():
        time_str = row['timestamp']
        stage_colors = {
            '初始建立': '#10b981',
            '出廠': '#3b82f6',
            '運輸': '#f59e0b',
            '再生處理': '#8b5cf6',
            '產品製造': '#ef4444',
            '銷售': '#06b6d4'
        }
        
        color = stage_colors.get(row['stage'], '#6b7280')
        
        st.markdown(f"""
        <div class="custom-card" style="border-left: 4px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 600; color: #1f2937;">{row['stage']} - {row['qr_id']}</div>
                    <div style="color: #6b7280; font-size: 0.875rem;">操作員: {row['operator']}</div>
                </div>
                <div style="text-align: right; color: #6b7280; font-size: 0.875rem;">
                    {time_str}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_qr_management():
    """現代化 QR 碼產生與管理功能"""
    st.markdown("## 🏷️ QR 碼產生與管理")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <h3 style="margin: 0 0 1rem 0; color: #1f2937;">✨ 產生新的 QR 碼</h3>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            batch_name = st.text_input(
                "批次名稱", 
                placeholder="例：廢塑膠批次-001",
                help="為您的批次命名，便於後續追蹤"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🎯 產生 QR 碼", type="primary", use_container_width=True):
                    if batch_name:
                        # 產生唯一ID
                        qr_id = str(uuid.uuid4())[:8].upper()
                        
                        # 產生包含自動偵測網址的QR碼
                        qr_buffer, qr_url = generate_qr_code(qr_id)
                        
                        # QR 碼展示區域
                        st.markdown(f"""
                        <div class="qr-display">
                            <h4 style="margin: 0 0 1rem 0;">🎉 QR 碼已生成！</h4>
                            <p style="margin: 0 0 1rem 0; color: #6b7280;">QR 碼 ID: <strong>{qr_id}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
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
            
            with col_b:
                st.markdown("""
                <div class="feature-card">
                    <h4 style="margin: 0 0 0.5rem 0;">💡 小提示</h4>
                    <ul style="margin: 0; padding-left: 1rem; color: #6b7280;">
                        <li>建議使用有意義的批次名稱</li>
                        <li>QR碼ID會自動生成</li>
                        <li>可直接用手機掃描測試</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <h3 style="margin: 0 0 1rem 0; color: #1f2937;">📋 已建立的 QR 碼</h3>
        </div>
        """, unsafe_allow_html=True)
        
        df = load_data()
        qr_codes = df[df['stage'] == '初始建立'][['qr_id', 'batch_name', 'timestamp']].drop_duplicates()
        
        if not qr_codes.empty:
            # 顯示QR碼列表
            for _, row in qr_codes.iterrows():
                st.markdown(f"""
                <div class="custom-card" style="margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #1f2937;">{row['qr_id']}</div>
                            <div style="color: #6b7280; font-size: 0.875rem;">{row['batch_name']}</div>
                        </div>
                        <div style="color: #6b7280; font-size: 0.75rem;">
                            {row['timestamp'][:10]}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 下載功能區域
            st.markdown("### 📥 下載 QR 碼")
            
            # 選擇要下載的QR碼
            selected_qr = st.selectbox(
                "選擇要下載的QR碼", 
                options=qr_codes['qr_id'].tolist(),
                format_func=lambda x: f"{x} - {qr_codes[qr_codes['qr_id']==x]['batch_name'].iloc[0]}"
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("📥 下載單個QR碼", type="secondary", use_container_width=True):
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
                if st.button("📦 批量下載所有QR碼", type="secondary", use_container_width=True):
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
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    st.success(f"✅ 已準備 {len(qr_codes)} 個QR碼的ZIP檔案")
        else:
            st.markdown("""
            <div class="custom-card" style="text-align: center; padding: 2rem;">
                <h4 style="color: #6b7280; margin: 0;">📋 尚未建立任何QR碼</h4>
                <p style="color: #9ca3af; margin: 1rem 0 0 0;">開始建立您的第一個QR碼吧！</p>
            </div>
            """, unsafe_allow_html=True)

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
    
    tab1, tab2, tab3, tab4 = st.tabs(["使用者管理", "資料管理", "Google Sheets", "系統資訊"])
    
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
        st.subheader("Google Sheets 管理")
        
        # 獲取資料管理器
        dm = get_data_manager()
        storage_info = dm.get_storage_info()
        
        # 顯示 Google Sheets 狀態
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Google Sheets 狀態：**")
            if storage_info["sheets_available"]:
                st.success("✅ Google Sheets 已連接")
                if storage_info.get("sheet_url"):
                    st.markdown(f"📊 [開啟試算表]({storage_info['sheet_url']})")
            else:
                st.error("❌ Google Sheets 未連接")
                st.info("請檢查認證設定或網路連線")
            
            st.write("**本地備份狀態：**")
            if storage_info["backup_available"]:
                st.success("✅ 本地備份檔案存在")
            else:
                st.warning("⚠️ 無本地備份檔案")
        
        with col2:
            st.write("**管理操作：**")
            
            # 環境診斷
            if st.button("🔍 環境診斷"):
                st.session_state['show_env_debug'] = True
                dm_new = get_data_manager()
                st.session_state['show_env_debug'] = False
                
                # 顯示詳細的環境資訊
                env_info = {
                    'STREAMLIT_SHARING_MODE': os.getenv('STREAMLIT_SHARING_MODE'),
                    'HOSTNAME': os.getenv('HOSTNAME', ''),
                    'SERVER_NAME': os.getenv('SERVER_NAME', ''),
                    'HOME': os.getenv('HOME', ''),
                    'USER': os.getenv('USER', ''),
                }
                
                st.write("**環境變數：**")
                for key, value in env_info.items():
                    if value:
                        st.write(f"   {key}: {value}")
                    else:
                        st.write(f"   {key}: (未設定)")
                
                # 檢查 Secrets
                if hasattr(st, 'secrets'):
                    if "gcp_service_account" in st.secrets:
                        st.success("✅ 找到 gcp_service_account secrets")
                        # 顯示 secrets 的欄位（不顯示實際值）
                        secrets_keys = list(st.secrets["gcp_service_account"].keys())
                        st.write(f"   可用欄位: {', '.join(secrets_keys)}")
                    else:
                        st.error("❌ 找不到 gcp_service_account secrets")
                        st.write("   可用的 secrets:", list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else "無")
            
            # 測試連接
            if st.button("🔍 測試 Google Sheets 連接"):
                if storage_info["sheets_available"]:
                    try:
                        sheets_manager = dm.sheets_manager
                        if sheets_manager and sheets_manager.test_connection():
                            st.success("✅ Google Sheets 連接正常")
                        else:
                            st.error("❌ Google Sheets 連接測試失敗")
                    except Exception as e:
                        st.error(f"❌ 連接測試失敗: {str(e)}")
                else:
                    st.error("❌ Google Sheets 不可用")
            
            # 手動同步
            if st.button("🔄 同步本地資料到 Google Sheets"):
                if storage_info["backup_available"]:
                    dm.sync_to_sheets()
                else:
                    st.warning("⚠️ 沒有本地資料可同步")
            
            # 重新初始化
            if st.button("🔁 重新初始化 Google Sheets"):
                try:
                    # 重新獲取資料管理器
                    global data_manager
                    data_manager = None  # 清除快取
                    dm_new = get_data_manager()
                    st.success("✅ Google Sheets 已重新初始化")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 重新初始化失敗: {str(e)}")
        
        # 設定說明
        st.markdown("---")
        st.subheader("Google Sheets 設定說明")
        
        with st.expander("📋 設定步驟"):
            st.markdown("""
            **1. 建立 Google Cloud 專案：**
            - 前往 [Google Cloud Console](https://console.cloud.google.com/)
            - 建立新專案或選擇現有專案
            
            **2. 啟用 API：**
            - 啟用 Google Sheets API
            - 啟用 Google Drive API
            
            **3. 建立服務帳號：**
            - 前往「IAM 和管理」→「服務帳號」
            - 建立新的服務帳號
            - 下載 JSON 金鑰檔案
            
            **4. 設定認證：**
            - **本地開發**：將 JSON 檔案重新命名為 `service_account.json` 並放在專案根目錄
            - **Streamlit Cloud**：在 Secrets 中設定 `gcp_service_account` 部分
            
            **5. 分享試算表：**
            - 將服務帳號的電子郵件地址加入試算表的編輯者
            """)
    
    with tab4:
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
        st.write("- 最後更新：2025-08-04")
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
st.markdown("**© 2025 財團法人台灣產業服務基金會 Foundation of Taiwan Industry Service**")

# 主程式執行
if __name__ == "__main__":
    main()
