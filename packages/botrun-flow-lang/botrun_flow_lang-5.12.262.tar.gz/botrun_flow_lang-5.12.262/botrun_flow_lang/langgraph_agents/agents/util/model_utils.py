"""
Utility module for LLM model-related functionality, including API key rotation.
"""

import os
import random
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


def get_model_instance(
    model_name: str, temperature: float = 0, enable_code_execution: bool = False
):
    """
    統一的模型實例獲取函數

    Args:
        model_name: 模型名稱
        temperature: 溫度參數
        enable_code_execution: 是否啟用代碼執行（僅 Gemini 2.5 支援）

    Returns:
        對應的模型實例
    """
    if model_name.startswith("gemini-"):
        model_kwargs = {}
        if enable_code_execution and "2.5" in model_name:
            model_kwargs["enable_code_execution"] = True

        return ChatGoogleGenerativeAI(
            model=model_name, temperature=temperature, **model_kwargs
        )

    elif model_name.startswith("claude-"):
        # 檢查是否有多個 Anthropic API keys
        anthropic_api_keys_str = os.getenv("ANTHROPIC_API_KEYS", "")
        anthropic_api_keys = [
            key.strip() for key in anthropic_api_keys_str.split(",") if key.strip()
        ]

        if anthropic_api_keys:
            return RotatingChatAnthropic(
                model_name=model_name,
                keys=anthropic_api_keys,
                temperature=temperature,
                max_tokens=64000,
            )
        elif os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_BASE_URL"):
            openrouter_model_name = "anthropic/claude-sonnet-4.5"
            return ChatOpenAI(
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
                model_name=openrouter_model_name,
                temperature=temperature,
                max_tokens=64000,
            )
        else:
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                max_tokens=64000,
            )

    elif model_name.startswith("gpt-"):
        if os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_BASE_URL"):
            return ChatOpenAI(
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
                model_name=f"openai/{model_name}",
                temperature=temperature,
                max_tokens=8192,
            )
        else:
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=8192,
            )

    else:
        # 預設使用 Gemini
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=temperature,
        )


class RotatingChatAnthropic:
    """A wrapper class for ChatAnthropic that rotates through multiple API keys."""

    def __init__(self, model_name, keys, temperature=0, max_tokens=8192):
        """
        Initialize the rotating key model.

        Args:
            model_name: The name of the Anthropic model to use
            keys: List of API keys to rotate through
            temperature: The temperature for model generation
            max_tokens: The maximum number of tokens to generate
        """
        self.keys = keys
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize with the first key
        self.base_model = ChatAnthropic(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=random.choice(self.keys) if self.keys else None,
        )

    def invoke(self, *args, **kwargs):
        """
        Invoke the model with a randomly selected API key.

        This method is called when the model is invoked through LangChain.
        """
        if self.keys:
            # Select a random key for this invocation
            self.base_model.client.api_key = random.choice(self.keys)
        return self.base_model.invoke(*args, **kwargs)

    def stream(self, *args, **kwargs):
        """
        Stream the model response with a randomly selected API key.

        This method handles streaming output from the model.
        """
        if self.keys:
            # Select a random key for this streaming invocation
            self.base_model.client.api_key = random.choice(self.keys)
        return self.base_model.stream(*args, **kwargs)

    def __getattr__(self, name):
        """
        Forward any other attribute access to the base model.

        This ensures compatibility with the original ChatAnthropic class.
        """
        return getattr(self.base_model, name)
