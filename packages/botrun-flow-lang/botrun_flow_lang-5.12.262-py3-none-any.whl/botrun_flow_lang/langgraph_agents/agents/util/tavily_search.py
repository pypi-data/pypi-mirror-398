"""
Tavily search utility for government research
參考 open_deep_research 的最佳實踐
"""

import os
import logging
from typing import List, Dict, Any, AsyncGenerator
from dataclasses import dataclass

try:
    from tavily import TavilyClient, AsyncTavilyClient
except ImportError:
    TavilyClient = None
    AsyncTavilyClient = None

logger = logging.getLogger(__name__)


@dataclass
class SearchEvent:
    """搜尋事件結構，與 perplexity_search 保持一致"""

    chunk: str
    raw_json: Dict[str, Any] = None


async def respond_with_tavily_search(
    query: str,
    user_prompt_prefix: str = "",
    messages: List[Dict[str, str]] = None,
    domain_filter: List[str] = None,
    stream: bool = False,
    model_name: str = "tavily",
) -> AsyncGenerator[SearchEvent, None]:
    """
    使用 Tavily 進行搜尋（參考 open_deep_research 實作）

    Args:
        query: 搜尋查詢
        user_prompt_prefix: 用戶提示前綴（保持與 perplexity 一致的介面）
        messages: 訊息列表（保持介面一致，但 Tavily 只使用 query）
        domain_filter: 領域過濾
        stream: 是否串流（Tavily 不支援，但保持介面一致）
        model_name: 模型名稱（保持介面一致）

    Yields:
        SearchEvent: 搜尋事件
    """

    if AsyncTavilyClient is None:
        logger.error("Tavily client not available. Please install tavily-python")
        yield SearchEvent(
            chunk="錯誤：Tavily 客戶端未安裝",
            raw_json={"error": "tavily-python not installed"},
        )
        return

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not found in environment variables")
        yield SearchEvent(
            chunk="錯誤：未設定 TAVILY_API_KEY",
            raw_json={"error": "TAVILY_API_KEY not set"},
        )
        return

    try:
        # 使用 AsyncTavilyClient 進行搜尋（現代寫法）
        logger.info(f"使用 Tavily 搜尋: {query}")

        # 初始化 async client
        async_client = AsyncTavilyClient(api_key=api_key)

        # 準備搜尋參數
        search_params = {
            "query": query,
            "search_depth": "advanced",
            # "include_raw_content": True,
            # "include_answer": "advanced",
            "max_results": 5,
        }

        # 如果有 domain filter，加入參數
        if domain_filter:
            search_params["include_domains"] = domain_filter

        # 執行 async 搜尋
        response = await async_client.search(**search_params)

        # 處理搜尋結果（參考 open_deep_research 格式化）
        if response and "results" in response and len(response["results"]) > 0:
            content_parts = []
            sources = []

            # 去重複 URL（參考 open_deep_research）
            seen_urls = set()
            unique_results = []
            for result in response["results"]:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)

            # 格式化結果
            for i, result in enumerate(unique_results[:5]):  # 限制結果數量
                title = result.get("title", "")
                content = result.get("content", "")
                raw_content = result.get("raw_content", "")
                url = result.get("url", "")

                # 優先使用 raw_content，回退到 content
                # display_content = raw_content if content else raw_content

                if title and content:
                    # 限制每個結果的長度（參考 open_deep_research）
                    # if len(display_content) > 1000:
                    #     display_content = display_content[:1000] + "..."

                    content_parts.append(
                        f"[{i+1}] Title: {title}\nContent: {content}\nURL: {url}"
                    )
                    sources.append(url)

            # 組合最終內容
            full_content = "\n\n".join(content_parts)

            # 限制總長度（參考 open_deep_research 的 30000 字元限制）
            # if len(full_content) > 10000:  # 適合政府研究的長度
            #     full_content = full_content[:10000] + "\n\n[內容已截斷以符合長度限制]"

            # 構建回應 JSON（與 Perplexity 格式保持一致）
            response_json = {
                "message": {"content": full_content},
                "usage": {
                    "prompt_tokens": len(query.split()),
                    "completion_tokens": len(full_content.split()),
                    "total_tokens": len(query.split()) + len(full_content.split()),
                },
                "model": "tavily-search",
                "sources": sources,
                "results_count": len(unique_results),
            }

            yield SearchEvent(chunk=full_content, raw_json=response_json)

        else:
            logger.warning("Tavily 搜尋回應中沒有結果")
            yield SearchEvent(
                chunk="未找到搜尋結果", raw_json={"error": "no results found"}
            )

    except Exception as e:
        logger.error(f"Tavily 搜尋失敗: {e}")
        yield SearchEvent(chunk=f"搜尋失敗: {str(e)}", raw_json={"error": str(e)})


# 為了保持一致性，提供同步版本
def search_with_tavily(
    query: str, domain_filter: List[str] = None, max_results: int = 5
) -> Dict[str, Any]:
    """
    同步版本的 Tavily 搜尋（參考 open_deep_research）

    Args:
        query: 搜尋查詢
        domain_filter: 領域過濾
        max_results: 最大結果數量

    Returns:
        搜尋結果字典
    """

    if TavilyClient is None:
        return {"error": "tavily-python not installed"}

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"error": "TAVILY_API_KEY not set"}

    try:
        client = TavilyClient(api_key=api_key)

        search_params = {
            "query": query,
            "search_depth": "advanced",
            "include_raw_content": True,  # 參考 open_deep_research
            "include_domains": domain_filter if domain_filter else None,
            "max_results": max_results,
        }

        search_params = {k: v for k, v in search_params.items() if v is not None}

        response = client.search(**search_params)
        return response

    except Exception as e:
        logger.error(f"Tavily 搜尋失敗: {e}")
        return {"error": str(e)}
