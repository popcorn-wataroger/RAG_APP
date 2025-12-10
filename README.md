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

# ② 仮想環境を有効化
.\.venv\Scripts\Activate.ps1

# ③ FastAPIアプリを起動
uvicorn app:app --reload --port 8000
