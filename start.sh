#!/bin/bash

echo "🚀 正在啟動 AI 會議記錄助手..."

# 取得專案根目錄
PROJECT_ROOT=$(pwd)

# 1. 啟動後端 (Python FastAPI)
echo "--------------------------------------"
echo "🐍 正在啟動後端 (Port 8000)..."
cd "$PROJECT_ROOT/backend"
# 檢查是否有 venv，若無則直接用系統 python
if [ -d "venv" ]; then
    source venv/bin/activate
fi
# 在背景執行，並將 log 輸出到檔案以免洗版
nohup python3 main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 後端已在背景啟動 (PID: $BACKEND_PID)"

# 2. 啟動前端 (Node.js Express)
echo "--------------------------------------"
echo "🌐 正在啟動前端 (Port 3200)..."
cd "$PROJECT_ROOT/frontend"
# 在背景執行
nohup npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 前端已在背景啟動 (PID: $FRONTEND_PID)"

echo "--------------------------------------"
echo "🎉 系統啟動完成！"
echo "👉 前端介面: http://localhost:3200"
echo "👉 後端 API : http://localhost:8000"
echo "--------------------------------------"
echo "📝 Logs 輸出於 backend.log 與 frontend.log"
echo "⚠️  按任意鍵或 Ctrl+C 停止所有服務..."

# 等待使用者輸入以結束
read -p ""

# 結束程序
echo "🛑 正在停止服務..."
kill $BACKEND_PID
kill $FRONTEND_PID
echo "👋 Bye!"

