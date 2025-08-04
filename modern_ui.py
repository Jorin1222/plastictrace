"""
現代化網頁布局設計
採用響應式設計、卡片式布局和現代 UI 元素
"""

import streamlit as st

def apply_modern_css():
    """應用現代化 CSS 樣式"""
    st.markdown("""
    <style>
    /* 全域樣式設定 */
    .main > div {
        padding-top: 2rem;
    }
    
    /* 標題樣式 */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .sub-title {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* 卡片樣式 */
    .custom-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    /* 功能卡片 */
    .feature-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #0ea5e9;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
        transform: translateX(4px);
    }
    
    /* 狀態指示器 */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .status-success {
        background-color: #d1fae5;
        color: #065f46;
    }
    
    .status-warning {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    .status-info {
        background-color: #dbeafe;
        color: #1e40af;
    }
    
    /* 按鈕樣式 */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 8px -1px rgba(0, 0, 0, 0.15);
    }
    
    /* 側邊欄樣式 */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* 導航卡片 */
    .nav-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #3b82f6;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .nav-card:hover {
        background: #f8fafc;
        border-left-color: #1d4ed8;
    }
    
    /* 統計卡片 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-top: 4px solid #3b82f6;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* QR 碼展示區域 */
    .qr-display {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 2px dashed #d1d5db;
    }
    
    /* 表格樣式 */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* 頁腳樣式 */
    .footer {
        margin-top: 3rem;
        padding: 2rem 0;
        border-top: 1px solid #e5e7eb;
        text-align: center;
        color: #6b7280;
        background: #f9fafb;
    }
    
    /* 響應式設計 */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .custom-card {
            padding: 1rem;
        }
        
        .feature-card {
            padding: 1rem;
        }
    }
    
    /* 動畫效果 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* 載入動畫 */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)

def create_header():
    """創建現代化頁首"""
    st.markdown("""
    <div class="fade-in">
        <h1 class="main-title">♻️ ELV 廢塑膠產銷履歷示範平台</h1>
        <p class="sub-title">追蹤每一步，守護環境每一刻</p>
    </div>
    """, unsafe_allow_html=True)

def create_status_bar():
    """創建狀態列"""
    from data_manager import get_data_manager
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 獲取系統狀態
    dm = get_data_manager()
    storage_info = dm.get_storage_info()
    df = dm.load_data()
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">總記錄數</div>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        unique_qrs = df['qr_id'].nunique() if not df.empty else 0
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">QR碼數量</div>
        </div>
        """.format(unique_qrs), unsafe_allow_html=True)
    
    with col3:
        storage_type = "雲端" if storage_info["sheets_available"] else "本地"
        color = "#10b981" if storage_info["sheets_available"] else "#f59e0b"
        st.markdown("""
        <div class="metric-card" style="border-top-color: {}">
            <div class="metric-value" style="color: {}">{}</div>
            <div class="metric-label">存儲類型</div>
        </div>
        """.format(color, color, storage_type), unsafe_allow_html=True)
    
    with col4:
        user_role = st.session_state.get('user_role', 'guest')
        role_colors = {
            'admin': '#ef4444',
            'operator': '#3b82f6', 
            'viewer': '#6b7280'
        }
        role_names = {
            'admin': '管理員',
            'operator': '操作員',
            'viewer': '查看者'
        }
        color = role_colors.get(user_role, '#6b7280')
        name = role_names.get(user_role, '訪客')
        
        st.markdown("""
        <div class="metric-card" style="border-top-color: {}">
            <div class="metric-value" style="color: {}">{}</div>
            <div class="metric-label">使用者角色</div>
        </div>
        """.format(color, color, name), unsafe_allow_html=True)

def create_feature_card(title, description, icon, action_text="", action_key=""):
    """創建功能卡片"""
    action_button = ""
    if action_text and action_key:
        action_button = f'<br><button class="action-btn" onclick="document.getElementById(\'{action_key}\').click()">{action_text}</button>'
    
    return f"""
    <div class="feature-card">
        <h3 style="margin: 0 0 0.5rem 0; color: #1f2937; display: flex; align-items: center;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            {title}
        </h3>
        <p style="margin: 0; color: #6b7280; line-height: 1.5;">{description}</p>
        {action_button}
    </div>
    """

def create_navigation_sidebar():
    """創建現代化側邊欄導航"""
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h2 style="color: #1f2937; margin: 0;">功能選單</h2>
        <p style="color: #6b7280; margin: 0.5rem 0 0 0; font-size: 0.875rem;">選擇您需要的功能</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 根據角色顯示不同功能
    user_role = st.session_state.get('user_role', 'guest')
    
    if user_role == 'admin':
        menu_options = [
            ("🏷️", "QR碼產生與管理", "建立和管理 QR 碼"),
            ("📱", "掃描登錄資料", "掃描 QR 碼並登錄資料"),
            ("🔍", "履歷查詢", "查詢產品履歷記錄"),
            ("📥", "資料下載", "匯出和下載資料"),
            ("⚙️", "系統管理", "系統設定與管理")
        ]
    elif user_role == 'operator':
        menu_options = [
            ("🏷️", "QR碼產生與管理", "建立和管理 QR 碼"),
            ("📱", "掃描登錄資料", "掃描 QR 碼並登錄資料"),
            ("🔍", "履歷查詢", "查詢產品履歷記錄"),
            ("📥", "資料下載", "匯出和下載資料")
        ]
    else:  # viewer
        menu_options = [
            ("🔍", "履歷查詢", "查詢產品履歷記錄"),
            ("📥", "資料下載", "匯出和下載資料")
        ]
    
    selected_menu = None
    for icon, title, desc in menu_options:
        if st.sidebar.button(f"{icon} {title}", key=f"nav_{title}", use_container_width=True):
            selected_menu = title
        
        # 添加功能描述
        st.sidebar.markdown(f"""
        <div style="margin: -0.5rem 0 1rem 2rem; color: #6b7280; font-size: 0.75rem;">
            {desc}
        </div>
        """, unsafe_allow_html=True)
    
    return selected_menu

def create_quick_actions():
    """創建快速操作區域"""
    st.markdown("### 🚀 快速操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🆕 建立新 QR 碼", use_container_width=True):
            st.session_state['quick_action'] = 'new_qr'
    
    with col2:
        if st.button("📊 查看統計", use_container_width=True):
            st.session_state['quick_action'] = 'view_stats'
    
    with col3:
        if st.button("🔄 同步資料", use_container_width=True):
            st.session_state['quick_action'] = 'sync_data'
