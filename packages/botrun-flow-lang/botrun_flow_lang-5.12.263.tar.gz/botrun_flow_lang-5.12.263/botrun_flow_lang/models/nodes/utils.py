import asyncio
from typing import Any, Dict, List
from urllib.parse import quote

import aiohttp

from yarl import URL


from io import StringIO
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


async def scrape_single_pdf(url: str) -> Dict[str, Any]:
    """從 URL 抓取單個 PDF 文件並轉換為純文字

    Args:
        url: PDF 文件的 URL

    Returns:
        Dict[str, Any]: 包含 URL 和轉換後內容的字典，如果失敗則包含錯誤信息
    """
    try:
        # 使用 aiohttp 下載 PDF 文件
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return {
                        "url": url,
                        "status": "error",
                        "error": f"HTTP error {response.status}",
                    }

                # 讀取 PDF 內容
                pdf_content = await response.read()

        # 創建輸出緩衝區
        output_string = StringIO()

        # 設置提取參數
        laparams = LAParams(
            line_margin=0.5,
            word_margin=0.1,
            char_margin=2.0,
            boxes_flow=0.5,
            detect_vertical=True,
        )

        # 從二進制內容提取文字
        from io import BytesIO

        pdf_file = BytesIO(pdf_content)

        # 提取文字
        extract_text_to_fp(
            pdf_file,
            output_string,
            laparams=laparams,
            output_type="text",
            codec="utf-8",
        )

        # 獲取提取的文字
        content = output_string.getvalue().strip()

        return {"url": url, "content": content, "status": "success"}
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"url": url, "status": "error", "error": str(e)}


async def scrape_pdfs(selected_urls: List[str]) -> List[Dict[str, Any]]:
    """並行抓取多個 PDF 文件的內容

    Args:
        selected_urls: PDF 文件 URL 列表

    Returns:
        List[Dict[str, Any]]: 包含每個 PDF 的 URL 和內容的字典列表，只返回成功的結果
    """
    # 創建所有 PDF 的抓取任務
    scrape_tasks = [scrape_single_url(url, FILE_FORMAT_PDF) for url in selected_urls]

    # 同時執行所有抓取任務
    scrape_results = await asyncio.gather(*scrape_tasks)

    # 只返回成功的結果
    return [result for result in scrape_results if result["status"] == "success"]


async def scrape_urls(selected_urls: List[str]) -> List[Dict[str, Any]]:
    """並行抓取所有 URL 的內容"""
    # 一次性創建所有 URL 的抓取任務
    scrape_tasks = [scrape_single_url(url) for url in selected_urls]

    # 同時執行所有抓取任務
    scrape_results = await asyncio.gather(*scrape_tasks)
    scrape_results = [
        scrape_result
        for scrape_result in scrape_results
        if scrape_result["status"] == "success"
    ]

    # 轉換為原來的輸出格式
    return scrape_results


FILE_FORMAT_PDF = "application/pdf"
FILE_FORMATS = [FILE_FORMAT_PDF]


async def scrape_single_url(url: str, file_format: str = None) -> Dict[str, Any]:
    """抓取單個 URL 的內容"""
    try:
        if "%" not in url:
            quoted_url = quote(url, safe="")
        else:
            quoted_url = url
        scrape_url = f"https://botrun-crawler-fastapi-prod-36186877499.asia-east1.run.app/scrape?url={quoted_url}"
        if file_format is not None and file_format in FILE_FORMATS:
            file_format = quote(file_format, safe="")
            scrape_url = f"{scrape_url}&file_format={file_format}"
        scrape_url = URL(scrape_url, encoded=True)
        async with aiohttp.ClientSession() as session:
            async with session.get(scrape_url) as response:
                if response.status == 200:
                    body = await response.json()
                    print(f"[scrape_single_url] url: {url}")
                    print(
                        f"[scrape_single_url] content: {body['data']['markdown'][:100]}"
                    )
                    return {
                        "url": url,
                        "title": body["data"]["metadata"]["title"],
                        "content": body["data"]["markdown"],
                        "status": "success",
                    }
                else:
                    return {
                        "url": url,
                        "status": "error",
                        "error": f"Scraping failed with status {response.status}",
                    }
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)}


async def scrape_vertexai_search_results(search_results: Dict, limit: int = 5):
    """處理 Vertex AI 搜尋結果，並將抓取的內容更新到原始結果中

    Args:
        search_results: Vertex AI 搜尋回傳的結果字典

    Returns:
        Dict: 包含更新後的完整結果和其他格式文件
    """
    # 分離一般網頁、PDF和其他格式文件
    web_urls = []
    pdf_urls = []
    web_results_map = {}  # 用於存放 url 到結果的映射
    pdf_results_map = {}  # 用於存放 PDF url 到結果的映射
    other_format_results = []
    updated_results = []

    for result in search_results["results"][:limit]:
        if result["fileFormat"] == "":
            web_urls.append(result["url"])
            web_results_map[result["url"]] = result
        elif result["fileFormat"] == "PDF/Adobe Acrobat":
            pdf_urls.append(result["url"])
            pdf_results_map[result["url"]] = result
        else:
            other_format_results.append(result)
        updated_results.append(result)

    # 並行抓取網頁和PDF內容
    scrape_tasks = []

    if web_urls:
        scrape_tasks.append(scrape_urls(web_urls))
    if pdf_urls:
        scrape_tasks.append(scrape_pdfs(pdf_urls))

    # 同時執行所有��取任務
    all_results = await asyncio.gather(*scrape_tasks) if scrape_tasks else []

    # 更新原始結果中的內容
    for results in all_results:
        for scrape_result in results:
            if scrape_result["url"] in web_results_map:
                web_results_map[scrape_result["url"]]["content"] = scrape_result[
                    "content"
                ]
            elif scrape_result["url"] in pdf_results_map:
                pdf_results_map[scrape_result["url"]]["content"] = scrape_result[
                    "content"
                ]

    return {
        "results": updated_results,
        "other_format_results": other_format_results,
    }
