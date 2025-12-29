"""
PDF 處理工具模組

提供 PDF 切割等功能，用於處理大型 PDF 檔案。
使用 pypdf（純 Python）實作，避免 C++ 庫的 segfault 問題。
"""

import io
from typing import List, Tuple

from pypdf import PdfReader, PdfWriter


def get_pdf_size(pdf_content: bytes) -> int:
    """
    取得 PDF 檔案大小（bytes）

    Args:
        pdf_content: PDF 檔案的二進位內容

    Returns:
        int: 檔案大小（bytes）
    """
    return len(pdf_content)


def get_pdf_size_mb(pdf_content: bytes) -> float:
    """
    取得 PDF 檔案大小（MB）

    Args:
        pdf_content: PDF 檔案的二進位內容

    Returns:
        float: 檔案大小（MB）
    """
    return len(pdf_content) / (1024 * 1024)


def get_pdf_page_count(pdf_content: bytes) -> int:
    """
    取得 PDF 總頁數

    Args:
        pdf_content: PDF 檔案的二進位內容

    Returns:
        int: 總頁數
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_content))
        return len(reader.pages)
    except Exception as e:
        print(f"[get_pdf_page_count] 無法讀取 PDF 頁數: {e}")
        return 0


def split_pdf_by_pages(
    pdf_content: bytes, pages_per_chunk: int = 15
) -> List[Tuple[bytes, str]]:
    """
    按頁數切割 PDF

    Args:
        pdf_content: PDF 檔案的二進位內容
        pages_per_chunk: 每個切片的頁數（預設 15 頁）

    Returns:
        List[Tuple[bytes, str]]: 切片清單，每個元素為 (切片內容, 頁碼範圍字串)
        例如: [(chunk_bytes, "page-001-015"), (chunk_bytes, "page-016-030"), ...]
    """
    chunks = []

    try:
        reader = PdfReader(io.BytesIO(pdf_content))
        total_pages = len(reader.pages)

        for start_idx in range(0, total_pages, pages_per_chunk):
            end_idx = min(start_idx + pages_per_chunk, total_pages)

            # 建立新的 PDF 並複製頁面
            writer = PdfWriter()
            for page_idx in range(start_idx, end_idx):
                writer.add_page(reader.pages[page_idx])

            # 輸出切片
            output = io.BytesIO()
            writer.write(output)
            chunk_bytes = output.getvalue()

            # 產生頁碼範圍字串（1-indexed）
            page_range = f"page-{start_idx + 1:03d}-{end_idx:03d}"

            chunks.append((chunk_bytes, page_range))

    except Exception as e:
        print(f"[split_pdf_by_pages] 切割 PDF 時發生錯誤: {e}")
        # 如果切割失敗，回傳整個 PDF 作為單一切片
        if pdf_content:
            chunks.append((pdf_content, "page-001-all"))

    return chunks


def calculate_optimal_chunk_size(
    pdf_content: bytes,
    target_size_mb: float = 4.0,
    min_pages: int = 5,
    max_pages: int = 30,
) -> int:
    """
    計算最佳切割頁數，確保每個切片小於目標大小

    策略：
    1. 先估算每頁平均大小
    2. 計算達到目標大小需要的頁數
    3. 限制在 min_pages 和 max_pages 之間

    Args:
        pdf_content: PDF 檔案的二進位內容
        target_size_mb: 目標切片大小（MB），預設 4MB
        min_pages: 最小頁數，預設 5 頁
        max_pages: 最大頁數，預設 30 頁

    Returns:
        int: 建議的每個切片頁數
    """
    total_size_mb = get_pdf_size_mb(pdf_content)
    total_pages = get_pdf_page_count(pdf_content)

    if total_pages == 0:
        return min_pages

    # 估算每頁平均大小
    avg_page_size_mb = total_size_mb / total_pages

    # 計算達到目標大小需要的頁數
    if avg_page_size_mb > 0:
        optimal_pages = int(target_size_mb / avg_page_size_mb)
    else:
        optimal_pages = max_pages

    # 限制在範圍內
    optimal_pages = max(min_pages, min(optimal_pages, max_pages))

    return optimal_pages


def split_pdf_smart(
    pdf_content: bytes, target_size_mb: float = 4.0
) -> List[Tuple[bytes, str]]:
    """
    智慧切割 PDF

    先計算最佳切割頁數，然後進行切割。
    如果切割後某個切片仍超過目標大小，會進一步分割。

    Args:
        pdf_content: PDF 檔案的二進位內容
        target_size_mb: 目標切片大小（MB），預設 4MB

    Returns:
        List[Tuple[bytes, str]]: 切片清單，每個元素為 (切片內容, 頁碼範圍字串)
    """
    # 計算最佳切割頁數
    pages_per_chunk = calculate_optimal_chunk_size(pdf_content, target_size_mb)
    print(f"[split_pdf_smart] 計算最佳切割頁數: {pages_per_chunk} 頁/切片")

    # 進行初步切割
    chunks = split_pdf_by_pages(pdf_content, pages_per_chunk)

    # 檢查是否有切片超過目標大小，如果有則進一步分割
    final_chunks = []
    for chunk_bytes, page_range in chunks:
        chunk_size_mb = get_pdf_size_mb(chunk_bytes)

        if chunk_size_mb > target_size_mb and pages_per_chunk > 5:
            # 這個切片太大，需要進一步分割
            print(
                f"[split_pdf_smart] 切片 {page_range} 大小 {chunk_size_mb:.2f}MB "
                f"超過目標 {target_size_mb}MB，進一步分割"
            )

            # 取得這個切片的頁碼範圍
            parts = page_range.replace("page-", "").split("-")
            start_page = int(parts[0])

            # 用更小的頁數重新切割
            smaller_chunks = split_pdf_by_pages(chunk_bytes, pages_per_chunk // 2)

            # 更新頁碼範圍
            chunk_page_count = get_pdf_page_count(chunk_bytes)
            for i, (sub_chunk, _) in enumerate(smaller_chunks):
                sub_start = start_page + i * (pages_per_chunk // 2)
                sub_end = min(
                    sub_start + (pages_per_chunk // 2) - 1,
                    start_page + chunk_page_count - 1,
                )
                sub_range = f"page-{sub_start:03d}-{sub_end:03d}"
                final_chunks.append((sub_chunk, sub_range))
        else:
            final_chunks.append((chunk_bytes, page_range))

    return final_chunks
