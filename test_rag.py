# test_rag.py - RAGシステムの診断スクリプト
import os
from rag import get_collection, ingest_files, retrieve

def test_chroma_status():
    """ChromaDBの状態を確認"""
    print("=== ChromaDB 状態確認 ===")
    try:
        col = get_collection()
        count = col.count()
        print(f"✓ コレクション接続成功")
        print(f"  保存されているチャンク数: {count}")
        
        if count == 0:
            print("⚠ データが空です。ingestが必要です。")
            return False
        else:
            # サンプルデータを取得
            sample = col.peek(limit=2)
            print(f"  サンプルID: {sample['ids'][:2]}")
            return True
    except Exception as e:
        print(f"✗ エラー: {e}")
        return False

def test_ingest():
    """サンプルデータをingest"""
    print("\n=== データIngest テスト ===")
    sample_path = os.path.join(os.getcwd(), "data", "sample.txt")
    if not os.path.exists(sample_path):
        print(f"✗ {sample_path} が見つかりません")
        return False
    
    try:
        result = ingest_files([sample_path])
        print(f"✓ Ingest成功: {result}")
        return True
    except Exception as e:
        print(f"✗ Ingest失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retrieve():
    """検索テスト"""
    print("\n=== 検索テスト ===")
    query = "GPTとGeminiの違い"
    try:
        results = retrieve(query)
        print(f"✓ 検索成功")
        print(f"  取得件数: {len(results)}")
        for i, r in enumerate(results, 1):
            print(f"\n  [{i}] {r['metadata']}")
            print(f"      {r['text'][:100]}...")
        return len(results) > 0
    except Exception as e:
        print(f"✗ 検索失敗: {e}")
        return False

if __name__ == "__main__":
    has_data = test_chroma_status()
    
    if not has_data:
        print("\n→ データをingestします...")
        if test_ingest():
            has_data = True
    
    if has_data:
        test_retrieve()
    
    print("\n診断完了")
