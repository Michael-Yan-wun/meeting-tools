const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, '../meetings.db'); // 沿用專案根目錄的資料庫
const db = new sqlite3.Database(dbPath);

// 初始化資料庫 (確保表格存在)
db.serialize(() => {
    db.run(`
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
    `);
    
    // 嘗試新增新欄位 (如果不存在)
    const columnsToAdd = ['summary', 'meeting_topics'];
    columnsToAdd.forEach(col => {
        db.run(`ALTER TABLE meetings ADD COLUMN ${col} TEXT`, (err) => {
            // 忽略 "duplicate column name" 錯誤
        });
    });
});

module.exports = db;

