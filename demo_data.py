import streamlit as st

def main():
    """
    示範資料生成器
    用於建立 ELV 廢塑膠產銷履歷示範平台的測試資料
    """
    st.title("🧪 示範資料生成器")
    st.markdown("---")
    
    if st.button("產生示範資料", type="primary"):
        import pandas as pd
        from datetime import datetime, timedelta
        import uuid
        
        # 建立示範資料
        demo_data = []
        
        # 示範批次 1: PP塑膠批次
        qr_id_1 = "DEMO0001"
        batch_name_1 = "PP塑膠批次-001"
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
                'notes': f'QR碼已建立，批次：{batch_name_1}',
                'location': ''
            },
            {
                'qr_id': qr_id_1,
                'batch_name': batch_name_1,
                'stage': '出廠',
                'operator': '張小明',
                'timestamp': (base_time_1 + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 500.0,
                'source': '報廢車輛拆解廠',
                'destination': '環保回收處理廠',
                'product_model': 'PP塑膠零件',
                'notes': '來自汽車儀表板、保險桿等部件',
                'location': '台北市'
            },
            {
                'qr_id': qr_id_1,
                'batch_name': batch_name_1,
                'stage': '運輸',
                'operator': '李運輸',
                'timestamp': (base_time_1 + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 500.0,
                'source': '報廢車輛拆解廠',
                'destination': '環保回收處理廠',
                'product_model': 'PP塑膠零件',
                'notes': '運輸過程順利，無損失',
                'location': '運輸途中'
            },
            {
                'qr_id': qr_id_1,
                'batch_name': batch_name_1,
                'stage': '後端機構接收',
                'operator': '王處理員',
                'timestamp': (base_time_1 + timedelta(days=1, hours=4)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 498.5,
                'source': '運輸公司',
                'destination': '再生塑膠廠',
                'product_model': 'PP塑膠零件',
                'notes': '分類檢查完畢，去除雜質',
                'location': '桃園市'
            },
            {
                'qr_id': qr_id_1,
                'batch_name': batch_name_1,
                'stage': '再生處理',
                'operator': '陳技師',
                'timestamp': (base_time_1 + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 450.0,
                'source': '分類後PP塑膠',
                'destination': '塑膠製品廠',
                'product_model': '再生PP塑膠粒',
                'notes': '破碎、清洗、造粒完成',
                'location': '台中市'
            },
            {
                'qr_id': qr_id_1,
                'batch_name': batch_name_1,
                'stage': '產品製造',
                'operator': '林製造',
                'timestamp': (base_time_1 + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 425.0,
                'source': '再生PP塑膠粒',
                'destination': '銷售通路',
                'product_model': '環保收納盒 ECO-BOX-001',
                'notes': '製造成環保收納盒 200個',
                'location': '台南市'
            }
        ])
        
        # 示範批次 2: PE塑膠批次
        qr_id_2 = "DEMO0002"
        batch_name_2 = "PE塑膠批次-002"
        base_time_2 = datetime.now() - timedelta(days=20)
        
        demo_data.extend([
            {
                'qr_id': qr_id_2,
                'batch_name': batch_name_2,
                'stage': '初始建立',
                'operator': 'QR碼產生系統',
                'timestamp': base_time_2.strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': '',
                'source': '',
                'destination': '',
                'product_model': '',
                'notes': f'QR碼已建立，批次：{batch_name_2}',
                'location': ''
            },
            {
                'qr_id': qr_id_2,
                'batch_name': batch_name_2,
                'stage': '出廠',
                'operator': '黃操作員',
                'timestamp': (base_time_2 + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 300.0,
                'source': '報廢車輛拆解廠B',
                'destination': '專業回收廠',
                'product_model': 'PE塑膠零件',
                'notes': '來自車體內裝、油箱等部件',
                'location': '高雄市'
            },
            {
                'qr_id': qr_id_2,
                'batch_name': batch_name_2,
                'stage': '後端機構接收',
                'operator': '劉品管',
                'timestamp': (base_time_2 + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 295.0,
                'source': '報廢車輛拆解廠B',
                'destination': '再生塑膠廠B',
                'product_model': 'PE塑膠零件',
                'notes': '品質檢驗合格',
                'location': '高雄市'
            }
        ])
        
        # 示範批次 3: ABS塑膠批次
        qr_id_3 = "DEMO0003"
        batch_name_3 = "ABS塑膠批次-003"
        base_time_3 = datetime.now() - timedelta(days=10)
        
        demo_data.extend([
            {
                'qr_id': qr_id_3,
                'batch_name': batch_name_3,
                'stage': '初始建立',
                'operator': 'QR碼產生系統',
                'timestamp': base_time_3.strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': '',
                'source': '',
                'destination': '',
                'product_model': '',
                'notes': f'QR碼已建立，批次：{batch_name_3}',
                'location': ''
            },
            {
                'qr_id': qr_id_3,
                'batch_name': batch_name_3,
                'stage': '出廠',
                'operator': '吳檢驗員',
                'timestamp': (base_time_3 + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 800.0,
                'source': '大型拆解廠',
                'destination': '塑膠分類廠',
                'product_model': 'ABS塑膠零件',
                'notes': '來自汽車外殼、格柵等硬質部件',
                'location': '新竹市'
            },
            {
                'qr_id': qr_id_3,
                'batch_name': batch_name_3,
                'stage': '再生處理',
                'operator': '鄭工程師',
                'timestamp': (base_time_3 + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 750.0,
                'source': 'ABS塑膠零件',
                'destination': '3C製品廠',
                'product_model': '再生ABS塑膠粒',
                'notes': '高溫處理、品質優良',
                'location': '新竹市'
            },
            {
                'qr_id': qr_id_3,
                'batch_name': batch_name_3,
                'stage': '產品製造',
                'operator': '蔡製造商',
                'timestamp': (base_time_3 + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 720.0,
                'source': '再生ABS塑膠粒',
                'destination': '電子產品通路',
                'product_model': '環保鍵盤外殼 ECO-KB-001',
                'notes': '製造環保鍵盤外殼 500個',
                'location': '新北市'
            },
            {
                'qr_id': qr_id_3,
                'batch_name': batch_name_3,
                'stage': '銷售',
                'operator': '徐業務',
                'timestamp': (base_time_3 + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'weight_kg': 720.0,
                'source': '環保鍵盤外殼',
                'destination': '終端消費者',
                'product_model': '環保鍵盤外殼 ECO-KB-001',
                'notes': '已銷售至電腦周邊通路',
                'location': '全台各地'
            }
        ])
        
        # 儲存示範資料
        df = pd.DataFrame(demo_data)
        df.to_csv("plastic_trace_data.csv", index=False, encoding='utf-8-sig')
        
        st.success("✅ 示範資料已成功生成！")
        st.info("📊 已建立 3 個示範批次，共 16 筆記錄")
        
        # 顯示統計資訊
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("總記錄數", len(df))
        with col2:
            st.metric("批次數量", df['qr_id'].nunique())
        with col3:
            st.metric("處理階段", df['stage'].nunique())
        
        # 顯示資料預覽
        st.subheader("📋 資料預覽")
        st.dataframe(df, use_container_width=True)
        
        st.markdown("### 🎯 示範場景說明")
        st.markdown("""
        **批次 DEMO0001 (PP塑膠):**
        - 完整流程從出廠到產品製造
        - 500公斤 → 425公斤最終產品
        - 製造成環保收納盒
        
        **批次 DEMO0002 (PE塑膠):**
        - 部分流程（出廠、接收）
        - 300公斤原料進入再生處理
        - 展示進行中的批次
        
        **批次 DEMO0003 (ABS塑膠):**
        - 完整流程到銷售階段
        - 800公斤 → 720公斤最終產品
        - 製造成電腦鍵盤外殼並完成銷售
        """)

if __name__ == "__main__":
    main()
