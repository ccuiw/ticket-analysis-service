"""TicketAnalysisService 测试。"""

import pytest
import httpx
from app.llm.mock_provider import MockLLMProvider
from app.llm.messages import LLMMessage, LLMResponse
from app.application.ticket_analysis_service import TicketAnalysisService
from app.domain.exceptions import (
    AnalysisError,
    LLMTimeoutError,
    LLMEmptyResponseError,
)
from app.models.responses import AnalysisResult


class TestTicketAnalysisService:
    @pytest.fixture
    def service(self):
        return TicketAnalysisService(MockLLMProvider())

    @pytest.mark.asyncio
    async def test_analyze_returns_analysis_result(self, service):
        result = await service.analyze("付款后会员没到账", "v1")
        assert isinstance(result, AnalysisResult)
        assert result.category == "支付问题"

    @pytest.mark.asyncio
    async def test_analyze_with_v2(self, service):
        result = await service.analyze("退款申请", "v2")
        assert isinstance(result, AnalysisResult)
        assert result.category == "退款问题"

    @pytest.mark.asyncio
    async def test_empty_ticket_text_raises(self, service):
        with pytest.raises(AnalysisError, match="不能为空"):
            await service.analyze("", "v1")

    @pytest.mark.asyncio
    async def test_whitespace_only_raises(self, service):
        with pytest.raises(AnalysisError, match="不能为空"):
            await service.analyze("   ", "v1")

    @pytest.mark.asyncio
    async def test_provider_name(self, service):
        assert service.provider_name == "mock"

    @pytest.mark.asyncio
    async def test_llm_timeout_mapped(self):
        """LLM timeout 异常映射测试。"""

        class TimeoutProvider(MockLLMProvider):
            async def analyze(self, messages):
                raise LLMTimeoutError("timeout")

        service = TicketAnalysisService(TimeoutProvider())
        with pytest.raises(LLMTimeoutError, match="timeout"):
            await service.analyze("test", "v1")

    @pytest.mark.asyncio
    async def test_llm_empty_response_mapped(self):
        """LLM 空响应异常映射测试。"""

        class EmptyProvider(MockLLMProvider):
            async def analyze(self, messages):
                raise LLMEmptyResponseError("empty")

        service = TicketAnalysisService(EmptyProvider())
        with pytest.raises(LLMEmptyResponseError, match="empty"):
            await service.analyze("test", "v1")


class TestServiceWithFakeLLM:
    """通过 monkeypatch 模拟真实 Provider 的 HTTP 调用。"""

    @pytest.mark.asyncio
    async def test_openai_compatible_mock_transport(self, monkeypatch):
        """模拟 OpenAI-compatible Provider 的 HTTP 响应。"""
        from app.llm.openai_compatible import OpenAICompatibleLLMProvider

        provider = OpenAICompatibleLLMProvider(
            model="test-model",
            base_url="https://test.example.com/v1",
            api_key="sk-test",
            timeout_seconds=5.0,
        )

        # 用 monkeypatch 替换 httpx.AsyncClient.post
        original_post = httpx.AsyncClient.post

        async def mock_post(self, url, **kwargs):
            class MockResponse:
                status_code = 200

                def json(self):
                    return {
                        "model": "test-model",
                        "choices": [
                            {
                                "message": {
                                    "content": '{"category":"支付问题","priority":"高","summary":"测试","tags":["测试"],"order_id":null,"confidence":0.9,"need_human_review":false,"uncertain_fields":[]}'
                                }
                            }
                        ],
                        "usage": {"total_tokens": 100},
                    }

            return MockResponse()

        monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

        service = TicketAnalysisService(provider)
        result = await service.analyze("测试工单", "v1")
        assert result.category == "支付问题"
        assert result.confidence == 0.9
