"""结构化和业务校验测试。"""

import pytest
from app.models.responses import AnalysisResult
from app.validation.structural import validate_structure
from app.validation.business import validate_business_rules
from app.domain.exceptions import OutputValidationError


class TestStructuralValidation:
    def test_valid_dict_passes(self):
        data = {
            "category": "支付问题",
            "priority": "高",
            "summary": "摘要",
            "tags": ["支付"],
            "order_id": None,
            "confidence": 0.9,
            "need_human_review": False,
            "uncertain_fields": [],
        }
        result = validate_structure(data)
        assert isinstance(result, AnalysisResult)
        assert result.category == "支付问题"

    def test_missing_required_field_raises(self):
        data = {
            "category": "测试",
            "priority": "低",
            # 缺少 summary、confidence 等必填字段
        }
        with pytest.raises(OutputValidationError):
            validate_structure(data)

    def test_invalid_confidence_type_raises(self):
        data = {
            "category": "测试",
            "priority": "低",
            "summary": "摘要",
            "tags": [],
            "order_id": None,
            "confidence": "high",
            "need_human_review": False,
            "uncertain_fields": [],
        }
        with pytest.raises(OutputValidationError):
            validate_structure(data)

    def test_confidence_out_of_range_raises(self):
        data = {
            "category": "测试",
            "priority": "低",
            "summary": "摘要",
            "tags": [],
            "order_id": None,
            "confidence": 2.0,
            "need_human_review": False,
            "uncertain_fields": [],
        }
        with pytest.raises(OutputValidationError):
            validate_structure(data)


class TestBusinessValidation:
    def test_passthrough_returns_same_result(self):
        result = AnalysisResult(
            category="测试",
            priority="低",
            summary="摘要",
            confidence=0.5,
            need_human_review=False,
        )
        assert validate_business_rules(result) is result
