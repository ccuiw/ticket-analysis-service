"""
LLM Provider 工厂函数。

根据环境变量选择并配置 Provider 实例。
"""

import os
from app.llm.base import BaseLLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_compatible import OpenAICompatibleLLMProvider
from app.domain.exceptions import LLMConfigurationError


def create_provider() -> BaseLLMProvider:
    """根据 LLM_PROVIDER 环境变量创建 Provider 实例。

    环境变量：
        LLM_PROVIDER: "mock"（默认）或 "openai_compatible"
        LLM_API_KEY: API 密钥（openai_compatible 时必需）
        LLM_BASE_URL: API 基础 URL（openai_compatible 时必需）
        LLM_MODEL: 模型名称（openai_compatible 时必需）
        LLM_TIMEOUT_SECONDS: 超时秒数（默认 30）

    Returns:
        BaseLLMProvider 实例。

    Raises:
        LLMConfigurationError: 配置无效或缺失。
    """
    provider_type = os.getenv("LLM_PROVIDER", "mock").strip().lower()

    if provider_type == "mock":
        return MockLLMProvider()

    if provider_type == "openai_compatible":
        api_key = os.getenv("LLM_API_KEY", "").strip()
        base_url = os.getenv("LLM_BASE_URL", "").strip()
        model = os.getenv("LLM_MODEL", "").strip()
        timeout_str = os.getenv("LLM_TIMEOUT_SECONDS", "30").strip()

        if not api_key:
            raise LLMConfigurationError(
                "已选择 openai_compatible Provider，但未配置 LLM_API_KEY"
            )
        if not base_url:
            raise LLMConfigurationError(
                "已选择 openai_compatible Provider，但未配置 LLM_BASE_URL"
            )
        if not model:
            raise LLMConfigurationError(
                "已选择 openai_compatible Provider，但未配置 LLM_MODEL"
            )

        try:
            timeout = float(timeout_str)
        except ValueError:
            raise LLMConfigurationError(
                f"LLM_TIMEOUT_SECONDS 必须是数字，当前值：{timeout_str}"
            )

        return OpenAICompatibleLLMProvider(
            model=model,
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=timeout,
        )

    raise LLMConfigurationError(
        f"不支持的 LLM_PROVIDER：{provider_type}。"
        f"支持的值：mock、openai_compatible"
    )
