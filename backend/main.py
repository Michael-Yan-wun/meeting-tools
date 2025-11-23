from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
import json
import sqlite3
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# 載入服務模組
from services.transcriber import analyze_audio_directly
from services.doc_gen import generate_meeting_minutes

load_dotenv()

# 設定資料庫路徑
DB_PATH = os.path.join(os.path.dirname(__file__), "meetings.db")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- 生命週期管理 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 系統啟動中...")
    init_db()            # 初始化資料庫
    yield
    print("🛑 系統關閉")

app = FastAPI(lifespan=lifespan)

# 允許跨域 (讓前端 Node.js 或瀏覽器直接呼叫)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 資料庫操作 ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            transcription TEXT,
            participants TEXT,
            key_points TEXT,
            discussion_topics TEXT,
            next_steps TEXT,
            summary TEXT,
            meeting_topics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 簡單的新增欄位檢查 (略過錯誤)
    try:
        c.execute("ALTER TABLE meetings ADD COLUMN summary TEXT")
        c.execute("ALTER TABLE meetings ADD COLUMN meeting_topics TEXT")
    except:
        pass
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- API Routes ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Meeting Tools API is running"}

@app.get("/api/meetings")
def get_meetings():
    conn = get_db_connection()
    meetings = conn.execute("SELECT id, filename, created_at, summary FROM meetings ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(m) for m in meetings]

@app.get("/api/meetings/{meeting_id}")
def get_meeting_detail(meeting_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # 解析 JSON 字串欄位
    data = dict(row)
    for key in ['participants', 'key_points', 'next_steps', 'meeting_topics']:
        try:
            if data[key]:
                data[key] = json.loads(data[key])
        except:
            pass
    return data

@app.post("/api/upload")
async def upload_audio(file: UploadFile = File(...)):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured")

    # 1. 儲存上傳檔案
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. 直接使用 Gemini 分析 (轉錄 + 結構化)
        transcription, structured_data = analyze_audio_directly(file_path, api_key=api_key)
        
        # 3. 生成 Word
        doc_io = generate_meeting_minutes({
            "filename": file.filename,
            "transcription": transcription,
            **structured_data
        })
        
        # 存檔 Word
        doc_filename = f"Meeting_{os.path.splitext(file.filename)[0]}.docx"
        doc_path = os.path.join(DOWNLOAD_DIR, doc_filename)
        with open(doc_path, "wb") as f:
            f.write(doc_io.getvalue())

        # 5. 存入資料庫
        conn = get_db_connection()
        cursor = conn.cursor()
        
        def to_json(obj):
            return json.dumps(obj, ensure_ascii=False)

        cursor.execute('''
            INSERT INTO meetings (
                filename, transcription, participants, key_points, 
                next_steps, summary, meeting_topics
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            file.filename,
            transcription,
            to_json(structured_data.get('participants', [])),
            to_json(structured_data.get('key_points', [])),
            to_json(structured_data.get('next_steps', [])),
            structured_data.get('summary', ''),
            to_json(structured_data.get('meeting_topics', []))
        ))
        
        meeting_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 清理原始檔
        os.remove(file_path)
        
        return {
            "id": meeting_id,
            "filename": file.filename,
            "doc_url": f"/api/download/{doc_filename}",
            **structured_data
        }

    except Exception as e:
        # os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

