# start_server.py - サーバー起動スクリプト
import os
import sys

# 現在のディレクトリを取得（柔軟性向上）
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

# uvicornを直接実行
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("RAG APP サーバーを起動しています...")
    print("URL: http://localhost:8080")
    print("Swagger UI: http://localhost:8080/docs")
    print("終了するには Ctrl+C を押してください")
    print("=" * 60)
    print(f"作業ディレクトリ: {current_dir}")
    print("=" * 60)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,  # 開発中は reload 有効
        log_level="info"
    )
