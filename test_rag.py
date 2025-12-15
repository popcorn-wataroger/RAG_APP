# test_rag.py
# ------------------------------------------------------------
# RAG の ingest と検索を確認する最小テスト
# ------------------------------------------------------------

from pathlib import Path

# ★ 重要：ingest_files を正しく import する
from rag import ingest_files, retrieve


def main():
    # ------------------------------------------------------------
    # 1) data フォルダ配下の .md / .txt をすべて集める
    # ------------------------------------------------------------
    md_files = [str(p) for p in Path("data").rglob("*.md")]
    txt_files = [str(p) for p in Path("data").rglob("*.txt")]
    files = md_files + txt_files

    print("INGEST TARGET FILES:", files)

    if not files:
        print("❌ data フォルダに .md / .txt がありません")
        return

    # ------------------------------------------------------------
    # 2) ingest 実行
    # ------------------------------------------------------------
    ingest_result = ingest_files(files)
    print("Ingest結果:", ingest_result)

    # ------------------------------------------------------------
    # 3) 検索テスト
    # ------------------------------------------------------------
    query = "これはどんなテストですか？"
    results = retrieve(query)

    print("\n" + "="*60)
    print(f"検索結果件数: {len(results)}")
    print("="*60)
    
    for i, doc in enumerate(results, 1):
        print(f"\n[結果 {i}]")
        print(f"ソース: {doc.metadata.get('source', 'unknown')}")
        print(f"チャンク: {doc.metadata.get('chunk', '?')}")
        print(f"内容: {doc.page_content[:100]}...\n")


if __name__ == "__main__":
    main()
