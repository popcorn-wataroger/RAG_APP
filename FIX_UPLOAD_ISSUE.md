# 🎯 PDF アップロード問題の解決

## ✅ 修正完了

Swagger UI から `/ask-with-media` に PDF をアップロードすると "Failed to fetch" エラーが発生する問題を解決しました。

---

## 🔧 実施した修正

### 1. CORS ミドルウェアの追加
**ファイル**: [app.py](app.py#L23-L29)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Swagger UI からのアクセスを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. ロギング機能の追加
**ファイル**: [app.py](app.py#L17-L19)

リクエストの処理状況をリアルタイムで確認できるようになりました：

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**ログ出力例**:
```
INFO:app:リクエスト受信: query='このPDFの内容を要約してください', files=1件
INFO:app:ファイル処理開始: sample.pdf
INFO:app:ファイル読み込み: sample.pdf (2.34 MB)
INFO:app:PDF読み込み成功: sample.pdf (1234 文字)
INFO:app:RAG検索開始: 'このPDFの内容を...'
INFO:rag:検索結果: 4 件
INFO:app:回答生成開始
INFO:app:回答生成完了: 123 文字
```

### 3. エラーハンドリングの強化
**ファイル**: [app.py](app.py#L81-L209)

- ファイルサイズチェック（20MB制限）
- 各処理段階での try-except
- 詳細なエラーメッセージ
- HTTPException による適切なステータスコード

### 4. テストスクリプトの追加
**ファイル**: [test_upload.py](test_upload.py)

```bash
python test_upload.py
```

---

## 🧪 動作確認手順

### ステップ 1: サーバー起動

```bash
python start_server.py
```

**出力例**:
```
============================================================
RAG APP サーバーを起動しています...
URL: http://localhost:8080
Swagger UI: http://localhost:8080/docs
終了するには Ctrl+C を押してください
============================================================
```

### ステップ 2: テストスクリプト実行

**別のターミナルで実行**:
```bash
python test_upload.py
```

**成功例**:
```
============================================================
サーバー稼働確認
============================================================
✅ サーバーは正常に稼働しています
   Swagger UI: http://127.0.0.1:8080/docs

============================================================
テキストのみのテスト
============================================================
📤 送信中...
✅ ステータスコード: 200

📝 質問: RAGシステムについて教えてください
💬 回答:
RAGは検索拡張生成の略で、外部知識ベースを活用してLLMの回答精度を向上させる技術です。

============================================================
PDF アップロードテスト
============================================================
📄 テストファイル: data\sample.pdf
   サイズ: 234.56 KB

📤 送信中...
✅ ステータスコード: 200

📝 質問: このPDFの内容を要約してください
💬 回答:
このドキュメントは...
```

### ステップ 3: Swagger UI でテスト

1. **ブラウザで開く**: http://localhost:8080/docs

2. **/ask-with-media** セクションを展開

3. **"Try it out"** をクリック

4. パラメータ入力:
   - `query`: "このPDFの内容を要約してください"
   - `files`: "Choose File" で PDF を選択

5. **"Execute"** をクリック

6. **レスポンス確認**:
   ```json
   {
     "query": "このPDFの内容を要約してください",
     "answer": "このドキュメントは..."
   }
   ```

---

## 🐛 トラブルシューティング

### エラー 1: "Failed to fetch"

**原因**: CORS 設定が反映されていない

**解決策**:
```bash
# サーバーを再起動
Ctrl+C で停止
python start_server.py
```

### エラー 2: タイムアウト

**原因**: 大きなPDF（20MB以上）の処理に時間がかかる

**解決策**:
- PDFを分割する
- テキストを抽出して .txt でアップロード

### エラー 3: "処理中にエラーが発生しました"

**確認方法**: サーバーログを確認

**サーバーターミナルの出力例**:
```
ERROR:app:PDF処理エラー sample.pdf: [Errno 2] No such file or directory
```

**解決策**: エラーメッセージに応じて対処

---

## 📂 関連ファイル

- **[app.py](app.py)** - FastAPI メインファイル（CORS設定追加）
- **[rag.py](rag.py)** - RAGロジック（Document クラス、ロギング）
- **[test_upload.py](test_upload.py)** - テストスクリプト（新規作成）
- **[start_server.py](start_server.py)** - サーバー起動スクリプト（修正）
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - トラブルシューティングガイド（更新）

---

## 🎓 技術的な詳細

### CORS（Cross-Origin Resource Sharing）とは

Swagger UI は同じサーバー上で動作していても、異なる「オリジン」として扱われます。

**修正前**:
```
ブラウザ → Swagger UI → FastAPI
          ❌ CORS エラー
```

**修正後**:
```
ブラウザ → Swagger UI → FastAPI
          ✅ CORS許可
```

### ファイルアップロードの処理フロー

```
1. Swagger UI で PDF 選択
   ↓
2. multipart/form-data で送信
   ↓
3. FastAPI が UploadFile として受信
   ↓
4. await f.read() でバイナリ読み込み
   ↓
5. 一時ファイルに書き込み
   ↓
6. read_pdf() で PDF → テキスト変換
   ↓
7. RAG 検索 + LLM で回答生成
   ↓
8. JSON レスポンス返却
```

---

## 🚀 本番環境への適用

### 1. CORS 設定の変更

**本番環境では具体的なドメインを指定**:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://api.yourdomain.com"
    ],  # ワイルドカード "*" は使わない
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### 2. ファイルサイズ制限の調整

```python
# 本番環境では nginx などでも制限を設定
# client_max_body_size 20M;
```

### 3. 認証の追加

**[DESIGN_GUIDE.md](DESIGN_GUIDE.md)** を参照

---

## ✅ まとめ

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| CORS | ❌ 未設定 | ✅ 設定済み |
| ロギング | ❌ なし | ✅ 詳細ログ |
| エラー処理 | ⚠️ 不十分 | ✅ 強化 |
| ファイルサイズ制限 | ❌ なし | ✅ 20MB |
| テスト方法 | ⚠️ 手動のみ | ✅ スクリプト化 |

**問題解決完了！Swagger UI から PDF アップロードが正常に動作します 🎉**
