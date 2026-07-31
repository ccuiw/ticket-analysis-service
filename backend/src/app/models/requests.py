from typing import Literal
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """工单分析请求。"""

    ticket_text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="待分析的工单文本",
        examples=["我已经付款，但是会员还没有生效。"],
    )
    prompt_version: Literal["v1", "v2"] = Field(
        "v1",
        description="提示词版本：v1 (Zero-shot) 或 v2 (Few-shot)",
    )
