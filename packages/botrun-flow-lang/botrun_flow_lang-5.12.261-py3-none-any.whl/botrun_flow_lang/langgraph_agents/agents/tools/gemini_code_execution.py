"""
Gemini Code Execution Tool for LangGraph
使用 Google Gemini API 的 code execution 功能執行 Python 程式碼
"""

import os
import json
from typing import ClassVar, Dict, Tuple, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import ToolMessage
from langgraph.config import get_stream_writer
from langgraph.types import StreamWriter

from botrun_flow_lang.constants import LANG_EN, LANG_ZH_TW
from botrun_flow_lang.utils.botrun_logger import BotrunLogger


class GeminiCodeExecutionTool(BaseTool):
    """
    使用 Google Gemini API 的 code execution 功能執行 Python 程式碼
    """

    # 類屬性定義
    tool_name: ClassVar[str] = "gemini_code_execution"

    # 定義多語言描述
    descriptions: ClassVar[Dict[str, str]] = {
        LANG_EN: """
    Execute Python code using Google Gemini's code execution feature.
    This tool allows Gemini to generate and run Python code iteratively until it produces a final output.
    
    Capabilities:
    - Mathematical calculations and data analysis
    - Text processing and manipulation
    - Using libraries: NumPy, Pandas, SymPy, and more
    - Iterative code improvement based on execution results
    - Maximum execution time: 30 seconds
    
    Examples:
    1. Mathematical calculation:
       User: "Calculate the sum of the first 50 prime numbers"
       gemini_code_execution("Calculate the sum of the first 50 prime numbers")
       Returns: Code and result showing the sum is 5117
    
    2. Text processing:
       User: "Count word frequency in a text"
       gemini_code_execution("Count word frequency in this text: 'The quick brown fox jumps over the lazy dog'")
    
    Args:
        code_request: Description of the code task to execute. Be specific about:
                     - What calculation or analysis to perform
                     - Input data (if any)
                     - Expected output format
        
    Returns:
        dict: Contains:
              - summary: Brief description of what was done
              - code_blocks: List of executed code blocks
              - results: Execution outputs
              - images: List of generated images (if any)
              - error: Error message (if any)
    """,
        LANG_ZH_TW: """
    使用 Google Gemini 的程式碼執行功能執行 Python 程式碼。
    此工具讓 Gemini 可以生成並執行 Python 程式碼，並根據結果反覆改進直到產生最終輸出。
    
    功能特色：
    - 數學計算和資料分析
    - 文字處理和操作
    - 支援函式庫：NumPy、Pandas、SymPy 等
    - 根據執行結果反覆改進程式碼
    - 最長執行時間：30 秒
    
    使用範例：
    1. 數學計算：
       使用者：「計算前 50 個質數的總和」
       gemini_code_execution("計算前 50 個質數的總和")
       回傳：程式碼和結果顯示總和為 5117
    
    2. 文字處理：
       使用者：「計算文字中的詞頻」
       gemini_code_execution("計算這段文字的詞頻：'The quick brown fox jumps over the lazy dog'")
    
    參數：
        code_request: 程式碼任務的描述。請具體說明：
                     - 要執行什麼計算或分析
                     - 輸入資料（如果有）
                     - 期望的輸出格式
        
    Returns:
        dict: 包含：
              - summary: 執行內容的簡短描述
              - code_blocks: 執行的程式碼區塊列表
              - results: 執行輸出
              - images: 產生的圖片列表（如果有）
              - error: 錯誤訊息（如果有）
    """,
    }

    # Pydantic 模型字段
    name: str = "gemini_code_execution"
    description: str = descriptions[LANG_EN]
    lang: str = LANG_EN
    response_format: str = "content_and_artifact"  # 支援 artifact 回傳

    @classmethod
    def for_language(cls, lang: str = LANG_EN):
        """創建特定語言版本的工具實例"""
        description = cls.descriptions.get(lang, cls.descriptions.get(LANG_EN))
        return cls(name=cls.tool_name, description=description, lang=lang)

    def _run(
        self,
        code_request: str,
        config: RunnableConfig = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        執行 Gemini code execution 並返回結果

        Returns:
            Tuple[str, Dict]: (給模型的訊息, 詳細執行結果)
        """
        logger = BotrunLogger()
        logger.info(
            f"gemini_code_execution request",
            code_request=code_request,
        )

        # 取得 stream writer 來輸出即時訊息
        try:
            writer = get_stream_writer()
            has_writer = True
        except Exception:
            # 如果不在 LangGraph context 中，writer 會是 None
            writer = None
            has_writer = False

        # 發送開始訊息
        if has_writer:
            writer(
                {
                    "type": "status",
                    "message": f"🚀 Starting code execution for: {code_request[:100]}...",
                }
            )

        try:
            # 初始化 Gemini client
            from google import genai
            from google.genai import types
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_FASTAPI"),
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )

            client = genai.Client(
                credentials=credentials,
                project="scoop-386004",
                location="us-central1",
            )

            # 發送 API 調用狀態
            if has_writer:
                writer(
                    {
                        "type": "progress",
                        "message": "📡 Calling Gemini API with code execution enabled...",
                    }
                )

            # 調用 Gemini API 並啟用 code execution
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=code_request,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution())]
                ),
            )

            # 發送收到回應的狀態
            if has_writer:
                writer(
                    {
                        "type": "progress",
                        "message": "✅ Received response from Gemini API",
                    }
                )

            # 解析回應
            executed_code = []
            execution_results = []
            summary_text = []
            images = []

            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    summary_text.append(part.text)
                    # 即時輸出 Gemini 的文字說明
                    if has_writer:
                        writer(
                            {
                                "type": "text",
                                "content": part.text,
                                "source": "gemini_explanation",
                            }
                        )

                if hasattr(part, "executable_code") and part.executable_code:
                    code_info = {
                        "code": part.executable_code.code,
                        "language": getattr(part.executable_code, "language", "PYTHON"),
                    }
                    executed_code.append(code_info)
                    logger.debug(f"Executed code block", code_info=code_info)

                    # 即時輸出程式碼
                    if has_writer:
                        writer(
                            {
                                "type": "code",
                                "language": code_info["language"],
                                "content": code_info["code"],
                                "message": f"💻 Executing {code_info['language']} code block #{len(executed_code)}",
                            }
                        )

                if (
                    hasattr(part, "code_execution_result")
                    and part.code_execution_result
                ):
                    result_info = {
                        "output": part.code_execution_result.output,
                        "outcome": getattr(
                            part.code_execution_result, "outcome", "UNKNOWN"
                        ),
                    }
                    execution_results.append(result_info)
                    logger.debug(f"Execution result", result_info=result_info)

                    # 即時輸出執行結果
                    if has_writer:
                        status_emoji = (
                            "✅" if result_info["outcome"] != "ERROR" else "❌"
                        )
                        writer(
                            {
                                "type": "execution_result",
                                "outcome": result_info["outcome"],
                                "output": result_info["output"],
                                "message": f"{status_emoji} Execution result (outcome: {result_info['outcome']})",
                            }
                        )

                # 檢查是否有圖片輸出（Matplotlib 產生的圖表）
                if hasattr(part, "inline_data") and part.inline_data:
                    image_info = {
                        "mime_type": part.inline_data.mime_type,
                        "data": part.inline_data.data,  # Base64 encoded image
                    }
                    images.append(image_info)
                    logger.info(f"Generated image", mime_type=image_info["mime_type"])

                    # 即時輸出圖片生成通知
                    if has_writer:
                        writer(
                            {
                                "type": "image_generated",
                                "mime_type": image_info["mime_type"],
                                "message": f"📊 Generated visualization ({image_info['mime_type']})",
                            }
                        )

            # 準備 artifact（詳細結果）
            artifact = {
                "executed_code": executed_code,
                "execution_results": execution_results,
                "images": images,
                "full_response": str(response),  # 保存完整回應以供調試
                "has_visualization": len(images) > 0,
            }

            # 準備給模型的簡潔訊息
            if summary_text:
                content = " ".join(summary_text)
            else:
                content = "Code execution completed successfully."

            if images:
                content += f" Generated {len(images)} visualization(s)."

            # 發送完成狀態
            if has_writer:
                writer(
                    {
                        "type": "completion",
                        "message": f"🎉 Code execution completed successfully!",
                        "stats": {
                            "code_blocks": len(executed_code),
                            "results": len(execution_results),
                            "images": len(images),
                        },
                    }
                )

            logger.info(
                "gemini_code_execution completed",
                num_code_blocks=len(executed_code),
                num_results=len(execution_results),
                num_images=len(images),
            )

            # 回傳 tuple 格式以支援 artifact
            return content, artifact

        except Exception as e:
            error_msg = f"Code execution failed: {str(e)}"
            logger.error(error_msg, error=str(e), exc_info=True)

            # 發送錯誤訊息
            if has_writer:
                writer(
                    {
                        "type": "error",
                        "message": f"❌ {error_msg}",
                        "error_type": type(e).__name__,
                    }
                )

            error_artifact = {
                "error": str(e),
                "error_type": type(e).__name__,
                "executed_code": [],
                "execution_results": [],
                "images": [],
            }

            return error_msg, error_artifact

    async def _arun(
        self,
        code_request: str,
        config: RunnableConfig = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        異步版本的 _run 方法
        目前直接調用同步版本，未來可以改為真正的異步實現
        """
        # 注意：在 Python < 3.11 中，異步函數可能無法使用 get_stream_writer()
        # 需要將 writer 作為參數傳入
        # 目前這裡保持簡單，直接調用同步版本
        return self._run(code_request, config)


# 建立一個便利的函數裝飾器版本，供簡單使用
from langchain_core.tools import tool


@tool(response_format="content_and_artifact")
def gemini_code_execution(
    code_request: str,
    config: RunnableConfig = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Execute Python code using Google Gemini's code execution feature.

    Args:
        code_request: Description of the code task to execute

    Returns:
        Tuple[str, Dict]: (message for model, detailed execution results)
    """
    tool_instance = GeminiCodeExecutionTool()
    return tool_instance._run(code_request, config)
