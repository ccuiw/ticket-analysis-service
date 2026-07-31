"""JSON 解析器测试。"""

import pytest
from app.parsing.parser import parse_raw_output
from app.domain.exceptions import OutputParseError


class TestParser:
    def test_valid_json(self):
        data = parse_raw_output('{"key": "value", "num": 42}')
        assert data == {"key": "value", "num": 42}

    def test_valid_analysis_result(self):
        json_str = (
            '{"category": "支付问题", "priority": "高", '
            '"summary": "测试摘要", "tags": ["支付"], '
            '"order_id": null, "confidence": 0.95, '
            '"need_human_review": false, "uncertain_fields": []}'
        )
        data = parse_raw_output(json_str)
        assert data["category"] == "支付问题"
        assert data["order_id"] is None

    def test_empty_string_raises(self):
        with pytest.raises(OutputParseError, match="空输出"):
            parse_raw_output("")

    def test_whitespace_only_raises(self):
        with pytest.raises(OutputParseError, match="空输出"):
            parse_raw_output("   \n  ")

    def test_invalid_json_raises(self):
        with pytest.raises(OutputParseError, match="解析失败"):
            parse_raw_output("not json at all")

    def test_markdown_fenced_json_fails(self):
        """Markdown 代码块在解析阶段会失败——修复逻辑在后续 repair 阶段实现。"""
        markdown_json = '```json\n{"key": "value"}\n```'
        with pytest.raises(OutputParseError):
            parse_raw_output(markdown_json)

    def test_array_instead_of_object_raises(self):
        with pytest.raises(OutputParseError, match="JSON 对象"):
            parse_raw_output('[{"key": "value"}]')

    def test_number_instead_of_object_raises(self):
        with pytest.raises(OutputParseError, match="JSON 对象"):
            parse_raw_output("42")
