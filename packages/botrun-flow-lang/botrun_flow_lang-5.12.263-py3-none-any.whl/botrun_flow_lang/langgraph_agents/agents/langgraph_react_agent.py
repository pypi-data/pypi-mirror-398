import os
import asyncio
import json
from datetime import datetime
from typing import ClassVar, Dict, List, Optional, Any

from langchain_core.messages import SystemMessage

from botrun_flow_lang.constants import LANG_EN, LANG_ZH_TW

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

from langchain_core.tools import BaseTool

from langchain_core.tools import tool

from botrun_flow_lang.utils.botrun_logger import get_default_botrun_logger

# All tools now provided by MCP server - no local tool imports needed

from botrun_flow_lang.langgraph_agents.agents.checkpointer.firestore_checkpointer import (
    AsyncFirestoreCheckpointer,
)

from langgraph.prebuilt import create_react_agent

from dotenv import load_dotenv

import copy  # 用於深拷貝 schema，避免意外修改原始對象

# Removed DALL-E and rate limiting imports - tools now provided by MCP server

# =========
# 📋 STAGE 4 REFACTORING COMPLETED (MCP Integration)
#
# This file has been refactored to integrate with MCP (Model Context Protocol):
#
# ✅ REMOVED (~600 lines):
#   - Language-specific system prompts (zh_tw_system_prompt, en_system_prompt)
#   - Local tool definitions: scrape, chat_with_pdf, chat_with_imgs, generate_image,
#     generate_tmp_public_url, create_html_page, compare_date_time
#   - Complex conditional logic (if botrun_flow_lang_url and user_id)
#   - Rate limiting exception and related imports
#   - Unused utility imports
#
# ✅ SIMPLIFIED:
#   - Direct system_prompt usage (no concatenation)
#   - Streamlined tools list (only language-specific tools)
#   - Clean MCP integration via mcp_config parameter
#   - Maintained backward compatibility for all parameters
#
# 🎯 RESULT:
#   - Reduced complexity while maintaining full functionality
#   - All tools available via MCP server at /mcp/default/mcp/
#   - Ready for Phase 2: language-specific tools migration
# =========

# 放到要用的時候才 init，不然loading 會花時間
# 因為要讓 langgraph 在本地端執行，所以這一段又搬回到外面了
from langchain_google_genai import ChatGoogleGenerativeAI

# =========
# 放到要用的時候才 import，不然loading 會花時間
# 因為LangGraph 在本地端執行，所以這一段又搬回到外面了
from botrun_flow_lang.langgraph_agents.agents.util.model_utils import (
    RotatingChatAnthropic,
)

# =========
# 放到要用的時候才 init，不然loading 會花時間
# 因為LangGraph 在本地端執行，所以這一段又搬回到外面了
from langchain_openai import ChatOpenAI

# =========
# 放到要用的時候才 init，不然loading 會花時間
# 因為LangGraph 在本地端執行，所以這一段又搬回到外面了
from langchain_anthropic import ChatAnthropic

# =========

# 假設 MultiServerMCPClient 和 StructuredTool 已經被正確導入
from langchain.tools import StructuredTool  # 或 langchain_core.tools
from langchain_mcp_adapters.client import MultiServerMCPClient

# ========
# for Vertex AI
from google.oauth2 import service_account
from langchain_google_vertexai import ChatVertexAI
from langchain_google_vertexai.model_garden import ChatAnthropicVertex

load_dotenv()

# logger = default_logger
logger = get_default_botrun_logger()


# Removed BotrunRateLimitException - rate limiting now handled by MCP server


# Load Anthropic API keys from environment
# anthropic_api_keys_str = os.getenv("ANTHROPIC_API_KEYS", "")
# anthropic_api_keys = [
#     key.strip() for key in anthropic_api_keys_str.split(",") if key.strip()
# ]

# Initialize the model with key rotation if multiple keys are available
# if anthropic_api_keys:
#     model = RotatingChatAnthropic(
#         model_name="claude-3-7-sonnet-latest",
#         keys=anthropic_api_keys,
#         temperature=0,
#         max_tokens=8192,
#     )
# 建立 AWS Session
# session = boto3.Session(
#     aws_access_key_id="",
#     aws_secret_access_key="",
#     region_name="us-west-2",
# )


# # 使用該 Session 初始化 Bedrock 客戶端
# bedrock_runtime = session.client(
#     service_name="bedrock-runtime",
# )
# model = ChatBedrockConverse(
#     model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
#     client=bedrock_runtime,
#     temperature=0,
#     max_tokens=8192,
# )
# else:
# Fallback to traditional initialization if no keys are specified
def get_react_agent_model_name(model_name: str = ""):
    final_model_name = model_name
    if final_model_name == "":
        final_model_name = "claude-sonnet-4-5-20250929"
    logger.info(f"final_model_name: {final_model_name}")
    return final_model_name


ANTHROPIC_MAX_TOKENS = 64000
GEMINI_MAX_TOKENS = 32000
TAIDE_MAX_TOKENS = 8192


def get_react_agent_model(model_name: str = ""):
    final_model_name = get_react_agent_model_name(model_name).strip()

    # 處理 taide/ 前綴的模型
    if final_model_name.startswith("taide/"):
        taide_api_key = os.getenv("TAIDE_API_KEY", "")
        taide_base_url = os.getenv("TAIDE_BASE_URL", "")

        if not taide_api_key or not taide_base_url:
            raise ValueError(
                f"Model name starts with 'taide/' but TAIDE_API_KEY or TAIDE_BASE_URL not set. "
                f"Both environment variables are required for: {final_model_name}"
            )

        # 取得 taide/ 後面的模型名稱
        taide_model_name = final_model_name[len("taide/"):]

        if not taide_model_name:
            raise ValueError(
                f"Invalid taide model format: {final_model_name}. "
                "Expected format: taide/<model_name>"
            )

        model = ChatOpenAI(
            openai_api_key=taide_api_key,
            openai_api_base=taide_base_url,
            model_name=taide_model_name,
            temperature=0,
            max_tokens=TAIDE_MAX_TOKENS,
        )
        logger.info(f"model ChatOpenAI (TAIDE) {taide_model_name} @ {taide_base_url}")
        return model

    # 處理 vertexai/ 前綴的模型
    if final_model_name.startswith("vertex-ai/"):
        vertex_project = os.getenv("VERTEX_AI_LANGCHAIN_PROJECT", "")

        # 如果沒有設定 VERTEX_AI_LANGCHAIN_PROJECT，則不處理 vertex-ai/ 前綴
        if not vertex_project:
            logger.warning(
                f"Model name starts with 'vertex-ai/' but VERTEX_AI_LANGCHAIN_PROJECT not set. "
                f"Skipping vertex-ai/ processing for {final_model_name}"
            )
            # 移除 vertex-ai/ 前綴後繼續處理
            final_model_name = final_model_name[len("vertex-ai/"):]
            # 移除 region 部分 (如果有的話)
            if "/" in final_model_name:
                parts = final_model_name.split("/", 1)
                if len(parts) == 2:
                    final_model_name = parts[1]
        else:
            # 解析 vertex-ai/region/model_name 格式
            parts = final_model_name.split("/")

            if len(parts) != 3:
                raise ValueError(
                    f"Invalid vertexai model format: {final_model_name}. "
                    "Expected format: vertex-ai/<region>/<model_name>"
                )

            vertex_region = parts[1]
            vertex_model_name = parts[2]

            if not vertex_region or not vertex_model_name:
                raise ValueError(
                    f"Missing region or model_name in: {final_model_name}. "
                    "Both region and model_name are required."
                )

            # 取得 credentials
            vertex_sa_path = os.getenv(
                "VERTEX_AI_LANGCHAIN_GOOGLE_APPLICATION_CREDENTIALS", ""
            )

            credentials = None
            if vertex_sa_path and os.path.exists(vertex_sa_path):
                SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
                credentials = service_account.Credentials.from_service_account_file(
                    vertex_sa_path, scopes=SCOPES
                )
                logger.info(f"Using Vertex AI service account from {vertex_sa_path}")
            else:
                logger.warning(
                    "VERTEX_AI_LANGCHAIN_GOOGLE_APPLICATION_CREDENTIALS not set. Using ADC."
                )

            # 判斷模型類型並創建相應實例
            if vertex_model_name.startswith("gemini-"):
                # Gemini 系列：gemini-2.5-pro, gemini-2.5-flash, gemini-pro
                model = ChatVertexAI(
                    model=vertex_model_name,
                    location=vertex_region,
                    project=vertex_project,
                    credentials=credentials,
                    temperature=0,
                    max_tokens=GEMINI_MAX_TOKENS,
                )
                logger.info(
                    f"model ChatVertexAI {vertex_model_name} @ {vertex_region} (project: {vertex_project})"
                )

            elif "claude" in vertex_model_name.lower() or vertex_model_name.startswith("maison/"):
                # Anthropic Claude (model garden)
                model = ChatAnthropicVertex(
                    model=vertex_model_name,
                    location=vertex_region,
                    project=vertex_project,
                    credentials=credentials,
                    temperature=0,
                    max_tokens=ANTHROPIC_MAX_TOKENS,
                )
                logger.info(
                    f"model ChatAnthropicVertex {vertex_model_name} @ {vertex_region} (project: {vertex_project})"
                )

            else:
                raise ValueError(
                    f"Unsupported Vertex AI model: {vertex_model_name}. "
                    "Supported types: gemini-*, claude*, maison/*"
                )

            return model

    if final_model_name.startswith("gemini-"):
        model = ChatGoogleGenerativeAI(
            model=final_model_name, temperature=0, max_tokens=GEMINI_MAX_TOKENS
        )
        logger.info(f"model ChatGoogleGenerativeAI {final_model_name}")
    elif final_model_name.startswith("claude-"):
        # use_vertex_ai = os.getenv("USE_VERTEX_AI", "false").lower() in ("true", "1", "yes")
        vertex_project = os.getenv("VERTEX_AI_LANGCHAIN_PROJECT", "")
        vertex_location = os.getenv("VERTEX_AI_LANGCHAIN_LOCATION", "")
        vertex_model = os.getenv("VERTEX_AI_LANGCHAIN_MODEL", "")
        vertex_sa_path = os.getenv(
            "VERTEX_AI_LANGCHAIN_GOOGLE_APPLICATION_CREDENTIALS", ""
        )

        if vertex_location and vertex_model and vertex_sa_path and vertex_project:
            # 從環境變數讀取設定

            # 驗證 service account
            credentials = None
            if vertex_sa_path and os.path.exists(vertex_sa_path):
                # 加入 Vertex AI 需要的 scopes
                SCOPES = [
                    "https://www.googleapis.com/auth/cloud-platform",
                ]
                credentials = service_account.Credentials.from_service_account_file(
                    vertex_sa_path, scopes=SCOPES
                )
                logger.info(f"Using Vertex AI service account from {vertex_sa_path}")
            else:
                logger.warning(
                    "VERTEX_AI_GOOGLE_APPLICATION_CREDENTIALS not set or file not found. Using ADC if available."
                )

            # 初始化 ChatAnthropicVertex
            model = ChatAnthropicVertex(
                project=vertex_project,
                model=vertex_model,
                location=vertex_location,
                credentials=credentials,
                temperature=0,
                max_tokens=ANTHROPIC_MAX_TOKENS,
            )
            logger.info(
                f"model ChatAnthropicVertex {vertex_project} @ {vertex_model} @ {vertex_location}"
            )

        else:
            anthropic_api_keys_str = os.getenv("ANTHROPIC_API_KEYS", "")
            anthropic_api_keys = [
                key.strip() for key in anthropic_api_keys_str.split(",") if key.strip()
            ]
            if anthropic_api_keys:

                model = RotatingChatAnthropic(
                    model_name=final_model_name,
                    keys=anthropic_api_keys,
                    temperature=0,
                    max_tokens=ANTHROPIC_MAX_TOKENS,
                )
                logger.info(f"model RotatingChatAnthropic {final_model_name}")
            elif os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_BASE_URL"):

                openrouter_model_name = "anthropic/claude-sonnet-4.5"
                # openrouter_model_name = "openai/o4-mini-high"
                # openrouter_model_name = "openai/gpt-4.1"
                model = ChatOpenAI(
                    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
                    model_name=openrouter_model_name,
                    temperature=0,
                    max_tokens=ANTHROPIC_MAX_TOKENS,
                    model_kwargs={
                        # "headers": {
                        #     "HTTP-Referer": getenv("YOUR_SITE_URL"),
                        #     "X-Title": getenv("YOUR_SITE_NAME"),
                        # }
                    },
                )
                logger.info(f"model OpenRouter {openrouter_model_name}")
            else:

                model = ChatAnthropic(
                    model=final_model_name,
                    temperature=0,
                    max_tokens=ANTHROPIC_MAX_TOKENS,
                    # model_kwargs={
                    # "extra_headers": {
                    # "anthropic-beta": "token-efficient-tools-2025-02-19",
                    # "anthropic-beta": "output-128k-2025-02-19",
                    # }
                    # },
                )
                logger.info(f"model ChatAnthropic {final_model_name}")

    else:
        raise ValueError(f"Unknown model name prefix: {final_model_name}")

    return model


# model = ChatOpenAI(model="gpt-4o", temperature=0)
# model = ChatGoogleGenerativeAI(model="gemini-2.0-pro-exp-02-05", temperature=0)
# model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)


# For this tutorial we will use custom tool that returns pre-defined values for weather in two cities (NYC & SF)


# Removed scrape and compare_date_time tools - now provided by MCP server


# Removed chat_with_pdf tool - now provided by MCP server


# Removed generate_image tool - now provided by MCP server


# Removed chat_with_imgs tool - now provided by MCP server


# Removed generate_tmp_public_url tool - now provided by MCP server


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


# Removed create_html_page tool - now provided by MCP server


# DICT_VAR = {}

# Define the graph

# Removed language-specific system prompts - now using user-provided system_prompt directly


def transform_anthropic_incompatible_schema(
    schema_dict: dict,
) -> tuple[dict, bool, str]:
    """
    轉換可能與 Anthropic 不相容的頂層 schema 結構。

    Args:
        schema_dict: 原始 schema 字典。

    Returns:
        tuple: (轉換後的 schema 字典, 是否進行了轉換, 附加到 description 的提示信息)
    """
    if not isinstance(schema_dict, dict):
        return schema_dict, False, ""

    keys_to_check = ["anyOf", "allOf", "oneOf"]
    problematic_key = None
    for key in keys_to_check:
        if key in schema_dict:
            problematic_key = key
            break

    if problematic_key:
        print(f"  發現頂層 '{problematic_key}'，進行轉換...")
        transformed = True
        new_schema = {"type": "object", "properties": {}, "required": []}
        description_notes = f"\n[開發者註記：此工具參數原使用 '{problematic_key}' 結構，已轉換。請依賴參數描述判斷必要輸入。]"

        # 1. 合併 Properties
        # 先加入頂層的 properties (如果存在)
        if "properties" in schema_dict:
            new_schema["properties"].update(copy.deepcopy(schema_dict["properties"]))
        # 再合併來自 problematic_key 內部的 properties
        for sub_schema in schema_dict.get(problematic_key, []):
            if isinstance(sub_schema, dict) and "properties" in sub_schema:
                # 注意：如果不同 sub_schema 有同名 property，後者會覆蓋前者
                new_schema["properties"].update(copy.deepcopy(sub_schema["properties"]))

        # 2. 處理 Required
        top_level_required = set(schema_dict.get("required", []))

        if problematic_key == "allOf":
            # allOf: 合併所有 required
            combined_required = top_level_required
            for sub_schema in schema_dict.get(problematic_key, []):
                if isinstance(sub_schema, dict) and "required" in sub_schema:
                    combined_required.update(sub_schema["required"])
            # 只保留實際存在於合併後 properties 中的 required 欄位
            new_schema["required"] = sorted(
                [req for req in combined_required if req in new_schema["properties"]]
            )
            description_notes += " 所有相關參數均需考慮。]"  # 簡單提示
        elif problematic_key in ["anyOf", "oneOf"]:
            # anyOf/oneOf: 只保留頂層 required，並在描述中說明選擇性
            new_schema["required"] = sorted(
                [req for req in top_level_required if req in new_schema["properties"]]
            )
            # 嘗試生成更具體的提示 (如果 sub_schema 結構簡單)
            options = []
            for sub_schema in schema_dict.get(problematic_key, []):
                if isinstance(sub_schema, dict) and "required" in sub_schema:
                    options.append(f"提供 '{', '.join(sub_schema['required'])}'")
            if options:
                description_notes += (
                    f" 通常需要滿足以下條件之一：{'; 或 '.join(options)}。]"
                )
            else:
                description_notes += " 請注意參數間的選擇關係。]"

        print(
            f"  轉換後 schema: {json.dumps(new_schema, indent=2, ensure_ascii=False)}"
        )
        return new_schema, transformed, description_notes
    else:
        return schema_dict, False, ""


# --- Schema 轉換輔助函數 (從 _get_mcp_tools_async 提取) ---
def _process_mcp_tools_for_anthropic(langchain_tools: List[Any]) -> List[Any]:
    """處理 MCP 工具列表，轉換不相容的 Schema 並記錄日誌"""
    if not langchain_tools:
        logger.info("[_process_mcp_tools_for_anthropic] 警告 - 未找到任何工具。")
        return []

    logger.info(
        f"[_process_mcp_tools_for_anthropic] --- 開始處理 {len(langchain_tools)} 個原始 MCP 工具 ---"
    )

    processed_tools = []
    for mcp_tool in langchain_tools:
        # 只處理 StructuredTool 或類似的有 args_schema 的工具
        if not hasattr(mcp_tool, "args_schema") or not mcp_tool.args_schema:
            logger.debug(
                f"[_process_mcp_tools_for_anthropic] 工具 '{mcp_tool.name}' 沒有 args_schema，直接加入。"
            )
            processed_tools.append(mcp_tool)
            continue

        original_schema_dict = {}
        try:
            # 嘗試獲取 schema 字典 (根據 Pydantic 版本可能不同)
            if hasattr(mcp_tool.args_schema, "model_json_schema"):  # Pydantic V2
                original_schema_dict = mcp_tool.args_schema.model_json_schema()
            elif hasattr(mcp_tool.args_schema, "schema"):  # Pydantic V1
                original_schema_dict = mcp_tool.args_schema.schema()
            elif isinstance(mcp_tool.args_schema, dict):  # 已經是字典？
                original_schema_dict = mcp_tool.args_schema
            else:
                logger.warning(
                    f"[_process_mcp_tools_for_anthropic] 無法獲取工具 '{mcp_tool.name}' 的 schema 字典 ({type(mcp_tool.args_schema)})，跳過轉換。"
                )
                processed_tools.append(mcp_tool)
                continue

            # 進行轉換檢查
            logger.debug(
                f"[_process_mcp_tools_for_anthropic] 檢查工具 '{mcp_tool.name}' 的 schema..."
            )
            new_schema_dict, transformed, desc_notes = (
                transform_anthropic_incompatible_schema(
                    copy.deepcopy(original_schema_dict)  # 使用深拷貝操作
                )
            )

            if transformed:
                mcp_tool.description += desc_notes
                logger.info(
                    f"[_process_mcp_tools_for_anthropic] 工具 '{mcp_tool.name}' 的描述已更新。"
                )
                if isinstance(mcp_tool.args_schema, dict):
                    logger.debug(
                        f"[_process_mcp_tools_for_anthropic] args_schema 是字典，直接替換工具 '{mcp_tool.name}' 的 schema。"
                    )
                    mcp_tool.args_schema = new_schema_dict
                else:
                    # 如果 args_schema 是 Pydantic 模型，直接修改可能無效或困難
                    # 附加轉換後的字典可能是一種備選方案，但 Langchain/LangGraph 可能不直接使用它
                    # 最好的方法是確保 get_tools 返回的工具的 args_schema 可以被修改，
                    # 或者在創建工具時就使用轉換後的 schema。
                    # 如果不能直接修改，附加屬性是一種標記方式，但可能需要在工具調用處處理。
                    logger.warning(
                        f"[_process_mcp_tools_for_anthropic] args_schema 不是字典 ({type(mcp_tool.args_schema)})，僅添加 _transformed_args_schema_dict 屬性到工具 '{mcp_tool.name}'。這可能不足以解決根本問題。"
                    )
                    setattr(mcp_tool, "_transformed_args_schema_dict", new_schema_dict)
            processed_tools.append(mcp_tool)

        except Exception as e_schema:
            logger.error(
                f"[_process_mcp_tools_for_anthropic] 處理工具 '{mcp_tool.name}' schema 時發生錯誤: {e_schema}",
                exc_info=True,
            )
            processed_tools.append(mcp_tool)  # 保留原始工具

    logger.info(
        f"[_process_mcp_tools_for_anthropic] --- 完成工具處理，返回 {len(processed_tools)} 個工具 ---"
    )
    return processed_tools


async def create_react_agent_graph(
    system_prompt: str = "",
    botrun_flow_lang_url: str = "",
    user_id: str = "",
    model_name: str = "",
    lang: str = LANG_EN,
    mcp_config: Optional[Dict[str, Any]] = None,  # <--- 接收配置而非客戶端實例
):
    """
    Create a react agent graph with simplified architecture.

    This function now creates a fully MCP-integrated agent with:
    - Direct system prompt usage (no language-specific prompt concatenation)
    - Zero local tools - all functionality provided by MCP server
    - Complete MCP server integration for all tools (web search, scraping, PDF/image analysis, time/date, visualizations, etc.)
    - Removed all complex conditional logic and local tool definitions

    Args:
        system_prompt: The system prompt to use for the agent (used directly, no concatenation)
        botrun_flow_lang_url: URL for botrun flow lang service (reserved for future use)
        user_id: User identifier (reserved for future use)
        model_name: AI model name to use (defaults to claude-sonnet-4-5-20250929)
        lang: Language code affecting language-specific tools (e.g., "en", "zh-TW")
        mcp_config: MCP servers configuration dict providing tools like scrape, chat_with_pdf, etc.

    Returns:
        A LangGraph react agent configured with simplified architecture

    Note:
        - Local MCP tools (scrape, chat_with_pdf, etc.) have been removed
        - compare_date_time tool has been completely removed
        - All advanced tools are now provided via MCP server configuration
        - Language-specific prompts have been removed for simplification
    """

    # Complete MCP migration - all tools are now provided by MCP server
    # No local tools remain - all functionality accessed via mcp_config
    tools = [
        # ✅ ALL MIGRATED TO MCP: scrape, chat_with_pdf, chat_with_imgs, generate_image,
        #    generate_tmp_public_url, create_html_page, create_plotly_chart,
        #    create_mermaid_diagram, current_date_time, web_search
        # ❌ REMOVED: compare_date_time (completely eliminated)
    ]

    mcp_tools = []
    if mcp_config:
        logger.info("偵測到 MCP 配置，直接創建 MCP 工具...")
        try:
            # 直接創建 MCP client 並獲取工具，不使用 context manager

            client = MultiServerMCPClient(mcp_config)
            raw_mcp_tools = await client.get_tools()
            print("raw_mcp_tools============>", raw_mcp_tools)

            if raw_mcp_tools:
                logger.info(f"從 MCP 配置獲取了 {len(raw_mcp_tools)} 個原始工具。")
                # 處理 Schema (使用提取的輔助函數)
                mcp_tools = _process_mcp_tools_for_anthropic(raw_mcp_tools)
                if mcp_tools:
                    tools.extend(mcp_tools)
                    logger.info(f"已加入 {len(mcp_tools)} 個處理後的 MCP 工具。")
                    logger.debug(
                        f"加入的 MCP 工具名稱: {[tool.name for tool in mcp_tools]}"
                    )
                else:
                    logger.warning("MCP 工具處理後列表為空。")
            else:
                logger.info("MCP Client 返回了空的工具列表。")

            # 注意：我們不在這裡關閉 client，因為 tools 可能需要它來執行
            # client 會在 graph 執行完畢後自動清理
            logger.info("MCP client 和工具創建完成，client 將保持活動狀態")

        except Exception as e_get:
            import traceback

            traceback.print_exc()
            logger.error(f"從 MCP 配置獲取或處理工具時發生錯誤: {e_get}", exc_info=True)
            # 即使出錯，也可能希望繼續執行（不帶 MCP 工具）
    else:
        logger.info("未提供 MCP 配置，跳過 MCP 工具。")

    # Simplified: use user-provided system_prompt directly (no language-specific prompts)
    new_system_prompt = system_prompt
    if botrun_flow_lang_url and user_id:
        new_system_prompt = (
            f"""IMPORTANT: Any URL returned by tools MUST be included in your response as a markdown link [text](URL).
            Please use the standard [text](URL) format to present links, ensuring the link text remains plain and unformatted.
            Example:
            User: "Create a new page for our project documentation"
            Tool returns: {{"page_url": "https://notion.so/workspace/abc123"}}
            Assistant: "I've created the new page for your project documentation. You can access it here: [Project Documentation](https://notion.so/workspace/abc123)"
            """
            + system_prompt
            + f"""\n\n
            - If the tool needs parameter like botrun_flow_lang_url or user_id, please use the following:
            botrun_flow_lang_url: {botrun_flow_lang_url}
            user_id: {user_id}
            """
        )
    system_message = SystemMessage(
        content=[
            {
                "text": new_system_prompt,
                "type": "text",
                "cache_control": {"type": "ephemeral"},
            }
        ]
    )

    # 目前先使用了 https://docs.anthropic.com/en/docs/build-with-claude/tool-use/token-efficient-tool-use
    # 這一段會遇到
    #       File "/Users/seba/Projects/botrun_flow_lang/.venv/lib/python3.11/site-packages/langgraph/prebuilt/tool_node.py", line 218, in __init__
    #     tool_ = create_tool(tool_)
    #             ^^^^^^^^^^^^^^^^^^
    #   File "/Users/seba/Projects/botrun_flow_lang/.venv/lib/python3.11/site-packages/langchain_core/tools/convert.py", line 334, in tool
    #     raise ValueError(msg)
    # ValueError: The first argument must be a string or a callable with a __name__ for tool decorator. Got <class 'dict'>
    # 所以先不使用這一段，這一段是參考 https://python.langchain.com/docs/integrations/chat/anthropic/#tools
    # 也許未來可以引用
    # if get_react_agent_model_name(model_name).startswith("claude-"):
    #     new_tools = []
    #     for tool in tools:
    #         new_tool = convert_to_anthropic_tool(tool)
    #         new_tool["cache_control"] = {"type": "ephemeral"}
    #         new_tools.append(new_tool)
    #     tools = new_tools

    env_name = os.getenv("ENV_NAME", "botrun-flow-lang-dev")
    result = create_react_agent(
        get_react_agent_model(model_name),
        tools=tools,
        prompt=system_message,
        checkpointer=MemorySaver(),  # 如果要執行在 botrun_back 裡面，就不需要 firestore 的 checkpointer
        # checkpointer=AsyncFirestoreCheckpointer(env_name=env_name),
    )
    return result


# Default graph instance with empty prompt
# if True:
# react_agent_graph = create_react_agent_graph()
# LangGraph Studio 測試用，把以下 un-comment 就可以測試
# react_agent_graph = create_react_agent_graph(
#     system_prompt="",
#     botrun_flow_lang_url="https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
#     user_id="sebastian.hsu@gmail.com",
# )
