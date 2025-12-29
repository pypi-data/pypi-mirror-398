from copy import deepcopy
from typing import AsyncGenerator
from pydantic import BaseModel
import os
import json
import aiohttp
from dotenv import load_dotenv
import re
import logging

load_dotenv()


class PerplexitySearchEvent(BaseModel):
    chunk: str
    raw_json: dict | None = None


PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def should_include_citation(citation: str, domain_filter: list[str]) -> bool:
    # 如果沒有任何過濾規則，接受所有網站
    if not domain_filter:
        return True

    # 分離排除規則和包含規則
    exclude_rules = [
        rule[1:].replace("*.", "") for rule in domain_filter if rule.startswith("-")
    ]
    include_rules = [
        rule.replace("*.", "") for rule in domain_filter if not rule.startswith("-")
    ]

    # 檢查是否符合任何排除規則
    for pattern in exclude_rules:
        if pattern in citation:
            return False

    # 如果沒有包含規則，且通過了排除規則檢查，就接受該網站
    if not include_rules:
        return True

    # 如果有包含規則，必須符合至少一個
    for pattern in include_rules:
        if pattern in citation:
            return True

    return False


def is_valid_domain(domain: str) -> bool:
    if not domain or "*." in domain:
        return False

    # 只允許包含 ://、.、% 和英數字的網址
    # ^ 表示開頭，$ 表示結尾
    # [a-zA-Z0-9] 表示英數字
    # [\\.\\:\\/\\%] 表示允許的特殊字符
    pattern = r"^[a-zA-Z0-9\\.\\:\\/\\%]+$"

    return bool(re.match(pattern, domain))


async def respond_with_perplexity_search_openrouter(
    input_content,
    user_prompt_prefix,
    messages_for_llm,
    domain_filter: list[str],
    stream: bool = False,
    model: str = "perplexity/sonar-small-online",
    structured_output: bool = False,
    return_images: bool = False,
) -> AsyncGenerator[PerplexitySearchEvent, None]:
    """
    使用 OpenRouter 提供的 Perplexity API 服務
    structured_output: 只有在 stream 為 False 時有效
    """
    # 確保模型是 Perplexity 的模型
    if not model.startswith("perplexity/"):
        model = "perplexity/sonar-small-online"

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openrouter.ai/api/v1",  # OpenRouter 需要提供來源
        "X-Title": "BotRun Flow Lang",  # 可選的應用名稱
    }

    messages = deepcopy(messages_for_llm)
    if len(messages) > 0 and messages[-1]["role"] == "user":
        messages.pop()
    if user_prompt_prefix:
        xml_input_content = f"<使用者提問>{input_content}</使用者提問>"
        messages.append(
            {"role": "user", "content": user_prompt_prefix + "\n\n" + xml_input_content}
        )
    else:
        messages.append({"role": "user", "content": input_content})

    filtered_domain_filter = []
    for domain in domain_filter:
        if domain and is_valid_domain(domain):
            filtered_domain_filter.append(domain)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "stream": stream,
        # OpenRouter 可能不支持 search_domain_filter 參數，如果有問題可以移除
        "search_domain_filter": filtered_domain_filter,
        "stream_usage": True,
        "return_images": return_images,
        # "reasoning_effort": "high",
    }

    try:
        input_token = 0
        output_token = 0
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_API_URL, headers=headers, json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"OpenRouter API error: {error_text}")

                if not stream:
                    # 非串流模式的處理
                    response_data = await response.json()
                    content = response_data["choices"][0]["message"]["content"]
                    content = remove_citation_number_from_content(content)
                    if not structured_output:
                        yield PerplexitySearchEvent(chunk=content, raw_json=response_data)

                    # 處理引用 (如果 OpenRouter 返回引用)
                    citations = response_data.get("citations", [])
                    final_citations = [
                        citation
                        for citation in citations
                        if should_include_citation(citation, domain_filter)
                    ]
                    images = response_data.get("images", [])

                    if final_citations:
                        references = f"\n\n參考來源：\n"
                        for citation in final_citations:
                            references += f"- {citation}\n"
                        if not structured_output:
                            yield PerplexitySearchEvent(chunk=references)

                    if structured_output:
                        yield PerplexitySearchEvent(
                            chunk=json.dumps(
                                {
                                    "content": content,
                                    "citations": final_citations,
                                    "images": images,
                                }
                            ),
                            raw_json=response_data,
                        )
                else:
                    # 串流模式的處理
                    full_response = ""
                    final_citations = []
                    async for line in response.content:
                        if line:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                line = line[6:]  # Remove 'data: ' prefix
                                if line == "[DONE]":
                                    break

                                try:
                                    chunk_data = json.loads(line)
                                    response_data = chunk_data

                                    if (
                                        chunk_data["choices"][0]
                                        .get("delta", {})
                                        .get("content")
                                    ):
                                        content = chunk_data["choices"][0]["delta"][
                                            "content"
                                        ]
                                        full_response += content
                                        yield PerplexitySearchEvent(
                                            chunk=content,
                                            raw_json=chunk_data,
                                        )
                                    if not final_citations and chunk_data.get(
                                        "citations", []
                                    ):
                                        citations = chunk_data.get("citations", [])
                                        final_citations = [
                                            citation
                                            for citation in citations
                                            if should_include_citation(
                                                citation, domain_filter
                                            )
                                        ]

                                except json.JSONDecodeError:
                                    continue

                    # 只在有符合條件的 citations 時才產生參考文獻
                    if final_citations:
                        references = f"\n\n參考來源：\n"
                        for citation in final_citations:
                            references += f"- {citation}\n"
                        yield PerplexitySearchEvent(chunk=references)

        if response_data.get("usage"):
            logging.info(
                f"perplexity_search_openrouter============> input_token: {response_data['usage'].get('prompt_tokens', 0) + response_data['usage'].get('citation_tokens', 0)}, output_token: {response_data['usage'].get('completion_tokens', 0)}",
            )
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(e)


async def respond_with_perplexity_search(
    input_content,
    user_prompt_prefix,
    messages_for_llm,
    domain_filter: list[str],
    stream: bool = False,
    model: str = "sonar-reasoning-pro",
    structured_output: bool = False,
    return_images: bool = False,
) -> AsyncGenerator[PerplexitySearchEvent, None]:
    """
    structured_output: 只有在 stream 為 False 時有效
    return_images: 是否返回圖片，但是 openrouter 不支援
    """
    # 檢查是否使用 OpenRouter
    is_use_openrouter = os.getenv("OPENROUTER_API_KEY") and os.getenv(
        "OPENROUTER_BASE_URL"
    )
    if return_images:
        # if os.getenv("PPLX_API_KEY", "") == "":
        #     raise ValueError(
        #         "PPLX_API_KEY environment variable not set, return_images needs PPLX_API_KEY"
        #     )
        # Openrouter 尚不支援 return_images
        is_use_openrouter = False

    if is_use_openrouter:
        # 若使用 OpenRouter，轉換模型名稱並呼叫 OpenRouter 版本的函數
        openrouter_model = "perplexity/sonar-reasoning-pro"
        if model == "sonar-reasoning-pro":
            openrouter_model = "perplexity/sonar-reasoning-pro"
        elif model == "sonar-reasoning":
            openrouter_model = "perplexity/sonar-reasoning"
        elif model == "sonar-pro":
            openrouter_model = "perplexity/sonar-pro"
        elif model == "sonar":
            openrouter_model = "perplexity/sonar"

        async for event in respond_with_perplexity_search_openrouter(
            input_content,
            user_prompt_prefix,
            messages_for_llm,
            domain_filter,
            stream,
            openrouter_model,
            structured_output,
        ):
            yield event
        return

    # 以下是原有的邏輯
    if model not in ["sonar-reasoning-pro", "sonar-reasoning", "sonar-pro", "sonar"]:
        model = "sonar-reasoning-pro"
    api_key = os.getenv("PPLX_API_KEY")
    if not api_key:
        raise ValueError("PPLX_API_KEY environment variable not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages = deepcopy(messages_for_llm)
    if len(messages) > 0 and messages[-1]["role"] == "user":
        messages.pop()
    if user_prompt_prefix:
        xml_input_content = f"<使用者提問>{input_content}</使用者提問>"
        messages.append(
            {"role": "user", "content": user_prompt_prefix + "\n\n" + xml_input_content}
        )
    else:
        messages.append({"role": "user", "content": input_content})
    filtered_domain_filter = []

    for domain in domain_filter:
        if domain and is_valid_domain(domain):
            filtered_domain_filter.append(domain)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "stream": stream,
        "search_domain_filter": filtered_domain_filter,
        "stream_usage": True,
        "return_images": return_images,

    }
    try:
        input_token = 0
        output_token = 0
        async with aiohttp.ClientSession() as session:
            async with session.post(
                PERPLEXITY_API_URL, headers=headers, json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"Perplexity API error: {error_text}")

                if not stream:
                    # 非串流模式的處理
                    response_data = await response.json()
                    content = response_data["choices"][0]["message"]["content"]
                    content = remove_citation_number_from_content(content)
                    if not structured_output:
                        yield PerplexitySearchEvent(chunk=content, raw_json=response_data)

                    # 處理引用
                    citations = response_data.get("citations", [])
                    final_citations = [
                        citation
                        for citation in citations
                        if should_include_citation(citation, domain_filter)
                    ]
                    images = response_data.get("images", [])

                    if final_citations:
                        references = f"\n\n參考來源：\n"
                        for citation in final_citations:
                            references += f"- {citation}\n"
                        if not structured_output:
                            yield PerplexitySearchEvent(chunk=references)

                    if structured_output:
                        yield PerplexitySearchEvent(
                            chunk=json.dumps(
                                {
                                    "content": content,
                                    "citations": final_citations,
                                    "images": images,
                                }
                            ),
                            raw_json=response_data,
                        )

                # 串流模式的處理
                full_response = ""
                final_citations = []
                async for line in response.content:
                    if line:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            line = line[6:]  # Remove 'data: ' prefix
                            if line == "[DONE]":
                                break

                            try:
                                chunk_data = json.loads(line)
                                response_data = chunk_data
                                # print(chunk_data)
                                if (
                                    chunk_data["choices"][0]
                                    .get("delta", {})
                                    .get("content")
                                ):
                                    content = chunk_data["choices"][0]["delta"][
                                        "content"
                                    ]
                                    full_response += content
                                    yield PerplexitySearchEvent(
                                        chunk=content,
                                        raw_json=chunk_data,
                                    )
                                if not final_citations and chunk_data.get(
                                    "citations", []
                                ):
                                    # 發現 perplexity 不會都有 finish_reason 為 stop 的狀況，但是 citations 會有
                                    # if chunk_data["choices"][0]["finish_reason"] == "stop":
                                    citations = chunk_data.get("citations", [])
                                    final_citations = [
                                        citation
                                        for citation in citations
                                        if should_include_citation(
                                            citation, domain_filter
                                        )
                                    ]

                            except json.JSONDecodeError:
                                continue

                # 只在有符合條件的 citations 時才產生參考文獻
                if final_citations:
                    references = f"\n\n參考來源：\n"
                    for citation in final_citations:
                        references += f"- {citation}\n"
                    yield PerplexitySearchEvent(chunk=references)
        # 安全地存取 usage 資訊，避免鍵不存在的錯誤
        if response_data and "usage" in response_data:
            usage = response_data["usage"]
            prompt_tokens = usage.get("prompt_tokens", 0)
            citation_tokens = usage.get("citation_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            logging.info(
                f"perplexity_search============> input_token: {prompt_tokens + citation_tokens}, output_token: {completion_tokens}",
            )
        else:
            logging.info("perplexity_search============> usage information not available")
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(e)


def remove_citation_number_from_content(content: str) -> str:
    """
    移除文字裡的 [1]、[2]、[3] 等數字
    """
    return re.sub(r"\[[0-9]+\]", "", content)
    # answer_message = await cl.Message(content="").send()
    # full_response = ""
    # for response in responses:
    #     if response.candidates[0].finish_reason != Candidate.FinishReason.STOP:
    #         # await answer_message.stream_token(response.text)
    #         yield GeminiGroundingEvent(chunk=response.text)
    #         full_response += response.text
    #         if response.candidates[0].grounding_metadata:
    #             if len(response.candidates[0].grounding_metadata.grounding_chunks) > 0:
    #                 references = f"\n\n{tr('Sources:')}\n"
    #                 for grounding_chunk in response.candidates[
    #                     0
    #                 ].grounding_metadata.grounding_chunks:
    #                     references += f"- [{grounding_chunk.web.title}]({grounding_chunk.web.uri})\n"
    #                 # await answer_message.stream_token(references)
    #                 yield GeminiGroundingEvent(chunk=references)
    #     else:
    #         if response.candidates[0].grounding_metadata:
    #             if len(response.candidates[0].grounding_metadata.grounding_chunks) > 0:
    #                 references = f"\n\n{tr('Sources:')}\n"
    #                 for grounding_chunk in response.candidates[
    #                     0
    #                 ].grounding_metadata.grounding_chunks:
    #                     references += f"- [{grounding_chunk.web.title}]({grounding_chunk.web.uri})\n"
    #                 # await answer_message.stream_token(references)
    #                 yield GeminiGroundingEvent(chunk=references)
