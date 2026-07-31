"""工单分析 API 路由。

只负责：接收请求、调用应用服务、将领域异常映射为 HTTP 响应。
不包含 LLM 调用、提示词加载或 JSON 解析逻辑。
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.models.requests import AnalyzeRequest
from app.models.responses import AnalysisResult, ErrorResponse
from app.domain.exceptions import (
    DomainError,
    AnalysisError,
    PromptNotFoundError,
    PromptRenderError,
    LLMConfigurationError,
    LLMAuthenticationError,
    LLMTimeoutError,
    LLMRequestError,
    LLMEmptyResponseError,
    OutputParseError,
    OutputValidationError,
)

router = APIRouter(tags=["tickets"])


def _get_service(request: Request):
    """从应用状态中获取 TicketAnalysisService。"""
    return request.app.state.analysis_service


@router.post(
    "/tickets/analyze",
    response_model=AnalysisResult,
    responses={
        422: {"model": ErrorResponse, "description": "请求参数或输出校验失败"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"},
        502: {"model": ErrorResponse, "description": "LLM 服务不可用"},
        503: {"model": ErrorResponse, "description": "LLM 配置错误"},
        504: {"model": ErrorResponse, "description": "LLM 请求超时"},
    },
    summary="分析工单文本",
    description="对工单文本进行结构化分析，返回类别、优先级、摘要、标签等信息。",
)
async def analyze_ticket_endpoint(
    request: AnalyzeRequest, req: Request
) -> AnalysisResult:
    service = _get_service(req)
    try:
        return await service.analyze(
            request.ticket_text, request.prompt_version
        )
    except OutputParseError as exc:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                detail=str(exc), error_type="output_parse_error"
            ).model_dump(),
        )
    except OutputValidationError as exc:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                detail=str(exc), error_type="output_validation_error"
            ).model_dump(),
        )
    except PromptNotFoundError as exc:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=str(exc), error_type="prompt_not_found"
            ).model_dump(),
        )
    except PromptRenderError as exc:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=str(exc), error_type="prompt_render_error"
            ).model_dump(),
        )
    except LLMConfigurationError as exc:
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                detail=str(exc), error_type="llm_configuration_error"
            ).model_dump(),
        )
    except LLMAuthenticationError as exc:
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                detail="LLM 鉴权失败，请检查服务配置",
                error_type="llm_authentication_error",
            ).model_dump(),
        )
    except LLMTimeoutError as exc:
        return JSONResponse(
            status_code=504,
            content=ErrorResponse(
                detail=str(exc), error_type="llm_timeout_error"
            ).model_dump(),
        )
    except (LLMRequestError, LLMEmptyResponseError) as exc:
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(
                detail=str(exc), error_type="llm_request_error"
            ).model_dump(),
        )
    except AnalysisError as exc:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=str(exc), error_type="analysis_error"
            ).model_dump(),
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail=str(exc), error_type="internal_error"
            ).model_dump(),
        )
