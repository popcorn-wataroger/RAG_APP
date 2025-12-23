# services/document_service.py
import os
import json
import hashlib
import logging
import shutil
from typing import List, Dict, Any
from fastapi import UploadFile

from rag import ingest_files  # 既存 ingest を再利用
from openai import OpenAI
from settings import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join("data", "uploads")
DATA_DIR = "data"  # rag.py が data/ 前提でも動くようにここにも配置する
REGISTRY_PATH = os.path.join(UPLOAD_DIR, "_ingested_registry.json")


# ------------------------------------------------------------
# 1) 初期化
# ------------------------------------------------------------
def _ensure_dirs() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def _load_registry() -> Dict[str, Dict[str, Any]]:
    _ensure_dirs()
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(reg: Dict[str, Dict[str, Any]]) -> None:
    _ensure_dirs()
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------
# 2) ユーティリティ
# ------------------------------------------------------------
def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _safe_filename(name: str) -> str:
    name = name.replace("\\", "_").replace("/", "_").strip()
    return name or "unknown"


# ------------------------------------------------------------
# 3) 一覧
# ------------------------------------------------------------
def list_ingested_documents() -> List[Dict[str, Any]]:
    reg = _load_registry()
    docs = []
    for sha, v in reg.items():
        docs.append({
            "sha": sha,
            "filename": v.get("filename", "unknown"),
            "path_uploads": v.get("path_uploads", ""),
            "path_data": v.get("path_data", ""),
            "ingested": bool(v.get("ingested", False)),
            "error": v.get("error", None),
        })
    docs.sort(key=lambda x: x["filename"])
    return docs


# ------------------------------------------------------------
# 3.5) 削除
# ------------------------------------------------------------
def delete_document(sha: str) -> Dict[str, Any]:
    """
    指定されたSHAのドキュメントを削除
    
    Args:
        sha: 削除するドキュメントのSHA256ハッシュ
    
    Returns:
        削除結果
    """
    registry = _load_registry()
    
    if sha not in registry:
        return {"success": False, "message": "ドキュメントが見つかりません"}
    
    doc_info = registry[sha]
    filename = doc_info.get("filename", "unknown")
    
    # ファイル削除
    deleted_files = []
    for path_key in ["path_uploads", "path_data"]:
        path = doc_info.get(path_key, "")
        if path and os.path.exists(path):
            try:
                os.remove(path)
                deleted_files.append(path)
                logger.info(f"ファイル削除: {path}")
            except Exception as e:
                logger.error(f"ファイル削除失敗: {path} - {e}")
    
    # レジストリから削除
    del registry[sha]
    _save_registry(registry)
    
    logger.info(f"ドキュメント削除完了: {filename} (SHA: {sha})")
    
    return {
        "success": True,
        "message": f"{filename} を削除しました",
        "deleted_files": deleted_files
    }


# ------------------------------------------------------------
# 4) 保存→取り込み（失敗したら ingested=True にしない）
# ------------------------------------------------------------
async def save_and_ingest_once(files: List[UploadFile], max_mb: int = 20) -> Dict[str, Any]:
    """
    - data/uploads に保存（sha.ext）
    - data/ にもコピー（original filename） ※rag.py が data/ 前提でも動くように
    - 新規分だけ ingest_files() を実行
    """
    _ensure_dirs()
    registry = _load_registry()

    # ingest 対象として rag.py に渡すパス一覧
    ingest_paths: List[str] = []

    newly_ingested: List[str] = []
    already_ingested: List[str] = []
    skipped_too_large: List[str] = []
    failed: List[str] = []

    # まず保存
    pending_shas: List[str] = []

    for f in files:
        filename = _safe_filename(f.filename or "unknown")
        data = await f.read()

        size_mb = len(data) / (1024 * 1024)
        if size_mb > max_mb:
            logger.warning(f"File too large: {filename} ({size_mb:.2f}MB)")
            skipped_too_large.append(filename)
            continue

        sha = _sha256_bytes(data)

        # 既に ingest 済みならスキップ
        if sha in registry and registry[sha].get("ingested") is True:
            already_ingested.append(filename)
            continue

        ext = os.path.splitext(filename)[1].lower()

        # uploads 側（衝突回避）
        upload_name = f"{sha}{ext}"
        path_uploads = os.path.join(UPLOAD_DIR, upload_name)

        # data 側（rag.py が data/ 前提でも動く）
        path_data = os.path.join(DATA_DIR, filename)

        try:
            if not os.path.exists(path_uploads):
                with open(path_uploads, "wb") as out:
                    out.write(data)

            # data/ にコピー（上書きOK）
            shutil.copyfile(path_uploads, path_data)

            registry[sha] = {
                "filename": filename,
                "path_uploads": path_uploads,
                "path_data": path_data,
                "ingested": False,
                "error": None,
            }
            pending_shas.append(sha)

            # ★ まずは data/ 側のパスを ingest に使う（既存実装互換が最強）
            ingest_paths.append(path_data)

        except Exception as e:
            logger.error(f"save failed: {filename}: {e}", exc_info=True)
            failed.append(filename)
            registry[sha] = {
                "filename": filename,
                "path_uploads": path_uploads,
                "path_data": path_data,
                "ingested": False,
                "error": str(e),
            }

    _save_registry(registry)

    # ingest 実行（新規分だけ）
    if ingest_paths:
        try:
            logger.info(f"ingest_files() start: {len(ingest_paths)} files")
            ingest_files(ingest_paths, openai_client=client)
            logger.info("ingest_files() done")

            # 成功したものだけ ingested=True
            for sha in pending_shas:
                if sha in registry:
                    registry[sha]["ingested"] = True
                    registry[sha]["error"] = None
                    newly_ingested.append(registry[sha]["filename"])

            _save_registry(registry)

        except Exception as e:
            # ingest 全体が失敗した場合は ingested=True にしない
            logger.error(f"ingest_files failed: {e}", exc_info=True)
            for sha in pending_shas:
                if sha in registry:
                    registry[sha]["ingested"] = False
                    registry[sha]["error"] = f"ingest_files failed: {e}"
            _save_registry(registry)

            # 失敗として返す
            failed.extend([registry[sha]["filename"] for sha in pending_shas if sha in registry])

    return {
        "newly_ingested": newly_ingested,
        "already_ingested": already_ingested,
        "skipped_too_large": skipped_too_large,
        "failed": failed,
        "total_registry": len(registry),
    }
