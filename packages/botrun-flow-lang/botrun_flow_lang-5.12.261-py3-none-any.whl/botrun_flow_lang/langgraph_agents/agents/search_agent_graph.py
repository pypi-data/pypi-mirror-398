from datetime import datetime
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage

from langgraph.graph import MessagesState

from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver

# from langchain_anthropic import ChatAnthropic
# from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph, START, END

from langchain_core.language_models.chat_models import ChatGenerationChunk
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables.config import (
    ensure_config,
    get_async_callback_manager_for_config,
    RunnableConfig,
)

from botrun_flow_lang.langgraph_agents.agents.util.perplexity_search import (
    respond_with_perplexity_search,
)


import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# configure logging to show timestamp and level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

REQUIREMENT_NODE = "requirement_node"
ADD_REQUIREMENT_TOOL_MESSAGE_NODE = "add_requirement_tool_message"
SEARCH_NODE = "search_node"
RELATED_NODE = "related_node"
NORMAL_CHAT_NODE = "normal_chat_node"


REQUIREMENT_PROMPT_TEMPLATE = """
妳是臺灣人，回答要用臺灣繁體中文正式用語，需要的時候也可以用英文，可以親切，但不能隨便輕浮。在使用者合理的要求下請盡量配合他的需求，不要隨便拒絕
你要參考以下的 <原系統提示工程> 來判斷是否需要上網搜尋，你會參考<原系統提示工程>的範圍，超過此範圍，就不會上網搜尋，可以參考 <範例1>，<範例2>。
你的任務就是要判斷：
- 是否要幫使用者上網搜尋(有/沒有)

<範例1>
使用者提問：可以幫我寫python遞迴的程式嗎？
系統提示工程：你會幫忙找政府的津貼
思考：因為寫程式跟津貼無關，因此我不會回覆跟程式有關的內容。
回覆：我無法處理你的需求
</範例1>

<範例2>
使用者提問：可以幫我寫一個 COSTAR 的新聞稿嗎？
系統提示工程：你會幫忙找政府的津貼
思考：因為寫新聞稿跟津貼無關，因此我不會回覆跟寫新聞稿有關的內容。
回覆：我無法處理你的需求
</範例2>

其它有搜尋需求的範例：
- 留學獎學金可以申請多少？
- 我上個月十月剛從馬偕醫院離職，我可以領勞保生育補助嗎
- 請問我有個兩歲的孩子，可以領育兒補助到幾歲？

其它沒有需求的範例：
- hi
- 你好
- 我是一個人
- 你叫什麼名字?
- 你今年幾歲?
- 你住在哪裡?
- 你喜歡吃什麼?
- 你喜歡做什麼?

請遵守以下規則：
- 瞭解使用者「有」需求之後，你不會跟他說類似「讓我先確認您是否有提出具體的需求。」、「需要更多細節」、「讓我先確認這個需求。」、「讓我先確認一下您是否已經提出具體的需求」、「我需要先了解一下您的情況。」的句子，你只會說「已經收到他的oo需求，讓我來處理」，但是你不會真的回覆。
- 你不會直接回覆使用者的需求，你只會說已經收到，會開始幫他研究。
- 你不會說任何有關「讓我先確認您是否有提出具體的需求。」、「讓我先確認您是否已經提出明確的需求」, 「讓我確認一下您目前是否有任何具體的需求。」的類似句子，如果你判斷他沒有提出需求，就直接先跟他聊天。
- 你不會跟使用者要更多的資訊

"""

default_search_prompt = """
001 你只會使用臺灣人習慣的語詞和繁體中文，採用正式但親和的語氣，以維護專業性並表達尊重。
002 妳會保持溫暖且親切的語氣，溫暖人心的護理師大姊姊，讓使用者在溝通時感受到支援和關愛。
003 妳會運用同理心來理解使用者的處境，特別是在討論敏感話題（如經濟困難）時，以謹慎和關懷的態度進行應，讓使用者感受到被傾聽和理解。 
004 請你使用清晰的格式呈現資訊，如項目符號或編號列表，以提高可讀性。 
005 請你在結尾附上參考來源，包含參考來源的名稱，以及參考來源的hyperlinks，以利使用者查詢。
"""

search_prompt = """
現在的西元時間：{western_date}
現在的民國時間：{taiwan_date}

{prompt}
"""

DEFAULT_RELATED_PROMPT = """
你是一個專業的助手，請根據使用者的原始問題以及之前的回答內容，提供 3-5 個相關的後續問題建議。
這些問題應該：
1. 與原始問題和回答內容相關
2. 能夠幫助使用者更深入了解相關的補助或福利
3. 涵蓋不同面向，但都要與福利補助有關
4. 使用繁體中文提問
5. 每個問題都要簡潔明瞭，不超過 30 個字

"""

related_question_text = """

使用者的原始問題是：
{original_question}

之前的回答內容是：
{previous_response}

請提供相關的後續問題建議。
"""

NORMAL_CHAT_PROMPT_TEXT = """
妳是臺灣人，回答要用臺灣繁體中文正式用語，需要的時候也可以用英文，可以親切、但不能隨便輕浮。在使用者合理的要求下請盡量配合他的需求，不要隨便拒絕
你本來是要參考以下的 <原系統提示工程> 來回答問題，但是因為判斷不需要上網搜尋，所以你可以直接回覆使用者，你還是會參考<系統提示工程>的範圍，超過此範圍，你會跟使用者說無法回覆，但是不會按照<系統提示工程>的格式來回覆，可以參考 <範例1>，<範例2>。

<範例1>
使用者提問：可以幫我寫python遞迴的程式嗎？
系統提示工程：你會幫忙找政府的津貼
思考：因為寫程式跟津貼無關，因此我不會回覆跟程式有關的內容。
回覆：我無法處理你的需求
</範例1>

<範例2>
使用者提問：可以幫我寫一個 COSTAR 的新聞稿嗎？
系統提示工程：你會幫忙找政府的津貼
思考：因為寫新聞稿跟津貼無關，因此我不會回覆跟寫新聞稿有關的內容。
回覆：我無法處理你的需求
</範例2>
"""

DEFAULT_MODEL_NAME = "gemini-2.5-flash"


def limit_messages_with_user_first(filtered_messages):
    """
    限制消息數量並確保第一個是用戶消息，達到兩個目的：
    1. 確保第一個消息是用戶消息（如果存在用戶消息）
    2. 限制返回的消息數量，避免輸入過長

    如果消息超過10個，先取最後10個，然後確保第一個是用戶消息
    如果第一個不是用戶消息，就往前多取，直到找到用戶消息
    """
    if len(filtered_messages) > 10:
        # 先取最後10個消息
        last_10_messages = filtered_messages[-10:]

        # 如果第一個已經是用戶消息，則直接使用最後10個
        if isinstance(last_10_messages[0], HumanMessage):
            return last_10_messages
        else:
            # 如果第一個不是用戶消息，就往前尋找用戶消息
            # 計算起始索引，從個數中減去10
            start_index = len(filtered_messages) - 10

            # 往前尋找用戶消息
            while start_index > 0:
                start_index -= 1
                # 檢查往前一個消息是否為用戶消息
                if isinstance(filtered_messages[start_index], HumanMessage):
                    # 找到用戶消息，取從這個索引開始的消息
                    return filtered_messages[start_index:]

            # 如果往前找到第一個位置依然沒有找到用戶消息，則保持原樣使用最後10個
            if start_index == 0 and not isinstance(filtered_messages[0], HumanMessage):
                return filtered_messages[-10:]

    # 如果消息不超過10個，直接返回原列表
    return filtered_messages


def get_requirement_messages(messages, config):
    # 過濾掉最後的 assistant 消息
    filtered_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            filtered_messages.append(msg)
        elif isinstance(msg, AIMessage) and not msg.tool_calls:
            # 只保留不含 tool_calls 的 AI 消息
            filtered_messages.append(msg)

    # 確保最後一條消息是 HumanMessage
    if filtered_messages and not isinstance(filtered_messages[-1], HumanMessage):
        filtered_messages.pop()

    # 縮短消息列表並確保第一個消息是用戶消息
    filtered_messages = limit_messages_with_user_first(filtered_messages)

    logging.info(
        f"[SearchAgentGraph:get_requirement_messages] return: {[SystemMessage(content=REQUIREMENT_PROMPT_TEMPLATE) + filtered_messages]}"
    )
    requirement_prompt = config["configurable"]["requirement_prompt"]
    requirement_prompt += """
    <原系統提示工程>
    {system_prompt}
    </原系統提示工程>
    """.format(
        system_prompt=config["configurable"]["search_prompt"]
    )

    return [SystemMessage(content=requirement_prompt)] + filtered_messages


def format_dates(dt):
    """
    將日期時間格式化為西元和民國格式
    西元格式：yyyy-mm-dd hh:mm:ss
    民國格式：(yyyy-1911)-mm-dd hh:mm:ss
    """
    western_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    taiwan_year = dt.year - 1911
    taiwan_date = f"{taiwan_year}-{dt.strftime('%m-%d %H:%M:%S')}"

    return {"western_date": western_date, "taiwan_date": taiwan_date}


def get_search_messages(state, config):
    filtered_messages = []

    # 取得當前時間並格式化
    now = datetime.now()
    dates = format_dates(now)

    for m in state["messages"]:
        if isinstance(m, HumanMessage):
            filtered_messages.append(m)
        elif isinstance(m, AIMessage) and not m.tool_calls:
            filtered_messages.append(m)

    # 縮短消息列表並確保第一個消息是用戶消息
    filtered_messages = limit_messages_with_user_first(filtered_messages)

    return [
        SystemMessage(
            content=search_prompt.format(
                western_date=dates["western_date"],
                taiwan_date=dates["taiwan_date"],
                prompt=config["configurable"]["search_prompt"],
            )
        )
    ] + filtered_messages


class RequirementPromptInstructions(BaseModel):
    has_requirement: bool


class RelatedQuestionsInstructions(BaseModel):
    related_questions: list[str]


# llm_requirement = ChatAnthropic(
#     model="claude-3-7-sonnet-latest",
#     temperature=0,
# )

# llm_with_requirement_tool = llm_requirement.bind_tools(
#     [RequirementPromptInstructions],
# )

# llm_normal_chat = ChatOpenAI(
#     model="gpt-4o-mini",
#     temperature=0.7,  # 使用較高的溫度以獲得更多樣化的建議
# )

# llm_related = ChatAnthropic(
#     model="claude-3-7-sonnet-latest",
#     temperature=0.7,  # 使用較高的溫度以獲得更多樣化的建議
# )
# llm_with_related_tool = llm_related.bind_tools(
#     [RelatedQuestionsInstructions], tool_choice="RelatedQuestionsInstructions"
# )


def remove_empty_messages(messages):
    def _get_content(msg):
        if isinstance(msg, dict):
            return str(msg.get("content", ""))
        return str(getattr(msg, "content", ""))

    return [msg for msg in messages if _get_content(msg).strip() != ""]


def clean_msg_for_search(messages):
    """
    - 移除 content 為空字串 / 空白 的訊息
    - 合併連續同角色 (只保留區段中的最後一筆)
    - 最後一筆一定為 user，否則往前尋找最近的 user
    """
    cleaned_msg = []

    def is_empty(msg):
        return str(msg.get("content", "")).strip() == ""

    for msg in messages:
        if is_empty(msg):
            continue
        if cleaned_msg and cleaned_msg[-1]["role"] == msg["role"]:
            cleaned_msg[-1] = msg
        else:
            cleaned_msg.append(msg)

    while cleaned_msg and cleaned_msg[-1]["role"] != "user":
        cleaned_msg.pop()

    return cleaned_msg


def get_requirement_model():
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI

    if os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_BASE_URL"):
        return ChatOpenAI(
            model=f"google/{DEFAULT_MODEL_NAME}",
            temperature=0,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        )
    else:
        return ChatGoogleGenerativeAI(
            model=DEFAULT_MODEL_NAME,
            temperature=0,
        )
    # llm_requirement = ChatAnthropic(
    #     model="claude-3-7-sonnet-latest",
    #     temperature=0,
    # )


def requirement_node(state, config):
    logging.info("[SearchAgentGraph:requirement_node] Enter node requirement_node")

    messages = get_requirement_messages(state["messages"], config)
    logging.info(
        f"[SearchAgentGraph:requirement_node] Get requirement messages:{messages}"
    )

    # 確保最後一條消息是 HumanMessage
    if not messages or not isinstance(messages[-1], HumanMessage):
        logging.info(
            f"[SearchAgentGraph:requirement_node] No requirement messages, return original messages"
        )
        return {"messages": state["messages"]}

    llm_requirement = get_requirement_model()
    from trustcall import create_extractor

    llm_with_requirement_tool = create_extractor(
        llm_requirement,
        tools=[RequirementPromptInstructions],
        tool_choice="RequirementPromptInstructions",
    )
    # llm_with_requirement_tool = llm_requirement.bind_tools(
    #     [RequirementPromptInstructions],
    # )
    # logging.info(f"[SearchAgentGraph:requirement_node] messages: {messages}")
    messages = remove_empty_messages(messages)
    logging.info(f"[SearchAgentGraph:requirement_node] messages len:{len(messages)}")
    response = llm_with_requirement_tool.invoke(messages)
    return response


async def search_with_perplexity_stream(state, config):
    messages = get_search_messages(state, config)
    logging.info(
        f"[SearchAgentGraph:search_with_perplexity_stream] messages len:{len(messages)}"
    )
    # 確保配置正確
    config = ensure_config(config | {"tags": ["agent_llm"]})
    callback_manager = get_async_callback_manager_for_config(config)

    # 開始 LLM 運行
    model_name_cfg = config["configurable"]["model_name"]
    llm_run_managers = await callback_manager.on_chat_model_start(
        {"name": f"perplexity/{model_name_cfg}"},
        [messages],
    )

    # llm_run_managers = await callback_manager.on_chat_model_start({}, [messages])
    llm_run_manager = llm_run_managers[0]

    # 將 messages 轉換為 Gemini 格式
    messages_for_llm = []
    input_content = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            messages_for_llm.append({"role": "user", "content": msg.content})
            input_content = msg.content
        elif isinstance(msg, AIMessage) and not msg.tool_calls:
            if (
                isinstance(msg.content, list)
                and isinstance(msg.content[0], dict)
                and msg.content[0].get("text", "")
            ):
                messages_for_llm.append(
                    {"role": "assistant", "content": msg.content[0].get("text", "")}
                )
            else:
                messages_for_llm.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, SystemMessage):
            if len(messages_for_llm) > 0 and messages_for_llm[0]["role"] != "system":
                messages_for_llm.insert(0, {"role": "system", "content": msg.content})
            elif len(messages_for_llm) > 0 and messages_for_llm[0]["role"] == "system":
                messages_for_llm[0]["content"] = msg.content
            elif len(messages_for_llm) == 0:
                messages_for_llm.append({"role": "system", "content": msg.content})

    messages_for_llm = clean_msg_for_search(messages_for_llm)
    logging.info(
        f"[SearchAgentGraph:search_with_perplexity_stream] messages_for_llm:{messages_for_llm}"
    )
    full_response = ""
    try:
        async for event in respond_with_perplexity_search(
            input_content,
            config["configurable"]["user_prompt_prefix"],
            messages_for_llm,
            config["configurable"]["domain_filter"],
            config["configurable"]["stream"],
            config["configurable"]["model_name"],
        ):
            # 將回應包裝成 ChatGenerationChunk 以支援 stream_mode="messages"
            chunk = ChatGenerationChunk(
                message=AIMessageChunk(
                    content=event.chunk,
                )
            )

            # 使用 callback manager 處理新的 token
            await llm_run_manager.on_llm_new_token(
                event.chunk,
                chunk=chunk,
            )
            full_response += event.chunk

            if event.raw_json:
                last_event_json = event.raw_json

    except Exception as e:
        await llm_run_manager.on_llm_error(e)
        raise
    finally:
        # 確保on_chat_model_end事件被觸發
        from langchain_core.outputs import ChatGeneration, LLMResult

        usage_raw = last_event_json.get("usage", {})
        usage_metadata = {
            "input_tokens": usage_raw.get("prompt_tokens", 0),
            "output_tokens": usage_raw.get("completion_tokens", 0),
            "total_tokens": usage_raw.get(
                "total_tokens",
                usage_raw.get("prompt_tokens", 0)
                + usage_raw.get("completion_tokens", 0),
            ),
            "input_token_details": {},
            "output_token_details": {},
        }
        model_name = last_event_json.get("model", "")

        ai_msg = AIMessage(
            content=full_response,
            response_metadata={"finish_reason": "tool_calls", "model_name": model_name},
            usage_metadata=usage_metadata,
        )

        generation = ChatGeneration(message=ai_msg)

        llm_result = LLMResult(
            generations=[[generation]],
            llm_output={"usage_metadata": usage_metadata},
        )

        await llm_run_manager.on_llm_end(llm_result)

    if full_response:
        return {"messages": [ai_msg]}
    else:
        return {}


async def search_with_gemini_grounding(state, config):
    # 放到要用的時候才 import，不然loading 會花時間
    from botrun_flow_lang.langgraph_agents.agents.util.gemini_grounding import (
        respond_with_gemini_grounding,
    )

    messages = get_search_messages(state, config)

    # 確保配置正確
    config = ensure_config(config | {"tags": ["agent_llm"]})
    callback_manager = get_async_callback_manager_for_config(config)

    # 開始 LLM 運行
    llm_run_managers = await callback_manager.on_chat_model_start({}, [messages])
    llm_run_manager = llm_run_managers[0]

    # 將 messages 轉換為 Gemini 格式
    messages_for_llm = []
    input_content = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            messages_for_llm.append({"role": "user", "content": msg.content})
            input_content = msg.content
        elif isinstance(msg, AIMessage) and not msg.tool_calls:
            if (
                isinstance(msg.content, list)
                and isinstance(msg.content[0], dict)
                and msg.content[0].get("text", "")
            ):
                messages_for_llm.append(
                    {"role": "assistant", "content": msg.content[0].get("text", "")}
                )
            else:
                messages_for_llm.append({"role": "assistant", "content": msg.content})

    full_response = ""
    async for event in respond_with_gemini_grounding(input_content, messages_for_llm):
        # 將回應包裝成 ChatGenerationChunk 以支援 stream_mode="messages"
        chunk = ChatGenerationChunk(
            message=AIMessageChunk(
                content=event.chunk,
            )
        )

        # await adispatch_custom_event(
        #     "on_custom_event",
        #     {"chunk": event.chunk},
        #     config=config,  # <-- propagate config
        # )
        # 使用 callback manager 處理新的 token
        await llm_run_manager.on_llm_new_token(
            event.chunk,
            chunk=chunk,
        )
        full_response += event.chunk

    if full_response:
        return {"messages": [AIMessage(content=full_response)]}
    else:
        return {}


async def search_node(state, config: RunnableConfig):
    start = time.time()
    logging.info("[SearchAgentGraph:search_node] Enter node search_node")

    t1 = time.time()
    for key in DEFAULT_SEARCH_CONFIG.keys():
        if key not in config["configurable"]:
            config["configurable"][key] = DEFAULT_SEARCH_CONFIG[key]

    search_vendor = config["configurable"]["search_vendor"]
    logging.info(
        f"[SearchAgentGraph:search_node] Check configurable settings, elapsed {time.time() - t1:.3f}s"
    )

    t2 = time.time()
    if search_vendor == SEARCH_VENDOR_PLEXITY:
        result = await search_with_perplexity_stream(state, config)
    else:
        result = await search_with_gemini_grounding(state, config)
    logging.info(
        f"[SearchAgentGraph:search_node] Completed search operation, elapsed {time.time() - t2:.3f}s"
    )

    logging.info(
        f"[SearchAgentGraph:search_node] Exit node search_node, elapsed {time.time() - start:.3f}s"
    )
    return result


def get_related_messages(state, config):
    """
    獲取用於生成相關問題的消息列表
    """
    # 只保留人類消息和不含工具調用的 AI 消息
    filtered_messages = []
    previous_question = ""
    previous_response = ""

    for m in state["messages"]:
        if isinstance(m, HumanMessage):
            previous_question = m.content
            filtered_messages.append(m)
        elif isinstance(m, AIMessage) and not m.tool_calls:
            previous_response = m.content
            filtered_messages.append(m)
        elif isinstance(m, ToolMessage):
            filtered_messages.append(AIMessage(content=f"Tool Result: {m.content}"))

    # 縮短消息列表並確保第一個消息是用戶消息
    filtered_messages = limit_messages_with_user_first(filtered_messages)

    # 驗證 related_prompt 格式
    related_prompt = config["configurable"]["related_prompt"]
    related_prompt += related_question_text

    # 添加用於生成相關問題的提示
    filtered_messages.append(
        HumanMessage(
            content=related_prompt.format(
                original_question=previous_question,
                previous_response=previous_response,
            )
        )
    )

    return filtered_messages


def get_normal_chat_messages(state, config):
    """
    獲取用於生成相關問題的消息列表
    """
    # 只保留人類消息和不含工具調用的 AI 消息
    filtered_messages = []

    # 加入 system message
    normal_chat_prompt = config["configurable"]["normal_chat_prompt"]
    normal_chat_prompt += """
    <原系統提示工程>
    {system_prompt}
    </原系統提示工程>
""".format(
        system_prompt=config["configurable"]["search_prompt"]
    )

    filtered_messages.append(SystemMessage(content=normal_chat_prompt))

    for m in state["messages"]:
        if isinstance(m, HumanMessage):
            filtered_messages.append(m)
        elif isinstance(m, AIMessage) and not m.tool_calls:
            filtered_messages.append(m)
        elif isinstance(m, ToolMessage):
            filtered_messages.append(AIMessage(content=f"Tool Result: {m.content}"))

    system_message = filtered_messages[0]
    # 縮短消息列表並確保第一個消息是用戶消息
    filtered_messages = limit_messages_with_user_first(filtered_messages)

    return [system_message] + filtered_messages


def get_related_model():
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI

    if os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_BASE_URL"):
        return ChatOpenAI(
            model=f"google/{DEFAULT_MODEL_NAME}",
            temperature=0,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        )
    else:
        return ChatGoogleGenerativeAI(
            model=DEFAULT_MODEL_NAME,
            temperature=0,
        )


def related_node(state, config: RunnableConfig):
    logging.info("[SearchAgentGraph:related_node] Enter node related_node")
    for key in DEFAULT_SEARCH_CONFIG.keys():
        if key not in config["configurable"]:
            config["configurable"][key] = DEFAULT_SEARCH_CONFIG[key]

    messages = get_related_messages(state, config)
    # 　放到要用的時候才 import，不然loading 會花時間
    # from langchain_anthropic import ChatAnthropic
    llm_related = get_related_model()
    # llm_related = ChatAnthropic(
    #     model="claude-3-7-sonnet-latest",
    #     temperature=0.7,  # 使用較高的溫度以獲得更多樣化的建議
    # )
    llm_with_related_tool = llm_related.bind_tools(
        [RelatedQuestionsInstructions], tool_choice="RelatedQuestionsInstructions"
    )

    messages = remove_empty_messages(messages)
    response = llm_with_related_tool.invoke(messages)

    if response.tool_calls:
        result = {
            "messages": [
                response,
                ToolMessage(
                    content=str(response.tool_calls[0]["args"]["related_questions"]),
                    tool_call_id=response.tool_calls[0]["id"],
                ),
            ],
            "related_questions": response.tool_calls[0]["args"]["related_questions"],
        }
        return result
    return {"messages": [response]}


def get_normal_chat_model():
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI

    if os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_BASE_URL"):
        return ChatOpenAI(
            model="google/gemini-2.5-flash",
            temperature=0,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        )
        # return ChatOpenAI(
        #     model="openai/gpt-4.1-mini",
        #     temperature=0.7,  # 使用較高的溫度以獲得更多樣化的建議
        #     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        #     openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        # )
    else:
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
        )
        # return ChatOpenAI(
        #     model="gpt-4.1-mini-2025-04-14",
        #     temperature=0.7,
        # )


def normal_chat_node(state, config: RunnableConfig):
    logging.info("[SearchAgentGraph:normal_chat_node] Enter node normal_chat_node")
    for key in DEFAULT_SEARCH_CONFIG.keys():
        if key not in config["configurable"]:
            config["configurable"][key] = DEFAULT_SEARCH_CONFIG[key]

    messages = get_normal_chat_messages(state, config)

    # 　放到要用的時候才 import，不然loading 會花時間
    # from langchain_openai import ChatOpenAI

    llm_normal_chat = get_normal_chat_model()
    messages = remove_empty_messages(messages)
    response = llm_normal_chat.invoke(messages)
    return {
        "messages": [response],
        "related_questions": [],
    }


def get_requirement_next_state(state):
    start = time.time()
    logging.info(
        "[SearchAgentGraph:get_requirement_next_state] Enter node get_requirement_next_state"
    )
    messages = state["messages"]
    if isinstance(messages[-1], AIMessage) and messages[-1].tool_calls:
        tool_call = messages[-1].tool_calls[0]
        if tool_call["args"].get("has_requirement", False):
            result = ADD_REQUIREMENT_TOOL_MESSAGE_NODE
        else:
            result = NORMAL_CHAT_NODE
    elif not isinstance(messages[-1], HumanMessage):
        result = END
    else:
        result = END
    logging.info(
        f"[SearchAgentGraph:get_requirement_next_state] Exit node get_requirement_next_state, elapsed {time.time() - start:.3f}s"
    )
    return result


class SearchState(MessagesState):
    related_questions: list[str] = []


SEARCH_VENDOR_PLEXITY = "perplexity"
SEARCH_VENDOR_GOOGLE = "google"
DEFAULT_SEARCH_CONFIG = {
    "search_prompt": default_search_prompt,
    "model_name": "sonar-reasoning-pro",
    "requirement_prompt": REQUIREMENT_PROMPT_TEMPLATE,
    "related_prompt": DEFAULT_RELATED_PROMPT,
    "normal_chat_prompt": NORMAL_CHAT_PROMPT_TEXT,
    "search_vendor": SEARCH_VENDOR_PLEXITY,
    "domain_filter": [],
    "user_prompt_prefix": "",
    "stream": True,
}


class SearchAgentGraph:
    def __init__(self, memory: BaseCheckpointSaver = None):
        self.memory = memory if memory is not None else MemorySaver()
        self._initialize_graph()

    def _initialize_graph(self):
        workflow = StateGraph(SearchState)
        workflow.add_node(REQUIREMENT_NODE, requirement_node)

        @workflow.add_node
        def add_requirement_tool_message(state: MessagesState):
            start = time.time()
            logging.info(
                "[SearchAgentGraph:add_requirement_tool_message] Enter node add_requirement_tool_message"
            )
            result = {
                "messages": [
                    ToolMessage(
                        content=f"""
                        使用者有提出需求
                        """,
                        tool_call_id=state["messages"][-1].tool_calls[0]["id"],
                    )
                ],
                "has_requirement": True,
            }
            logging.info(
                f"[SearchAgentGraph:add_requirement_tool_message] Exit node add_requirement_tool_message, elapsed {time.time() - start:.3f}s"
            )
            return result

        workflow.add_node(SEARCH_NODE, search_node)
        workflow.add_node(RELATED_NODE, related_node)
        workflow.add_node(NORMAL_CHAT_NODE, normal_chat_node)
        workflow.add_edge(START, REQUIREMENT_NODE)
        workflow.add_conditional_edges(
            REQUIREMENT_NODE,
            get_requirement_next_state,
            [ADD_REQUIREMENT_TOOL_MESSAGE_NODE, NORMAL_CHAT_NODE, END],
        )
        workflow.add_edge(ADD_REQUIREMENT_TOOL_MESSAGE_NODE, SEARCH_NODE)

        workflow.add_edge(SEARCH_NODE, RELATED_NODE)
        workflow.add_edge(NORMAL_CHAT_NODE, END)
        workflow.add_edge(RELATED_NODE, END)
        self._graph = workflow.compile(checkpointer=self.memory)
        self._graph2 = workflow.compile()

    @property
    def graph(self):
        return self._graph

    @property
    def graph2(self):
        return self._graph2


search_agent_graph = SearchAgentGraph().graph2
