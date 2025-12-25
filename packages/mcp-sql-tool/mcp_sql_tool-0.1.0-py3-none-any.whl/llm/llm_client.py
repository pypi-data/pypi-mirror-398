"""LLM 客户端：支持多种 LLM 提供商"""

import os
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """LLM 客户端基类"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本

        Args:
            prompt: 输入提示
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        pass


class OpenAIClient(LLMClient):
    """OpenAI 客户端"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", **kwargs):
        """
        初始化 OpenAI 客户端

        Args:
            api_key: API 密钥
            model: 模型名称
            **kwargs: 其他参数（temperature, max_tokens 等）
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required. Install it with: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.default_params = {
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        params = {**self.default_params, **kwargs}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **params,
        )
        return response.choices[0].message.content


class ClaudeClient(LLMClient):
    """Anthropic Claude 客户端"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229", **kwargs):
        """
        初始化 Claude 客户端

        Args:
            api_key: API 密钥
            model: 模型名称
            **kwargs: 其他参数
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic package is required. Install it with: pip install anthropic")

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        self.model = model
        self.client = Anthropic(api_key=self.api_key)
        self.default_params = {
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        params = {**self.default_params, **kwargs}
        response = self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **params,
        )
        return response.content[0].text


class QwenClient(LLMClient):
    """通义千问客户端"""

    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-turbo", **kwargs):
        """
        初始化通义千问客户端

        Args:
            api_key: API 密钥
            model: 模型名称
            **kwargs: 其他参数
        """
        try:
            import dashscope
        except ImportError:
            raise ImportError("dashscope package is required. Install it with: pip install dashscope")

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DashScope API key is required")

        dashscope.api_key = self.api_key
        self.model = model
        self.default_params = {
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        from dashscope import Generation

        params = {**self.default_params, **kwargs}
        response = Generation.call(
            model=self.model,
            prompt=prompt,
            **params,
        )

        if response.status_code == 200:
            return response.output.text
        else:
            raise Exception(f"Qwen API error: {response.message}")


def create_llm_client(provider: str, **kwargs) -> LLMClient:
    """
    创建 LLM 客户端

    Args:
        provider: 提供商名称（'openai', 'claude', 'qwen'）
        **kwargs: 客户端参数

    Returns:
        LLM 客户端实例
    """
    provider = provider.lower()
    if provider == "openai":
        return OpenAIClient(**kwargs)
    elif provider == "claude" or provider == "anthropic":
        return ClaudeClient(**kwargs)
    elif provider == "qwen" or provider == "dashscope":
        return QwenClient(**kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

