# RAG_APP
# 🧠 NotebookLM-like RAG Bot

このアプリは **FastAPI** と **OpenAI API** を利用して構築された、  
NotebookLM風の **RAG（Retrieval-Augmented Generation）チャットボット** です。  

---

## 🚀 起動方法（Windows PowerShellの場合）

以下の手順でアプリを起動できます。

```bash
# 1️⃣ 作業フォルダに移動
cd C:\Users\User\Desktop\ragbot

# 2️⃣ 仮想環境を有効化
.\.venv\Scripts\Activate.ps1

# 3️⃣ FastAPIアプリを起動
uvicorn app:app --reload --port 8000
