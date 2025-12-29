"""
PDF 分析模組

提供 PDF 檔案分析功能，支援：
- 小檔 (< 5MB)：直接多模態問答
- 大檔 (>= 5MB)：壓縮 → 切割 → 平行多模態問答 → LLM 統整結果
"""

import anthropic
import asyncio
import base64
import httpx
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv()

# 檔案大小閾值（MB）
PDF_SIZE_THRESHOLD_MB = 30.0

# 切片目標大小（MB）
PDF_CHUNK_TARGET_SIZE_MB = 30.0

# 最大平行問答數量
MAX_CONCURRENT_CHUNKS = 5


def analyze_pdf_with_claude(
    pdf_data: str, user_input: str, model_name: str = "claude-sonnet-4-5-20250929"
):
    """
    Analyze a PDF file using Claude API

    Args:
        pdf_data: Base64-encoded PDF data
        user_input: User's query about the PDF content

    Returns:
        str: Claude's analysis of the PDF content based on the query
    """
    # Initialize Anthropic client
    client = anthropic.Anthropic()

    # Send to Claude
    message = client.messages.create(
        model=model_name,
        max_tokens=4096,  # Increased token limit for detailed analysis
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {"type": "text", "text": user_input},
                ],
            }
        ],
    )

    print(
        f"analyze_pdf_with_claude============> input_token: {message.usage.input_tokens} output_token: {message.usage.output_tokens}",
    )
    return message.content[0].text


def analyze_pdf_with_gemini(
    pdf_data: str, user_input: str, model_name: str = "gemini-2.5-flash", pdf_url: str = ""
):
    """
    Analyze a PDF file using Gemini API

    Args:
        pdf_data: Base64-encoded PDF data
        user_input: User's query about the PDF content
        model_name: Gemini model name to use

    Returns:
        str: Gemini's analysis of the PDF content based on the query
    """
    # 放到要用的時候才 import，不然loading 會花時間
    from google import genai
    from google.genai import types

    credentials = service_account.Credentials.from_service_account_file(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_FASTAPI"),
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    client = genai.Client(
        credentials=credentials,
        project="scoop-386004",
        location="us-central1",
    )
    response = client.models.generate_content(
        model=model_name,
        contents=[
            user_input,
            types.Part(
                inline_data={
                    "mime_type": "application/pdf",
                    "data": pdf_data,
                }
            ),
        ],
    )
    # Log token usage if available
    if hasattr(response, "usage_metadata"):
        print(
            f"analyze_pdf_with_gemini============> input_token: {response.usage_metadata.prompt_token_count} output_token: {response.usage_metadata.candidates_token_count}",
        )

    print(f"{pdf_url} success")
    return response.text


def _analyze_single_chunk(
    chunk_data: str, page_range: str, user_input: str, model_name: str
) -> Dict[str, Any]:
    """
    分析單一 PDF 切片

    Args:
        chunk_data: Base64-encoded PDF chunk data
        page_range: 頁碼範圍字串 (e.g., "page-001-015")
        user_input: 使用者問題
        model_name: 使用的模型名稱

    Returns:
        Dict: {"page_range": str, "answer": str, "relevant": bool, "error": str|None}
    """
    # 構建切片專用的 prompt
    chunk_prompt = f"""你正在閱讀一份大型 PDF 文件的其中一部分（{page_range}）。

使用者問題：{user_input}

請根據這個部分的內容回答問題：
- 如果這個部分包含與問題相關的資訊，請詳細回答
- 如果這個部分與問題完全無關，請只回答「NOT_RELEVANT」（不要回答其他內容）
- 回答時請標註資訊來源的頁碼"""

    try:
        if model_name.startswith("gemini-"):
            answer = analyze_pdf_with_gemini(chunk_data, chunk_prompt, model_name)
        elif model_name.startswith("claude-"):
            answer = analyze_pdf_with_claude(chunk_data, chunk_prompt, model_name)
        else:
            return {
                "page_range": page_range,
                "answer": "",
                "relevant": False,
                "error": f"Unknown model type: {model_name}",
            }

        # 判斷是否相關
        is_relevant = "NOT_RELEVANT" not in answer.upper()

        return {
            "page_range": page_range,
            "answer": answer if is_relevant else "",
            "relevant": is_relevant,
            "error": None,
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "page_range": page_range,
            "answer": "",
            "relevant": False,
            "error": str(e),
        }


async def analyze_pdf_chunks_parallel(
    chunks: List[tuple], user_input: str, model_name: str, max_concurrent: int = 5
) -> List[Dict[str, Any]]:
    """
    平行問答多個 PDF 切片

    Args:
        chunks: 切片清單 [(chunk_bytes, page_range), ...]
        user_input: 使用者問題
        model_name: 使用的模型名稱
        max_concurrent: 最大平行數量

    Returns:
        List[Dict]: 每個切片的回答結果
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def analyze_with_semaphore(chunk_bytes: bytes, page_range: str):
        async with semaphore:
            # 將 bytes 轉為 base64
            chunk_data = base64.standard_b64encode(chunk_bytes).decode("utf-8")

            # 使用 run_in_executor 執行同步函數
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                _analyze_single_chunk,
                chunk_data,
                page_range,
                user_input,
                model_name,
            )

    # 建立所有任務
    tasks = [
        analyze_with_semaphore(chunk_bytes, page_range)
        for chunk_bytes, page_range in chunks
    ]

    # 平行執行
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 處理例外
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append(
                {
                    "page_range": chunks[i][1],
                    "answer": "",
                    "relevant": False,
                    "error": str(result),
                }
            )
        else:
            processed_results.append(result)

    return processed_results


def merge_chunk_results(
    chunk_results: List[Dict[str, Any]],
    user_input: str,
    model_name: str = "gemini-2.5-flash",
) -> str:
    """
    使用 LLM 統整多個切片的回答

    Args:
        chunk_results: 切片回答結果清單
        user_input: 原始使用者問題
        model_name: 統整使用的模型名稱

    Returns:
        str: 統整後的回答
    """
    # 過濾出相關的回答
    relevant_results = [r for r in chunk_results if r.get("relevant", False)]

    if not relevant_results:
        # 沒有找到相關內容
        error_results = [r for r in chunk_results if r.get("error")]
        if error_results:
            error_msgs = [f"{r['page_range']}: {r['error']}" for r in error_results]
            return f"分析 PDF 時發生錯誤：\n" + "\n".join(error_msgs)
        return "在 PDF 文件中未找到與您問題相關的內容。"

    # 只有一個相關結果，直接回傳
    if len(relevant_results) == 1:
        return relevant_results[0]["answer"]

    # 多個相關結果，需要統整
    combined_content = "\n\n".join(
        [
            f"【{r['page_range']}】\n{r['answer']}"
            for r in relevant_results
        ]
    )

    merge_prompt = f"""以下是從一份大型 PDF 文件的不同部分擷取的回答，請統整這些資訊來回答使用者的問題。

使用者問題：{user_input}

各部分的回答：
{combined_content}

請統整以上資訊，提供一個完整、連貫的回答。如果不同部分有互補的資訊，請整合在一起。請保留頁碼引用。"""

    try:
        # 使用 LLM 統整（這裡不需要傳 PDF，只是純文字統整）
        from google import genai

        credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_FASTAPI"),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        client = genai.Client(
            credentials=credentials,
            project="scoop-386004",
            location="us-central1",
        )

        response = client.models.generate_content(
            model=model_name,
            contents=[merge_prompt],
        )

        if hasattr(response, "usage_metadata"):
            print(
                f"merge_chunk_results============> input_token: {response.usage_metadata.prompt_token_count} output_token: {response.usage_metadata.candidates_token_count}",
            )

        return response.text

    except Exception as e:
        import traceback

        traceback.print_exc()
        # 統整失敗，直接回傳合併的內容
        return f"統整時發生錯誤，以下是各部分的回答：\n\n{combined_content}"


async def analyze_pdf_async(pdf_url: str, user_input: str) -> str:
    """
    非同步分析 PDF 檔案（智慧處理策略）

    根據檔案大小自動選擇處理策略：
    - < 5MB: 直接多模態問答
    - >= 5MB: 壓縮 → 切割 → 平行多模態問答 → LLM 統整結果

    Args:
        pdf_url: PDF 檔案的 URL
        user_input: 使用者問題

    Returns:
        str: 分析結果
    """
    try:
        # 1. 下載 PDF
        print(f"[analyze_pdf_async] 下載 PDF: {pdf_url}")
        pdf_content = httpx.get(pdf_url, timeout=60.0).content
        pdf_size_mb = len(pdf_content) / (1024 * 1024)
        print(f"[analyze_pdf_async] PDF 大小: {pdf_size_mb:.2f} MB")

        # 取得模型設定
        models_str = os.getenv("PDF_ANALYZER_MODEL", "gemini-2.5-flash")
        print(f"[analyze_pdf_async] 使用模型: {models_str}")
        models = [model.strip() for model in models_str.split(",")]
        primary_model = models[0]

        # 2. 判斷處理策略
        if pdf_size_mb < PDF_SIZE_THRESHOLD_MB:
            # 小檔：直接多模態問答
            print(f"[analyze_pdf_async] 小檔模式 (< {PDF_SIZE_THRESHOLD_MB}MB)")
            pdf_data = base64.standard_b64encode(pdf_content).decode("utf-8")

            # 嘗試所有模型
            last_error = None
            for model in models:
                try:
                    if model.startswith("gemini-"):
                        return analyze_pdf_with_gemini(pdf_data, user_input, model, pdf_url)
                    elif model.startswith("claude-"):
                        return analyze_pdf_with_claude(pdf_data, user_input, model)
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    last_error = str(e)
                    continue

            return f"分析 PDF 時所有模型都失敗。最後錯誤: {last_error}"

        # 3. 大檔：壓縮 → 切割 → 平行問答 → 統整
        print(f"[analyze_pdf_async] 大檔模式 (>= {PDF_SIZE_THRESHOLD_MB}MB)")

        # 延遲 import 以加快載入
        from botrun_flow_lang.langgraph_agents.agents.util.pdf_processor import (
            split_pdf_smart,
            get_pdf_page_count,
        )
        from botrun_flow_lang.langgraph_agents.agents.util.pdf_cache import (
            get_cache_key,
            check_cache,
            save_to_cache,
        )

        # 3.1 檢查快取
        cache_key = get_cache_key(pdf_url)
        print(f"[analyze_pdf_async] 檢查快取: {cache_key}")
        cached_chunks = await check_cache(cache_key)

        if cached_chunks:
            # 有快取，直接使用
            print(f"[analyze_pdf_async] 使用快取: {len(cached_chunks)} 個切片")
            chunks = cached_chunks
            total_pages = sum(
                int(pr.split("-")[-1]) - int(pr.split("-")[-2]) + 1
                for _, pr in chunks
                if pr.startswith("page-")
            ) if chunks else 0
        else:
            # 無快取，切割後存入快取

            # 3.2 切割
            print("[analyze_pdf_async] 切割 PDF...")
            chunks = split_pdf_smart(pdf_content, target_size_mb=PDF_CHUNK_TARGET_SIZE_MB)
            total_pages = get_pdf_page_count(pdf_content)
            print(
                f"[analyze_pdf_async] 切割完成: {len(chunks)} 個切片, 共 {total_pages} 頁"
            )

            # 3.3 存入快取
            print("[analyze_pdf_async] 存入快取...")
            await save_to_cache(
                cache_key=cache_key,
                chunks=chunks,
                original_url=pdf_url,
                original_size_mb=pdf_size_mb,
                total_pages=total_pages,
            )

        # 3.3 平行問答
        print(f"[analyze_pdf_async] 開始平行問答 (最大並行: {MAX_CONCURRENT_CHUNKS})...")
        chunk_results = await analyze_pdf_chunks_parallel(
            chunks, user_input, primary_model, max_concurrent=MAX_CONCURRENT_CHUNKS
        )

        # 統計結果
        relevant_count = sum(1 for r in chunk_results if r.get("relevant", False))
        error_count = sum(1 for r in chunk_results if r.get("error"))
        print(
            f"[analyze_pdf_async] 問答完成: {relevant_count}/{len(chunks)} 個切片有相關內容, "
            f"{error_count} 個錯誤"
        )

        # 3.4 統整結果
        print("[analyze_pdf_async] 統整結果...")
        result = merge_chunk_results(chunk_results, user_input, primary_model)
        print("[analyze_pdf_async] 完成")

        return result

    except Exception as e:
        import traceback

        traceback.print_exc()
        return f"分析 PDF {pdf_url} 時發生錯誤: {str(e)}"


def analyze_pdf(pdf_url: str, user_input: str) -> str:
    """
    分析 PDF 檔案（同步包裝函數）

    這是一個同步函數，內部會建立事件迴圈來執行非同步的 analyze_pdf_async。
    為了向後相容，保留這個同步介面。

    Args:
        pdf_url: PDF 檔案的 URL
        user_input: 使用者問題

    Returns:
        str: 分析結果
    """
    try:
        # 嘗試取得現有的事件迴圈
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已經在事件迴圈中，建立新的任務
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, analyze_pdf_async(pdf_url, user_input)
                )
                return future.result()
        else:
            return loop.run_until_complete(analyze_pdf_async(pdf_url, user_input))
    except RuntimeError:
        # 沒有事件迴圈，建立新的
        return asyncio.run(analyze_pdf_async(pdf_url, user_input))
