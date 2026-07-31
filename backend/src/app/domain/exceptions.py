"""
领域异常层次结构。

这些异常不依赖 FastAPI、Pydantic 或任何外部 SDK，
保持领域层的纯净性和可移植性。
"""


class DomainError(Exception):
    """所有领域异常的基类。"""
    pass


class AnalysisError(DomainError):
    """分析流程中的错误。"""
    pass


class ValidationError(DomainError):
    """数据校验失败。"""
    pass


class RepairFailedError(DomainError):
    """JSON 修复失败。"""
    pass


class PromptNotFoundError(DomainError):
    """提示词文件未找到。"""
    pass
