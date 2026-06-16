# 內附字型(QR 列印標籤/套表 PDF 用)

## NotoSansTC-Regular.ttf
- **字型**:Noto Sans TC(繁體中文)
- **來源/版權**:Google LLC
- **授權**:SIL Open Font License 1.1（見 `OFL.txt`）—— **可自由商用、可內嵌進散佈的 PDF、可隨本 repo 散佈**。

## 為什麼放在 repo 裡
產生 QR 列印標籤/套表 PDF 時要內嵌中文字型,字形才會烤進 PDF、在任何機器與閱讀器都正確顯示(非內嵌的 CID 字型會依賴閱讀器代換、容易變亂碼)。
內附這支 OFL 字型可保證雲端/本機都能正確產出,不必依賴系統字型或 `packages.txt`。

`app.py` 的 `_register_cjk_font()` 會優先載入本資料夾的字型;找不到才退回系統 Noto。

> ⚠️ 只放 OFL/開源授權字型。**切勿**把微軟正黑體/細明體/標楷體、蘋果 PingFang 等專有字型放進來(授權不允許散佈與內嵌)。
