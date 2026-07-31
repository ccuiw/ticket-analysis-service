"""
LLM 消息和响应的领域类型。

这些数据类不依赖任何外部框架或 SDK，
是 LLM 层与应用层之间的约定。
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class LLMMessage:
    """一条聊天消息。"""
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    """LLM 返回的原始响应。"""
    content: str
    model: str
    usage: dict | None = None  # {"prompt_tokens": N, "completion_tokens": M, "total_tokens": T}
