@echo off
echo ===============================================
echo   ELV 廢塑膠產銷履歷示範平台 啟動程式
echo ===============================================
echo.

echo 正在檢查 Python 環境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 錯誤：未找到 Python，請先安裝 Python 3.8 或更新版本
    pause
    exit /b 1
)

echo ✅ Python 環境正常

echo.
echo 正在檢查依賴套件...
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 正在安裝必要套件...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 套件安裝失敗，請檢查網路連線
        pause
        exit /b 1
    )
) else (
    echo ✅ 依賴套件已安裝
)

echo.
echo 🚀 正在啟動應用程式...
echo 📱 應用程式將在瀏覽器中開啟: http://localhost:8501
echo 💡 按 Ctrl+C 可停止服務
echo.

streamlit run app.py

pause
