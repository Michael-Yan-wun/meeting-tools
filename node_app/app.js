const express = require('express');
const multer = require('multer');
const path = require('path');
const { spawn } = require('child_process');
const db = require('./database');
const fs = require('fs');
require('dotenv').config();

const app = express();
const port = 3000;

// 設定 View Engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 設定靜態檔案目錄
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// 設定上傳
const upload = multer({ dest: 'node_app/uploads/' });

// 首頁
app.get('/', (req, res) => {
    res.render('index');
});

// 歷史記錄 API
app.get('/api/meetings', (req, res) => {
    db.all("SELECT id, filename, created_at, summary FROM meetings ORDER BY created_at DESC", [], (err, rows) => {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }
        res.json(rows);
    });
});

// 取得單一會議詳情 API
app.get('/api/meetings/:id', (req, res) => {
    db.get("SELECT * FROM meetings WHERE id = ?", [req.params.id], (err, row) => {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }
        if (row) {
            // 解析 JSON 字串
            try {
                row.participants = JSON.parse(row.participants || '[]');
                row.key_points = JSON.parse(row.key_points || '[]');
                row.next_steps = JSON.parse(row.next_steps || '[]');
                row.meeting_topics = JSON.parse(row.meeting_topics || '[]');
            } catch (e) {
                console.error("JSON Parse Error:", e);
            }
            res.json(row);
        } else {
            res.status(404).json({ error: "Not found" });
        }
    });
});

// 處理上傳與分析
app.post('/api/upload', upload.single('audio'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }

    const filePath = req.file.path;
    const originalName = req.file.originalname;
    const apiKey = process.env.GEMINI_API_KEY;

    if (!apiKey) {
        return res.status(500).json({ error: 'Gemini API Key not configured' });
    }

    // 呼叫 Python 腳本
    const pythonProcess = spawn('python3', [
        path.join(__dirname, 'python_scripts', 'process_meeting.py'),
        filePath,
        '--api_key', apiKey,
        '--output_dir', path.join(__dirname, 'public', 'downloads') // Word 檔存到這裡供下載
    ]);

    // 確保下載目錄存在
    const downloadDir = path.join(__dirname, 'public', 'downloads');
    if (!fs.existsSync(downloadDir)){
        fs.mkdirSync(downloadDir, { recursive: true });
    }

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorString += data.toString();
        console.error(`Python Stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        // 刪除上傳的暫存音訊檔
        fs.unlink(filePath, (err) => { if (err) console.error("Failed to delete temp file:", err); });

        if (code !== 0) {
            return res.status(500).json({ error: `Process failed with code ${code}`, details: errorString });
        }

        try {
            const result = JSON.parse(dataString);
            if (!result.success) {
                return res.status(500).json(result);
            }

            // 存入資料庫
            const stmt = db.prepare(`
                INSERT INTO meetings (
                    filename, transcription, participants, key_points, 
                    discussion_topics, next_steps, summary, meeting_topics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            `);

            stmt.run(
                originalName,
                result.transcription,
                JSON.stringify(result.structured_data.participants),
                JSON.stringify(result.structured_data.key_points),
                JSON.stringify([]), // discussion_topics deprecated
                JSON.stringify(result.structured_data.next_steps),
                result.structured_data.summary,
                JSON.stringify(result.structured_data.meeting_topics),
                function(err) {
                    if (err) {
                        return res.status(500).json({ error: err.message });
                    }
                    // 回傳成功結果與 ID
                    res.json({ 
                        id: this.lastID, 
                        ...result 
                    });
                }
            );
            stmt.finalize();

        } catch (e) {
            res.status(500).json({ error: "Failed to parse Python output", raw: dataString });
        }
    });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});

