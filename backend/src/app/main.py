import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.tickets import router as tickets_router


def create_app() -> FastAPI:
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    app = FastAPI(
        title="Ticket Analysis Service",
        description="工单文本分析服务",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    app.include_router(tickets_router, prefix="/api/v1")

    return app


app = create_app()
