# loaders.py
import pdfplumber
from typing import List, Optional
import re
import logging
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)


def read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text_with_vision(page_image: Image.Image, openai_client) -> str:
    """
    画像からVision APIでテキストを抽出
    
    Args:
        page_image: PIL Image object
        openai_client: OpenAI client instance
    
    Returns:
        抽出されたテキスト
    """
    try:
        # PIL ImageをBase64に変換
        buffer = io.BytesIO()
        page_image.save(buffer, format='PNG')
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # Vision APIで処理
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "この画像に記載されているテキストをすべて抽出してください。日本語と英語の両方を正確に認識してください。テキストのみを返し、説明は不要です。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]
            }
        ]
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Vision API処理エラー: {e}")
        return ""

def read_pdf(path: str, openai_client=None) -> str:
    """
    PDFからテキストを抽出（pdfplumber + Vision API使用）
    
    Args:
        path: PDFファイルのパス
        openai_client: OpenAI client instance（画像ページ処理用）
    
    Returns:
        抽出されたテキスト
    """
    texts = []
    
    try:
        with pdfplumber.open(path) as pdf:
            logger.info(f"PDF総ページ数: {len(pdf.pages)}")
            
            for i, page in enumerate(pdf.pages, 1):
                # テキスト抽出
                text = page.extract_text()
                
                if text and text.strip():
                    texts.append(text)
                    # ページ内容のプレビューを表示（最初の100文字）
                    preview = text[:100].replace('\n', ' ').replace('\r', '')
                    logger.info(f"ページ {i}: {len(text)} 文字抽出 - 内容: {preview}...")
                else:
                    # テキストがない場合はVision APIで処理
                    logger.warning(f"ページ {i}: テキストなし（画像ページの可能性）")
                    
                    if openai_client:
                        try:
                            # pdfplumberでページを画像化
                            page_image = page.to_image(resolution=150)
                            pil_image = page_image.original
                            
                            # Vision APIで処理
                            vision_text = extract_text_with_vision(pil_image, openai_client)
                            
                            if vision_text:
                                texts.append(vision_text)
                                logger.info(f"ページ {i}: Vision APIで {len(vision_text)} 文字抽出 - 内容: {vision_text[:100]}...")
                            else:
                                logger.warning(f"ページ {i}: Vision API抽出失敗")
                        
                        except Exception as e:
                            logger.error(f"ページ {i} の画像処理エラー: {e}")
                    else:
                        logger.warning(f"ページ {i}: OpenAIクライアントが未設定のため、画像ページをスキップ")
            
            result = "\n".join(texts)
            
            if not result.strip():
                logger.error("PDFからテキストを抽出できませんでした")
                return ""
            
            logger.info(f"PDF抽出完了: 合計 {len(result)} 文字")
            return result
            
    except Exception as e:
        logger.error(f"PDF読み込みエラー: {e}", exc_info=True)
        return ""

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
