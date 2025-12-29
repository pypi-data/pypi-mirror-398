from typing import Dict, List, Any, Optional
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    message_to_dict,
)
import json
from botrun_flow_lang.models.token_usage import TokenUsage, NodeUsage, ToolUsage


def litellm_msgs_to_langchain_msgs(
    msgs: List[Dict], enable_prompt_caching: bool = False
) -> List[BaseMessage]:
    """
    Convert LiteLLM style messages to Langchain messages.

    Args:
        msgs: List of dictionaries with 'role' and 'content' keys
        enable_prompt_caching: Whether to enable prompt caching, anthropic only
    Returns:
        List of Langchain message objects
    """
    converted_msgs = []
    for msg in msgs:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            if enable_prompt_caching:
                converted_msgs.append(
                    SystemMessage(
                        content=[
                            {
                                "text": content,
                                "type": "text",
                                "cache_control": {"type": "ephemeral"},
                            }
                        ]
                    )
                )
            else:
                converted_msgs.append(SystemMessage(content=content))
        elif role == "user":
            if enable_prompt_caching and isinstance(content, str):
                converted_msgs.append(
                    HumanMessage(
                        content=[
                            {
                                "text": content,
                                "type": "text",
                                "cache_control": {"type": "ephemeral"},
                            }
                        ]
                    )
                )
            elif enable_prompt_caching and isinstance(content, list):
                for item in content:
                    converted_msgs.append(
                        HumanMessage(
                            content=[
                                {
                                    "text": item.get("text", ""),
                                    "type": "text",
                                    "cache_control": {"type": "ephemeral"},
                                }
                            ]
                        )
                    )
            elif content != "":
                converted_msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            if enable_prompt_caching:
                converted_msgs.append(
                    AIMessage(
                        content=[
                            {
                                "text": content,
                                "type": "text",
                                "cache_control": {"type": "ephemeral"},
                            }
                        ]
                    )
                )
            elif content != "":
                converted_msgs.append(AIMessage(content=content))
        else:
            raise ValueError(f"Unsupported role: {role}")

    return converted_msgs


def langgraph_msgs_to_json(messages: List) -> Dict:
    new_messages = []
    for message in messages:
        if isinstance(message, BaseMessage):
            msg_dict = message_to_dict(message)
            new_messages.append(msg_dict)
        elif isinstance(message, list):
            inner_messages = []
            for inner_message in message:
                if isinstance(inner_message, BaseMessage):
                    inner_messages.append(message_to_dict(inner_message))
                else:
                    inner_messages.append(inner_message)
            new_messages.append(inner_messages)
        else:
            new_messages.append(message)
    return new_messages


def convert_nested_structure(obj: Any) -> Any:
    """
    Recursively convert BaseMessage objects in nested dictionaries and lists.
    Always returns a new object without modifying the original.
    Also handles special cases like dict_keys and functools.partial.

    Args:
        obj: Any object that might contain BaseMessage objects

    Returns:
        A new object with all BaseMessage objects converted to dictionaries
    """
    if isinstance(obj, BaseMessage):
        return message_to_dict(obj)
    elif isinstance(obj, dict):
        return {key: convert_nested_structure(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_nested_structure(item) for item in obj]
    else:
        return obj


class LangGraphEventEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseMessage):
            # 將 BaseMessage 轉換為可序列化的 dict
            return message_to_dict(obj)
        # 處理其他不可序列化物件，略過或轉為簡單表示
        try:
            return super().default(obj)
        except:
            return str(obj)


def langgraph_event_to_json(event: Dict) -> str:
    """
    Convert a LangGraph event to JSON string, handling all nested BaseMessage objects.

    Args:
        event: Dictionary containing LangGraph event data

    Returns:
        JSON string representation of the event
    """
    # 直接使用 convert_nested_structure 轉換，不需要先 deepcopy
    # 因為 convert_nested_structure 已經會創建新物件
    # new_event = convert_nested_structure(event)
    return json.dumps(event, ensure_ascii=False, cls=LangGraphEventEncoder)


def extract_token_usage_from_state(
    state: Dict[str, Any], possible_model_name: Optional[str] = None
) -> TokenUsage:
    """
    從 state 中提取並整理 token usage 資訊，轉換成 TokenUsage 格式

    Args:
        state: Graph state dictionary
        possible_model_name: 可能的 model name，如果message 有找到，會使用 message 的 model name，否則會使用 possible_model_name

    Returns:
        TokenUsage object containing structured token usage information
    """
    try:
        nodes_usage = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        import pathlib

        # current_dir = pathlib.Path(__file__).parent
        # with open(current_dir / "messages.json", "w", encoding="utf-8") as f:
        #     json_messages = {"messages": []}
        #     for i, message in enumerate(state["messages"]):
        #         if not isinstance(message, dict):
        #             message = message_to_dict(message)
        #         json_messages["messages"].append(message)
        #     json.dump(json_messages, f, ensure_ascii=False, indent=2, sort_keys=True)

        # 檢查 messages 是否存在
        if "messages" in state:
            messages = state["messages"]
            # write messages to file
            for i, message in enumerate(messages):
                if not isinstance(message, dict):
                    message = message_to_dict(message)

                # 檢查 usage_metadata 是否在 data 中
                usage_metadata = None
                if isinstance(message.get("data"), dict):
                    usage_metadata = message["data"].get("usage_metadata")
                elif "usage_metadata" in message:
                    usage_metadata = message["usage_metadata"]

                if usage_metadata:
                    node_name = f"message_{i}"
                    if message.get("data", {}).get("id"):
                        node_name = message["data"]["id"]
                    elif message.get("id"):
                        node_name = message["id"]

                    # 提取 model_name
                    model_name = None
                    if (
                        message.get("data", {})
                        .get("response_metadata", {})
                        .get("model_name")
                    ):
                        model_name = message["data"]["response_metadata"]["model_name"]
                    elif message.get("response_metadata", {}).get("model_name"):
                        model_name = message["response_metadata"]["model_name"]
                    if not model_name:
                        model_name = possible_model_name

                    # 提取 tool_calls 資訊
                    tools = []
                    if message.get("data", {}).get("tool_calls"):
                        for tool_call in message["data"]["tool_calls"]:
                            tools.append(
                                ToolUsage(
                                    tool_name=tool_call["name"],
                                    input_tokens=0,
                                    output_tokens=0,
                                    total_tokens=0,
                                )
                            )
                    elif message.get("tool_calls"):
                        for tool_call in message["tool_calls"]:
                            tools.append(
                                ToolUsage(
                                    tool_name=tool_call["name"],
                                    input_tokens=0,
                                    output_tokens=0,
                                    total_tokens=0,
                                )
                            )

                    node_usage = NodeUsage(
                        node_name=node_name,
                        model_name=model_name,
                        input_tokens=usage_metadata.get("input_tokens", 0),
                        output_tokens=usage_metadata.get("output_tokens", 0),
                        total_tokens=usage_metadata.get("total_tokens", 0),
                        tools=tools if tools else None,
                    )

                    # 如果有 input_token_details，加入到 metadata
                    if "input_token_details" in usage_metadata:
                        node_usage.metadata = {
                            "input_token_details": usage_metadata["input_token_details"]
                        }

                    nodes_usage.append(node_usage)
                    total_input_tokens += node_usage.input_tokens
                    total_output_tokens += node_usage.output_tokens
                    total_tokens += node_usage.total_tokens

        # 遍歷 state 中的其他 node
        for key, value in state.items():
            if (
                isinstance(value, dict)
                and "usage_metadata" in value
                and key != "messages"
            ):
                node_usage = NodeUsage(
                    node_name=key,
                    input_tokens=value["usage_metadata"].get("input_tokens", 0),
                    output_tokens=value["usage_metadata"].get("output_tokens", 0),
                    total_tokens=value["usage_metadata"].get("total_tokens", 0),
                )

                # 如果有 tool usage 資訊，也加入
                if "tools_usage" in value["usage_metadata"]:
                    tools = []
                    for tool_name, tool_usage in value["usage_metadata"][
                        "tools_usage"
                    ].items():
                        tools.append(
                            ToolUsage(
                                tool_name=tool_name,
                                input_tokens=tool_usage.get("input_tokens", 0),
                                output_tokens=tool_usage.get("output_tokens", 0),
                                total_tokens=tool_usage.get("total_tokens", 0),
                                metadata=tool_usage.get("metadata", None),
                            )
                        )
                    node_usage.tools = tools

                nodes_usage.append(node_usage)
                total_input_tokens += node_usage.input_tokens
                total_output_tokens += node_usage.output_tokens
                total_tokens += node_usage.total_tokens

        # 即使沒有找到任何 token usage 資訊，也返回一個空的 TokenUsage
        return TokenUsage(
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_tokens=total_tokens,
            nodes=nodes_usage,
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"Error extracting token usage: {str(e)}")
        # 發生錯誤時返回空的 TokenUsage
        return TokenUsage(
            total_input_tokens=0,
            total_output_tokens=0,
            total_tokens=0,
            nodes=[],
        )
