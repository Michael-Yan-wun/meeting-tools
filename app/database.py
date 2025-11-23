import sqlite3
import json
from datetime import datetime
import pandas as pd

DB_NAME = "meetings.db"

def init_db():
    """初始化資料庫，建立 meetings 表格，並確保所有新欄位都存在"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 建立基本表格
    c.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            transcription TEXT,
            participants TEXT,
            key_points TEXT,
            discussion_topics TEXT,
            next_steps TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 檢查並新增 summary 欄位
    try:
        c.execute("ALTER TABLE meetings ADD COLUMN summary TEXT")
    except sqlite3.OperationalError:
        pass # 欄位已存在
        
    # 檢查並新增 meeting_topics 欄位
    try:
        c.execute("ALTER TABLE meetings ADD COLUMN meeting_topics TEXT")
    except sqlite3.OperationalError:
        pass # 欄位已存在

    conn.commit()
    conn.close()

def save_meeting(filename, transcription, structured_data):
    """儲存會議記錄"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    def to_json(data):
        return json.dumps(data, ensure_ascii=False) if isinstance(data, (list, dict)) else str(data)

    c.execute('''
        INSERT INTO meetings (
            filename, transcription, participants, key_points, 
            discussion_topics, next_steps, summary, meeting_topics
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename, 
        transcription,
        to_json(structured_data.get('participants', [])),
        to_json(structured_data.get('key_points', [])),
        to_json(structured_data.get('discussion_topics', [])), # 保留舊欄位相容
        to_json(structured_data.get('next_steps', [])),
        structured_data.get('summary', ''),
        to_json(structured_data.get('meeting_topics', []))
    ))
    conn.commit()
    meeting_id = c.lastrowid
    conn.close()
    return meeting_id

def get_all_meetings():
    """取得所有會議記錄列表"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, filename, created_at FROM meetings ORDER BY created_at DESC", conn)
    conn.close()
    return df

def get_meeting_details(meeting_id):
    """取得單一會議詳細資料"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None
