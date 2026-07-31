from fastapi import APIRouter
from app.models.requests import AnalyzeRequest
from app.models.responses import AnalysisResult, ErrorResponse
from app.application.analyzer import analyze_ticket

router = APIRouter(tags=["tickets"])


@router.post(
    "/tickets/analyze",
    response_model=AnalysisResult,
    responses={
        422: {"model": ErrorResponse, "description": "请求参数校验失败"},
    },
    summary="分析工单文本",
    description="对工单文本进行结构化分析，返回类别、优先级、摘要、标签等信息。",
)
async def analyze_ticket_endpoint(request: AnalyzeRequest) -> AnalysisResult:
    result = analyze_ticket(request.ticket_text, request.prompt_version)
    return result
