# app.py
import base64, io, tempfile, os
from typing import Optional, List, Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
from openai import OpenAI

from settings import OPENAI_API_KEY, CHAT_MODEL, TRANSCRIBE_MODEL
from rag import ingest_files, retrieve, build_context_snippets, build_rag_prompt
from loaders import read_pdf

app = FastAPI(title="NotebookLM-like RAG Bot")
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

@app.post("/ingest")
def ingest_endpoint(paths: List[str]):
    try:
        result = ingest_files(paths)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ask", response_model=AskOut)
def ask_endpoint(body: AskIn):
    query = body.query
    retrieved = retrieve(query)
    context = build_context_snippets(retrieved) if retrieved else "（該当コンテキストなし）"
    prompt = build_rag_prompt(query, context)
    answer = openai_chat([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ])
    return AskOut(query=query, answer=answer)

@app.post("/ask-with-media", response_model=AskOut)
async def ask_with_media_endpoint(
    query: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
):
    extra_parts = []

    if files:
        for f in files:
            name = (f.filename or "")
            ext = name.lower()
            data = await f.read()

            if ext.endswith((".wav", ".mp3", ".m4a", ".ogg")):
                try:
                    text = transcribe_audio_bytes(data, name)
                    extra_parts.append(f"[音声:{name}]\n{text}\n")
                except Exception as e:
                    extra_parts.append(f"[音声:{name}] 文字起こし失敗: {e}\n")

            elif ext.endswith((".png", ".jpg", ".jpeg")):
                try:
                    Image.open(io.BytesIO(data))  # 形式検証
                    desc = vision_describe_image(data)
                    extra_parts.append(f"[画像:{name}]\n{desc}\n")
                except Exception as e:
                    extra_parts.append(f"[画像:{name}] 説明生成失敗: {e}\n")

            elif ext.endswith(".pdf"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                try:
                    txt = read_pdf(tmp_path)
                    extra_parts.append(f"[PDF:{name}]\n{txt[:8000]}\n")
                finally:
                    os.remove(tmp_path)

            elif ext.endswith(".txt"):
                extra_parts.append(f"[TXT:{name}]\n{data.decode('utf-8', errors='ignore')[:8000]}\n")

            else:
                extra_parts.append(f"[未対応:{name}] この拡張子は簡易処理対象外です。\n")

    retrieved = retrieve(query)
    rag_context = build_context_snippets(retrieved) if retrieved else ""
    extra_context = "\n".join(extra_parts) if extra_parts else "（追加メディアなし）"

    final_prompt = (
        "以下の情報を活用して日本語で正確に回答してください。\n\n"
        f"【RAGコンテキスト】\n{rag_context}\n\n"
        f"【メディア由来コンテキスト】\n{extra_context}\n\n"
        f"【質問】\n{query}\n\n"
        "不明点は推測しすぎず、根拠も示してください。"
    )

    answer = openai_chat([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": final_prompt}
    ])
    return AskOut(query=query, answer=answer)
