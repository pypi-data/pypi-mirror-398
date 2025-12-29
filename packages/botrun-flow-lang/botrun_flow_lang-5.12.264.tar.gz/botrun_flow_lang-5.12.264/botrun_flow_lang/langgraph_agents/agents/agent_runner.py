from typing import AsyncGenerator, Dict, List, Optional, Union, Any
import logging

from pydantic import BaseModel


class StepsUpdateEvent(BaseModel):
    """
    for step in steps:
        print("Description:", step.get("description", ""))
        print("Status:", step.get("status", ""))
        print("Updates:", step.get("updates", ""))
    """

    steps: List = []


class OnNodeStreamEvent(BaseModel):
    chunk: str


class ChatModelEndEvent(BaseModel):
    """
    Chat Model End Event 資料模型
    提供 on_chat_model_end 事件的原始資料，供呼叫端自行處理
    """

    # 原始事件資料
    raw_output: Any = None  # 來自 event["data"]["output"]
    raw_input: Any = None  # 來自 event["data"]["input"]

    # 基本 metadata
    langgraph_node: str = ""
    usage_metadata: Dict = {}
    model_name: str = ""

    # chunk
    chunk: str = ""


MAX_RECURSION_LIMIT = 25


# graph 是 CompiledStateGraph，不傳入型別的原因是，loading import 需要 0.5秒
async def langgraph_runner(
    thread_id: str,
    init_state: dict,
    graph,
    need_resume: bool = False,
    extra_config: Optional[Dict] = None,
) -> AsyncGenerator:
    """
    這個 function 與 agent_runner 的差別在於，langgraph_runner 是回傳原原本本 LangGraph 的 event，而 agent_runner 是回傳 LangGraph 的 event 經過處理後的 event。
    """
    invoke_state = init_state
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_RECURSION_LIMIT,
    }
    if extra_config:
        config["configurable"].update(extra_config)
    if need_resume:
        state_history = []
        async for state in graph.aget_state_history(config):
            state_history.append(state)

        # 如果 state_history 的長度超過 MAX_RECURSION_LIMIT，動態調整 recursion_limit
        if len(state_history) > MAX_RECURSION_LIMIT:
            # 計算超出的倍數
            multiplier = (len(state_history) - 1) // MAX_RECURSION_LIMIT
            # 設定新的 recursion_limit 為 (multiplier + 1) * MAX_RECURSION_LIMIT
            config["recursion_limit"] = (multiplier + 1) * MAX_RECURSION_LIMIT

    try:
        async for event in graph.astream_events(
                invoke_state,
                config,
                version="v2",
        ):
            yield event
    except Exception as e:
        # 捕獲 SSE 流讀取錯誤（如 httpcore.ReadError）
        import logging
        logging.error(f"Error reading SSE stream: {e}", exc_info=True)
        # 產生錯誤 event 讓調用者知道
        yield {"error": f"SSE stream error: {str(e)}"}


# graph 是 CompiledStateGraph，不傳入型別的原因是，loading import 需要 0.5秒
async def agent_runner(
    thread_id: str,
    init_state: dict,
    graph,
    need_resume: bool = False,
    extra_config: Optional[Dict] = None,
) -> AsyncGenerator[
    Union[StepsUpdateEvent, OnNodeStreamEvent, ChatModelEndEvent], None
]:
    invoke_state = init_state
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": MAX_RECURSION_LIMIT,
    }
    if extra_config:
        config["configurable"].update(extra_config)
    if need_resume:
        state_history = []
        async for state in graph.aget_state_history(config):
            state_history.append(state)

        # 如果 state_history 的長度超過 MAX_RECURSION_LIMIT，動態調整 recursion_limit
        if len(state_history) > MAX_RECURSION_LIMIT:
            # 計算超出的倍數
            multiplier = (len(state_history) - 1) // MAX_RECURSION_LIMIT
            # 設定新的 recursion_limit 為 (multiplier + 1) * MAX_RECURSION_LIMIT
            config["recursion_limit"] = (multiplier + 1) * MAX_RECURSION_LIMIT

    async for event in graph.astream_events(
        invoke_state,
        config,
        version="v2",
    ):
        if event["event"] == "on_chain_end":
            pass
        if event["event"] == "on_chat_model_end":
            data = event.get("data", {})
            logging.info(f"[Agent Runner] on_chat_model_end data: {data}")
            metadata = event.get("metadata", {})
            langgraph_node = metadata.get("langgraph_node", {})
            output = data.get("output", {})

            # 提取常用的 metadata（為了向後相容性）
            usage_metadata = {}
            model_name = ""

            if hasattr(output, "usage_metadata"):
                usage_metadata = output.usage_metadata if output.usage_metadata else {}

            if hasattr(output, "response_metadata"):
                model_name = output.response_metadata.get("model_name", "")

            chat_model_end_event = ChatModelEndEvent(
                raw_output=data.get("output", {}),
                raw_input=data.get("input", {}),
                langgraph_node=langgraph_node,
                usage_metadata=usage_metadata,
                model_name=model_name,
            )
            yield chat_model_end_event
        if event["event"] == "on_chat_model_stream":
            data = event["data"]
            if (
                data["chunk"].content
                and isinstance(data["chunk"].content[0], dict)
                and data["chunk"].content[0].get("text", "")
            ):
                yield OnNodeStreamEvent(chunk=data["chunk"].content[0].get("text", ""))
            elif data["chunk"].content and isinstance(data["chunk"].content, str):
                yield OnNodeStreamEvent(chunk=data["chunk"].content)


# def handle_copilotkit_intermediate_state(event: dict):
#     print("Handling copilotkit intermediate state")
#     copilotkit_intermediate_state = event["metadata"].get(
#         "copilotkit:emit-intermediate-state"
#     )
#     print(f"Intermediate state: {copilotkit_intermediate_state}")
#     if copilotkit_intermediate_state:
#         for intermediate_state in copilotkit_intermediate_state:
#             if intermediate_state.get("state_key", "") == "steps":
#                 for tool_call in event["data"]["output"].tool_calls:
#                     if tool_call.get("name", "") == intermediate_state.get("tool", ""):
#                         steps = tool_call["args"].get(
#                             intermediate_state.get("tool_argument")
#                         )
#                         print(f"Yielding steps: {steps}")
#                         yield StepsUpdateEvent(steps=steps)
#     print("--------------------------------")
