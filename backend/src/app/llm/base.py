"""
大模型供应商抽象接口。

所有模型供应商必须实现此接口，从而将具体 SDK
与业务逻辑隔离。
"""

from abc import ABC, abstractmethod
from app.llm.messages import LLMMessage, LLMResponse


class BaseLLMProvider(ABC):
    """大模型供应商抽象基类。

    每个具体实现必须：
    1. 实现 analyze 方法，接收结构化消息列表，返回 LLMResponse；
    2. 实现 model_name 属性；
    3. 将供应商或网络异常转换成 app.domain.exceptions 中定义的领域异常。
    """

    @abstractmethod
    async def analyze(self, messages: list[LLMMessage]) -> LLMResponse:
        """发送消息到模型并返回原始文本响应。

        Args:
            messages: 结构化消息列表（至少包含一条 system 和一条 user 消息）。

        Returns:
            LLMResponse，包含模型返回的文本和元数据。

        Raises:
            LLMConfigurationError: 配置无效。
            LLMAuthenticationError: 鉴权失败。
            LLMTimeoutError: 请求超时。
            LLMRequestError: 其他请求错误。
            LLMEmptyResponseError: 模型返回空内容。
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回模型标识符（用于日志和审计）。"""
        ...
