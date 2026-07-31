"""
OpenAI-compatible Chat Completions Provider。

通过 httpx 调用任意兼容 OpenAI Chat Completions API 的服务。
不依赖 openai SDK。
"""

import os
import httpx
from app.llm.base import BaseLLMProvider
from app.llm.messages import LLMMessage, LLMResponse
from app.domain.exceptions import (
    LLMConfigurationError,
    LLMAuthenticationError,
    LLMTimeoutError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMServerError,
    LLMRequestError,
    LLMEmptyResponseError,
)


class OpenAICompatibleLLMProvider(BaseLLMProvider):
    """OpenAI-compatible Chat Completions 供应商。

    通过 httpx.AsyncClient 发送请求，将网络异常
    和 API 错误统一转换为领域异常。
    """

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key:
            raise LLMConfigurationError("未配置 LLM_API_KEY")
        if not base_url:
            raise LLMConfigurationError("未配置 LLM_BASE_URL")
        if not model:
            raise LLMConfigurationError("未配置 LLM_MODEL")

        self._model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client: httpx.AsyncClient | None = None

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze(self, messages: list[LLMMessage]) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "temperature": 0.0,
        }

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with self._get_client() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
            except httpx.ConnectError as exc:
                raise LLMConnectionError(f"LLM 连接失败：{exc}") from exc
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(
                    f"LLM 请求超时（{self._timeout} 秒）"
                ) from exc
            except httpx.RequestError as exc:
                raise LLMRequestError(f"LLM 请求失败：{exc}") from exc

        status = response.status_code

        if status == 401 or status == 403:
            raise LLMAuthenticationError("LLM 鉴权失败，请检查 LLM_API_KEY")
        if status == 429:
            retry_after = response.headers.get("Retry-After", "未知")
            raise LLMRateLimitError(
                f"LLM 速率限制（HTTP 429），Retry-After: {retry_after}"
            )
        _RETRYABLE_5XX = {500, 502, 503, 504}
        if status in _RETRYABLE_5XX:
            raise LLMServerError(
                f"LLM 服务端错误（HTTP {status}）：{response.text[:500]}"
            )
        if status != 200:
            raise LLMRequestError(
                f"LLM 服务返回错误（HTTP {status}）：{response.text[:500]}"
            )

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LLMEmptyResponseError("LLM 返回了空响应")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise LLMEmptyResponseError("LLM 返回了空内容")

        return LLMResponse(
            content=content,
            model=data.get("model", self._model),
            usage=data.get("usage"),
        )

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self._timeout)
