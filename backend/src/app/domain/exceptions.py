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
    """LLM 鉴权失败（API Key 无效或过期）。"""
    pass


class LLMTimeoutError(LLMError):
    """LLM 请求超时。"""
    pass


class LLMRequestError(LLMError):
    """LLM 请求失败（网络错误、服务端错误等）。"""
    pass


class LLMEmptyResponseError(LLMError):
    """LLM 返回空响应。"""
    pass


# -- 输出处理异常 --

class OutputParseError(DomainError):
    """模型输出 JSON 解析失败。"""
    pass


class OutputValidationError(DomainError):
    """模型输出结构校验失败。"""
    pass


# -- 保留的旧异常（兼容） --

class ValidationError(DomainError):
    """数据校验失败（已废弃，请使用 OutputValidationError）。"""
    pass


class RepairFailedError(DomainError):
    """JSON 修复失败（后续阶段实现）。"""
    pass
