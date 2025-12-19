# 🔍 不明確な回答の原因と対策

## 🐛 問題の症状

Swagger UI で PDF をアップロードして質問しても、以下のような不明確な回答が返る：

```json
{
  "query": "この資料を要約して",
  "answer": "資料の内容は不明瞭であり、具体的な情報や要点を把握することができませんね。"
}
```

---

## 🔎 原因の特定

### 考えられる原因

1. **PDFの内容が正しく抽出されていない**
   - 画像のみのPDF（スキャンPDF）
   - 暗号化されたPDF
   - 壊れたPDF

2. **ChromaDB にデータが登録されていない**
   - `ingest` を実行していない
   - RAG検索結果が0件

3. **プロンプトの構成が不適切**
   - アップロードファイルよりRAGを優先している
   - コンテキストが空の場合の処理が不十分

---

## ✅ 実施した修正

### 1. プロンプト構成の改善

**修正前:**
```python
# RAGとメディアを同列に扱っていた
final_prompt = (
    f"【RAGコンテキスト】\n{rag_context}\n\n"
    f"【メディア由来コンテキスト】\n{extra_context}\n\n"
)
```

**修正後:**
```python
# ケース別に適切なプロンプトを生成
if extra_context and not rag_context:
    # アップロードファイルのみ → ファイル内容を優先
    final_prompt = f"【ファイル内容】\n{extra_context}\n\n"
    
elif extra_context and rag_context:
    # 両方ある → アップロードファイルを優先
    final_prompt = (
        f"【アップロードされたファイル】\n{extra_context}\n\n"
        f"【参考情報（データベース）】\n{rag_context}\n\n"
    )
    
elif rag_context and not extra_context:
    # RAGのみ → データベースから検索
    final_prompt = f"【コンテキスト】\n{rag_context}\n\n"
    
else:
    # 何もない → 一般知識で回答
    final_prompt = "注：参照できる資料がないため、一般的な回答になります。"
```

### 2. PDF読み込みの詳細ログ

```python
logger.info(f"PDF読み込み開始: {name}")
txt = read_pdf(tmp_path)

if not txt or not txt.strip():
    logger.warning(f"PDF内容が空: {name}")
else:
    logger.info(f"PDF読み込み成功: {len(txt)} 文字")
    preview = txt[:200].replace('\n', ' ')
    logger.info(f"PDF内容プレビュー: {preview}...")
```

### 3. デバッグ情報の追加

```python
logger.info(f"RAGコンテキスト長: {len(rag_context)} 文字")
logger.info(f"メディアコンテキスト長: {len(extra_context)} 文字")
logger.info(f"メディアファイル数: {len(extra_parts)}")
logger.info(f"プロンプト長: {len(final_prompt)} 文字")
```

---

## 🧪 テスト手順

### ステップ 1: サーバー再起動

```bash
# 現在のサーバーを停止 (Ctrl+C)
# 再起動
python start_server.py
```

### ステップ 2: PDFアップロードテスト

1. http://localhost:8080/docs を開く
2. `/ask-with-media` → "Try it out"
3. パラメータ入力:
   - `query`: "この資料を要約してください"
   - `files`: PDF ファイルを選択
4. "Execute"

### ステップ 3: ログ確認

**サーバーターミナルで以下を確認:**

```
INFO:app:リクエスト受信: query='この資料を要約してください', files=1件
INFO:app:ファイル処理開始: sample.pdf
INFO:app:ファイル読み込み: sample.pdf (2.34 MB)
INFO:app:PDF読み込み開始: sample.pdf
INFO:app:PDF読み込み成功: sample.pdf (全体: 5432 文字, 使用: 5432 文字)
INFO:app:PDF内容プレビュー: これはサンプルPDFです...
INFO:app:RAG検索開始: 'この資料を要約してください'
INFO:rag:検索結果: 0 件
INFO:app:RAGコンテキスト長: 0 文字
INFO:app:メディアコンテキスト長: 5450 文字  ← PDFの内容が読めている
INFO:app:メディアファイル数: 1
INFO:app:プロンプト長: 5600 文字
INFO:app:回答生成開始
INFO:app:回答生成完了: 150 文字
```

### ステップ 4: 結果の確認

**期待される結果:**
```json
{
  "query": "この資料を要約してください",
  "answer": "このPDFは〇〇について説明しており、主なポイントは..."
}
```

---

## 🔍 問題が続く場合の診断

### 1. PDFが画像のみの場合

**ログに表示:**
```
WARNING:app:PDF内容が空: sample.pdf
```

**対処法:**
- OCR処理が必要（現在未対応）
- テキスト形式のPDFを使用
- または画像として処理（vision API 使用）

### 2. ChromaDB にデータがない場合

**ログに表示:**
```
INFO:rag:検索結果: 0 件
INFO:app:メディアコンテキスト長: 0 文字
```

**対処法:**
```bash
# データを登録
python test_rag.py
```

### 3. ファイルが読み込めない場合

**ログに表示:**
```
ERROR:app:PDF処理エラー sample.pdf: ...
```

**対処法:**
- PDFファイルの破損確認
- 別のPDFで試す
- ファイルサイズを確認（20MB以下）

---

## 📊 ログの見方（チェックリスト）

正常な処理の場合、以下の順序でログが出力されます：

- [ ] `リクエスト受信: query='...', files=1件`
- [ ] `ファイル処理開始: sample.pdf`
- [ ] `ファイル読み込み: sample.pdf (X.XX MB)`
- [ ] `PDF読み込み開始: sample.pdf`
- [ ] `PDF読み込み成功: sample.pdf (XXXX 文字)` ← **重要**
- [ ] `PDF内容プレビュー: ...` ← **内容確認**
- [ ] `RAG検索開始: '...'`
- [ ] `検索結果: X 件`
- [ ] `メディアコンテキスト長: XXXX 文字` ← **0以上であること**
- [ ] `回答生成開始`
- [ ] `回答生成完了: XXX 文字`

---

## 🎯 改善ポイントまとめ

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| **プロンプト優先度** | RAGとメディア同列 | メディア優先 |
| **空コンテキスト** | エラーメッセージ不明瞭 | 明確なメッセージ |
| **ログ詳細度** | 最小限 | 詳細なデバッグ情報 |
| **PDF内容確認** | なし | プレビュー表示 |

---

## 💡 推奨される使い分け

### `/ask` エンドポイント
- データベースに登録済みの資料から検索
- 複数の資料をまたいだ質問
- 長期的に参照する資料

### `/ask-with-media` エンドポイント
- 一時的なファイル分析
- アップロードしたPDF/画像の内容確認
- データベースに登録しない資料

---

## 🚀 次回以降の改善案

1. **OCR対応** - 画像のみのPDFにも対応
2. **ファイル分析結果のキャッシュ** - 同じファイルの再アップロード高速化
3. **コンテキスト長の最適化** - トークン数制限を考慮
4. **複数ファイルの優先順位** - 複数PDFアップロード時の処理

---

サーバーを再起動して、詳細なログを確認しながらテストしてください 🔍
