"""
schema.py 純邏輯單元測試(headless,不需 streamlit)。
執行:python -m pytest test_schema.py -v   (用已裝依賴的 Python 3.13)
"""

import pandas as pd
import pytest

import schema
from schema import (
    COLUMNS, ensure_schema, to_float, compute_mass_balance, threshold_color,
    STAGE_FACTORY_OUT, STAGE_TRANSPORT, STAGE_BACKEND_IN, STAGE_RECYCLE,
    STAGE_PRODUCT, STAGE_INITIAL,
)


# ─── ensure_schema / migration ──────────────────────────────────
def test_columns_has_16_with_new_fields():
    assert len(COLUMNS) == 16
    for c in ['recycled_ratio', 'data_tier', 'is_elv_closedloop',
              'rrms_doc_id', 'material_type']:
        assert c in COLUMNS


def test_ensure_schema_migrates_old_11_column_frame():
    old = pd.DataFrame([{
        'qr_id': 'A1', 'batch_name': 'b', 'stage': STAGE_FACTORY_OUT,
        'operator': 'op', 'timestamp': '2026-06-16 10:00:00', 'weight_kg': 100,
        'source': '', 'destination': '', 'product_model': '', 'notes': '',
        'location': '',
    }])
    out = ensure_schema(old)
    assert list(out.columns) == COLUMNS            # 補齊到 16 欄、順序固定
    assert out.loc[0, 'recycled_ratio'] == ''      # 新欄補空
    assert out.loc[0, 'weight_kg'] == 100          # 舊值不動


def test_ensure_schema_drops_unknown_columns():
    df = pd.DataFrame([{**{c: '' for c in COLUMNS}, 'junk': 'x'}])
    out = ensure_schema(df)
    assert 'junk' not in out.columns
    assert list(out.columns) == COLUMNS


def test_ensure_schema_does_not_mutate_caller():
    old = pd.DataFrame([{'qr_id': 'A1'}])
    ensure_schema(old)
    assert list(old.columns) == ['qr_id']          # caller 未被原地改


def test_ensure_schema_none_returns_empty_16col():
    out = ensure_schema(None)
    assert out.empty and list(out.columns) == COLUMNS


def test_ensure_schema_converts_nan_to_empty_string():
    """CSV 空格讀進來是 NaN;ensure_schema 須轉成 '',否則 sorted()/顯示會壞。"""
    import numpy as np
    df = pd.DataFrame([
        {'qr_id': 'A', 'material_type': 'PP', 'weight_kg': 100},
        {'qr_id': 'B', 'material_type': np.nan, 'weight_kg': np.nan},
    ])
    out = ensure_schema(df)
    assert out.loc[1, 'material_type'] == ''
    assert out.loc[1, 'weight_kg'] == ''
    # 混型欄位可正常 sorted(模擬 app.py 的物料篩選)
    mats = sorted({str(m).strip() for m in out['material_type']
                   if str(m).strip() and str(m).strip().lower() != 'nan'})
    assert mats == ['PP']


def test_roundtrip_append_then_load_keeps_new_columns():
    """模擬 append→reload:新欄不可在來回後消失(對應 A2 的回歸測試)。"""
    rec = {c: '' for c in COLUMNS}
    rec.update({'qr_id': 'Z9', 'stage': STAGE_RECYCLE,
                'recycled_ratio': '27', 'data_tier': '實測(初級)'})
    df = ensure_schema(pd.DataFrame([rec]))
    # 模擬經過 str() round-trip(Sheets 行為)後再 ensure_schema
    df2 = ensure_schema(df.astype(str))
    assert df2.loc[0, 'recycled_ratio'] == '27'
    assert df2.loc[0, 'data_tier'] == '實測(初級)'


# ─── to_float 邊界 ──────────────────────────────────────────────
@pytest.mark.parametrize("value,expected", [
    ('', None), ('   ', None), ('nan', None), ('NaN', None), ('none', None),
    (None, None), ('abc', None),
    ('0', 0.0), (0, 0.0), ('100', 100.0), (100, 100.0),
    ('12.5', 12.5), (12.5, 12.5), ('  30 ', 30.0),
])
def test_to_float_boundaries(value, expected):
    assert to_float(value) == expected


def test_to_float_nan_float():
    assert to_float(float('nan')) is None


# ─── recycled_ratio 邊界(透過 compute) ─────────────────────────
def _row(**kw):
    base = {c: '' for c in COLUMNS}
    base.update(kw)
    return base


def test_recycled_ratio_zero_and_hundred_and_empty():
    df = pd.DataFrame([
        _row(qr_id='Q', batch_name='b', stage=STAGE_RECYCLE,
             timestamp='2026-06-16 09:00:00', recycled_ratio='0'),
        _row(qr_id='Q', batch_name='b', stage=STAGE_PRODUCT,
             timestamp='2026-06-16 10:00:00', recycled_ratio='100'),
        _row(qr_id='Q', batch_name='b', stage=STAGE_SALE_OR_EMPTY(),
             timestamp='2026-06-16 11:00:00', recycled_ratio=''),
    ])
    mb = compute_mass_balance(df, 'b')
    # 最新非空那筆是 100(銷售那筆為空應被跳過)
    assert mb['recycled_content'] == 100.0


def STAGE_SALE_OR_EMPTY():
    return schema.STAGE_SALE


# ─── compute_mass_balance 業務規則(規劃方 2026-06-16 定義) ──────
def test_mass_balance_node_values_not_sum():
    """禁止 SUM 全 stage;進料取出廠、產出取再生/製造、運輸不計、損耗=進−產。"""
    df = pd.DataFrame([
        _row(batch_name='b', stage=STAGE_FACTORY_OUT,
             timestamp='2026-06-16 08:00:00', weight_kg='1000'),
        _row(batch_name='b', stage=STAGE_TRANSPORT,
             timestamp='2026-06-16 09:00:00', weight_kg='1000'),  # 不該計入
        _row(batch_name='b', stage=STAGE_BACKEND_IN,
             timestamp='2026-06-16 10:00:00', weight_kg='980'),   # 對帳,不進加總
        _row(batch_name='b', stage=STAGE_PRODUCT,
             timestamp='2026-06-16 11:00:00', weight_kg='850',
             recycled_ratio='27', data_tier='實測(初級)'),
    ])
    mb = compute_mass_balance(df, 'b')
    assert mb['feed_kg'] == 1000.0
    assert mb['received_kg'] == 980.0
    assert mb['output_kg'] == 850.0
    assert mb['loss_kg'] == 150.0                 # 1000 - 850,不含運輸
    assert mb['recovery_rate'] == 85.0
    assert mb['recycled_content'] == 27.0
    assert mb['data_tier'] == '實測(初級)'
    assert mb['output_stage'] == STAGE_PRODUCT   # 產出取自產品製造階段


def test_mass_balance_same_stage_takes_latest_not_sum():
    df = pd.DataFrame([
        _row(batch_name='b', stage=STAGE_FACTORY_OUT,
             timestamp='2026-06-16 08:00:00', weight_kg='500'),
        _row(batch_name='b', stage=STAGE_FACTORY_OUT,
             timestamp='2026-06-16 09:00:00', weight_kg='1000'),  # 較新 → 取這筆
    ])
    mb = compute_mass_balance(df, 'b')
    assert mb['feed_kg'] == 1000.0                # 不是 1500


def test_mass_balance_source_purity_vs_product_content_distinct():
    """出廠 ratio = 來源純度(不對門檻);後端 ratio = 成品再生含量(對門檻)。"""
    df = pd.DataFrame([
        _row(batch_name='b', stage=STAGE_FACTORY_OUT,
             timestamp='2026-06-16 08:00:00', weight_kg='1000',
             recycled_ratio='95'),                # 來源純度
        _row(batch_name='b', stage=STAGE_RECYCLE,
             timestamp='2026-06-16 10:00:00', weight_kg='800',
             recycled_ratio='27'),                # 成品再生含量
    ])
    mb = compute_mass_balance(df, 'b')
    assert mb['source_purity'] == 95.0
    assert mb['recycled_content'] == 27.0         # 兩者不混用


def test_mass_balance_insufficient_data_returns_none():
    df = pd.DataFrame([
        _row(batch_name='b', stage=STAGE_INITIAL,
             timestamp='2026-06-16 08:00:00'),
    ])
    mb = compute_mass_balance(df, 'b')
    assert mb['feed_kg'] is None
    assert mb['output_kg'] is None
    assert mb['loss_kg'] is None
    assert mb['recovery_rate'] is None
    assert mb['recycled_content'] is None


def test_mass_balance_filters_by_batch():
    df = pd.DataFrame([
        _row(batch_name='b1', stage=STAGE_FACTORY_OUT,
             timestamp='2026-06-16 08:00:00', weight_kg='1000'),
        _row(batch_name='b2', stage=STAGE_FACTORY_OUT,
             timestamp='2026-06-16 08:00:00', weight_kg='9999'),
    ])
    assert compute_mass_balance(df, 'b1')['feed_kg'] == 1000.0


# ─── threshold_color(歐盟門檻) ────────────────────────────────
@pytest.mark.parametrize("ratio,color", [
    (None, 'gray'), (0, 'red'), (14.9, 'red'),
    (15, 'amber'), (24.9, 'amber'),
    (25, 'green'), (40, 'green'),
])
def test_threshold_color(ratio, color):
    assert threshold_color(ratio) == color
