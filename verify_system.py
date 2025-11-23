import sys
import os
import streamlit as st

# 模擬環境變數載入 (因為此腳本不透過 streamlit run 執行，需手動讀取 secrets)
try:
    import toml
    secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit/secrets.toml')
    if os.path.exists(secrets_path):
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)
            os.environ['GEMINI_API_KEY'] = secrets.get('GEMINI_API_KEY', '')
            print("✅ 成功讀取 secrets.toml")
    else:
        print("⚠️ 警告: 找不到 .streamlit/secrets.toml")
except Exception as e:
    print(f"⚠️ 讀取 secrets 失敗: {e}")

# 加入路徑
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def verify_imports():
    print("\n--- 1. 驗證模組引用 ---")
    try:
        from app.database import init_db
        from app.utils.transcriber import transcribe_audio, structure_meeting_notes
        from app.utils.doc_gen import generate_meeting_minutes
        print("✅ 所有模組引用成功")
        return True
    except ImportError as e:
        print(f"❌ 模組引用失敗: {e}")
        return False

def verify_gemini_api():
    print("\n--- 2. 驗證 Gemini API 連線 ---")
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ 未找到 GEMINI_API_KEY")
        return False
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        print("正在發送測試請求給 Gemini...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hello, reply with 'OK' if you see this.",
        )
        print(f"Gemini 回應: {response.text}")
        if response.text:
            print("✅ Gemini API 連線測試成功")
            return True
        return False
    except Exception as e:
        print(f"❌ Gemini API 測試失敗: {e}")
        return False

def verify_database():
    print("\n--- 3. 驗證資料庫 ---")
    try:
        from app.database import init_db
        init_db()
        if os.path.exists("meetings.db"):
            print("✅ 資料庫初始化成功 (meetings.db 存在)")
            return True
        return False
    except Exception as e:
        print(f"❌ 資料庫測試失敗: {e}")
        return False

def verify_whisper():
    print("\n--- 4. 驗證 Whisper 載入 ---")
    try:
        import whisper
        # 這裡只檢查套件是否存在，載入模型太慢，略過
        print("✅ Whisper 套件已安裝")
        return True
    except ImportError:
        print("❌ Whisper 套件未安裝")
        return False

if __name__ == "__main__":
    print("開始自我驗證程序...")
    
    checks = [
        verify_imports(),
        verify_database(),
        verify_whisper(),
        verify_gemini_api()
    ]
    
    if all(checks):
        print("\n🎉🎉🎉 系統自我驗證全部通過！ 🎉🎉🎉")
    else:
        print("\n⚠️⚠️⚠️ 系統驗證發現問題，請檢查上方錯誤訊息。 ⚠️⚠️⚠️")

