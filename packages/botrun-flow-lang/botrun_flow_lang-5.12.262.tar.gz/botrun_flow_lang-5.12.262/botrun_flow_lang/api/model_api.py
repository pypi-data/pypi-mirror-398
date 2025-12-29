import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

router = APIRouter()


class ModelInfo(BaseModel):
    """Model information structure"""

    display_name: str
    model_name: str
    provider: str


class ModelsResponse(BaseModel):
    """Response model for listing supported models"""

    models: List[ModelInfo]
    total_count: int


class AgentModelsResponse(BaseModel):
    """Response model for listing supported agent models"""

    models: List[str]
    total_count: int


def read_google_sheet(
    credentials_path: str, spreadsheet_id: str, sheet_name: str
) -> pd.DataFrame:
    """
    讀取 Google Spreadsheet 指定 sheet，回傳 pandas DataFrame。
    """
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=scopes
        )
        service = build("sheets", "v4", credentials=credentials)
        sheet = service.spreadsheets()
        result = (
            sheet.values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
        )
        values = result.get("values", [])
        if not values:
            return pd.DataFrame()
        # 第一列為欄位名稱
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception:
        import traceback

        traceback.print_exc()
        return pd.DataFrame()


def get_models_from_google_sheet() -> List[ModelInfo]:
    """
    從 Google Sheets 讀取模型列表
    優先順序：ENV_NAME sheet -> default sheet -> DEFAULT_SUPPORTED_MODELS
    """
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_MODELS_SHEET")
    spreadsheet_id = os.getenv("MODELS_GSPREAD_ID")
    env_name = os.getenv("ENV_NAME", "")

    if not credentials_path or not spreadsheet_id:
        return DEFAULT_SUPPORTED_MODELS

    # 首先嘗試使用 ENV_NAME 作為 sheet_name
    if env_name:
        df = read_google_sheet(credentials_path, spreadsheet_id, env_name)
        if not df.empty and all(
            col in df.columns for col in ["display_name", "model_name", "provider"]
        ):
            try:
                return [
                    ModelInfo(
                        display_name=row["display_name"],
                        model_name=row["model_name"],
                        provider=row["provider"],
                    )
                    for _, row in df.iterrows()
                ]
            except Exception:
                pass

    # 如果 ENV_NAME sheet 找不到或有問題，嘗試 default sheet
    df = read_google_sheet(credentials_path, spreadsheet_id, "default")
    if not df.empty and all(
        col in df.columns for col in ["display_name", "model_name", "provider"]
    ):
        try:
            return [
                ModelInfo(
                    display_name=row["display_name"],
                    model_name=row["model_name"],
                    provider=row["provider"],
                )
                for _, row in df.iterrows()
            ]
        except Exception:
            pass

    # 如果都失敗，回退到 DEFAULT_SUPPORTED_MODELS
    return DEFAULT_SUPPORTED_MODELS


def get_agent_models_from_google_sheet() -> List[str]:
    """
    從 Google Sheets 讀取 agent 模型列表
    優先順序：ENV_NAME-agents sheet -> default-agents sheet -> DEFAULT_AGENT_MODELS
    """
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_FOR_MODELS_SHEET")
    spreadsheet_id = os.getenv("MODELS_GSPREAD_ID")
    env_name = os.getenv("ENV_NAME", "")

    if not credentials_path or not spreadsheet_id:
        return DEFAULT_AGENT_MODELS

    # 首先嘗試使用 ENV_NAME-agents 作為 sheet_name
    if env_name:
        sheet_name = f"{env_name}-agents"
        df = read_google_sheet(credentials_path, spreadsheet_id, sheet_name)
        if not df.empty and "model_name" in df.columns:
            try:
                return [
                    row["model_name"] for _, row in df.iterrows() if row["model_name"]
                ]
            except Exception:
                pass

    # 如果 ENV_NAME-agents sheet 找不到或有問題，嘗試 default-agents sheet
    df = read_google_sheet(credentials_path, spreadsheet_id, "default-agents")
    if not df.empty and "model_name" in df.columns:
        try:
            return [row["model_name"] for _, row in df.iterrows() if row["model_name"]]
        except Exception:
            pass

    # 如果都失敗，回退到 DEFAULT_AGENT_MODELS
    return DEFAULT_AGENT_MODELS


# 定義支援的 LLM models
DEFAULT_SUPPORTED_MODELS = [
    ModelInfo(
        display_name="gemini-2.5-flash",
        model_name="gemini-2.5-flash",
        provider="gemini",
    ),
    ModelInfo(
        display_name="claude-sonnet-4-5-20250929",
        model_name="claude-sonnet-4-5-20250929",
        provider="anthropic",
    ),
    ModelInfo(
        display_name="gemini-2.5-pro",
        model_name="gemini-2.5-pro",
        provider="gemini",
    ),
    ModelInfo(
        display_name="gpt-4.1-2025-04-14",
        model_name="gpt-4.1-2025-04-14",
        provider="openai",
    ),
    ModelInfo(
        display_name="o4-mini-2025-04-16",
        model_name="o4-mini-2025-04-16",
        provider="openai",
    ),
    ModelInfo(
        display_name="claude-3-5-haiku-latest",
        model_name="claude-3-5-haiku-latest",
        provider="anthropic",
    ),
    ModelInfo(display_name="gpt-4o-mini", model_name="gpt-4o-mini", provider="openai"),
    ModelInfo(
        display_name="gpt-4o-2024-08-06",
        model_name="gpt-4o-2024-08-06",
        provider="openai",
    ),
    ModelInfo(
        display_name="Meta-Llama-3.1-8B-Instruct",
        model_name="meta-llama/Meta-Llama-3.1-8B-Instruct",
        provider="deepinfra",
    ),
    ModelInfo(
        display_name="Meta-Llama-3.1-70B-Instruct-Turbo",
        model_name="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        provider="deepinfra",
    ),
    ModelInfo(
        display_name="Meta-Llama-3.1-405B-Instruct-Turbo",
        model_name="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        provider="together_ai",
    ),
    ModelInfo(
        display_name="Llama-3.1-Nemotron-70B-Instruct",
        model_name="nvidia/Llama-3.1-Nemotron-70B-Instruct",
        provider="deepinfra",
    ),
    ModelInfo(
        display_name="Llama-3.2-11B-Vision-Instruct-Turbo",
        model_name="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        provider="together_ai",
    ),
    ModelInfo(
        display_name="Llama-3.2-90B-Vision-Instruct-Turbo",
        model_name="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
        provider="together_ai",
    ),
    ModelInfo(
        display_name="gemma-2-9b-it",
        model_name="google/gemma-2-9b-it",
        provider="deepinfra",
    ),
    ModelInfo(
        display_name="gemma-2-27b-it",
        model_name="google/gemma-2-27b-it",
        provider="deepinfra",
    ),
    ModelInfo(
        display_name="Mixtral-8x7B-Instruct-v0.1",
        model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
        provider="deepinfra",
    ),
    ModelInfo(
        display_name="Mixtral-8x22B-Instruct-v0.1",
        model_name="mistralai/Mixtral-8x22B-Instruct-v0.1",
        provider="deepinfra",
    ),
    ModelInfo(
        display_name="WizardLM-2-8x22B",
        model_name="microsoft/WizardLM-2-8x22B",
        provider="deepinfra",
    ),
    ModelInfo(
        display_name="Meta-Llama-Guard-3-8B",
        model_name="meta-llama/Meta-Llama-Guard-3-8B",
        provider="together_ai",
    ),
    ModelInfo(display_name="o1-mini", model_name="o1-mini", provider="openai"),
    ModelInfo(display_name="o1-preview", model_name="o1-preview", provider="openai"),
]

# 定義支援 agent 的 LLM models
DEFAULT_AGENT_MODELS = [
    "claude-sonnet-4-5-20250929",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """
    列出所有支援的 LLM models
    優先從 Google Sheets 讀取，回退到預設列表

    Args:
        provider: 可選的提供商篩選 (openai, anthropic, google, perplexity, etc.)

    Returns:
        ModelsResponse: 包含 models 清單和總數
    """
    try:
        # 從 Google Sheets 或預設列表獲取模型
        all_models = get_models_from_google_sheet()

        return ModelsResponse(models=all_models, total_count=len(all_models))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve models: {str(e)}"
        )


@router.get("/models/agent-models", response_model=AgentModelsResponse)
async def list_agent_models():
    """
    列出所有支援的 agent models
    優先從 Google Sheets 讀取，回退到預設列表

    Returns:
        AgentModelsResponse: 包含 models 清單和總數
    """
    try:
        # 從 Google Sheets 或預設列表獲取模型
        all_models = get_agent_models_from_google_sheet()

        return AgentModelsResponse(models=all_models, total_count=len(all_models))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve agent models: {str(e)}"
        )
