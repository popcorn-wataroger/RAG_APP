# RAGBOTトラブルシューティングと使用方法

## 🔧 修正した問題

### 1. `loaders.py`の無限ループ問題
**症状**: データをingestしようとすると`MemoryError`が発生  
**原因**: `chunk_text`関数で無限ループが発生していた  
**修正**: `start`位置が前進することを保証するロジックを追加

### 2. FastAPIサーバーの起動とテスト方法
**問題**: ターミナルで直接uvicornコマンドを実行するとPowerShellの制約で不具合が発生  
**解決策**: 専用の起動スクリプト`start_server.py`を作成

### 3. Swagger UI からの PDF アップロード失敗（CORS / Network Error）
**症状**: `/ask-with-media` に PDF をアップロードすると "Failed to fetch" エラー  
**原因**: 
- CORS 設定が未設定
- エラーハンドリング不足
- タイムアウト対策なし

**修正内容**:
- ✅ CORS ミドルウェアを追加
- ✅ 詳細なロギング機能
- ✅ ファイルサイズ制限（20MB）
- ✅ try-except による適切なエラーハンドリング
- ✅ HTTPException による明確なエラーレスポンス

---

## 🚀 使用方法

### サーバーの起動

**方法1: 起動スクリプトを使用（推奨）**
```powershell
python start_server.py
```

**方法2: uvicornを直接実行**
```powershell
python -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

サーバーが起動したら、以下のURLにアクセスできます：
- Swagger UI: http://localhost:8080/docs
- API: http://localhost:8080

---

## 📝 APIエンドポイント

### 1. `/ingest` - ドキュメントの取り込み
**説明**: テキストファイルやPDFをChromaDBに取り込みます

**リクエスト例**:
```json
[
  "data/sample.txt",
  "data/sample.md"
]
```

**Swagger UIでの使用方法**:
1. http://localhost:8000/docs を開く
2. `POST /ingest` セクションを展開
3. "Try it out" をクリック
4. ファイルパスの配列を入力
5. "Execute" をクリック

### 2. `/ask` - 質問に回答
**説明**: RAGシステムを使って質問に回答します

**リクエスト例**:
```json
{
  "query": "GPTとGeminiの違いは何ですか？"
}
```

**レスポンス例**:
```json
{
  "query": "GPTとGeminiの違いは何ですか？",
  "answer": "質問を短く言い換えると、「GPTとGeminiの違いは？」となります..."
}
```

**Swagger UIでの使用方法**:
1. http://localhost:8000/docs を開く
2. `POST /ask` セクションを展開
3. "Try it out" をクリック
4. queryフィールドに質問を入力
5. "Execute" をクリック

### 3. `/ask-with-media` - メディアファイル付き質問
**説明**: 音声、画像、PDF、テキストファイルと一緒に質問できます

**対応ファイル形式**:
- 音声: .wav, .mp3, .m4a, .ogg (Whisperで文字起こし)
- 画像: .png, .jpg, .jpeg (GPT-4 Visionで説明生成)
- PDF: .pdf (テキスト抽出)
- テキスト: .txt

**Swagger UIでの使用方法**:
1. http://localhost:8000/docs を開く
2. `POST /ask-with-media` セクションを展開
3. "Try it out" をクリック
4. queryフィールドに質問を入力
5. "Add file" をクリックしてファイルをアップロード
6. "Execute" をクリック

---

## 🧪 テストスクリプト

### RAGシステムの診断
```powershell
.\.venv\Scripts\python.exe test_rag.py
```

このスクリプトは以下を確認します：
- ChromaDBの接続状態
- データの存在確認
- Ingest機能
- 検索機能

### RAGパイプラインの直接テスト
```powershell
.\.venv\Scripts\python.exe c:\Users\User\Desktop\direct_test.py
```

このスクリプトはFastAPIを経由せず、直接RAGシステムをテストします。

---

## 💡 トラブルシューティング

### サーバーが起動しない
1. 仮想環境がアクティベートされているか確認
2. ポート8000が既に使用中でないか確認:
   ```powershell
   Get-NetTCPConnection -LocalPort 8000
   ```
3. 他のPythonプロセスが実行中でないか確認:
   ```powershell
   Get-Process python*
   ```

### データがingestできない
1. ファイルパスが正しいか確認（絶対パスを使用）
2. ファイルが存在するか確認
3. `.env`ファイルに`OPENAI_API_KEY`が設定されているか確認

### 質問に回答が返らない
1. ChromaDBにデータがingested確認:
   ```powershell
   .\.venv\Scripts\python.exe test_rag.py
   ```
2. OpenAI APIキーが有効か確認
3. インターネット接続を確認

### Swagger UIでエラーが発生
1. ブラウザのコンソールでエラーを確認
2. サーバーのログを確認
3. リクエストの形式が正しいか確認

### `/ask-with-media` で "Failed to fetch" エラー
**原因と対処法**:

#### 1. CORS エラー
**確認方法**: ブラウザの開発者ツール（F12）→ Console タブ
```
Access to fetch at 'http://127.0.0.1:8080/ask-with-media' from origin 'http://127.0.0.1:8080' has been blocked by CORS policy
```

**解決策**: 
- ✅ `app.py` に CORS ミドルウェアを追加済み
- サーバーを再起動: `python app.py`

#### 2. ファイルサイズ超過
**症状**: 大きなPDF（20MB以上）をアップロードすると失敗

**解決策**:
```python
# ファイルサイズ制限: 20MB
# より大きなファイルは分割してください
```

**回避方法**:
- PDF を分割（Adobe Acrobat / オンラインツール）
- テキスト抽出して .txt でアップロード

#### 3. タイムアウト
**症状**: 大きなファイルの処理中に接続が切れる

**解決策**:
```python
# test_upload.py でテスト（タイムアウト60秒設定済み）
python test_upload.py
```

#### 4. ログで原因を特定
**サーバーログの確認方法**:
```bash
# サーバー起動時のターミナル出力を確認
INFO:app:リクエスト受信: query='...', files=1件
INFO:app:ファイル読み込み: sample.pdf (2.34 MB)
INFO:app:PDF読み込み成功: sample.pdf (1234 文字)
```

**エラー例**:
```
ERROR:app:PDF処理エラー sample.pdf: ...
```

---

## 🧪 テスト方法

### 1. コマンドラインでテスト（推奨）
```bash
# テストスクリプト実行
python test_upload.py
```

**出力例**:
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
RAGは検索拡張生成の略で...
```

### 2. curl でテスト
```bash
# テキストのみ
curl -X POST "http://127.0.0.1:8080/ask-with-media" \
  -F "query=これは何のテストですか？"

# PDFアップロード
curl -X POST "http://127.0.0.1:8080/ask-with-media" \
  -F "query=このPDFの内容を要約してください" \
  -F "files=@data/sample.pdf"
```

### 3. Swagger UI でテスト
1. http://127.0.0.1:8080/docs にアクセス
2. `/ask-with-media` セクションを展開
3. "Try it out" をクリック
4. `query` に質問を入力
5. `files` で "Add string item" → "Choose File" で PDF 選択
6. "Execute" をクリック

**成功時のレスポンス**:
```json
{
  "query": "このPDFの内容を要約してください",
  "answer": "このドキュメントは..."
}
```

**失敗時のレスポンス**:
```json
{
  "detail": "処理中にエラーが発生しました: ..."
}
```

---

## 📊 動作確認済み

✅ ChromaDBへのデータingest  
✅ ベクトル検索  
✅ OpenAI APIとの連携  
✅ RAGパイプライン全体の動作  
✅ FastAPIサーバーの起動  
✅ Swagger UIの表示  
✅ CORS 設定  
✅ PDF/画像/音声のアップロード  
✅ エラーハンドリング  
✅ ロギング機能

---

## 🎯 次のステップ

1. **テストスクリプトで動作確認**:
   ```bash
   python test_upload.py
   ```

2. **Swagger UI でテスト**:
   - http://127.0.0.1:8080/docs にアクセス
   - `/ask` エンドポイントで質問をテスト
   - `/ask-with-media` でPDFアップロード

3. **追加データをingest**:
   - `data/`フォルダに新しいPDFやTXTファイルを配置
   - `/ingest` エンドポイントで取り込み

4. **本番環境へのデプロイ**:
   - CORS 設定を本番ドメインに変更
   - 認証機能の追加（DESIGN_GUIDE.md 参照）
   - HTTPS 設定

3. **マルチモーダル機能のテスト**:
   - `/ask-with-media` エンドポイントで画像や音声ファイルをアップロード

---

## 📌 重要な注意事項

- サーバーを起動する際は、必ず `start_server.py` を使用するか、正しいディレクトリで実行してください
- Swagger UIからテストする場合は、外部ブラウザ（Chrome、Edge等）を使用してください
- VS CodeのSimple Browserは一部の機能で問題が発生する可能性があります
- データのingestには時間がかかる場合があります（ファイルサイズによる）
