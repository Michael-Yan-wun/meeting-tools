# Cursor Vibe Coding 提示詞（簡潔版）

建立一個 **AI 會議記錄助手**：Node.js 前端 (Port 3200) + Python FastAPI 後端 (Port 8000)。

## 核心流程

1. 使用者上傳音訊 → FastAPI 接收
2. 上傳檔案至 Google Gemini API (`client.files.upload`)
3. 等待處理完成後，發送 Prompt 要求 JSON 格式的結構化資料
4. Gemini 回傳：`{transcription, meeting_topics, participants, key_points, next_steps, summary}`
5. 使用 `python-docx` 生成 Word 檔案（格式參照「中正北路24號_會議記錄整理.docx」）
6. 存入 SQLite 並回傳結果給前端

## 技術棧

- **前端**: Express + EJS + Bootstrap 5
- **後端**: FastAPI + `google-genai` SDK
- **AI**: Gemini 1.5 Flash（直接處理音訊，不需 Whisper）
- **資料庫**: SQLite
- **Word**: python-docx

## 關鍵程式碼片段

### Gemini 音訊分析
```python
upload_result = client.files.upload(file=file_path)
while upload_result.state.name == "PROCESSING":
    upload_result = client.files.get(name=upload_result.name)

response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=[types.Content(role="user", parts=[
        types.Part.from_uri(file_uri=upload_result.uri, mime_type=upload_result.mime_type),
        types.Part.from_text(text=prompt)
    ])],
    config=types.GenerateContentConfig(response_mime_type="application/json")
)
```

### Word 格式
- 標題、一、會議主題（條列）、二、參與人物（表格）、三、重點內容（編號+內容）、四、行動項目（表格）、五、總結摘要
- **不包含逐字稿**

### 前端 API
- Base URL: `http://localhost:8000/api`
- 上傳欄位名：`file` (FormData)

