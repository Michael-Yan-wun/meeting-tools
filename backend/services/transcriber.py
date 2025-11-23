from google import genai
from google.genai import types
import json
import os
import time

def analyze_audio_directly(file_path, api_key=None):
    """
    直接上傳音訊給 Gemini 進行分析 (不透過本地 Whisper)
    回傳: (transcription_text, structured_data_dict)
    """
    if not api_key:
        raise ValueError("API Key is required")

    client = genai.Client(api_key=api_key)

    # 1. 上傳檔案
    print(f"正在上傳檔案至 Gemini: {file_path}...")
    file_size = os.path.getsize(file_path)
    
    # 使用新的 SDK 上傳方式
    # 注意：google-genai SDK 的 upload_file 用法
    upload_result = client.files.upload(file=file_path)
    print(f"檔案上傳成功: {upload_result.name}")

    # 等待檔案處理完成 (如果是影片或大檔可能需要，音訊通常很快)
    while upload_result.state.name == "PROCESSING":
        print("等待 Gemini 處理檔案中...")
        time.sleep(2)
        upload_result = client.files.get(name=upload_result.name)

    if upload_result.state.name == "FAILED":
        raise ValueError("Gemini 檔案處理失敗")

    # 2. 發送請求 (同時要求逐字稿 + 結構化資料)
    # 為了確保 JSON 格式正確，我們使用單一 Prompt 同時要求兩者，或者分兩階段?
    # 為了省錢且效率高，我們一次請求完成：讓 JSON 中包含一個 "transcription" 欄位
    
    prompt = """
    你是一個專業的會議記錄秘書。請聆聽這段會議錄音，並完成以下兩項任務：
    1. 產出完整的繁體中文逐字稿（Transcripts）。
    2. 將會議內容整理成結構化記錄。

    請依照以下 JSON Schema 回傳資料，不要包含 markdown 標記，直接回傳 JSON：
    {
        "transcription": "完整的會議逐字稿內容...",
        "meeting_topics": ["主題1", "主題2"],
        "participants": [
            {"name": "姓名", "role": "職稱或在會議中的職責描述"}
        ],
        "key_points": [
            {"title": "重點標題", "content": "詳細內容說明"}
        ],
        "next_steps": [
            {"action": "具體行動項目", "owner": "負責人或協調人"}
        ],
        "summary": "一段約 100-200 字的會議總結摘要"
    }
    """

    print("正在發送分析請求給 Gemini...")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", # 1.5 Flash 對多模態支援較好且快速
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=upload_result.uri,
                            mime_type=upload_result.mime_type
                        ),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        result_json = json.loads(response.text)
        
        # 提取逐字稿與結構化資料
        transcription = result_json.get("transcription", "")
        # 移除 transcription 欄位以免重複儲存到 structured_data
        if "transcription" in result_json:
            del result_json["transcription"]
            
        return transcription, result_json

    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        raise e
