from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """工单分析结果。"""

    category: str = Field(..., description="工单类别")
    priority: str = Field(..., description="优先级")
    summary: str = Field(..., description="工单简短摘要")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    order_id: str | None = Field(None, description="关联订单号，无法提取时为 null")
    confidence: float = Field(..., ge=0.0, le=1.0, description="模型置信度")
    need_human_review: bool = Field(..., description="是否需要人工审核")
    uncertain_fields: list[str] = Field(
        default_factory=list,
        description="信息不足的字段列表",
    )


class ErrorResponse(BaseModel):
    """标准化错误响应。"""

    detail: str = Field(..., description="人类可读的错误说明")
    error_type: str = Field(
        ...,
        description="错误类型：validation_error | analysis_error | internal_error",
    )
