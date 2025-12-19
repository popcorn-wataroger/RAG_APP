# app.py
import base64, io, tempfile, os
import logging
from typing import Optional, List, Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from openai import OpenAI

from settings import OPENAI_API_KEY, CHAT_MODEL, TRANSCRIBE_MODEL
from rag import ingest_files, retrieve, build_context_snippets, build_rag_prompt
from loaders import read_pdf

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NotebookLM-like RAG Bot")

# CORS設定（Swagger UIからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では具体的なURLを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)

class AskIn(BaseModel):
    query: str

class AskOut(BaseModel):
    query: str
    answer: str

def openai_chat(messages, max_tokens: int = 1024) -> str:
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content

def transcribe_audio_bytes(audio_bytes: bytes, filename: str) -> str:
    bio = io.BytesIO(audio_bytes); bio.name = filename
    transcript = client.audio.transcriptions.create(
        model=TRANSCRIBE_MODEL,
        file=bio
    )
    return transcript.text

def vision_describe_image(image_bytes: bytes) -> str:
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
    resp = client.chat.completions.create(model=CHAT_MODEL, messages=messages, temperature=0)
    return resp.choices[0].message.content.strip()

@app.post("/chat", response_model=AskOut)
def chat_endpoint(body: AskIn):
    query = body.query
    retrieved = retrieve(query)
    context = build_context_snippets(retrieved) if retrieved else "（該当コンテキストなし）"
    prompt = build_rag_prompt(query, context)
    answer = openai_chat([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ])
    return AskOut(query=query, answer=answer)

@app.post("/RAG_chat", response_model=AskOut)
async def RAG_chat_endpoint(
    query: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
):
    """
    メディアファイル（PDF/画像/音声/テキスト）を含む質問に回答
    """
    logger.info(f"リクエスト受信: query='{query[:50]}...', files={len(files) if files else 0}件")
    
    extra_parts = []

    try:
        if files:
            for f in files:
                name = (f.filename or "unknown")
                ext = name.lower()
                
                logger.info(f"ファイル処理開始: {name}")
                
                try:
                    data = await f.read()
                    file_size_mb = len(data) / (1024 * 1024)
                    logger.info(f"ファイル読み込み: {name} ({file_size_mb:.2f} MB)")
                    
                    # ファイルサイズチェック（20MB制限）
                    if file_size_mb > 20:
                        logger.warning(f"ファイルサイズ超過: {name} ({file_size_mb:.2f} MB)")
                        extra_parts.append(f"[{name}] ファイルサイズが大きすぎます（20MB以下にしてください。\n")
                        continue

                    if ext.endswith((".wav", ".mp3", ".m4a", ".ogg")):
                        try:
                            text = transcribe_audio_bytes(data, name)
                            extra_parts.append(f"[音声:{name}]\n{text}\n")
                            logger.info(f"音声文字起こし成功: {name}")
                        except Exception as e:
                            logger.error(f"音声処理エラー {name}: {e}")
                            extra_parts.append(f"[音声:{name}] 文字起こし失敗: {e}\n")

                    elif ext.endswith((".png", ".jpg", ".jpeg")):
                        try:
                            Image.open(io.BytesIO(data))  # 形式検証
                            desc = vision_describe_image(data)
                            extra_parts.append(f"[画像:{name}]\n{desc}\n")
                            logger.info(f"画像説明生成成功: {name}")
                        except Exception as e:
                            logger.error(f"画像処理エラー {name}: {e}")
                            extra_parts.append(f"[画像:{name}] 説明生成失敗: {e}\n")

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
                                    f"原因の可能性：\n"
                                    f"- 完全に空のPDF\n"
                                    f"- 暗号化されたPDF\n"
                                )
                            else:
                                # 全文を使用（制限なし）
                                full_txt = txt
                                
                                # Vision API処理済みページがあるか確認
                                vision_processed = "Vision APIで" in txt
                                if vision_processed:
                                    note = "\n✅ 画像ページはVision APIで自動的にテキスト化されました。\n\n"
                                    extra_parts.append(f"[PDF:{name}]{note}{full_txt}\n")
                                else:
                                    extra_parts.append(f"[PDF:{name}]\n{full_txt}\n")
                                
                                logger.info(f"✅ PDF読み込み成功: {name} (全体: {len(txt)} 文字)")
                                
                                # 先頭・中盤・末尾をプレビュー（デバッグ用）
                                preview_start = txt[:200].replace('\n', ' ')
                                preview_mid = txt[len(txt)//2:len(txt)//2+200].replace('\n', ' ') if len(txt) > 400 else ""
                                preview_end = txt[-200:].replace('\n', ' ') if len(txt) > 200 else ""
                                logger.info(f"PDF先頭200文字: {preview_start}...")
                                if preview_mid:
                                    logger.info(f"PDF中盤200文字: ...{preview_mid}...")
                                if preview_end:
                                    logger.info(f"PDF末尾200文字: ...{preview_end}")
                        except Exception as e:
                            logger.error(f"PDF処理エラー {name}: {e}", exc_info=True)
                            extra_parts.append(f"[PDF:{name}] ❌ 読み込み失敗: {str(e)}\n")
                        finally:
                            if tmp_path and os.path.exists(tmp_path):
                                os.remove(tmp_path)
                                logger.info(f"一時ファイル削除: {tmp_path}")

                    elif ext.endswith(".txt"):
                        try:
                            txt_content = data.decode('utf-8', errors='ignore')[:8000]
                            extra_parts.append(f"[TXT:{name}]\n{txt_content}\n")
                            logger.info(f"テキスト読み込み成功: {name}")
                        except Exception as e:
                            logger.error(f"テキスト処理エラー {name}: {e}")
                            extra_parts.append(f"[TXT:{name}] 読み込み失敗: {e}\n")

                    else:
                        logger.warning(f"未対応の拡張子: {name}")
                        extra_parts.append(f"[未対応:{name}] この拡張子は簡易処理対象外です。\n")
                
                except Exception as e:
                    logger.error(f"ファイル読み込みエラー {name}: {e}")
                    extra_parts.append(f"[{name}] ファイル処理中にエラーが発生しました: {str(e)}\n")

        # RAG検索（アップロードファイルがない場合のみ）
        if extra_parts:
            # アップロードファイルがある場合はRAG検索をスキップ
            logger.info("アップロードファイルあり: RAG検索をスキップ")
            rag_context = ""
        else:
            logger.info(f"RAG検索開始: '{query[:50]}...'")
            retrieved = retrieve(query)
            rag_context = build_context_snippets(retrieved) if retrieved else ""
        
        extra_context = "\n".join(extra_parts) if extra_parts else ""
        
        # デバッグログ
        logger.info(f"RAGコンテキスト長: {len(rag_context)} 文字")
        logger.info(f"メディアコンテキスト長: {len(extra_context)} 文字")
        logger.info(f"メディアファイル数: {len(extra_parts)}")
        
        # メディアコンテキストの先頭を確認
        if extra_context:
            context_preview = extra_context[:300].replace('\n', ' ')
            logger.info(f"メディアコンテキスト先頭: {repr(context_preview)}")

        # コンテキストの優先順位を調整
        if extra_context:
            # アップロードファイルがある場合（RAGは使用しない）
            vision_note = ""
            if "Vision APIで" in extra_context:
                vision_note = "✅ 画像ページはVision APIで自動的にテキスト化されました。\n\n"
            
            final_prompt = (
                "以下のファイル内容に基づいて、質問に対して日本語で簡潔に回答してください。\n"
                "回答は結論のみを述べ、余計な前置きや説明は不要です。\n\n"
                f"{vision_note}"
                f"【ファイル内容】\n{extra_context}\n\n"
                f"【質問】\n{query}\n\n"
                "【回答】"
            )
        elif rag_context and not extra_context:
            # RAGのみ
            final_prompt = (
                "以下のコンテキストに基づいて、質問に対して日本語で簡潔に回答してください。\n"
                "回答は結論のみを述べ、余計な前置きや説明は不要です。\n\n"
                f"【コンテキスト】\n{rag_context}\n\n"
                f"【質問】\n{query}\n\n"
                "【回答】"
            )
        else:
            # 何もない場合
            final_prompt = (
                "以下の質問に対して、一般的な知識に基づいて日本語で簡潔に回答してください。\n"
                "回答は結論のみを述べ、余計な前置きや説明は不要です。\n\n"
                f"【質問】\n{query}\n\n"
                f"注：参照できる資料がないため、一般的な回答になります。\n\n"
                "【回答】"
            )

        logger.info(f"プロンプト長: {len(final_prompt)} 文字")
        logger.info("回答生成開始")
        answer = openai_chat([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": final_prompt}
        ])
        
        logger.info(f"回答生成完了: {len(answer)} 文字")
        return AskOut(query=query, answer=answer)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期せぬエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"処理中にエラーが発生しました: {str(e)}"
        )
