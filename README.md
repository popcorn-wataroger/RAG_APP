# RAG_APP
# 🧠 NotebookLM-like RAG Bot

このプロジェクトは、FastAPIを使って構築された「NotebookLM風のRAG（Retrieval-Augmented Generation）Bot」です。  
PDFやテキストファイルをアップロードし、ChatGPT APIを通して要約や質問応答を行うことができます。

---

## 🚀 起動方法（Windows PowerShell の場合）

以下の手順でアプリを起動できます。

```bash
# ① 作業フォルダに移動
cd C:\Users\User\Desktop\RAG_APP

# ② 仮想環境を作成（rag_appは任意の名前で）
python3 -m venv rag_app

# ③ 仮装環境を起動
source rag_app/bin/activate

# ④ 必要なモジュールをインストール
pip install -r requirements.txt

# ⑤ 環境変数ファイル（.env）を作成
# プロジェクトルートに .env ファイルを作成し、以下の内容を記載してください：
PROVIDER=openai
OPENAI_API_KEY=<あなたのAPIキーをここに入力>
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-large
OPENAI_TRANSCRIBE_MODEL=whisper-1
CHROMA_DIR=./chroma_store

# ⑥ FastAPIアプリを起動
uvicorn app:app --reload --port 8000

## 開発メモ：いま使っている起動コマンド（Windows）

> 開発中メモ。自分が実行して動作確認したコマンドを残しています。

### 1) 仮想環境を使わないシンプル実行
```bat
python app.py
