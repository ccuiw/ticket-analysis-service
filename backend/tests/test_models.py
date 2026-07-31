"""Pydantic 模型验证测试。"""

import pytest
from pydantic import ValidationError as PydanticValidationError
from app.models.requests import AnalyzeRequest
from app.models.responses import AnalysisResult, ErrorResponse


class TestAnalyzeRequest:
    def test_valid_request(self):
        req = AnalyzeRequest(ticket_text="我需要帮助", prompt_version="v1")
        assert req.ticket_text == "我需要帮助"
        assert req.prompt_version == "v1"

    def test_empty_ticket_text_raises_error(self):
        with pytest.raises(PydanticValidationError):
            AnalyzeRequest(ticket_text="", prompt_version="v1")

    def test_ticket_text_too_long_raises_error(self):
        long_text = "x" * 10001
        with pytest.raises(PydanticValidationError):
            AnalyzeRequest(ticket_text=long_text, prompt_version="v1")

    def test_invalid_prompt_version_raises_error(self):
        with pytest.raises(PydanticValidationError):
            AnalyzeRequest(ticket_text="help", prompt_version="v3")

    def test_default_prompt_version_is_v1(self):
        req = AnalyzeRequest(ticket_text="help")
        assert req.prompt_version == "v1"

    def test_missing_ticket_text_raises_error(self):
        with pytest.raises(PydanticValidationError):
            AnalyzeRequest(prompt_version="v1")

    def test_prompt_version_v2_is_valid(self):
        req = AnalyzeRequest(ticket_text="help", prompt_version="v2")
        assert req.prompt_version == "v2"


class TestAnalysisResult:
    def test_minimal_result(self):
        result = AnalysisResult(
            category="测试",
            priority="低",
            summary="测试摘要",
            tags=[],
            confidence=0.5,
            need_human_review=False,
            uncertain_fields=[],
        )
        assert result.category == "测试"
        assert result.order_id is None

    def test_full_result(self):
        result = AnalysisResult(
            category="支付问题",
            priority="高",
            summary="用户付款后会员未生效",
            tags=["支付", "会员"],
            order_id="ORD-12345",
            confidence=0.95,
            need_human_review=False,
            uncertain_fields=[],
        )
        assert result.order_id == "ORD-12345"
        assert len(result.tags) == 2

    def test_default_tags_is_empty_list(self):
        result = AnalysisResult(
            category="测试",
            priority="低",
            summary="测试",
            confidence=0.5,
            need_human_review=False,
        )
        assert result.tags == []
        assert result.uncertain_fields == []

    def test_confidence_out_of_range_raises_error(self):
        with pytest.raises(PydanticValidationError):
            AnalysisResult(
                category="测试",
                priority="低",
                summary="测试",
                confidence=1.5,
                need_human_review=False,
            )


class TestErrorResponse:
    def test_error_response(self):
        err = ErrorResponse(detail="出错了", error_type="validation_error")
        assert err.detail == "出错了"
        assert err.error_type == "validation_error"
