# app.py
import base64
import io
import os
import json
import time
import logging
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image
from openai import OpenAI

from settings import OPENAI_API_KEY, CHAT_MODEL, TRANSCRIBE_MODEL
from services.document_service import save_and_ingest_once, list_ingested_documents
from services.rag_service import answer_with_rag

# ------------------------------------------------------------
# 0) ロギング設定
# ------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# 1) アプリ初期化
# ------------------------------------------------------------
app = FastAPI(title="NotebookLM-like RAG Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番ではUIドメインを指定推奨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------------------------------------
# 2) 型定義
# ------------------------------------------------------------
class AskIn(BaseModel):
    query: str

class AskOut(BaseModel):
    query: str
    answer: str

# ------------------------------------------------------------
# 3) 計測用タイマー
# ------------------------------------------------------------
class Timer:
    def __init__(self, name: str):
        self.name = name
        self.t0 = None

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        dt = time.perf_counter() - (self.t0 or time.perf_counter())
        logger.info(f"[TIMER] {self.name}: {dt:.3f}s")

# ------------------------------------------------------------
# 4) OpenAIユーティリティ
# ------------------------------------------------------------
def openai_chat(messages, max_tokens: int = 512, temperature: float = 0.2) -> str:
    with Timer("openai_chat"):
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return resp.choices[0].message.content

def transcribe_audio_bytes(audio_bytes: bytes, filename: str) -> str:
    with Timer(f"transcribe_audio ({filename})"):
        bio = io.BytesIO(audio_bytes)
        bio.name = filename
        transcript = client.audio.transcriptions.create(
            model=TRANSCRIBE_MODEL,
            file=bio
        )
    return transcript.text

def vision_describe_image(image_bytes: bytes) -> str:
    with Timer("vision_describe_image"):
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "この画像の内容を日本語で要約してください。事実ベースで簡潔に。"},
                    {"type": "input_image", "image_data": b64, "mime_type": "image/png"}
                ]
            }
        ]
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=256,
        )
    return resp.choices[0].message.content.strip()

# ------------------------------------------------------------
# 5) ドキュメント管理 API（NotebookLMっぽさの要）
# ------------------------------------------------------------
@app.get("/documents")
def api_list_documents():
    """
    取り込み済み資料一覧（UIがこれを表示して「状態の可視化」を作る）
    """
    return {"documents": list_ingested_documents()}

@app.delete("/documents/{sha}")
def api_delete_document(sha: str):
    """
    指定されたドキュメントを削除
    """
    from services.document_service import delete_document
    result = delete_document(sha)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.post("/documents")
async def api_upload_documents(files: list[UploadFile] = File(...)):
    """
    資料アップロード（重い処理はここで1回だけ）
    """
    if not files:
        raise HTTPException(status_code=400, detail="files is required")

    with Timer("save_and_ingest_once"):
        result = await save_and_ingest_once(files)

    return result

# ------------------------------------------------------------
# 6) /chat（JSON：queryだけで高速応答）
# ------------------------------------------------------------
@app.post("/chat", response_model=AskOut)
def chat_endpoint(body: AskIn):
    query = body.query
    # temperature=0で厳密な出力を得る
    def strict_openai_chat(messages, max_tokens=512):
        return openai_chat(messages, max_tokens=max_tokens, temperature=0)
    
    out = answer_with_rag(query=query, openai_chat_fn=strict_openai_chat)
    return AskOut(**out)

# ------------------------------------------------------------
# 7) /RAG_chat（FormData：query + files）
#    Vision API対応：PDFの画像ページも自動抽出
# ------------------------------------------------------------
@app.post("/RAG_chat", response_model=AskOut)
async def RAG_chat_endpoint(
    query: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
):
    """
    メディアファイル（PDF/画像/音声/テキスト）を含む質問に回答
    """
    from loaders import read_pdf, read_txt
    import tempfile
    
    logger.info(f"リクエスト受信: query='{query[:50]}...', files={len(files) if files else 0}件")
    
    extra_parts = []

    try:
        if files:
            for f in files:
                name = (f.filename or "unknown")
                ext = name.lower()
                
                logger.info(f"ファイル処理開始: {name}")
                data = await f.read()
                logger.info(f"ファイル読み込み: {name} ({len(data) / 1024 / 1024:.2f} MB)")

                # 音声ファイル
                if ext.endswith((".wav", ".mp3", ".m4a", ".ogg")):
                    try:
                        text = transcribe_audio_bytes(data, name)
                        extra_parts.append(f"[音声:{name}]\n{text}\n")
                        logger.info(f"✅ 音声処理成功: {name}")
                    except Exception as e:
                        logger.error(f"❌ 音声処理失敗: {name} - {e}")
                        extra_parts.append(f"[音声:{name}] 文字起こし失敗: {e}\n")

                # 画像ファイル
                elif ext.endswith((".png", ".jpg", ".jpeg")):
                    try:
                        Image.open(io.BytesIO(data))
                        desc = vision_describe_image(data)
                        extra_parts.append(f"[画像:{name}]\n{desc}\n")
                        logger.info(f"✅ 画像処理成功: {name}")
                    except Exception as e:
                        logger.error(f"❌ 画像処理失敗: {name} - {e}")
                        extra_parts.append(f"[画像:{name}] 説明生成失敗: {e}\n")

                # PDFファイル（Vision API対応）
                elif ext.endswith(".pdf"):
                    tmp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(data)
                            tmp_path = tmp.name
                        
                        logger.info(f"PDF読み込み開始: {name} (一時ファイル: {tmp_path})")
                        # OpenAIクライアントを渡して画像ページもVision APIで処理
                        txt = read_pdf(tmp_path, openai_client=client)
                        
                        if not txt or not txt.strip():
                            logger.warning(f"PDF内容が空: {name}")
                            extra_parts.append(
                                f"[PDF:{name}] ⚠️ このPDFからテキストを抽出できませんでした。\n"
                            )
                        else:
                            extra_parts.append(f"[PDF:{name}]\n{txt}\n")
                            logger.info(f"✅ PDF読み込み成功: {name} (全体: {len(txt)} 文字)")
                    except Exception as e:
                        logger.error(f"❌ PDF処理失敗: {name} - {e}", exc_info=True)
                        extra_parts.append(f"[PDF:{name}] 読み込み失敗: {e}\n")
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                            logger.info(f"一時ファイル削除: {tmp_path}")

                # テキストファイル
                elif ext.endswith(".txt"):
                    try:
                        txt = data.decode("utf-8", errors="ignore")
                        extra_parts.append(f"[テキスト:{name}]\n{txt}\n")
                        logger.info(f"✅ テキスト処理成功: {name}")
                    except Exception as e:
                        logger.error(f"❌ テキスト処理失敗: {name} - {e}")
                        extra_parts.append(f"[テキスト:{name}] 読み込み失敗: {e}\n")

                else:
                    extra_parts.append(f"[未対応:{name}] この拡張子は対応していません。\n")

        # ファイルコンテキストの作成
        extra_context = "".join(extra_parts) if extra_parts else ""
        
        logger.info(f"メディアコンテキスト長: {len(extra_context)} 文字")
        logger.info(f"メディアファイル数: {len(extra_parts)}")
        
        if extra_context:
            logger.info(f"メディアコンテキスト先頭: {extra_context[:200]}")
        
        # ファイルがある場合はRAG検索をスキップ
        if extra_parts:
            logger.info("アップロードファイルあり: RAG検索をスキップ")
            rag_context = ""
        else:
            logger.info("ファイルなし: RAG検索を実行")
            from services.rag_service import answer_with_rag
            out = answer_with_rag(query=query, openai_chat_fn=openai_chat)
            return AskOut(**out)

        # プロンプト構築
        logger.info(f"プロンプト長: {len(extra_context) + len(query)} 文字")
        
        final_prompt = (
            "以下のファイル内容に基づいて、質問に対して日本語で簡潔に回答してください。\n"
            "回答は結論のみを述べ、余計な前置きや説明は不要です。\n\n"
            f"【ファイル内容】\n{extra_context}\n\n"
            f"【質問】\n{query}\n\n"
            "【回答】"
        )
        
        logger.info("回答生成開始")
        answer = openai_chat(
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": final_prompt}
            ],
            max_tokens=512
        )
        logger.info(f"回答生成完了: {len(answer)} 文字")

        return AskOut(query=query, answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期せぬエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"処理中にエラーが発生しました: {str(e)}")

# ------------------------------------------------------------
# 8) UI静的ファイル配信
# ------------------------------------------------------------
@app.get("/")
def root():
    """ルートパスでUIを表示"""
    return FileResponse("ui/index.html")

# 静的ファイル（CSS、JSなど）を配信
if os.path.exists("ui"):
    app.mount("/ui", StaticFiles(directory="ui"), name="ui")
