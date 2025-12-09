# rag.py
import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict
from settings import CHROMA_DIR, EMBED_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, OPENAI_API_KEY
from loaders import read_pdf, read_txt, chunk_text

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name=EMBED_MODEL
)

def get_client():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)

def get_collection(name: str = "docs"):
    client = get_client()
    return client.get_or_create_collection(name=name, embedding_function=openai_ef)

def ingest_files(file_paths: List[str]) -> Dict:
    col = get_collection()
    added = 0
    meta_list = []
    docs = []
    ids = []
    for path in file_paths:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".txt":
            raw = read_txt(path)
        elif ext == ".pdf":
            raw = read_pdf(path)
        else:
            continue
        chunks = chunk_text(raw, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, ch in enumerate(chunks):
            ids.append(f"{path}__{i}")
            docs.append(ch)
            meta_list.append({"source": path, "chunk": i})
            added += 1
    if docs:
        col.add(documents=docs, metadatas=meta_list, ids=ids)
    return {"added_chunks": added}

def retrieve(query: str, top_k: int = TOP_K) -> List[Dict]:
    col = get_collection()
    res = col.query(query_texts=[query], n_results=top_k)
    out = []
    for i in range(len(res["documents"][0])):
        out.append({
            "text": res["documents"][0][i],
            "metadata": res["metadatas"][0][i]
        })
    return out

def build_context_snippets(retrieved: List[Dict]) -> str:
    lines = []
    for i, r in enumerate(retrieved, 1):
        src = r["metadata"].get("source", "unknown")
        lines.append(f"[{i}] source: {src}\n{r['text']}\n")
    return "\n---\n".join(lines)

def build_rag_prompt(query: str, context_snippets: str) -> str:
    return (
        "あなたは丁寧で正確なアシスタントです。以下のコンテキストに基づいて、"
        "質問に日本語で分かりやすく答えてください。わからない時は正直にわからないと述べ、"
        "無理に作りません。\n\n"
        f"【コンテキスト】\n{context_snippets}\n\n"
        f"【質問】\n{query}\n\n"
        "【出力フォーマット】\n"
        "質問を短く言い換えた後、根拠を要約し、最後に結論を述べてください。"
    )
