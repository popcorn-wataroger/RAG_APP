# 🌐 RAG APP アクセスURL

## ✅ サーバー起動完了

FastAPI サーバーが正常に起動しています。

---

## 📡 正しいアクセスURL

### ⚠️ 重要な注意点

**❌ 使えないURL:**
```
http://0.0.0.0:8080  ← これは使えません！
```

**✅ 正しいURL:**
```
http://localhost:8080
または
http://127.0.0.1:8080
```

### 理由
- `0.0.0.0` はサーバー側の設定（すべてのネットワークインターフェースでリッスン）
- ブラウザからは `localhost` または `127.0.0.1` を使用する必要があります

---

## 🎯 アクセス先一覧

| 用途 | URL | 説明 |
|------|-----|------|
| **Swagger UI** | **http://localhost:8080/docs** | 📝 API テスト画面（推奨） |
| **ReDoc** | http://localhost:8080/redoc | 📚 API ドキュメント |
| **API エンドポイント** | http://localhost:8080 | 🔌 直接API呼び出し |

---

## 🧪 動作確認手順

### 1. ブラウザでアクセス

**おすすめ:** http://localhost:8080/docs

```
1. ブラウザ（Chrome/Edge/Firefox）を開く
2. アドレスバーに「localhost:8080/docs」と入力
3. Enter キー
```

**表示されるもの:**
- Swagger UI（緑色のヘッダー）
- 3つのエンドポイント:
  - POST /ingest
  - POST /ask
  - POST /ask-with-media

### 2. /ask エンドポイントをテスト

```
1. "POST /ask" セクションを展開
2. "Try it out" をクリック
3. query に質問を入力: 「RAGとは何ですか？」
4. "Execute" をクリック
5. Response body に回答が表示される
```

**期待される結果:**
```json
{
  "query": "RAGとは何ですか？",
  "answer": "RAG（Retrieval-Augmented Generation）は..."
}
```

### 3. /ask-with-media でPDFテスト

```
1. "POST /ask-with-media" セクションを展開
2. "Try it out" をクリック
3. query: 「このPDFの内容を要約してください」
4. files: "Choose File" で PDF を選択
5. "Execute" をクリック
```

---

## 🔍 トラブルシューティング

### ❌ 「このサイトにアクセスできません」と表示される

**原因1:** サーバーが起動していない

**確認方法:**
```powershell
# ターミナルで以下が表示されているか確認
INFO:     Application startup complete.
```

**解決策:**
```powershell
python start_server.py
```

---

**原因2:** 間違ったURLを使っている

**確認:**
- ❌ http://0.0.0.0:8080
- ✅ http://localhost:8080

---

**原因3:** ポートが競合している

**確認方法:**
```powershell
netstat -ano | findstr :8080
```

**解決策:**
```powershell
# 別のポートを使用
# start_server.py の port=8080 を port=8081 に変更
```

---

### ⚠️ Swagger UI は表示されるが API が動かない

**確認項目:**

1. **OpenAI API キーの設定**
   ```powershell
   # .env ファイルを確認
   type .env
   ```
   `OPENAI_API_KEY=sk-...` が設定されているか確認

2. **ChromaDB のデータ**
   ```powershell
   # ingest を実行
   python test_rag.py
   ```

3. **ブラウザのコンソールログ**
   - F12 キーを押す
   - Console タブでエラーを確認

---

## 📊 サーバーログの見方

**正常な起動:**
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Application startup complete.
```

**リクエスト受信時:**
```
INFO:app:リクエスト受信: query='...', files=0件
INFO:app:RAG検索開始: '...'
INFO:rag:検索結果: 4 件
INFO:app:回答生成完了: 123 文字
```

**エラー発生時:**
```
ERROR:app:PDF処理エラー: ...
ERROR:rag:検索エラー: ...
```

---

## 🎓 よくある質問

### Q1. localhost と 127.0.0.1 の違いは？

**A:** 実質的に同じです。

- `localhost` → DNS で `127.0.0.1` に解決される
- `127.0.0.1` → 直接IPアドレスを指定

どちらを使っても構いません。

### Q2. 外部からアクセスできますか？

**A:** 現在の設定では同じPC内のみです。

**他のPCからアクセスする場合:**
1. Windows ファイアウォールで 8080 ポートを開放
2. PCのIPアドレスを確認: `ipconfig`
3. `http://<PCのIP>:8080` でアクセス

### Q3. サーバーを止めるには？

**A:** ターミナルで `Ctrl+C` を押す

```
INFO:     Shutting down
INFO:     Application shutdown complete.
```

---

## 🚀 次のステップ

1. **まず確認:** http://localhost:8080/docs
2. **データ登録:** `/ingest` エンドポイントでドキュメントを追加
3. **質問テスト:** `/ask` で質問してみる
4. **PDFテスト:** `/ask-with-media` でPDFアップロード

---

## ✅ チェックリスト

- [ ] サーバーが起動している (`python start_server.py`)
- [ ] http://localhost:8080/docs にアクセスできる
- [ ] Swagger UI が表示される
- [ ] `/ask` エンドポイントが動く
- [ ] レスポンスが返ってくる

すべてチェックが付けば成功です！🎉
