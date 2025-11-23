import whisper
from google import genai
from google.genai import types
import json
import os
import streamlit as st

# 預設載入 base 模型，速度較快。若需要更高準確度可改用 "medium" 或 "large"
MODEL_SIZE = "base"

def transcribe_audio(file_path, model_name=MODEL_SIZE):
    """
    使用 Whisper 將音訊檔案轉錄為文字
    """
    print(f"正在載入 Whisper 模型: {model_name}...")
    model = whisper.load_model(model_name)
    
    print(f"正在轉錄檔案: {file_path}...")
    # fp16=False 是為了避免在某些 CPU 上報錯
    result = model.transcribe(file_path, fp16=False)
    
    return result["text"]

def structure_meeting_notes(transcript_text, api_key=None):
    """
    使用 Google Gemini 模型將逐字稿整理為結構化資料
    """
    # 嘗試從 secrets 或參數取得 API Key
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            return {
                "meeting_topics": [],
                "participants": [],
                "key_points": ["請設定 Gemini API Key 以進行智慧分析"],
                "next_steps": [],
                "summary": "未設定 API Key"
            }

    # 初始化 Gemini Client
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    你是一個專業的會議記錄秘書。你的任務是閱讀會議逐字稿，並將其整理成繁體中文的結構化 JSON 格式。
    請特別注意參與者的職責與待辦事項的負責人。
    
    請依照以下 JSON Schema 回傳資料：
    {{
        "meeting_topics": ["主題1", "主題2"],
        "participants": [
            {{"name": "姓名", "role": "職稱或在會議中的職責描述"}},
            {{"name": "姓名2", "role": "職稱或職責"}}
        ],
        "key_points": [
            {{"title": "重點標題", "content": "詳細內容說明"}}
        ],
        "next_steps": [
            {{"action": "具體行動項目", "owner": "負責人或協調人"}}
        ],
        "summary": "一段約 100-200 字的會議總結摘要"
    }}

    以下是會議逐字稿：
    {transcript_text[:30000]}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)
    
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {
            "meeting_topics": [],
            "participants": [],
            "key_points": [{"title": "錯誤", "content": f"AI 分析發生錯誤: {str(e)}"}],
            "next_steps": [],
            "summary": ""
        }
