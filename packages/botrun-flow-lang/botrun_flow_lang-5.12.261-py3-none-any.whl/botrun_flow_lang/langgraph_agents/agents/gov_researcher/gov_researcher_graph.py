import os
import time
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables.config import RunnableConfig

from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver

from botrun_flow_lang.langgraph_agents.agents.util.perplexity_search import (
    respond_with_perplexity_search,
)
from botrun_flow_lang.langgraph_agents.agents.util.tavily_search import (
    respond_with_tavily_search,
)
from botrun_flow_lang.langgraph_agents.agents.util.model_utils import (
    get_model_instance,
)

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 節點名稱常數
TOPIC_DECOMPOSITION_NODE = "topic_decomposition_node"
PARALLEL_SEARCH_NODE = "parallel_search_node"
REASONING_ANALYSIS_NODE = "reasoning_analysis_node"
COMPUTATION_VERIFICATION_NODE = "computation_verification_node"
HALLUCINATION_VERIFICATION_NODE = "hallucination_verification_node"
SUMMARY_RESPONSE_NODE = "summary_response_node"

# 預設 General Guide
DEFAULT_GENERAL_GUIDE = """
<General Guide>
妳回應時會採用臺灣繁體中文，並且避免中國大陸用語
妳絕對不會使用 markdown 語法回應
但是你絕對不會使用 ** 或者 ### ，各種類型的 markdown 語法都禁止使用
如果要比較美觀排版的話，妳可以搭配使用 emoji or 純文字 or 斷行 or 空白 來展示你想講的
每一個 step 的前面增添適當斷行
每個分段的標題「前面」要增添適當 emoji （這個 emoji 挑選必須跟動態情境吻合）
</General Guide>
"""

# 題目拆解提示詞模板
TOPIC_DECOMPOSITION_PROMPT = """
{general_guide}

你是一位專業的政府研究分析師，負責將使用者的政府相關問題進行智能分析和拆解。

你的任務：
1. 分析用戶提問的複雜度
2. 如果是單純問題：轉化為更細緻的單一子題目
3. 如果是複雜問題：拆解為多個子題目以確保回答的準確性

重要考量因素：
- 考量使用者的身份、年齡、性別、居住地等個人條件
- 考量時間性：政策、法規的生效日期、申請期限、變更時程
- 考量地域性：中央 vs 地方政府、縣市差異、區域特殊規定
- 考量適用性：不同身份別、不同條件下的差異化規定

請將用戶問題拆解為 1-5 個具體的子題目，每個子題目都應該：
- 明確且具體，但涵蓋全面性考量
- 可以透過搜尋找到答案
- 與政府政策、法規、程序相關
- 盡量包含多個思考面向：時效性、地域性、身份差異、適用條件等
- 每個子題目都要設計得廣泛且深入，以獲取豐富的搜尋資訊
- 使用繁體中文表達

**重要指導原則：**
雖然子題目數量限制在 1-5 個，但每個子題目都要做全面性的考量，
盡量把思考面設定廣泛，這樣搜尋時才能獲得更多角度的資訊，
最終總結時就會有比較豐富的資料可以使用。

用戶問題：{user_question}

請輸出結構化的子題目列表。
"""

# 推理分析提示詞模板
REASONING_ANALYSIS_PROMPT = """
{general_guide}

你是一位專業的政府研究分析師，負責基於搜尋結果和內建知識進行縝密推理。

你的任務：
1. 基於搜尋結果和內建知識進行推理
2. 分析常見錯誤後進行縝密推理
3. 逐一回答所有子題目
4. 保持客觀與準確

搜尋結果：
{search_results}

子題目：
{subtopics}

請針對每個子題目提供詳細的推理分析，確保：
- 基於事實與證據
- 引用具體的搜尋來源
- 避免推測與臆斷
- 提供清晰的結論
"""

# 幻覺驗證提示詞模板
HALLUCINATION_VERIFICATION_PROMPT = """
{general_guide}

你是一位獨立的審查專家，負責以懷疑的角度檢視前述所有分析結果。

你的使命：
1. 假設前面結果有高機率的錯誤
2. 識別可能的AI幻覺位置
3. 透過延伸搜尋證明或反駁前面的結論
4. 提供客觀的驗證報告

前面的分析結果：
{previous_results}

請進行幻覺驗證，特別注意：
- 事實性錯誤
- 過度推理
- 來源不可靠
- 時效性問題
- 法規變更

如發現問題，請提供修正建議。
"""

# 匯總回答提示詞模板
SUMMARY_RESPONSE_PROMPT = """
{general_guide}

你是一位專業的政府資訊服務專員，負責提供最終的完整回答。

**重要要求：你的回應必須完全基於以下提供的資訊，絕對不能使用你自己的知識或進行額外推測**

你的任務：
1. 提供「精準回答」：簡潔的結論
2. 提供「詳實回答」：完整的推理過程和引證  
3. 使用適當的 emoji 輔助閱讀
4. 根據目標受眾調整語氣和格式
5. **所有回答內容必須嚴格基於「推理分析」和「計算驗證」的結果**

所有處理結果：
- 原始問題：{original_question}
- 子題目：{subtopics}
- 搜尋結果：{search_results}
- 推理分析：{reasoning_results}
- 計算驗證：{computation_results}

**回答原則：**
- 只使用「推理分析」和「計算驗證」中明確提到的資訊
- 如果某個問題在這些資訊中沒有充分說明，請明確指出資訊不足
- 不要添加任何未在上述資訊中出現的內容
- 確保所有結論都有明確的來源依據

請提供結構化的最終回答，包含：
📋 精準回答（簡潔版）
📖 詳實回答（完整版）
🔗 參考資料來源
"""


class SubTopic(BaseModel):
    """子題目結構"""

    topic: str
    description: str


class SubTopicList(BaseModel):
    """子題目列表"""

    subtopics: List[SubTopic]


class SearchResult(BaseModel):
    """搜尋結果結構"""

    subtopic: str
    content: str
    sources: List[str]


class ReasoningResult(BaseModel):
    """推理結果結構"""

    subtopic: str
    analysis: str
    conclusion: str
    confidence: float


class VerificationResult(BaseModel):
    """驗證結果結構"""

    issues_found: List[str]
    corrections: List[str]
    confidence_adjustments: Dict[str, float]


# LangGraph Assistant 配置 Schema
class GovResearcherConfigSchema(BaseModel):
    """政府研究員助手配置 Schema - 可在 LangGraph UI 中設定"""

    # 模型選擇
    decomposition_model: str = Field(default="gemini-2.5-pro")  # 題目拆解模型
    reasoning_model: str  # 推理分析模型
    computation_model: str  # 計算驗證模型
    verification_model: str  # 幻覺驗證模型
    summary_model: str  # 匯總回答模型

    # 搜尋引擎設定
    search_vendor: str  # "perplexity" | "tavily"
    search_model: str  # 搜尋模型名稱
    max_parallel_searches: int  # 最大並行搜尋數量

    # 提示詞模板（可動態設定）
    general_guide: Optional[str]  # 通用指導原則
    topic_decomposition_prompt: Optional[str]  # 題目拆解提示詞
    reasoning_analysis_prompt: Optional[str]  # 推理分析提示詞
    hallucination_verification_prompt: Optional[str]  # 幻覺驗證提示詞
    summary_response_prompt: Optional[str]  # 匯總回答提示詞


class GovResearcherState(MessagesState):
    """政府研究員 LangGraph 狀態"""

    original_question: str = ""
    decomposed_topics: List[SubTopic] = []
    search_tasks: List[SubTopic] = []
    search_results: Annotated[List[SearchResult], lambda x, y: x + y] = (
        []
    )  # 支援 fan-in 合併
    reasoning_results: List[ReasoningResult] = []
    computation_results: Optional[str] = None
    needs_computation: bool = False
    hallucination_check: Optional[VerificationResult] = None
    final_answer: str = ""
    general_guide: str = DEFAULT_GENERAL_GUIDE
    search_completed: bool = False


def format_dates(dt):
    """將日期時間格式化為西元和民國格式"""
    western_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    taiwan_year = dt.year - 1911
    taiwan_date = f"{taiwan_year}-{dt.strftime('%m-%d %H:%M:%S')}"
    return {"western_date": western_date, "taiwan_date": taiwan_date}


def get_config_value(config: RunnableConfig, key: str, default_value: Any) -> Any:
    """統一獲取配置值的輔助函數"""
    # 如果 config.get("configurable", {}).get(key, default_value) 是 None，則返回 default_value
    return config.get("configurable", {}).get(key, default_value) or default_value


def get_decomposition_model(config: RunnableConfig):
    """獲取題目拆解用的模型"""
    model_name = get_config_value(config, "decomposition_model", "gemini-2.5-pro")
    return get_model_instance(model_name, temperature=0)


def get_reasoning_model(config: RunnableConfig):
    """獲取推理分析用的模型"""
    model_name = get_config_value(config, "reasoning_model", "gemini-2.5-flash")
    return get_model_instance(model_name, temperature=0)


def get_computation_model(config: RunnableConfig):
    """獲取計算驗證用的模型"""
    model_name = get_config_value(config, "computation_model", "gemini-2.5-flash")
    return get_model_instance(model_name, temperature=0, enable_code_execution=True)


def get_verification_model(config: RunnableConfig):
    """獲取幻覺驗證用的模型"""
    model_name = get_config_value(config, "verification_model", "gemini-2.5-flash")
    return get_model_instance(model_name, temperature=0)


def get_summary_model(config: RunnableConfig):
    """獲取匯總回答用的模型"""
    model_name = get_config_value(config, "summary_model", "gemini-2.5-flash")
    return get_model_instance(model_name, temperature=0)


def get_prompt_template(
    config: RunnableConfig, prompt_key: str, default_prompt: str
) -> str:
    """獲取可配置的提示詞模板"""
    return get_config_value(config, prompt_key, default_prompt)


def topic_decomposition_node(
    state: GovResearcherState, config: RunnableConfig
) -> Dict[str, Any]:
    """Step-001: 題目拆解節點"""
    logging.info("[GovResearcherGraph:topic_decomposition_node] 開始題目拆解")

    # 獲取用戶最新問題
    user_question = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_question = msg.content
            break

    if not user_question:
        logging.warning("未找到用戶問題")
        return {"decomposed_topics": []}

    # 獲取可配置的提示詞模板
    prompt_template = get_prompt_template(
        config, "topic_decomposition_prompt", TOPIC_DECOMPOSITION_PROMPT
    )
    general_guide = get_config_value(config, "general_guide", DEFAULT_GENERAL_GUIDE)

    # 準備提示詞
    prompt = prompt_template.format(
        general_guide=general_guide,
        user_question=user_question,
    )

    # 調用模型
    model = get_decomposition_model(config)
    from trustcall import create_extractor

    extractor = create_extractor(
        model, tools=[SubTopicList], tool_choice="SubTopicList"
    )

    response = extractor.invoke([HumanMessage(content=prompt)])

    # 解析結果 - 統一處理 trustcall 的回應格式
    subtopics = []

    try:
        # 直接是 SubTopicList 實例
        if isinstance(response, SubTopicList):
            subtopics = response.subtopics
        # 有 subtopics 屬性
        elif hasattr(response, "subtopics"):
            subtopics = response.subtopics
        # trustcall 字典格式（主要情況）
        elif isinstance(response, dict):
            if "responses" in response and response["responses"]:
                first_response = response["responses"][0]
                if hasattr(first_response, "subtopics"):
                    subtopics = first_response.subtopics
            elif "subtopics" in response:
                subtopics_data = response["subtopics"]
                subtopics = [
                    SubTopic(**item) if isinstance(item, dict) else item
                    for item in subtopics_data
                ]

        logging.info(f"成功解析 {len(subtopics)} 個子題目")

    except Exception as e:
        logging.error(f"解析 trustcall 回應失敗: {e}")
        subtopics = []

    # 備選方案：使用原始問題
    if not subtopics:
        logging.warning("未能解析出子題目，使用原始問題")
        subtopics = [SubTopic(topic=user_question, description="原始問題")]

    logging.info(f"題目拆解完成，共 {len(subtopics)} 個子題目")

    # 額外的調試資訊
    for i, subtopic in enumerate(subtopics):
        logging.info(f"子題目 {i+1}: {subtopic.topic[:50]}...")  # 只顯示前50字元

    return {"original_question": user_question, "decomposed_topics": subtopics}


def search_preparation_node(
    state: GovResearcherState, config: RunnableConfig
) -> Dict[str, Any]:
    """搜尋準備節點：準備並分發搜尋任務"""
    logging.info("[GovResearcherGraph:search_preparation_node] 準備搜尋任務")

    subtopics = state.get("decomposed_topics", [])
    if not subtopics:
        logging.warning("無子題目可搜尋")
        return {"search_tasks": []}

    # 限制並行搜尋數量
    max_parallel_searches = get_config_value(config, "max_parallel_searches", 5)
    limited_subtopics = subtopics[:max_parallel_searches]

    logging.info(f"準備平行搜尋 {len(limited_subtopics)} 個子題目")

    return {"search_tasks": limited_subtopics, "search_completed": False}


async def search_subtopic_node(
    state: GovResearcherState, config: RunnableConfig
) -> Dict[str, Any]:
    """搜尋所有子題目（支援多搜尋引擎，不使用LLM）"""
    logging.info("[GovResearcherGraph:search_subtopic_node] 開始搜尋所有子題目")

    search_tasks = state.get("search_tasks", [])
    if not search_tasks:
        logging.warning("無搜尋任務")
        return {"search_results": []}

    # 獲取搜尋引擎配置
    search_vendor = get_config_value(config, "search_vendor", "tavily")
    search_model = get_config_value(config, "search_model", "sonar")
    domain_filter = get_config_value(config, "domain_filter", [])

    logging.info(f"使用搜尋服務商: {search_vendor}, 模型: {search_model}")

    # 使用 asyncio.gather 進行真正的平行搜尋（PRD要求：不使用LLM，僅搜尋API）
    async def search_single_topic(subtopic: SubTopic) -> SearchResult:
        try:
            content = ""
            sources = []
            search_query = subtopic.topic

            # 根據搜尋服務商選擇不同的搜尋服務
            if search_vendor == "tavily":
                async for event in respond_with_tavily_search(
                    search_query,
                    "",  # 無前綴
                    [{"role": "user", "content": search_query}],  # 最直接的查詢
                    domain_filter,
                    False,  # 不stream
                    search_model,
                ):
                    content += event.chunk
                    if event.raw_json and "sources" in event.raw_json:
                        sources = event.raw_json["sources"]
                    else:
                        sources = ["Tavily Search"]

            else:  # 預設使用 perplexity
                async for event in respond_with_perplexity_search(
                    search_query,
                    "",  # 無前綴
                    [{"role": "user", "content": search_query}],  # 最直接的查詢
                    domain_filter,
                    False,  # 不stream
                    search_model,
                ):
                    content += event.chunk
                    sources = ["Perplexity Search"]

            return SearchResult(
                subtopic=subtopic.topic, content=content, sources=sources
            )

        except Exception as e:
            logging.error(f"搜尋 '{subtopic.topic}' 失敗: {e}")
            return SearchResult(
                subtopic=subtopic.topic, content=f"搜尋失敗: {str(e)}", sources=[]
            )

    # 平行執行所有搜尋
    search_results = await asyncio.gather(
        *[search_single_topic(subtopic) for subtopic in search_tasks]
    )

    logging.info(f"搜尋完成，共 {len(search_results)} 個結果")

    return {"search_results": search_results, "search_completed": True}


def reasoning_analysis_node(
    state: GovResearcherState, config: RunnableConfig
) -> Dict[str, Any]:
    """Step-003: 推理分析節點"""
    logging.info("[GovResearcherGraph:reasoning_analysis_node] 開始推理分析")

    search_results = state.get("search_results", [])
    subtopics = state.get("decomposed_topics", [])

    if not search_results or not subtopics:
        logging.warning("缺少搜尋結果或子題目")
        return {"reasoning_results": []}

    # 準備搜尋結果文本
    search_text = "\n\n".join(
        [
            f"子題目: {result.subtopic}\n內容: {result.content}\n來源: {', '.join(result.sources)}"
            for result in search_results
        ]
    )

    subtopics_text = "\n".join(
        [
            f"{i+1}. {topic.topic} - {topic.description}"
            for i, topic in enumerate(subtopics)
        ]
    )

    # 獲取可配置的提示詞模板
    prompt_template = get_prompt_template(
        config, "reasoning_analysis_prompt", REASONING_ANALYSIS_PROMPT
    )
    general_guide = get_config_value(config, "general_guide", DEFAULT_GENERAL_GUIDE)

    # 準備提示詞
    prompt = prompt_template.format(
        general_guide=general_guide,
        search_results=search_text,
        subtopics=subtopics_text,
    )

    # 調用模型
    model = get_reasoning_model(config)
    response = model.invoke([HumanMessage(content=prompt)])

    # 簡化版結果解析
    reasoning_results = []
    for i, subtopic in enumerate(subtopics):
        reasoning_results.append(
            ReasoningResult(
                subtopic=subtopic.topic,
                analysis=response.content,  # 實際應該分段解析
                conclusion=f"針對 '{subtopic.topic}' 的分析結論",
                confidence=0.8,
            )
        )

    # 檢查是否需要計算驗證
    needs_computation = (
        "計算" in response.content
        or "金額" in response.content
        or "數量" in response.content
    )

    logging.info(f"推理分析完成，需要計算驗證: {needs_computation}")

    return {
        "reasoning_results": reasoning_results,
        "needs_computation": needs_computation,
    }


def computation_verification_node(
    state: GovResearcherState, config: RunnableConfig
) -> Dict[str, Any]:
    """Step-004: 計算驗證節點（條件性）"""
    logging.info("[GovResearcherGraph:computation_verification_node] 開始計算驗證")

    if not state.get("needs_computation", False):
        logging.info("無需計算驗證，跳過")
        return {"computation_results": None}

    reasoning_results = state.get("reasoning_results", [])

    # 準備計算驗證提示詞
    reasoning_text = "\n\n".join(
        [
            f"子題目: {result.subtopic}\n分析: {result.analysis}\n結論: {result.conclusion}"
            for result in reasoning_results
        ]
    )

    # 獲取可配置的通用指導原則
    general_guide = get_config_value(config, "general_guide", DEFAULT_GENERAL_GUIDE)

    prompt = f"""
    {general_guide}
    
    你是專業的計算驗證專家，請針對以下推理結果中的計算部分進行獨立驗算：
    
    {reasoning_text}
    
    請使用程式碼執行功能驗證任何涉及數字計算的部分，並提供驗證結果。
    """

    # 使用支援代碼執行的模型
    model = get_computation_model(config)
    response = model.invoke([HumanMessage(content=prompt)])

    logging.info("計算驗證完成")

    return {"computation_results": response.content}


async def hallucination_verification_node(
    state: GovResearcherState, config: RunnableConfig
) -> Dict[str, Any]:
    """Step-005: 幻覺驗證節點（支援搜尋引擎選擇）"""
    logging.info("[GovResearcherGraph:hallucination_verification_node] 開始幻覺驗證")

    # 收集前面所有結果
    previous_results = {
        "原始問題": state.get("original_question", ""),
        "子題目": [topic.topic for topic in state.get("decomposed_topics", [])],
        "搜尋結果": [result.content for result in state.get("search_results", [])],
        "推理結果": [result.analysis for result in state.get("reasoning_results", [])],
        "計算結果": state.get("computation_results", "無"),
    }

    results_text = "\n\n".join(
        [f"{key}: {value}" for key, value in previous_results.items()]
    )

    # 獲取可配置的提示詞模板
    prompt_template = get_prompt_template(
        config, "hallucination_verification_prompt", HALLUCINATION_VERIFICATION_PROMPT
    )
    general_guide = get_config_value(config, "general_guide", DEFAULT_GENERAL_GUIDE)

    # 準備驗證提示詞
    prompt = prompt_template.format(
        general_guide=general_guide,
        previous_results=results_text,
    )

    # 調用模型
    model = get_verification_model(config)
    response = model.invoke([HumanMessage(content=prompt)])

    # 如果發現問題，進行額外搜尋驗證（PRD要求：透過延伸搜尋證明或反駁前面的結論）
    if "問題" in response.content or "錯誤" in response.content:
        logging.info("發現潛在問題，進行額外搜尋驗證")

        # 獲取搜尋引擎配置（PRD要求：搜尋引擎選擇）
        search_vendor = get_config_value(
            config,
            "verification_search_vendor",
            get_config_value(config, "search_vendor", "perplexity"),
        )
        search_model = get_config_value(config, "search_model", "sonar")
        domain_filter = get_config_value(config, "domain_filter", [])

        # 提取需要驗證的關鍵問題
        verification_query = (
            f"驗證以下政府資訊的準確性：{state.get('original_question', '')}"
        )

        try:
            verification_content = ""

            # 根據搜尋服務商進行驗證搜尋
            if search_vendor == "tavily":
                async for event in respond_with_tavily_search(
                    verification_query,
                    "",
                    [{"role": "user", "content": verification_query}],
                    domain_filter,
                    False,
                    search_model,
                ):
                    verification_content += event.chunk
            else:  # perplexity
                async for event in respond_with_perplexity_search(
                    verification_query,
                    "",
                    [{"role": "user", "content": verification_query}],
                    domain_filter,
                    False,
                    search_model,
                ):
                    verification_content += event.chunk

            logging.info(f"完成額外搜尋驗證，使用服務商: {search_vendor}")

        except Exception as e:
            logging.error(f"額外搜尋驗證失敗: {e}")
            verification_content = f"驗證搜尋失敗: {str(e)}"
    else:
        verification_content = "未發現明顯問題，無需額外搜尋"

    # 簡化版驗證結果
    verification_result = VerificationResult(
        issues_found=["待實作：問題識別"],
        corrections=["待實作：修正建議"],
        confidence_adjustments={},
    )

    logging.info("幻覺驗證完成")

    return {
        "hallucination_check": verification_result,
        "verification_search_results": verification_content,
    }


def summary_response_node(
    state: GovResearcherState, config: RunnableConfig
) -> Dict[str, Any]:
    """Step-006: 匯總回答節點"""
    logging.info("[GovResearcherGraph:summary_response_node] 開始匯總回答")

    # 收集所有處理結果
    summary_data = {
        "original_question": state.get("original_question", ""),
        "subtopics": [topic.topic for topic in state.get("decomposed_topics", [])],
        "search_results": "\n".join(
            [result.content for result in state.get("search_results", [])]
        ),
        "reasoning_results": "\n".join(
            [result.analysis for result in state.get("reasoning_results", [])]
        ),
        "computation_results": state.get("computation_results", "無計算需求"),
    }

    # 獲取可配置的提示詞模板
    prompt_template = get_prompt_template(
        config, "summary_response_prompt", SUMMARY_RESPONSE_PROMPT
    )
    general_guide = get_config_value(config, "general_guide", DEFAULT_GENERAL_GUIDE)

    # 準備匯總提示詞
    prompt = prompt_template.format(general_guide=general_guide, **summary_data)

    # 調用模型
    model = get_summary_model(config)
    response = model.invoke([HumanMessage(content=prompt)])

    final_answer = response.content

    logging.info("匯總回答完成")

    return {"final_answer": final_answer, "messages": [AIMessage(content=final_answer)]}


def should_compute(state: GovResearcherState) -> str:
    """條件分支：決定是否需要計算驗證"""
    if state.get("needs_computation", False):
        return COMPUTATION_VERIFICATION_NODE
    else:
        return SUMMARY_RESPONSE_NODE


# 預設配置（根據PRD規格修正）
DEFAULT_GOV_RESEARCHER_CONFIG = {
    "decomposition_model": "gemini-2.5-pro",  # PRD 預設
    "reasoning_model": "gemini-2.5-flash",
    "computation_model": "gemini-2.5-flash",
    "verification_model": "gemini-2.5-flash",
    "summary_model": "gemini-2.5-flash",  # PRD 預設
    "search_vendor": "perplexity",  # PRD 預設
    "max_parallel_searches": 5,
    "domain_filter": [],
    "search_model": "sonar",  # PRD 預設，非 sonar-reasoning-pro
    "general_guide": DEFAULT_GENERAL_GUIDE,
}


def get_content_for_gov_researcher(state: Dict[str, Any]) -> str:
    """從狀態中取得內容"""
    return state.get("final_answer", "")


class GovResearcherGraph:
    """政府研究員 LangGraph Agent"""

    def __init__(self, memory: BaseCheckpointSaver = None):
        self.memory = memory if memory is not None else MemorySaver()
        self._initialize_graph()

    def _initialize_graph(self):
        """初始化 LangGraph 工作流"""
        workflow = StateGraph(
            GovResearcherState, context_schema=GovResearcherConfigSchema
        )

        # 添加節點
        workflow.add_node(TOPIC_DECOMPOSITION_NODE, topic_decomposition_node)
        workflow.add_node("search_preparation", search_preparation_node)
        workflow.add_node("search_subtopic", search_subtopic_node)
        workflow.add_node(REASONING_ANALYSIS_NODE, reasoning_analysis_node)
        workflow.add_node(COMPUTATION_VERIFICATION_NODE, computation_verification_node)
        workflow.add_node(
            HALLUCINATION_VERIFICATION_NODE, hallucination_verification_node
        )
        workflow.add_node(SUMMARY_RESPONSE_NODE, summary_response_node)

        # 定義邊（工作流程）
        workflow.add_edge(START, TOPIC_DECOMPOSITION_NODE)
        workflow.add_edge(TOPIC_DECOMPOSITION_NODE, "search_preparation")
        workflow.add_edge("search_preparation", "search_subtopic")
        workflow.add_edge("search_subtopic", REASONING_ANALYSIS_NODE)

        # 條件分支：是否需要計算驗證
        workflow.add_conditional_edges(
            REASONING_ANALYSIS_NODE,
            should_compute,
            [COMPUTATION_VERIFICATION_NODE, SUMMARY_RESPONSE_NODE],
        )

        workflow.add_edge(COMPUTATION_VERIFICATION_NODE, SUMMARY_RESPONSE_NODE)
        workflow.add_edge(SUMMARY_RESPONSE_NODE, END)

        # 編譯圖
        self._graph = workflow.compile(checkpointer=self.memory)
        self._graph_no_memory = workflow.compile()

    @property
    def graph(self):
        """帶記憶的圖"""
        return self._graph

    @property
    def graph_no_memory(self):
        """不帶記憶的圖"""
        return self._graph_no_memory


# 導出實例
gov_researcher_graph = GovResearcherGraph().graph_no_memory
