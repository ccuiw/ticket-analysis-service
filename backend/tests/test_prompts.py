"""提示词加载和构建测试。"""

import pytest
from app.prompts.loader import load_prompt, list_versions
from app.prompts.builder import build_messages
from app.domain.exceptions import PromptNotFoundError, PromptRenderError
from app.llm.messages import LLMMessage


class TestPromptLoader:
    def test_load_v1_prompt(self):
        text = load_prompt("ticket_analysis_v1")
        assert "工单分析" in text
        assert "category" in text
        assert "Zero-shot" not in text  # v1 文件不应包含 v2 特有名词

    def test_load_v2_prompt(self):
        text = load_prompt("ticket_analysis_v2")
        assert "工单分析" in text
        assert "示例" in text  # v2 文件包含 few-shot 示例

    def test_load_nonexistent_prompt_raises(self):
        with pytest.raises(PromptNotFoundError):
            load_prompt("nonexistent_version_x99")

    def test_list_versions(self):
        versions = list_versions()
        assert "v1" in versions
        assert "v2" in versions


class TestPromptBuilder:
    def test_build_messages_v1(self):
        messages = build_messages("测试工单内容", "v1")
        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert "工单分析" in messages[0].content
        assert "<ticket>" in messages[1].content
        assert "测试工单内容" in messages[1].content
        assert "</ticket>" in messages[1].content

    def test_build_messages_v2(self):
        messages = build_messages("付款问题", "v2")
        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert "示例" in messages[0].content

    def test_user_message_isolates_ticket(self):
        messages = build_messages("敏感内容 <script>alert(1)</script>", "v1")
        user_content = messages[1].content
        assert user_content.startswith("<ticket>")
        assert user_content.endswith("</ticket>")

    def test_build_messages_validates_version(self):
        with pytest.raises(PromptRenderError):
            build_messages("test", "v99")
