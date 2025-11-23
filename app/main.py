import streamlit as st
import os
import sys

# 將專案根目錄加入 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import json
import pandas as pd
from app.database import init_db, save_meeting, get_all_meetings, get_meeting_details
from app.utils.transcriber import transcribe_audio, structure_meeting_notes
from app.utils.doc_gen import generate_meeting_minutes

# 初始化資料庫
init_db()

st.set_page_config(page_title="AI 智慧會議記錄助手", layout="wide")

st.title("🎙️ AI 智慧會議記錄助手 (Gemini Edition)")
st.markdown("上傳錄音檔，自動轉錄並透過 Google Gemini 整理成結構化會議記錄。")

# 側邊欄設定
with st.sidebar:
    st.header("設定")
    if "GEMINI_API_KEY" in st.secrets:
        st.success("✅ Gemini API Key 已設定")
    else:
        st.error("❌ 未偵測到 Gemini API Key")
        st.info("請在 .streamlit/secrets.toml 中設定 GEMINI_API_KEY")
    
    st.markdown("---")
    st.info("此工具使用 Google Gemini 2.5 Flash 進行內容分析，並依照「中正北路24號」格式輸出。")

# 主畫面分頁
tab1, tab2 = st.tabs(["📝 新增會議記錄", "🗄️ 歷史紀錄"])

with tab1:
    uploaded_file = st.file_uploader("上傳錄音檔案", type=["mp3", "wav", "m4a", "mp4"])

    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/mp3')
        
        if st.button("開始分析處理", type="primary"):
            if "GEMINI_API_KEY" not in st.secrets:
                st.warning("⚠️ 未檢測到 API Key，將僅進行逐字稿轉錄。")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 1. 儲存暫存檔
                status_text.text("正在處理檔案...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # 2. 轉錄
                status_text.text("⏳ 正在進行語音轉錄 (Whisper)...")
                progress_bar.progress(30)
                transcription = transcribe_audio(tmp_file_path)
                
                # 3. 結構化分析
                status_text.text("🤖 正在透過 Google Gemini 進行分析...")
                progress_bar.progress(70)
                structured_data = structure_meeting_notes(transcription)
                
                # 4. 存入資料庫
                status_text.text("💾 正在儲存資料...")
                progress_bar.progress(90)
                
                meeting_id = save_meeting(
                    filename=uploaded_file.name,
                    transcription=transcription,
                    structured_data=structured_data
                )
                
                os.unlink(tmp_file_path)
                
                progress_bar.progress(100)
                status_text.success("✅ 處理完成！")
                
                # 顯示結果
                st.divider()
                
                # 顯示會議主題
                st.subheader("📌 會議主題")
                topics = structured_data.get("meeting_topics", [])
                if topics:
                    for t in topics:
                        st.write(f"- {t}")
                else:
                    st.write("(無特定主題)")

                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("👥 參與人員")
                    participants = structured_data.get("participants", [])
                    if participants:
                        # 判斷是舊格式還是新格式
                        if isinstance(participants[0], dict):
                            df_p = pd.DataFrame(participants)
                            st.dataframe(df_p, hide_index=True, use_container_width=True)
                        else:
                            st.write(", ".join(participants))
                    
                    st.subheader("📝 總結摘要")
                    st.write(structured_data.get("summary", "(無總結)"))
                
                with col2:
                    st.subheader("🚀 下一步行動")
                    next_steps = structured_data.get("next_steps", [])
                    if next_steps:
                        if isinstance(next_steps[0], dict):
                            df_ns = pd.DataFrame(next_steps)
                            st.dataframe(df_ns, hide_index=True, use_container_width=True)
                        else:
                            for step in next_steps:
                                st.write(f"- {step}")

                st.subheader("🔑 重點內容")
                key_points = structured_data.get("key_points", [])
                for kp in key_points:
                    if isinstance(kp, dict):
                        st.markdown(f"**{kp.get('title', '')}**")
                        st.write(kp.get('content', ''))
                    else:
                        st.write(f"- {kp}")

                with st.expander("查看完整逐字稿 (不會匯出至 Word)"):
                    st.text_area("逐字稿", transcription, height=200)
                
                # 產生 Word 下載
                doc_file = generate_meeting_minutes({
                    "filename": uploaded_file.name,
                    "transcription": transcription,
                    **structured_data
                })
                
                st.download_button(
                    label="📥 下載 Word 會議記錄 (自訂格式)",
                    data=doc_file,
                    file_name=f"會議記錄_{os.path.splitext(uploaded_file.name)[0]}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            except Exception as e:
                st.error(f"發生錯誤: {str(e)}")
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

with tab2:
    st.subheader("歷史會議記錄")
    df = get_all_meetings()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        selected_id = st.selectbox("選擇會議 ID 以查看詳情", df['id'].tolist())
        
        if selected_id:
            details = get_meeting_details(selected_id)
            if details:
                st.divider()
                st.markdown(f"### 📄 {details['filename']}")
                
                # 解析 JSON
                def safe_json_load(json_str, default_val):
                    try:
                        return json.loads(json_str)
                    except:
                        return default_val

                participants = safe_json_load(details['participants'], [])
                key_points = safe_json_load(details['key_points'], [])
                next_steps = safe_json_load(details['next_steps'], [])
                meeting_topics = safe_json_load(details.get('meeting_topics'), [])
                summary = details.get('summary', '')

                # 顯示詳細資訊 (簡化版)
                st.write(f"**總結**: {summary}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**參與人:**")
                    if participants and isinstance(participants[0], dict):
                        st.dataframe(pd.DataFrame(participants), hide_index=True)
                    else:
                        st.write(participants)

                with col2:
                    st.markdown("**待辦事項:**")
                    if next_steps and isinstance(next_steps[0], dict):
                        st.dataframe(pd.DataFrame(next_steps), hide_index=True)
                    else:
                        st.write(next_steps)
                
                # 下載按鈕
                doc_file_hist = generate_meeting_minutes({
                    "filename": details['filename'],
                    "created_at": details['created_at'],
                    "participants": participants,
                    "key_points": key_points,
                    "next_steps": next_steps,
                    "summary": summary,
                    "meeting_topics": meeting_topics,
                    "transcription": details['transcription']
                })
                
                st.download_button(
                    label="📥 下載此記錄 (Word)",
                    data=doc_file_hist,
                    file_name=f"會議記錄_{details['filename']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_hist"
                )
