# start_server.py - サーバー起動スクリプト
import os
import sys

# 作業ディレクトリを設定
os.chdir(r"c:\Users\User\Desktop\ragbot")

# uvicornを直接実行（reloadなしで安定動作）
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("RAGBOTサーバーを起動しています...")
    print("URL: http://localhost:8000")
    print("Swagger UI: http://localhost:8000/docs")
    print("終了するには Ctrl+C を押してください")
    print("=" * 60)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # reloadを無効化して安定動作
        log_level="info"
    )
