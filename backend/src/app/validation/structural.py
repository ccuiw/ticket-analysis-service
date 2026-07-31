"""
结构化校验。

将解析后的字典通过 Pydantic 模型进行校验，
确保数据结构符合 API 契约。
"""

from pydantic import ValidationError as PydanticValidationError
from app.models.responses import AnalysisResult
from app.domain.exceptions import ValidationError


def validate_structure(data: dict) -> AnalysisResult:
    """使用 Pydantic 模型校验字典数据结构。

    Args:
        data: 解析后的原始字典。

    Returns:
        校验通过的 AnalysisResult 实例。

    Raises:
        ValidationError: 数据不符合 AnalysisResult 结构。
    """
    try:
        return AnalysisResult.model_validate(data)
    except PydanticValidationError as exc:
        raise ValidationError(f"分析结果结构校验失败：{exc}") from exc
