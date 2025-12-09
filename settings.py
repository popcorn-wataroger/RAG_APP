# settings.py
from dotenv import load_dotenv
import os

# .env ファイルを読み込み
load_dotenv()

# OpenAI APIキーを取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# モデル設定
CHAT_MODEL = "gpt-4o-mini"           # 回答生成（マルチモーダル対応）
EMBED_MODEL = "text-embedding-3-small"  # ベクトル化
TRANSCRIBE_MODEL = "whisper-1"       # 音声→テキスト

# Chroma（ベクトルDB）設定
CHROMA_DIR = "./chroma_db"

# テキスト分割設定
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
TOP_K = 4
