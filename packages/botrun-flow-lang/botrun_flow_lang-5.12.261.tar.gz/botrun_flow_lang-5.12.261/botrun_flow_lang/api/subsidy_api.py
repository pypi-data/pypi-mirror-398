from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Union, AsyncIterator, Optional
import os
import uuid

from pydantic import BaseModel
import time
import json
from pathlib import Path
from botrun_flow_lang.api.line_bot_api import (
    get_subsidy_api_system_prompt,
    get_subsidy_bot_normal_chat_prompt,
    get_subsidy_bot_related_prompt,
    get_subsidy_bot_requirement_prompt,
)
from botrun_flow_lang.langgraph_agents.agents.util.perplexity_search import (
    respond_with_perplexity_search,
)
from botrun_flow_lang.langgraph_agents.agents.agent_runner import agent_runner
from botrun_flow_lang.langgraph_agents.agents.search_agent_graph import (
    SearchAgentGraph,
    DEFAULT_SEARCH_CONFIG,
)
from fastapi import HTTPException, Depends

from dotenv import load_dotenv

from botrun_flow_lang.utils.langchain_utils import litellm_msgs_to_langchain_msgs
from botrun_flow_lang.api.auth_utils import verify_token

load_dotenv()

router = APIRouter(prefix="/subsidy")


# 自定義 Pydantic 模型替換 litellm 類型
class Delta(BaseModel):
    """Delta represents a change in the message content."""

    content: Optional[str] = None
    role: Optional[str] = None


class Message(BaseModel):
    """Message represents a chat message."""

    content: str
    role: str = "assistant"


class Choices(BaseModel):
    """Choices represents a set of alternatives in the API response."""

    index: int
    delta: Optional[Delta] = None
    message: Optional[Message] = None
    finish_reason: Optional[str] = None


# 讀取系統提示詞文件
# current_dir = Path(__file__).parent
# DEFAULT_SYSTEM_PROMPT = (current_dir / "subsidy_api_system_prompt.txt").read_text(
#     encoding="utf-8"
# )

# 建立 subsidy_api 專用的 SearchAgentGraph 實例
subsidy_api_graph = SearchAgentGraph().graph


class SubsidyCompletionRequest(BaseModel):
    messages: List[Dict]
    stream: bool = False
    system_prompt_roy: Optional[str] = None  # 新增這行


class SubsidyCompletionResponse(BaseModel):
    """
    Non-streaming response format for completion endpoint
    """

    id: str
    object: str = "chat.completion"
    created: int
    choices: List[Choices] = []
    state: Dict = {}


class SubsidyCompletionStreamChunk(BaseModel):
    """
    Streaming response chunk format for completion endpoint
    """

    id: str
    object: str = "chat.completion.chunk"
    created: int
    choices: List[Choices] = []
    state: Dict = {}


def validate_messages(messages: List[Dict]) -> str:
    """
    Validate messages and extract the last user message content

    Args:
        messages: List of message dictionaries

    Returns:
        The content of the last user message

    Raises:
        HTTPException: If the last message is not from user
    """
    if not messages or messages[-1].get("role") != "user":
        raise HTTPException(
            status_code=400, detail="The last message must have role 'user'"
        )
    return messages[-1].get("content", "")


def get_subsidy_search_config(stream: bool = True) -> dict:
    return {
        **DEFAULT_SEARCH_CONFIG,
        "requirement_prompt": get_subsidy_bot_requirement_prompt(),
        "search_prompt": get_subsidy_api_system_prompt(),
        "related_prompt": get_subsidy_bot_related_prompt(),
        "normal_chat_prompt": get_subsidy_bot_normal_chat_prompt(),
        "domain_filter": ["*.gov.tw", "-*.gov.cn"],
        "user_prompt_prefix": "你是台灣人，你不可以講中國用語也不可以用簡體中文，禁止！",
        "stream": stream,
    }


async def process_stream_response(messages: List[Dict]) -> AsyncIterator[str]:
    """
    Process streaming response from perplexity search

    Args:
        messages: List of message dictionaries

    Yields:
        SSE formatted string chunks
    """
    input_content = validate_messages(messages)
    messages_for_langchain = litellm_msgs_to_langchain_msgs(messages)
    messages_for_llm = messages[:-1]
    env_name = os.getenv("ENV_NAME")
    thread_id = str(uuid.uuid4())
    async for event in agent_runner(
        thread_id,
        {"messages": messages_for_langchain},
        subsidy_api_graph,
        extra_config=get_subsidy_search_config(),
    ):
        chunk_content = event.chunk
        choice = Choices(
            index=0,
            delta=Delta(content=chunk_content),
            finish_reason=None,
        )
        id = f"{env_name}-{uuid.uuid4()}"
        stream_chunk = SubsidyCompletionStreamChunk(
            id=id,
            created=int(time.time()),
            choices=[choice],
        )
        yield f"data: {json.dumps(stream_chunk.model_dump(), ensure_ascii=False)}\n\n"
    choice = Choices(
        index=0,
        delta=Delta(content=""),
        finish_reason=None,
    )
    id = f"{env_name}-{uuid.uuid4()}"
    state = subsidy_api_graph.get_state({"configurable": {"thread_id": thread_id}})
    related_questions = state.values.get("related_questions", [])
    stream_chunk = SubsidyCompletionStreamChunk(
        id=id,
        created=int(time.time()),
        choices=[choice],
        state={"related_questions": related_questions},
    )
    yield f"data: {json.dumps(stream_chunk.model_dump(), ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


async def process_non_stream_response(
    messages: List[Dict],
) -> SubsidyCompletionResponse:
    """
    Process non-streaming response from perplexity search

    Args:
        messages: List of message dictionaries

    Returns:
        SubsidyCompletionResponse with the complete response
    """
    input_content = validate_messages(messages)
    messages_for_langchain = litellm_msgs_to_langchain_msgs(messages)
    messages_for_llm = messages[:-1]

    full_content = ""
    #  async for event in respond_with_perplexity_search(
    #      input_content=input_content,
    #      user_prompt_prefix="",
    #      messages_for_llm=messages_for_llm,
    #      domain_filter=["*.gov.tw", "-*.gov.cn"],
    #  ):
    thread_id = str(uuid.uuid4())

    print(f"[subsidy_api: process_non_stream_response()] start")
    t1 = time.time()
    async for event in agent_runner(
        thread_id,
        {"messages": messages_for_langchain},
        subsidy_api_graph,
        extra_config=get_subsidy_search_config(stream=False),
    ):
        full_content += event.chunk
    print(f"[subsidy_api: process_non_stream_response()] end")
    t2 = time.time()
    print(f"[subsidy_api: process_non_stream_response()] took {t2-t1}")

    choice = Choices(
        index=0,
        message=Message(content=full_content),
        finish_reason="stop",
    )
    env_name = os.getenv("ENV_NAME")
    id = f"{env_name}-{uuid.uuid4()}"
    state = subsidy_api_graph.get_state({"configurable": {"thread_id": thread_id}})
    related_questions = state.values.get("related_questions", [])

    return SubsidyCompletionResponse(
        id=id,
        created=int(time.time()),
        choices=[choice],
        state={"related_questions": related_questions},
    )


def process_messages(
    messages: List[Dict], system_prompt_roy: Optional[str] = None
) -> List[Dict]:
    # Remove any existing system messages
    return [msg for msg in messages if msg.get("role") != "system"]


@router.post("/completion", dependencies=[Depends(verify_token)])
async def completion(
    request: SubsidyCompletionRequest,
):
    """
    Generates a text completion using perplexity search.

    Args:
        request: CompletionRequest containing messages and stream flag

    Returns:
        If stream is False, returns a CompletionResponse
        If stream is True, returns a StreamingResponse with SSE format
    """
    try:
        processed_messages = process_messages(
            request.messages, request.system_prompt_roy
        )
        # system_prompt = (
        #     request.system_prompt_roy
        #     if request.system_prompt_roy is not None
        #     else DEFAULT_SYSTEM_PROMPT
        # )
        # system_prompt = get_subsidy_api_system_prompt()
        if request.stream:
            return StreamingResponse(
                process_stream_response(processed_messages),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
        else:
            return await process_non_stream_response(processed_messages)

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
