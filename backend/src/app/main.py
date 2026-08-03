"""FastAPI 应用工厂。"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.tickets import router as tickets_router
from app.application.ticket_analysis_service import TicketAnalysisService
from app.llm.provider_factory import create_provider
from app.repair.retry_policy import RetryPolicy
from app.repair.output_repair_service import OutputRepairService
from app.domain.exceptions import LLMConfigurationError, RetryConfigurationError

logger = logging.getLogger(__name__)


def _create_retry_policy() -> RetryPolicy:
    """从环境变量创建 RetryPolicy。"""
    max_attempts_str = os.getenv("LLM_MAX_ATTEMPTS", "2")
    base_delay_str = os.getenv("LLM_RETRY_BASE_DELAY_SECONDS", "0.5")

    try:
        max_attempts = int(max_attempts_str)
        base_delay = float(base_delay_str)
    except (ValueError, TypeError) as exc:
        raise RetryConfigurationError(
            f"重试配置无效：LLM_MAX_ATTEMPTS={max_attempts_str}，"
            f"LLM_RETRY_BASE_DELAY_SECONDS={base_delay_str}"
        ) from exc

    return RetryPolicy(
        max_attempts=max_attempts,
        base_delay_seconds=base_delay,
    )


def create_app() -> FastAPI:
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    app = FastAPI(
        title="Ticket Analysis Service",
        description="工单文本分析服务",
        version="0.3.0",
    )

    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=[origin.strip() for origin in cors_origins],
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    

    # 创建 Provider
    try:
        provider = create_provider()
        logger.info("LLM Provider: %s", provider.model_name)
    except LLMConfigurationError as exc:
        logger.error("LLM 配置错误：%s", exc)
        raise

    # 创建 RetryPolicy
    try:
        retry_policy = _create_retry_policy()
        logger.info(
            "RetryPolicy: max_attempts=%d, base_delay=%.2fs",
            retry_policy.max_attempts,
            retry_policy.base_delay_seconds,
        )
    except RetryConfigurationError as exc:
        logger.error("重试配置错误：%s", exc)
        raise

    # 创建 OutputRepairService
    repair_enabled = os.getenv("LLM_OUTPUT_REPAIR_ENABLED", "true").strip().lower() == "true"
    repair_service = OutputRepairService(provider) if repair_enabled else None
    if repair_enabled:
        logger.info("OutputRepairService: enabled")
    else:
        logger.info("OutputRepairService: disabled")

    # 创建 Analysis Service
    app.state.analysis_service = TicketAnalysisService(
        provider=provider,
        retry_policy=retry_policy,
        repair_service=repair_service,
        repair_enabled=repair_enabled,
    )

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    app.include_router(tickets_router, prefix="/api/v1")

    return app


app = create_app()
