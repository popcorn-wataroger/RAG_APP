# rag.py
import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from settings import (
    CHROMA_DIR,
    EMBED_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
    OPENAI_API_KEY,
)

from loaders import read_pdf, read_txt, chunk_text

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Document クラス（LangChain 互換）
# ------------------------------------------------------------
@dataclass
class Document:
    """検索結果を格納するドキュメントクラス"""
    page_content: str
    metadata: Dict[str, any]
    
    def __str__(self) -> str:
        source = self.metadata.get('source', 'unknown')
        chunk_id = self.metadata.get('chunk', '?')
        preview = self.page_content[:100].replace('\n', ' ')
        return f"Document(source={source}, chunk={chunk_id}, preview={preview}...)"


# ------------------------------------------------------------
# Embedding 設定
# ------------------------------------------------------------
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name=EMBED_MODEL
)


# ------------------------------------------------------------
# ChromaDB クライアント
# ------------------------------------------------------------
def get_client():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection(name: str = "docs"):
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        embedding_function=openai_ef
    )


# ------------------------------------------------------------
# ingest（★ 修正版：.md / .txt / .pdf を確実に読む）
# ------------------------------------------------------------
def ingest_files(file_paths: List[str]) -> Dict:
    """
    複数ファイルを読み込み、ChromaDB に登録する
    
    Args:
        file_paths: 読み込むファイルパスのリスト
    
    Returns:
        {'added_chunks': int, 'failed_files': List[str], 'total_files': int}
    """
    col = get_collection()

    docs: List[str] = []
    metadatas: List[Dict] = []
    ids: List[str] = []
    added = 0
    failed_files: List[str] = []

    for path in file_paths:
        try:
            if not os.path.exists(path):
                logger.warning(f"ファイルが存在しません: {path}")
                failed_files.append(path)
                continue
            
            ext = os.path.splitext(path)[1].lower()

            # --- ファイル読み込み ---
            if ext in (".txt", ".md"):
                raw = read_txt(path)
            elif ext == ".pdf":
                raw = read_pdf(path)
            else:
                logger.info(f"サポート対象外の拡張子: {path}")
                continue

            if not raw or not raw.strip():
                logger.warning(f"空のファイル: {path}")
                continue

            # --- チャンク分割 ---
            chunks = [
                ch for ch in chunk_text(raw, CHUNK_SIZE, CHUNK_OVERLAP)
                if ch.strip()
            ]

            for i, ch in enumerate(chunks):
                ids.append(f"{path}__{i}")
                docs.append(ch)
                metadatas.append({
                    "source": path,
                    "chunk": i
                })
                added += 1
            
            logger.info(f"✓ {path}: {len(chunks)} chunks")
        
        except Exception as e:
            logger.error(f"ファイル読み込みエラー {path}: {e}")
            failed_files.append(path)

    if docs:
        try:
            col.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"ChromaDB に {added} チャンクを追加")
        except Exception as e:
            logger.error(f"ChromaDB 追加エラー: {e}")
            return {"added_chunks": 0, "failed_files": file_paths, "total_files": len(file_paths)}

    return {
        "added_chunks": added,
        "failed_files": failed_files,
        "total_files": len(file_paths)
    }


# ------------------------------------------------------------
# 検索
# ------------------------------------------------------------
def retrieve(query: str, top_k: int = TOP_K) -> List[Document]:
    """
    クエリに基づいてドキュメントを検索
    
    Args:
        query: 検索クエリ
        top_k: 返す結果の最大数
    
    Returns:
        Document オブジェクトのリスト
    """
    col = get_collection()
    
    try:
        res = col.query(
            query_texts=[query],
            n_results=top_k
        )

        results = []
        for i in range(len(res["documents"][0])):
            results.append(Document(
                page_content=res["documents"][0][i],
                metadata=res["metadatas"][0][i]
            ))

        logger.info(f"検索結果: {len(results)} 件")
        return results
    
    except Exception as e:
        logger.error(f"検索エラー: {e}")
        return []


# ------------------------------------------------------------
# RAG 用コンテキスト生成
# ------------------------------------------------------------
def build_context_snippets(retrieved: List[Document]) -> str:
    """
    検索結果からコンテキスト文字列を生成
    
    Args:
        retrieved: Document オブジェクトのリスト
    
    Returns:
        整形されたコンテキスト文字列
    """
    lines = []
    for i, doc in enumerate(retrieved, 1):
        src = doc.metadata.get("source", "unknown")
        chunk_id = doc.metadata.get("chunk", "?")
        lines.append(
            f"[{i}] source: {src} (chunk {chunk_id})\n{doc.page_content}\n"
        )
    return "\n---\n".join(lines)


# ------------------------------------------------------------
# プロンプト生成
# ------------------------------------------------------------
def build_rag_prompt(query: str, context_snippets: str) -> str:
    return (
        "あなたは丁寧で正確なアシスタントです。\n"
        "以下のコンテキストに基づいて、日本語で簡潔に答えてください。\n\n"
        f"【コンテキスト】\n{context_snippets}\n\n"
        f"【質問】\n{query}\n\n"
        "【出力フォーマット】\n"
        "質問を短く言い換えた後、根拠を要約し、最後に結論を述べてください。"
    )
