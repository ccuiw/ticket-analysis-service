"""修复 + 重试 集成测试。

使用 Mock/Fake Provider，不访问真实网络。
"""

import json
import pytest
from fastapi.testclient import TestClient
from app.llm.base import BaseLLMProvider
from app.llm.messages import LLMMessage, LLMResponse
from app.llm.mock_provider import MockLLMProvider
from app.application.ticket_analysis_service import TicketAnalysisService
from app.repair.retry_policy import RetryPolicy
from app.repair.output_repair_service import OutputRepairService
from app.domain.exceptions import (
    LLMTimeoutError,
    LLMAuthenticationError,
    OutputRepairExhaustedError,
    OutputParseError,
)
from app.models.responses import AnalysisResult


class TestServiceWithRetry:
    """TicketAnalysisService 重试测试。"""

    @pytest.mark.asyncio
    async def test_valid_json_no_retry(self):
        """首次合法 JSON 不触发重试或修复。"""
        provider = MockLLMProvider()
        service = TicketAnalysisService(
            provider,
            retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0),
            repair_service=OutputRepairService(provider),
        )
        result = await service.analyze("付款问题", "v1")
        assert isinstance(result, AnalysisResult)
        assert result.category == "支付问题"

    @pytest.mark.asyncio
    async def test_timeout_retry_succeeds(self):
        """Timeout 后重试成功。"""
        call_count = 0

        class RetryOKProvider(MockLLMProvider):
            async def analyze(self, messages):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise LLMTimeoutError("timeout")
                return await super().analyze(messages)

        service = TicketAnalysisService(
            RetryOKProvider(),
            retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0, backoff_multiplier=0),
        )
        result = await service.analyze("付款", "v1")
        assert result.category == "支付问题"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_retry_exhausted(self):
        """Timeout 达到上限后失败。"""
        class AlwaysTimeout(MockLLMProvider):
            async def analyze(self, messages):
                raise LLMTimeoutError("always timeout")

        service = TicketAnalysisService(
            AlwaysTimeout(),
            retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0, backoff_multiplier=0),
        )
        with pytest.raises(LLMTimeoutError):
            await service.analyze("test", "v1")

    @pytest.mark.asyncio
    async def test_401_no_retry(self):
        """鉴权错误不重试。"""
        call_count = 0

        class AuthFailProvider(MockLLMProvider):
            async def analyze(self, messages):
                nonlocal call_count
                call_count += 1
                raise LLMAuthenticationError("bad key")

        service = TicketAnalysisService(
            AuthFailProvider(),
            retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0, backoff_multiplier=0),
        )
        with pytest.raises(LLMAuthenticationError):
            await service.analyze("test", "v1")
        assert call_count == 1


class TestServiceWithRepair:
    """TicketAnalysisService 输出修复测试。"""

    @pytest.mark.asyncio
    async def test_markdown_wrapped_repair_succeeds(self):
        """Markdown 包裹 JSON → 修复成功。"""
        valid_json = json.dumps({
            "category": "支付问题", "priority": "高",
            "summary": "测试", "tags": ["支付"],
            "order_id": None, "confidence": 0.95,
            "need_human_review": False, "uncertain_fields": [],
        }, ensure_ascii=False)

        class MarkdownProvider(MockLLMProvider):
            async def analyze(self, messages):
                return LLMResponse(
                    content=f"```json\n{valid_json}\n```",
                    model="markdown",
                )

        # Repair provider returns clean JSON (fixes the markdown wrapping)
        class CleanRepairProvider(MockLLMProvider):
            async def analyze(self, messages):
                return LLMResponse(content=valid_json, model="clean-fix")

        provider = MarkdownProvider()
        repair_svc = OutputRepairService(CleanRepairProvider())

        service = TicketAnalysisService(
            provider,
            retry_policy=RetryPolicy(max_attempts=1),
            repair_service=repair_svc,
        )
        result = await service.analyze("付款", "v1")
        assert result.category == "支付问题"

    @pytest.mark.asyncio
    async def test_invalid_json_repair_succeeds(self):
        """非法 JSON → 修复成功。"""
        repaired_json = json.dumps({
            "category": "支付问题", "priority": "高",
            "summary": "修复后", "tags": ["支付"],
            "order_id": None, "confidence": 0.9,
            "need_human_review": False, "uncertain_fields": [],
        }, ensure_ascii=False)

        class BrokenThenFixedProvider(MockLLMProvider):
            def __init__(self):
                super().__init__()
                self.call_count = 0

            async def analyze(self, messages):
                self.call_count += 1
                if self.call_count == 1:
                    # First call: broken
                    return LLMResponse(content="not valid json {{{", model="broken")
                # Repair call: fixed
                return LLMResponse(content=repaired_json, model="fixed")

        provider = BrokenThenFixedProvider()
        service = TicketAnalysisService(
            provider,
            retry_policy=RetryPolicy(max_attempts=1),
            repair_service=OutputRepairService(provider),
        )
        result = await service.analyze("test", "v1")
        assert result.category == "支付问题"

    @pytest.mark.asyncio
    async def test_repair_still_fails(self):
        """修复后仍非法 → OutputRepairExhaustedError。"""

        class AlwaysBroken(MockLLMProvider):
            async def analyze(self, messages):
                return LLMResponse(content="not json at all {{{", model="broken")

        service = TicketAnalysisService(
            AlwaysBroken(),
            retry_policy=RetryPolicy(max_attempts=1),
            repair_service=OutputRepairService(AlwaysBroken()),
        )
        with pytest.raises(OutputRepairExhaustedError):
            await service.analyze("test", "v1")

    @pytest.mark.asyncio
    async def test_repair_disabled(self):
        """修复关闭时不触发修复。"""
        broken_json = "not valid json {{{"

        class BrokenProvider(MockLLMProvider):
            async def analyze(self, messages):
                return LLMResponse(content=broken_json, model="broken")

        service = TicketAnalysisService(
            BrokenProvider(),
            retry_policy=RetryPolicy(max_attempts=1),
            repair_service=None,
            repair_enabled=False,
        )
        with pytest.raises(OutputParseError):
            await service.analyze("test", "v1")

    @pytest.mark.asyncio
    async def test_repair_count_never_exceeds_limit(self):
        """修复调用次数永不超过配置。"""
        call_count = 0

        class CountingProvider(MockLLMProvider):
            async def analyze(self, messages):
                nonlocal call_count
                call_count += 1
                return LLMResponse(content="not json {{{", model="broken")

        provider = CountingProvider()
        service = TicketAnalysisService(
            provider,
            retry_policy=RetryPolicy(max_attempts=1),
            repair_service=OutputRepairService(provider),
        )
        with pytest.raises(OutputRepairExhaustedError):
            await service.analyze("test", "v1")
        # 1 initial call + 1 repair call = 2 (repair itself calls the same broken provider)
        # The repair provider is the same broken one, so it also fails
        assert call_count <= 3  # initial + repair + any retries = bounded


class TestApiRepairIntegration:
    """API 层面的修复集成测试。"""

    def test_valid_request_still_returns_200(self, client: TestClient):
        body = {"ticket_text": "付款后会员没到账", "prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 200

    def test_empty_ticket_still_returns_422(self, client: TestClient):
        body = {"ticket_text": "", "prompt_version": "v1"}
        response = client.post("/api/v1/tickets/analyze", json=body)
        assert response.status_code == 422

    def test_health_still_works(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
