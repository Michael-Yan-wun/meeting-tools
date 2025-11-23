import sys
import os
import json
import argparse
from transcriber import transcribe_audio, structure_meeting_notes
from doc_gen import generate_meeting_minutes

# 設定 stdout 編碼為 utf-8，避免中文輸出亂碼
sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description='Process meeting audio')
    parser.add_argument('file_path', help='Path to the audio file')
    parser.add_argument('--api_key', help='Gemini API Key', required=True)
    parser.add_argument('--output_dir', help='Directory to save generated files', required=True)
    
    args = parser.parse_args()
    
    file_path = args.file_path
    filename = os.path.basename(file_path)
    
    try:
        # 1. 轉錄
        # print(f"Step 1/3: Transcribing {filename}...", file=sys.stderr)
        transcription = transcribe_audio(file_path)
        
        # 2. AI 分析
        # print(f"Step 2/3: Analyzing with Gemini...", file=sys.stderr)
        structured_data = structure_meeting_notes(transcription, api_key=args.api_key)
        
        # 3. 生成 Word
        # print(f"Step 3/3: Generating Word document...", file=sys.stderr)
        doc_stream = generate_meeting_minutes({
            "filename": filename,
            "transcription": transcription,
            **structured_data
        })
        
        # 儲存 Word 檔
        doc_filename = f"Meeting_Minutes_{os.path.splitext(filename)[0]}.docx"
        doc_path = os.path.join(args.output_dir, doc_filename)
        
        with open(doc_path, "wb") as f:
            f.write(doc_stream.getvalue())
            
        # 輸出最終結果 JSON 給 Node.js
        result = {
            "success": True,
            "filename": filename,
            "transcription": transcription,
            "structured_data": structured_data,
            "doc_path": doc_path
        }
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result, ensure_ascii=False))

if __name__ == "__main__":
    main()

