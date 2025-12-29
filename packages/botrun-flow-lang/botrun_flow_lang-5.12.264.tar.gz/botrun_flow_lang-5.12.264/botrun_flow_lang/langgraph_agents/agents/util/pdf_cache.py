"""
PDF 快取模組

提供 PDF 切片的 GCS 快取功能，避免重複切割相同的 PDF 檔案。
快取會自動在 7 天後過期（透過 GCS Lifecycle Rule）。
"""

import hashlib
import json
from io import BytesIO
from typing import List, Tuple, Optional
from datetime import datetime

from botrun_flow_lang.services.storage.storage_factory import storage_store_factory

# 快取目錄前綴
PDF_CACHE_PREFIX = "pdf-cache"

# 快取過期天數（用於 lifecycle rule）
PDF_CACHE_EXPIRY_DAYS = 7


def get_cache_key(pdf_url: str) -> str:
    """
    根據 PDF URL 產生快取 key（hash）

    Args:
        pdf_url: PDF 檔案的 URL

    Returns:
        str: 32 字元的 MD5 hash
    """
    return hashlib.md5(pdf_url.encode()).hexdigest()


def _get_cache_path(cache_key: str) -> str:
    """
    取得快取目錄路徑

    Args:
        cache_key: 快取 key

    Returns:
        str: GCS 路徑，格式為 "pdf-cache/{cache_key}"
    """
    return f"{PDF_CACHE_PREFIX}/{cache_key}"


def _get_metadata_path(cache_key: str) -> str:
    """取得 metadata 檔案路徑"""
    return f"{_get_cache_path(cache_key)}/metadata.json"


def _get_chunk_path(cache_key: str, chunk_index: int) -> str:
    """取得切片檔案路徑"""
    return f"{_get_cache_path(cache_key)}/chunk-{chunk_index:03d}.pdf"


async def check_cache(cache_key: str) -> Optional[List[Tuple[bytes, str]]]:
    """
    檢查 GCS 是否有快取

    Args:
        cache_key: 快取 key（來自 get_cache_key）

    Returns:
        Optional[List[Tuple[bytes, str]]]: 如果有快取，回傳切片清單；否則回傳 None
    """
    try:
        storage = storage_store_factory()
        metadata_path = _get_metadata_path(cache_key)

        # 檢查 metadata 檔案是否存在
        if not await storage.file_exists(metadata_path):
            print(f"[pdf_cache] 快取不存在: {cache_key}")
            return None

        # 讀取 metadata
        metadata_file = await storage.retrieve_file(metadata_path)
        if not metadata_file:
            print(f"[pdf_cache] 無法讀取 metadata: {cache_key}")
            return None

        metadata = json.loads(metadata_file.getvalue().decode("utf-8"))
        chunk_count = metadata.get("chunk_count", 0)
        page_ranges = metadata.get("page_ranges", [])

        if chunk_count == 0:
            print(f"[pdf_cache] 快取無切片: {cache_key}")
            return None

        print(f"[pdf_cache] 找到快取: {cache_key}, {chunk_count} 個切片")

        # 讀取所有切片
        chunks = []
        for i in range(chunk_count):
            chunk_path = _get_chunk_path(cache_key, i)
            chunk_file = await storage.retrieve_file(chunk_path)

            if not chunk_file:
                print(f"[pdf_cache] 無法讀取切片 {i}: {cache_key}")
                return None  # 快取不完整，放棄使用

            chunk_bytes = chunk_file.getvalue()
            page_range = page_ranges[i] if i < len(page_ranges) else f"chunk-{i:03d}"
            chunks.append((chunk_bytes, page_range))

        print(f"[pdf_cache] 成功載入快取: {cache_key}")
        return chunks

    except Exception as e:
        print(f"[pdf_cache] 檢查快取時發生錯誤: {e}")
        return None


async def save_to_cache(
    cache_key: str,
    chunks: List[Tuple[bytes, str]],
    original_url: str,
    original_size_mb: float,
    total_pages: int,
) -> bool:
    """
    將切片存入 GCS 快取

    Args:
        cache_key: 快取 key
        chunks: 切片清單 [(chunk_bytes, page_range), ...]
        original_url: 原始 PDF URL
        original_size_mb: 原始檔案大小（MB）
        total_pages: 總頁數

    Returns:
        bool: 是否成功存入快取
    """
    try:
        storage = storage_store_factory()

        # 1. 存入所有切片
        page_ranges = []
        for i, (chunk_bytes, page_range) in enumerate(chunks):
            chunk_path = _get_chunk_path(cache_key, i)
            chunk_file = BytesIO(chunk_bytes)

            success, _ = await storage.store_file(
                chunk_path, chunk_file, public=False, content_type="application/pdf"
            )

            if not success:
                print(f"[pdf_cache] 無法存入切片 {i}: {cache_key}")
                return False

            page_ranges.append(page_range)

        # 2. 存入 metadata
        metadata = {
            "original_url": original_url,
            "cache_key": cache_key,
            "chunk_count": len(chunks),
            "page_ranges": page_ranges,
            "original_size_mb": original_size_mb,
            "total_pages": total_pages,
            "created_at": datetime.utcnow().isoformat(),
        }

        metadata_path = _get_metadata_path(cache_key)
        metadata_file = BytesIO(json.dumps(metadata, ensure_ascii=False).encode("utf-8"))

        success, _ = await storage.store_file(
            metadata_path, metadata_file, public=False, content_type="application/json"
        )

        if not success:
            print(f"[pdf_cache] 無法存入 metadata: {cache_key}")
            return False

        print(
            f"[pdf_cache] 成功存入快取: {cache_key}, "
            f"{len(chunks)} 個切片, {total_pages} 頁"
        )
        return True

    except Exception as e:
        print(f"[pdf_cache] 存入快取時發生錯誤: {e}")
        return False


async def get_cache_metadata(cache_key: str) -> Optional[dict]:
    """
    取得快取的 metadata（不載入切片內容）

    Args:
        cache_key: 快取 key

    Returns:
        Optional[dict]: metadata 字典，或 None
    """
    try:
        storage = storage_store_factory()
        metadata_path = _get_metadata_path(cache_key)

        if not await storage.file_exists(metadata_path):
            return None

        metadata_file = await storage.retrieve_file(metadata_path)
        if not metadata_file:
            return None

        return json.loads(metadata_file.getvalue().decode("utf-8"))

    except Exception as e:
        print(f"[pdf_cache] 讀取 metadata 時發生錯誤: {e}")
        return None


async def delete_cache(cache_key: str) -> bool:
    """
    刪除快取

    Args:
        cache_key: 快取 key

    Returns:
        bool: 是否成功刪除
    """
    try:
        storage = storage_store_factory()

        # 先讀取 metadata 取得切片數量
        metadata = await get_cache_metadata(cache_key)
        if not metadata:
            return True  # 快取不存在，視為成功

        chunk_count = metadata.get("chunk_count", 0)

        # 刪除所有切片
        for i in range(chunk_count):
            chunk_path = _get_chunk_path(cache_key, i)
            await storage.delete_file(chunk_path)

        # 刪除 metadata
        metadata_path = _get_metadata_path(cache_key)
        await storage.delete_file(metadata_path)

        print(f"[pdf_cache] 已刪除快取: {cache_key}")
        return True

    except Exception as e:
        print(f"[pdf_cache] 刪除快取時發生錯誤: {e}")
        return False
