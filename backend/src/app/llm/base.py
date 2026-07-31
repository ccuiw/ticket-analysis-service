"""
大模型供应商抽象接口。

所有模型供应商必须实现此接口，从而将具体 SDK
与业务逻辑隔离。初始化阶段仅有接口定义，无具体实现。
"""

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """大模型供应商抽象基类。

    每个具体实现（如 OpenAI、Anthropic）必须：
    1. 实现 analyze 方法；
    2. 实现 model_name 属性；
    3. 自行处理认证、超时和重试。
    """

    @abstractmethod
    async def analyze(self, prompt: str) -> str:
        """发送提示词到模型并返回原始文本响应。"""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回模型标识符（用于日志和审计）。"""
        ...
