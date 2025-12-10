# loaders.py
from pypdf import PdfReader
from typing import List
import re

def read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def read_pdf(path: str) -> str:
    reader = PdfReader(path)
    texts = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        texts.append(txt)
    return "\n".join(texts)

def clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def chunk_text(s: str, size: int, overlap: int) -> List[str]:
    s = clean_text(s)
    chunks = []
    start = 0
    n = len(s)
    while start < n:
        end = min(start + size, n)
        chunks.append(s[start:end])
        # 次のチャンクの開始位置を計算
        # overlapを考慮して戻るが、必ず前進する
        next_start = end - overlap
        if next_start <= start:
            # 無限ループ防止：最低でも1文字は前進
            next_start = start + 1
        start = next_start
        if start >= n:
            break
    return chunks
