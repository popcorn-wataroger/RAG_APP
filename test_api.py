# test_api.py - APIエンドポイントのテストスクリプト
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_ask():
    """ASKエンドポイントのテスト"""
    print("=== /ask エンドポイント テスト ===")
    url = f"{BASE_URL}/ask"
    payload = {"query": "GPTとGeminiの違いは何ですか？"}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 成功")
            print(f"\n【質問】\n{data['query']}")
            print(f"\n【回答】\n{data['answer']}")
            return True
        else:
            print(f"✗ 失敗: {response.text}")
            return False
    except Exception as e:
        print(f"✗ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ingest():
    """INGESTエンドポイントのテスト（既にデータがある場合はスキップ可能）"""
    print("\n=== /ingest エンドポイント テスト ===")
    url = f"{BASE_URL}/ingest"
    payload = ["c:\\Users\\User\\Desktop\\ragbot\\data\\sample.txt"]
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 成功: {data}")
            return True
        else:
            print(f"✗ 失敗: {response.text}")
            return False
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False

if __name__ == "__main__":
    print("FastAPIサーバーが http://127.0.0.1:8000 で起動していることを確認してください。\n")
    
    # /ask エンドポイントのテスト
    test_ask()
    
    print("\n" + "="*50)
    print("テスト完了")
