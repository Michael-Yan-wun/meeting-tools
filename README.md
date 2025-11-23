# AI 智慧會議記錄助手

這是一個基於 **Node.js 前端 + Python FastAPI 後端** 開發的會議記錄工具。它能夠將上傳的錄音檔直接透過 Google Gemini API 進行語音轉文字與智慧分析，自動整理會議重點、參與人與待辦事項，最後產生專業的 Word 報告。

## 功能特色

- **語音轉文字 + 智慧分析**：使用 Google Gemini 1.5 Flash API 直接處理音訊檔案，一次完成轉錄與結構化分析（無需本地 Whisper 模型）。
- **專業 Word 報告**：自動生成符合「中正北路24號」格式的會議記錄，包含：
  - 會議主題
  - 參與人員表格
  - 重點內容摘要
  - 待辦事項表格
  - 總結摘要
- **資料庫儲存**：自動儲存歷史記錄至 SQLite。
- **現代化 UI**：使用 Bootstrap 5 設計的響應式介面。

## 系統架構

```
meeting-tools/
├── frontend/          # Node.js Express 前端 (Port 3200)
│   ├── server.js     # Express 伺服器
│   ├── views/        # EJS 模板
│   └── public/       # CSS/JS 靜態檔案
│
├── backend/          # Python FastAPI 後端 (Port 8000)
│   ├── main.py       # FastAPI 主程式
│   ├── services/     # 業務邏輯
│   │   ├── transcriber.py  # Gemini 音訊分析
│   │   └── doc_gen.py      # Word 生成
│   └── requirements.txt
│
└── start.sh          # 一鍵啟動腳本
```

## 安裝說明

### 1. 系統需求

- **Python 3.8+**
- **Node.js 18+**
- **Google Gemini API Key** (免費取得：https://ai.google.dev/)

### 2. 安裝後端依賴

```bash
cd backend
pip install -r requirements.txt
```

### 3. 安裝前端依賴

```bash
cd frontend
npm install
```

### 4. 設定環境變數

在 `backend/` 目錄下建立 `.env` 檔案：

```env
GEMINI_API_KEY=your_api_key_here
```

## 啟動方式

### 快速啟動（推薦）

在專案根目錄執行：

```bash
./start.sh
```

這會同時啟動：
- 前端服務：http://localhost:3200
- 後端 API：http://localhost:8000

### 手動啟動

**終端機 1 - 後端：**
```bash
cd backend
python3 main.py
```

**終端機 2 - 前端：**
```bash
cd frontend
npm start
```

## 使用說明

1. 開啟瀏覽器前往 http://localhost:3200
2. 點擊右上角「新增會議記錄」按鈕
3. 上傳 mp3/wav/m4a 錄音檔
4. 點擊「開始分析」
5. 等待 Gemini API 處理完成（通常 10-30 秒，視檔案大小而定）
6. 查看分析結果並下載 Word 報告

## 技術棧

- **前端**：Node.js, Express, EJS, Bootstrap 5
- **後端**：Python, FastAPI, Uvicorn
- **AI**：Google Gemini 1.5 Flash (多模態音訊分析)
- **資料庫**：SQLite
- **文件生成**：python-docx

## 注意事項

- Gemini API 有免費額度限制，請注意使用量
- 音訊檔案建議不超過 50MB
- 支援的格式：mp3, wav, m4a
