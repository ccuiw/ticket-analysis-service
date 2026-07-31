"""FastAPI 应用工厂。"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.tickets import router as tickets_router
from app.application.ticket_analysis_service import TicketAnalysisService
from app.llm.provider_factory import create_provider
from app.domain.exceptions import LLMConfigurationError

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    app = FastAPI(
        title="Ticket Analysis Service",
        description="工单文本分析服务",
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 创建 Provider 和 Analysis Service
    try:
        provider = create_provider()
        logger.info("LLM Provider: %s", provider.model_name)
    except LLMConfigurationError as exc:
        logger.error("LLM 配置错误：%s", exc)
        raise

    app.state.analysis_service = TicketAnalysisService(provider)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    app.include_router(tickets_router, prefix="/api/v1")

    return app


app = create_app()
