#!/bin/bash

echo "==============================================="
echo "   ELV 廢塑膠產銷履歷示範平台 啟動程式"
echo "==============================================="
echo

echo "正在檢查 Python 環境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤：未找到 Python 3，請先安裝 Python 3.8 或更新版本"
    exit 1
fi

echo "✅ Python 環境正常"

echo
echo "正在檢查依賴套件..."
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📦 正在安裝必要套件..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 套件安裝失敗，請檢查網路連線"
        exit 1
    fi
else
    echo "✅ 依賴套件已安裝"
fi

echo
echo "🚀 正在啟動應用程式..."
echo "📱 應用程式將在瀏覽器中開啟: http://localhost:8501"
echo "💡 按 Ctrl+C 可停止服務"
echo

streamlit run app.py
