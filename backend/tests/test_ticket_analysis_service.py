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


class TestThinkingMode:
    """思考模式测试。"""

    @pytest.mark.asyncio
    async def test_thinking_disabled_in_payload(self, monkeypatch):
        """确认非思考模式下请求体包含 thinking=disabled。"""
        from app.llm.openai_compatible import OpenAICompatibleLLMProvider

        provider = OpenAICompatibleLLMProvider(
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            api_key="sk-test",
            timeout_seconds=5.0,
            thinking_mode="disabled",
        )

        captured_payload: dict | None = None

        async def mock_post(self, url, **kwargs):
            nonlocal captured_payload
            captured_payload = kwargs.get("json", {})

            class MockResponse:
                status_code = 200

                def json(self):
                    return {
                        "model": "deepseek-v4-flash",
                        "choices": [{"message": {"content": '{"category":"支付问题","priority":"高","summary":"测试","tags":["测试"],"order_id":null,"confidence":0.9,"need_human_review":false,"uncertain_fields":[]}'}}],
                        "usage": {"total_tokens": 100},
                    }

            return MockResponse()

        monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

        # Run analysis through TicketAnalysisService (with repair disabled)
        from app.repair.retry_policy import RetryPolicy
        service = TicketAnalysisService(
            provider,
            retry_policy=RetryPolicy(max_attempts=1),
            repair_service=None,
        )
        await service.analyze("测试工单", "v1")

        assert captured_payload is not None, "请求未被发送"
        assert "thinking" in captured_payload, f"请求体缺少 thinking 字段: {captured_payload}"
        assert captured_payload["thinking"] == {"type": "disabled"}, \
            f"thinking 应为 disabled，实际：{captured_payload['thinking']}"

    @pytest.mark.asyncio
    async def test_repair_also_uses_disabled_thinking(self, monkeypatch):
        """确认修复请求同样使用 thinking=disabled。"""
        from app.llm.openai_compatible import OpenAICompatibleLLMProvider
        from app.repair.output_repair_service import OutputRepairService
        from app.repair.retry_policy import RetryPolicy

        provider = OpenAICompatibleLLMProvider(
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            api_key="sk-test",
            timeout_seconds=5.0,
            thinking_mode="disabled",
        )

        captured_payloads: list[dict] = []
        call_count = 0

        async def mock_post(self, url, **kwargs):
            nonlocal call_count
            call_count += 1
            captured_payloads.append(kwargs.get("json", {}))

            class MockResponse:
                status_code = 200

                def json(self):
                    if call_count == 1:
                        return {
                            "model": "deepseek-v4-flash",
                            "choices": [{"message": {"content": "not valid json {{{"}}],
                        }
                    return {
                        "model": "deepseek-v4-flash",
                        "choices": [{"message": {"content": '{"category":"支付问题","priority":"高","summary":"测试","tags":["测试"],"order_id":null,"confidence":0.9,"need_human_review":false,"uncertain_fields":[]}'}}],
                    }

            return MockResponse()

        monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

        repair_service = OutputRepairService(provider)
        service = TicketAnalysisService(
            provider,
            retry_policy=RetryPolicy(max_attempts=1),
            repair_service=repair_service,
            repair_enabled=True,
        )
        await service.analyze("测试工单", "v1")

        # Both first call and repair call should have thinking=disabled
        for i, payload in enumerate(captured_payloads):
            assert "thinking" in payload, f"调用 {i + 1} 缺少 thinking: {payload}"
            assert payload["thinking"] == {"type": "disabled"}, \
                f"调用 {i + 1} thinking 应为 disabled: {payload['thinking']}"

    def test_invalid_thinking_mode_rejected(self):
        """非法 thinking_mode 应抛出配置错误。"""
        from app.llm.openai_compatible import OpenAICompatibleLLMProvider

        with pytest.raises(Exception) as exc_info:
            OpenAICompatibleLLMProvider(
                model="test",
                base_url="https://test.example.com",
                api_key="sk-test",
                thinking_mode="invalid",
            )
        assert "LLM_THINKING_MODE" in str(exc_info.value) or "thinking" in str(exc_info.value).lower()
