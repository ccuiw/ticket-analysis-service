import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient 实例。"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def valid_ticket_text() -> str:
    """有效的工单测试文本。"""
    return "我已经付款，但是会员还没有生效。"


@pytest.fixture
def valid_request_body(valid_ticket_text: str) -> dict:
    """有效的完整请求体。"""
    return {
        "ticket_text": valid_ticket_text,
        "prompt_version": "v1",
    }
