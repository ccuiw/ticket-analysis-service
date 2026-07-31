"""
网络重试策略。

确定哪些 LLM 异常可重试，控制重试次数和等待时间。
不包含输出修复逻辑——修复由 OutputRepairService 负责。
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, Awaitable, TypeVar
from app.domain.exceptions import (
    LLMError,
    LLMTimeoutError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMServerError,
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMRequestError,
    LLMEmptyResponseError,
    RetryConfigurationError,
)

logger = logging.getLogger(__name__)
T = TypeVar("T")

# 默认可重试的错误类型
_RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    LLMTimeoutError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMServerError,
)


@dataclass
class RetryPolicy:
    """网络重试策略。

    控制哪些 LLM 错误可以重试，以及重试次数和等待策略。
    """

    max_attempts: int = 2
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 5.0
    backoff_multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise RetryConfigurationError(
                f"LLM_MAX_ATTEMPTS 必须 >= 1，当前值：{self.max_attempts}"
            )
        if self.base_delay_seconds < 0:
            raise RetryConfigurationError(
                "LLM_RETRY_BASE_DELAY_SECONDS 不能为负数"
            )

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试。

        Args:
            error: 发生的异常。
            attempt: 当前是第几次尝试（1-indexed）。

        Returns:
            是否应该重试。
        """
        if attempt >= self.max_attempts:
            return False
        return isinstance(error, _RETRYABLE_ERRORS)

    def delay_for(self, attempt: int) -> float:
        """计算第 attempt 次重试前的等待秒数。

        使用指数退避：base * multiplier^(attempt-1)，上限 max_delay_seconds。
        """
        delay = self.base_delay_seconds * (self.backoff_multiplier ** (attempt - 1))
        return min(delay, self.max_delay_seconds)

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str = "LLM call",
    ) -> T:
        """执行操作，在可重试错误时自动重试。

        Args:
            operation: 要执行的异步操作（如 provider.analyze）。
            operation_name: 操作名称，用于日志。

        Returns:
            操作成功的结果。

        Raises:
            最后一次尝试的异常（不可重试，或达到最大次数）。
        """
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.debug("%s 尝试 %d/%d", operation_name, attempt, self.max_attempts)
                return await operation()
            except Exception as exc:
                last_error = exc
                if self.should_retry(exc, attempt):
                    delay = self.delay_for(attempt)
                    logger.warning(
                        "%s 尝试 %d/%d 失败（%s），%s 秒后重试",
                        operation_name,
                        attempt,
                        self.max_attempts,
                        type(exc).__name__,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "%s 尝试 %d/%d 失败（%s），不重试",
                        operation_name,
                        attempt,
                        self.max_attempts,
                        type(exc).__name__,
                    )
                    raise

        raise last_error  # type: ignore[misc]
