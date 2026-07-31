"""
领域异常层次结构。

这些异常不依赖 FastAPI、Pydantic 或任何外部 SDK，
保持领域层的纯净性和可移植性。
"""


class DomainError(Exception):
    """所有领域异常的基类。"""
    pass


# -- 分析流程异常 --

class AnalysisError(DomainError):
    """分析流程中的通用错误。"""
    pass


# -- 提示词异常 --

class PromptNotFoundError(DomainError):
    """提示词文件未找到。"""
    pass


class PromptRenderError(DomainError):
    """提示词模板渲染失败（变量缺失或语法错误）。"""
    pass


# -- LLM 供应商异常 --

class LLMError(DomainError):
    """LLM 供应商相关的基类异常。"""
    pass


class LLMConfigurationError(LLMError):
    """LLM 配置缺失或无效（如缺少 API Key、非法 Provider 名称）。"""
    pass


class LLMAuthenticationError(LLMError):
    """LLM 鉴权失败（API Key 无效或过期）。不可重试。"""
    pass


class LLMTimeoutError(LLMError):
    """LLM 请求超时。可重试。"""
    pass


class LLMConnectionError(LLMError):
    """LLM 连接失败（DNS、TCP 或 TLS 错误）。可重试。"""
    pass


class LLMRateLimitError(LLMError):
    """LLM 速率限制（HTTP 429）。可重试。"""
    pass


class LLMServerError(LLMError):
    """LLM 服务端错误（HTTP 5xx，可重试）。"""
    pass


class LLMRequestError(LLMError):
    """LLM 请求失败（其他不可重试的错误）。"""
    pass


class LLMEmptyResponseError(LLMError):
    """LLM 返回空响应。"""
    pass


# -- 输出处理异常 --

class OutputParseError(DomainError):
    """模型输出 JSON 解析失败。可触发修复。"""
    pass


class OutputValidationError(DomainError):
    """模型输出结构校验失败。可触发修复。"""
    pass


# -- 修复异常 --

class OutputRepairError(DomainError):
    """输出修复相关的基类异常。"""
    pass


class OutputRepairExhaustedError(OutputRepairError):
    """输出修复已达到最大尝试次数。"""
    pass


# -- 重试配置异常 --

class RetryConfigurationError(DomainError):
    """重试配置无效。"""
    pass


# -- 保留的旧异常（兼容） --

class ValidationError(DomainError):
    """数据校验失败（已废弃，请使用 OutputValidationError）。"""
    pass


class RepairFailedError(DomainError):
    """JSON 修复失败（已废弃，请使用 OutputRepairExhaustedError）。"""
    pass
