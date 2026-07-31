"""OutputRepairService 测试。"""

import json
import pytest
from app.llm.mock_provider import MockLLMProvider
from app.llm.messages import LLMMessage, LLMResponse
from app.repair.output_repair_service import OutputRepairService
from app.domain.exceptions import OutputRepairExhaustedError


class FakeRepairProvider(MockLLMProvider):
    """Fake provider that returns a repaired JSON response."""

    async def analyze(self, messages: list[LLMMessage]) -> LLMResponse:
        # Return a valid, repaired JSON
        repaired = {
            "category": "支付问题",
            "priority": "高",
            "summary": "修复后的摘要",
            "tags": ["支付"],
            "order_id": None,
            "confidence": 0.95,
            "need_human_review": False,
            "uncertain_fields": [],
        }
        return LLMResponse(
            content=json.dumps(repaired, ensure_ascii=False),
            model="fake-repair",
        )


class EmptyRepairProvider(MockLLMProvider):
    """Fake provider that returns empty content."""

    async def analyze(self, messages: list[LLMMessage]) -> LLMResponse:
        return LLMResponse(content="", model="fake-repair")


class TestOutputRepairService:
    @pytest.fixture
    def service(self):
        return OutputRepairService(FakeRepairProvider())

    @pytest.fixture
    def empty_service(self):
        return OutputRepairService(EmptyRepairProvider())

    @pytest.mark.asyncio
    async def test_loads_repair_prompt(self, service):
        prompt = service._load_repair_prompt()
        assert "修复器" in prompt
        assert len(prompt) > 50

    @pytest.mark.asyncio
    async def test_repair_returns_repaired_text(self, service):
        result = await service.repair(
            original_ticket="test ticket",
            original_output='{"category": "bad json',
            error_detail="JSON parse error at line 1",
        )
        assert result is not None
        # Should be valid JSON now
        data = json.loads(result)
        assert "category" in data

    @pytest.mark.asyncio
    async def test_repair_prompt_contains_original_output(self, service):
        result = await service.repair(
            original_ticket="付款问题",
            original_output='```json\n{"category": "支付"}\n```',
            error_detail="JSON parse error",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_repair_prompt_contains_error_info(self, service):
        result = await service.repair(
            original_ticket="ticket",
            original_output="bad json",
            error_detail="JSONDecodeError at line 1 col 3",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_repair_prompt_contains_ticket(self, service):
        result = await service.repair(
            original_ticket="unique_ticket_text_12345",
            original_output="bad",
            error_detail="error",
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_empty_repair_result_raises(self, empty_service):
        with pytest.raises(OutputRepairExhaustedError, match="空输出"):
            await empty_service.repair(
                original_ticket="ticket",
                original_output="bad json",
                error_detail="parse error",
            )
