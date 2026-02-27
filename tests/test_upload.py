# test_upload.py
"""
/ask-with-media エンドポイントのテストスクリプト
"""
import requests
from pathlib import Path

# サーバーURL
BASE_URL = "http://127.0.0.1:8080"

def test_pdf_upload():
    """PDFアップロードのテスト"""
    print("=" * 60)
    print("PDF アップロードテスト")
    print("=" * 60)
    
    # テスト用PDFファイル（存在する場合）
    pdf_files = list(Path("data").glob("*.pdf"))
    
    if not pdf_files:
        print("❌ data フォルダに PDF ファイルがありません")
        print("   テスト用PDFを配置してください")
        return
    
    pdf_path = pdf_files[0]
    print(f"📄 テストファイル: {pdf_path}")
    print(f"   サイズ: {pdf_path.stat().st_size / 1024:.2f} KB")
    
    # リクエスト送信
    try:
        with open(pdf_path, "rb") as f:
            files = {"files": (pdf_path.name, f, "application/pdf")}
            data = {"query": "このPDFの内容を要約してください"}
            
            print(f"\n📤 送信中...")
            response = requests.post(
                f"{BASE_URL}/ask-with-media",
                files=files,
                data=data,
                timeout=60  # 60秒タイムアウト
            )
        
        print(f"✅ ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📝 質問: {result['query']}")
            print(f"\n💬 回答:\n{result['answer']}")
        else:
            print(f"❌ エラー: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ タイムアウト: サーバーが60秒以内に応答しませんでした")
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: サーバーが起動していません")
        print("   python app.py を実行してください")
    except Exception as e:
        print(f"❌ エラー: {e}")


def test_text_only():
    """テキストのみのテスト"""
    print("\n" + "=" * 60)
    print("テキストのみのテスト")
    print("=" * 60)
    
    try:
        data = {"query": "RAGシステムについて教えてください"}
        
        print(f"📤 送信中...")
        response = requests.post(
            f"{BASE_URL}/ask-with-media",
            data=data,
            timeout=30
        )
        
        print(f"✅ ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📝 質問: {result['query']}")
            print(f"\n💬 回答:\n{result['answer']}")
        else:
            print(f"❌ エラー: {response.text}")
    
    except Exception as e:
        print(f"❌ エラー: {e}")


def check_server_health():
    """サーバーの稼働確認"""
    print("=" * 60)
    print("サーバー稼働確認")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ サーバーは正常に稼働しています")
            print(f"   Swagger UI: {BASE_URL}/docs")
            return True
        else:
            print(f"⚠️ サーバーは起動していますが、異常なステータス: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ サーバーに接続できません")
        print("   python app.py を実行してください")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


if __name__ == "__main__":
    # サーバー稼働確認
    if check_server_health():
        # テスト実行
        test_text_only()
        test_pdf_upload()
    else:
        print("\n" + "=" * 60)
        print("サーバーを起動してください:")
        print("  python app.py")
        print("=" * 60)
