# RAG アプリケーション設計ガイド

## 📖 概要

このドキュメントは、RAG（Retrieval-Augmented Generation）アプリケーションの設計方針とベストプラクティスをまとめたものです。

---

## 🏗️ アーキテクチャ設計

### 1. データフロー

```
ファイル (.md/.txt/.pdf)
    ↓
ingest_files()  ← チャンク分割
    ↓
ChromaDB (Persistent)
    ↓
retrieve()  ← ベクトル検索
    ↓
Document オブジェクト
    ↓
build_context_snippets()
    ↓
LLM (GPT-4o-mini)
```

---

## 🎯 Q&A：設計判断

### Q1. retrieve の戻り値設計について

**A: Document オブジェクトを推奨**

#### ✅ 採用した設計
```python
@dataclass
class Document:
    page_content: str
    metadata: Dict[str, any]
```

#### 理由
1. **LangChain 互換性**: 将来的な拡張が容易
2. **型安全性**: IDE の補完・型チェックが効く
3. **可読性**: `doc.page_content` の方が直感的
4. **標準パターン**: RAG 実装の事実上の標準

#### ❌ dict を避ける理由
```python
# 非推奨
{"text": "...", "metadata": {...}}

# 問題点
- タイポに気づきにくい（r["txt"] など）
- 型推論が効かない
- IDE のサポートが弱い
```

---

### Q2. ingest API を残すべきか？

**A: 認証付きで残す（運用専用 API として）**

#### 実装方針

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/ingest")
async def api_ingest(
    files: List[UploadFile],
    token: str = Depends(security)
):
    # 認証チェック
    if token.credentials != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(401, "Unauthorized")
    
    # ingest 実行
    ...
```

#### ユースケース
- ✅ 管理者による手動アップロード
- ✅ バッチ処理での定期更新
- ✅ CI/CD パイプラインからの登録
- ❌ 一般ユーザーからの直接呼び出し（禁止）

---

### Q3. chunk_size / chunk_overlap の考え方

#### 用途別推奨値

| 用途 | CHUNK_SIZE | CHUNK_OVERLAP | 理由 |
|------|------------|---------------|------|
| **日本語ドキュメント** | 1000-1500 | 150-300 | 全角1文字=2-3byte。文脈を保持するため overlap は 15-20% |
| **コード・技術文書** | 800-1200 | 100-200 | 関数・クラス単位で区切れるサイズ |
| **PDF（数十ページ）** | 1500-2000 | 200-400 | ページまたぎ対策。overlap を大きめに |
| **FAQ・短文** | 500-800 | 50-100 | 1質問1チャンクを目指す |

#### 調整の指針

```python
# 日本語中心の場合
CHUNK_SIZE = 1500  # 全角750文字程度
CHUNK_OVERLAP = 200  # 約13%

# 英語中心の場合
CHUNK_SIZE = 1000  # 約250単語
CHUNK_OVERLAP = 150  # 15%
```

#### ⚠️ 注意点

1. **overlap が大きすぎる**
   - 検索結果が重複しやすい
   - ストレージ増加
   - 推奨: chunk_size の 10-20%

2. **size が大きすぎる**
   - LLM のコンテキスト制限に引っかかる
   - 関連性の低い情報が混入
   - 推奨: 2000 以下

3. **size が小さすぎる**
   - 文脈が失われる
   - 検索精度低下
   - 推奨: 500 以上

---

## 🛡️ 実運用のベストプラクティス

### 1. エラーハンドリング

```python
# 実装済み
try:
    raw = read_pdf(path)
except Exception as e:
    logger.error(f"ファイル読み込みエラー {path}: {e}")
    failed_files.append(path)
```

### 2. ロギング

```python
# 実装済み
logger.info(f"✓ {path}: {len(chunks)} chunks")
logger.warning(f"空のファイル: {path}")
logger.error(f"ChromaDB 追加エラー: {e}")
```

### 3. 戻り値の詳細化

```python
# 実装済み
return {
    "added_chunks": 43,
    "failed_files": ["data/broken.pdf"],
    "total_files": 5
}
```

### 4. 型ヒントの徹底

```python
# 実装済み
def retrieve(query: str, top_k: int = TOP_K) -> List[Document]:
```

---

## 📊 パフォーマンス最適化

### 1. バッチ処理

```python
# 推奨: 大量ファイルは分割して ingest
BATCH_SIZE = 100
for i in range(0, len(files), BATCH_SIZE):
    batch = files[i:i + BATCH_SIZE]
    ingest_files(batch)
```

### 2. インデックス最適化

```python
# ChromaDB のコレクション作成時
collection = client.get_or_create_collection(
    name="docs",
    embedding_function=openai_ef,
    metadata={"hnsw:space": "cosine"}  # デフォルトは l2
)
```

### 3. キャッシュ戦略

```python
# 同じクエリの結果をキャッシュ
from functools import lru_cache

@lru_cache(maxsize=100)
def retrieve_cached(query: str) -> List[Document]:
    return retrieve(query)
```

---

## 🔒 セキュリティ考慮事項

### 1. API 認証

```python
# 環境変数で管理
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# JWT 推奨
from jose import jwt
```

### 2. ファイルアップロード制限

```python
# FastAPI 設定
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com"]
)

# ファイルサイズ制限
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
```

### 3. 入力検証

```python
# パストラバーサル対策
import os.path

def safe_file_path(path: str) -> str:
    if ".." in path or path.startswith("/"):
        raise ValueError("Invalid path")
    return os.path.normpath(path)
```

---

## 🧪 テスト戦略

### 1. ユニットテスト

```python
# test_rag.py
def test_ingest_empty_file():
    result = ingest_files(["data/empty.txt"])
    assert result["added_chunks"] == 0

def test_retrieve_returns_documents():
    docs = retrieve("test query")
    assert all(isinstance(d, Document) for d in docs)
```

### 2. 統合テスト

```bash
# 実際のデータで動作確認
python test_rag.py
```

---

## 📈 モニタリング

### 1. メトリクス収集

```python
# ログベースでモニタリング
logger.info(f"検索レイテンシ: {elapsed:.2f}s")
logger.info(f"取得件数: {len(results)}")
```

### 2. アラート設定

- ingest 失敗率が 10% 超過
- 検索レイテンシが 3秒超過
- ChromaDB サイズが 10GB 超過

---

## 🔄 バージョン管理

### 1. スキーマバージョニング

```python
# metadata にバージョン情報を追加
metadatas.append({
    "source": path,
    "chunk": i,
    "schema_version": "1.0",  # 追加
    "ingest_date": datetime.now().isoformat()
})
```

### 2. マイグレーション

```python
# 古いデータの移行スクリプト
def migrate_v0_to_v1():
    col = get_collection()
    # バッチで更新
    ...
```

---

## 📚 参考リンク

- [LangChain Document](https://python.langchain.com/docs/modules/data_connection/document_loaders/)
- [ChromaDB Best Practices](https://docs.trychroma.com/usage-guide)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

---

## 🎓 まとめ

| 項目 | 推奨 | 理由 |
|------|------|------|
| 戻り値 | `Document` オブジェクト | 型安全性・拡張性 |
| ingest API | 認証付きで残す | 運用での柔軟性 |
| chunk_size | 1000-1500 (日本語) | 文脈保持とバランス |
| chunk_overlap | 150-300 (15-20%) | 重複と精度のトレードオフ |
| エラー処理 | 必須 | 本番運用での安定性 |
| ロギング | 詳細に | デバッグ・モニタリング |

**設計の基本方針**: 
「動く」だけでなく「安全に変更できる構成」を目指す ✅
