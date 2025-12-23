# services/rag_service.py
import logging
from typing import Callable, Dict

from rag import retrieve, build_context_snippets, build_rag_prompt

logger = logging.getLogger(__name__)

def answer_with_rag(query: str, openai_chat_fn: Callable[[list], str]) -> Dict[str, str]:
    retrieved = retrieve(query)
    context = build_context_snippets(retrieved) if retrieved else "（該当コンテキストなし）"
    prompt = build_rag_prompt(query, context)

    logger.info(f"プロンプト長: {len(prompt)} 文字、コンテキスト長: {len(context)} 文字")

    # temperature=0、max_tokens=1024で厳密な出力を得る
    answer = openai_chat_fn(
        [
            {"role": "system", "content": "You are a helpful and accurate assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1024
    )
    return {"query": query, "answer": answer}
