# RAGBOTトラブルシューティングと使用方法

## 🔧 修正した問題

### 1. `loaders.py`の無限ループ問題
**症状**: データをingestしようとすると`MemoryError`が発生  
**原因**: `chunk_text`関数で無限ループが発生していた  
**修正**: `start`位置が前進することを保証するロジックを追加

### 2. FastAPIサーバーの起動とテスト方法
**問題**: ターミナルで直接uvicornコマンドを実行するとPowerShellの制約で不具合が発生  
**解決策**: 専用の起動スクリプト`start_server.py`を作成

---

## 🚀 使用方法

### サーバーの起動

**方法1: 起動スクリプトを使用（推奨）**
```powershell
c:\Users\User\Desktop\ragbot\.venv\Scripts\python.exe c:\Users\User\Desktop\ragbot\start_server.py
```

**方法2: uvicornを直接実行**
```powershell
cd c:\Users\User\Desktop\ragbot
.\.venv\Scripts\Activate.ps1
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

サーバーが起動したら、以下のURLにアクセスできます：
- Swagger UI: http://localhost:8000/docs
- API: http://localhost:8000

---

## 📝 APIエンドポイント

### 1. `/ingest` - ドキュメントの取り込み
**説明**: テキストファイルやPDFをChromaDBに取り込みます

**リクエスト例**:
```json
[
  "c:\\Users\\User\\Desktop\\ragbot\\data\\sample.txt"
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

---

## 📊 動作確認済み

✅ ChromaDBへのデータingest  
✅ ベクトル検索  
✅ OpenAI APIとの連携  
✅ RAGパイプライン全体の動作  
✅ FastAPIサーバーの起動  
✅ Swagger UIの表示

---

## 🎯 次のステップ

1. **外部ブラウザでSwagger UIを開く**:
   - http://localhost:8000/docs にアクセス
   - `/ask` エンドポイントで質問をテスト

2. **追加データをingest**:
   - `data/`フォルダに新しいPDFやTXTファイルを配置
   - `/ingest` エンドポイントで取り込み

3. **マルチモーダル機能のテスト**:
   - `/ask-with-media` エンドポイントで画像や音声ファイルをアップロード

---

## 📌 重要な注意事項

- サーバーを起動する際は、必ず `start_server.py` を使用するか、正しいディレクトリで実行してください
- Swagger UIからテストする場合は、外部ブラウザ（Chrome、Edge等）を使用してください
- VS CodeのSimple Browserは一部の機能で問題が発生する可能性があります
- データのingestには時間がかかる場合があります（ファイルサイズによる）
