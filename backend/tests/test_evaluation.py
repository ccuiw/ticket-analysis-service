"""评估模块测试。所有测试使用 Mock Provider。"""

import json
import tempfile
from pathlib import Path
import pytest
from app.evaluation.dataset import load_dataset, compute_dataset_hash
from app.evaluation.metrics import evaluate_case, compute_metrics
from app.evaluation.models import TestCase, EvaluationCaseResult, EvaluationMetrics


def _write_temp_jsonl(cases: list[dict]) -> Path:
    """将案例列表写入临时 JSONL 文件。"""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8")
    for c in cases:
        tmp.write(json.dumps(c, ensure_ascii=False) + "\n")
    tmp.close()
    return Path(tmp.name)


class TestDatasetLoader:
    def test_loads_20_cases(self):
        path = Path(__file__).resolve().parents[2] / "data" / "test_cases.jsonl"
        cases = load_dataset(path)
        assert len(cases) == 20

    def test_all_have_required_fields(self):
        path = Path(__file__).resolve().parents[2] / "data" / "test_cases.jsonl"
        cases = load_dataset(path)
        for c in cases:
            assert c.id
            assert c.input
            assert isinstance(c.expected, dict)
            assert c.case_type

    def test_invalid_jsonl_rejected(self):
        path = _write_temp_jsonl([{"id": "test", "input": "x", "expected": {}, "case_type": "clear"}])
        # Corrupt it
        path.write_text("not json {{{")
        with pytest.raises(ValueError, match="JSON"):
            load_dataset(path)
        path.unlink()

    def test_missing_expected(self):
        path = _write_temp_jsonl([{"id": "test", "input": "x", "case_type": "clear"}])
        with pytest.raises(ValueError, match="缺少必填字段"):
            load_dataset(path)
        path.unlink()

    def test_duplicate_id_rejected(self):
        path = _write_temp_jsonl([
            {"id": "dup", "input": "a", "expected": {}, "case_type": "clear"},
            {"id": "dup", "input": "b", "expected": {}, "case_type": "clear"},
        ])
        with pytest.raises(ValueError, match="重复"):
            load_dataset(path)
        path.unlink()

    def test_compute_hash(self):
        path = _write_temp_jsonl([{"id": "t", "input": "x", "expected": {}, "case_type": "clear"}])
        h = compute_dataset_hash(path)
        assert len(h) == 16
        path.unlink()


class TestMetrics:
    def test_json_parse_rate(self):
        m = EvaluationMetrics(total_cases=10, raw_parse_success=8)
        assert m.raw_parse_rate == 0.8

    def test_structured_success_rate(self):
        m = EvaluationMetrics(total_cases=10, final_structured_success=9)
        assert m.structured_success_rate == 0.9

    def test_category_accuracy(self):
        m = EvaluationMetrics(category_correct=8, category_evaluable=10)
        assert m.category_accuracy == 0.8

    def test_category_accuracy_none_when_zero_evaluable(self):
        m = EvaluationMetrics()
        assert m.category_accuracy is None

    def test_order_id_null_correct(self):
        case = TestCase(
            id="test", input="x",
            expected={"order_id": None},
            case_type="anti_fabrication",
        )
        result = {"order_id": None}
        cr = evaluate_case(case, "v1", result, True, False, 1, None, None, 0.0)
        assert cr.order_id_match is True

    def test_order_id_fabricated_detected(self):
        case = TestCase(
            id="test", input="x",
            expected={"order_id": None, "forbidden_fabricated_fields": ["order_id"]},
            case_type="anti_fabrication",
        )
        result = {"order_id": "FAKE-123"}
        cr = evaluate_case(case, "v1", result, True, False, 1, None, None, 0.0)
        assert cr.fabricated is True
        assert "order_id" in cr.fabricated_fields

    def test_tag_recall_full(self):
        case = TestCase(
            id="test", input="x",
            expected={"must_include_tags": ["支付", "会员"]},
            case_type="clear",
        )
        result = {"tags": ["支付", "会员", "权益"]}
        cr = evaluate_case(case, "v1", result, True, False, 1, None, None, 0.0)
        assert cr.tags_recall == 1.0

    def test_tag_recall_partial(self):
        case = TestCase(
            id="test", input="x",
            expected={"must_include_tags": ["支付", "会员", "退款"]},
            case_type="clear",
        )
        result = {"tags": ["支付"]}
        cr = evaluate_case(case, "v1", result, True, False, 1, None, None, 0.0)
        assert cr.tags_recall == 1 / 3

    def test_repair_trigger_rate(self):
        m = EvaluationMetrics(total_cases=10, cases_repair_triggered=3)
        assert m.repair_trigger_rate == 0.3

    def test_average_provider_calls(self):
        m = EvaluationMetrics(total_cases=10, total_provider_calls=15)
        assert m.average_provider_calls == 1.5

    def test_end_to_end_success(self):
        case = TestCase(
            id="test", input="x",
            expected={"category": "支付问题", "order_id": None, "need_human_review": False, "must_include_tags": []},
            case_type="clear",
        )
        result = {"category": "支付问题", "order_id": None, "need_human_review": False}
        cr = evaluate_case(case, "v1", result, True, False, 1, None, None, 0.0)
        assert cr.category_match is True
        assert cr.order_id_match is True
        assert not cr.fabricated

    def test_zero_cases_no_division_by_zero(self):
        m = EvaluationMetrics()
        assert m.raw_parse_rate == 0.0
        assert m.structured_success_rate == 0.0
        assert m.end_to_end_success_rate == 0.0
        assert m.average_provider_calls == 0.0
        assert m.tag_recall == 1.0
