"""
資料 schema 單一來源 + 純邏輯(不 import streamlit,方便 headless 單元測試)。

設計重點(對應 plan-eng / plan-design review 結論):
- COLUMNS 是「唯一」的欄位真相來源;app.py / data_manager.py / google_sheets_manager.py
  全部引用這裡,不再各自硬寫(修 DRY + 修「save 默默丟新欄」的 A2 critical gap）。
- _ensure_schema() 是唯一的向後相容進入點:任何來源(舊 11 欄 CSV / 舊表頭 Sheets)
  載入後補齊缺欄、依 COLUMNS 排序,讓 16 欄程式不會在舊資料上 KeyError。
- compute_mass_balance() 依規劃方 2026-06-16 業務定義:節點取值、禁止 SUM 全 stage。
"""

# ─── 欄位真相來源 ────────────────────────────────────────────────
# 前 11 欄為既有 schema(順序不可動,舊 CSV/Sheets 依賴);後 5 欄為 9.2.2 新增。
BASE_COLUMNS = [
    'qr_id', 'batch_name', 'stage', 'operator', 'timestamp',
    'weight_kg', 'source', 'destination', 'product_model', 'notes', 'location',
]
NEW_COLUMNS = [
    'recycled_ratio',      # 再生料比率 %(語意依 stage 不同,見 compute_mass_balance)
    'data_tier',           # 資料可信度:實測(初級)/ 推估(二級)
    'is_elv_closedloop',   # 報廢車閉環來源:是 / 否 / 未知
    'rrms_doc_id',         # RRMS／報廢系統申報單號
    'material_type',       # 物料類別:PP/PE/PS/PVC/ABS/其他
]
COLUMNS = BASE_COLUMNS + NEW_COLUMNS

# ─── 選單值常數(app.py 表單與本模組共用,避免字串散落) ──────────────
STAGE_INITIAL = '初始建立'
STAGE_FACTORY_OUT = '出廠'
STAGE_TRANSPORT = '運輸'
STAGE_BACKEND_IN = '後端機構接收'
STAGE_RECYCLE = '再生處理'
STAGE_PRODUCT = '產品製造'
STAGE_SALE = '銷售'
# 掃描登錄表單可選的階段(不含「初始建立」,那是產生 QR 時系統寫的）
SCAN_STAGES = [
    STAGE_FACTORY_OUT, STAGE_TRANSPORT, STAGE_BACKEND_IN,
    STAGE_RECYCLE, STAGE_PRODUCT, STAGE_SALE,
]
# 「成品再生含量」對歐盟門檻的取值來源階段(後端段)
BACKEND_RATIO_STAGES = [STAGE_RECYCLE, STAGE_PRODUCT, STAGE_SALE]

DATA_TIER_OPTIONS = ['實測(初級)', '推估(二級)']
ELV_CLOSEDLOOP_OPTIONS = ['是', '否', '未知']
MATERIAL_TYPE_OPTIONS = ['PP', 'PE', 'PS', 'PVC', 'ABS', '其他']

# 歐盟 ELV 再生料門檻(顏色對照用)
EU_THRESHOLD_LOW = 15.0
EU_THRESHOLD_HIGH = 25.0


def empty_frame():
    """回傳具正確 16 欄的空 DataFrame。"""
    import pandas as pd
    return pd.DataFrame(columns=COLUMNS)


def ensure_schema(df):
    """補齊缺欄、依 COLUMNS 排序的唯一 migration 進入點。

    - 舊資料缺新欄 → 補空字串。
    - 未知欄(不在 COLUMNS)→ 丟棄,讓 CSV 與 Sheets 兩條路欄位一致
      (避免 Sheets save 的 reindex 與 CSV 不同步)。
    - 不原地修改 caller 的 df(回傳新物件,避免 SettingWithCopy 與測試 flakiness)。
    """
    import pandas as pd
    if df is None:
        return empty_frame()
    df = df.copy()
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ''
    # CSV 空格讀進來是 NaN(float),Sheets 則是 '';統一成 '' 讓全 app 看到一致的空值
    # (否則 material_type 等欄會混 str/float → sorted() TypeError、顯示出現 'nan')
    return df[COLUMNS].fillna('')


def to_float(value):
    """把可能是 ''/字串/數值的儲存格安全轉成 float;無法轉則回 None。

    既有設計把空重量存成 ''、整表又經 str() round-trip,所以數值欄常是字串,
    質量平衡求和前必須統一轉型(修 review C3)。
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            import math
            return None if isinstance(value, float) and math.isnan(value) else float(value)
        except (TypeError, ValueError):
            return None
    s = str(value).strip()
    if s == '' or s.lower() in ('nan', 'none'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _latest_row(df, stages):
    """取 df 中 stage 屬於 stages 的、timestamp 最新的一列(Series);無則 None。

    timestamp 為 '%Y-%m-%d %H:%M:%S' 字串,可直接字典序比較。
    """
    if df.empty:
        return None
    sub = df[df['stage'].isin(stages)]
    if sub.empty:
        return None
    return sub.sort_values('timestamp').iloc[-1]


def _latest_weight(df, stages):
    row = _latest_row(df, stages)
    return None if row is None else to_float(row.get('weight_kg'))


def compute_mass_balance(df, batch):
    """依規劃方 2026-06-16 業務定義計算某 batch 的質量平衡。

    規則(節點取值,禁止 SUM 全 stage;同一 stage 多筆取時間最新一筆):
      進料   = 出廠 重量
      收料   = 後端機構接收 重量(僅供對帳,不進加總)
      產出   = 再生處理／產品製造 成品重量(取最終一筆)
      損耗   = 進料 − 產出
      回收率 = 產出 ÷ 進料
      運輸階段不計入。
    再生含量(分兩種語意):
      成品再生含量(對歐盟門檻)= 後端段(再生處理/產品製造/銷售)時間最新非空 recycled_ratio
      再生料來源純度          = 出廠 那筆 recycled_ratio(不對門檻)
      data_tier               = 與成品再生含量同一筆的可信度分級
    回傳值欄位資料不足時為 None。
    """
    df = ensure_schema(df)
    b = df[df['batch_name'] == batch]

    feed = _latest_weight(b, [STAGE_FACTORY_OUT])
    received = _latest_weight(b, [STAGE_BACKEND_IN])
    out_row = _latest_row(b, [STAGE_RECYCLE, STAGE_PRODUCT])
    output = None if out_row is None else to_float(out_row.get('weight_kg'))
    output_stage = None if out_row is None else str(out_row.get('stage') or '') or None

    loss = None
    if feed is not None and output is not None:
        loss = round(feed - output, 4)

    recovery_rate = None
    if feed not in (None, 0) and output is not None:
        recovery_rate = round(output / feed * 100, 2)

    # 成品再生含量:後端段時間最新「非空」那筆
    recycled_content = None
    data_tier = None
    backend = b[b['stage'].isin(BACKEND_RATIO_STAGES)].sort_values('timestamp')
    for _, row in backend.iloc[::-1].iterrows():
        r = to_float(row.get('recycled_ratio'))
        if r is not None:
            recycled_content = r
            data_tier = str(row.get('data_tier') or '').strip() or None
            break

    # 再生料來源純度:出廠那筆
    source_purity = None
    fac = _latest_row(b, [STAGE_FACTORY_OUT])
    if fac is not None:
        source_purity = to_float(fac.get('recycled_ratio'))

    return {
        'batch': batch,
        'feed_kg': feed,                  # 進料
        'received_kg': received,          # 收料(對帳)
        'output_kg': output,              # 產出
        'output_stage': output_stage,     # 產出取自哪個 stage(再生處理/產品製造)
        'loss_kg': loss,                  # 損耗
        'recovery_rate': recovery_rate,   # 回收率 %
        'recycled_content': recycled_content,  # 成品再生含量 %(對歐盟門檻)
        'data_tier': data_tier,           # 上述數字的可信度
        'source_purity': source_purity,   # 再生料來源純度 %(不對門檻)
        'records': int(len(b)),
    }


def threshold_color(ratio):
    """回傳成品再生含量對歐盟門檻的顏色標記:red / amber / green / gray。"""
    if ratio is None:
        return 'gray'
    if ratio < EU_THRESHOLD_LOW:
        return 'red'
    if ratio < EU_THRESHOLD_HIGH:
        return 'amber'
    return 'green'
