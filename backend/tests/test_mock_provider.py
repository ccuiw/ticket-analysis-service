"""Mock Provider 测试。"""

import json
import pytest
from app.llm.mock_provider import MockLLMProvider
from app.llm.messages import LLMMessage


class TestMockProvider:
    @pytest.fixture
    def provider(self):
        return MockLLMProvider()

    @pytest.mark.asyncio
    async def test_returns_valid_json(self, provider):
        messages = [
            LLMMessage(role="system", content="test"),
            LLMMessage(role="user", content="<ticket>\n付款后会员没到账\n</ticket>"),
        ]
        response = await provider.analyze(messages)
        data = json.loads(response.content)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_payment_keyword(self, provider):
        messages = [
            LLMMessage(role="system", content="test"),
            LLMMessage(role="user", content="<ticket>\n付款后会员没到账\n</ticket>"),
        ]
        response = await provider.analyze(messages)
        data = json.loads(response.content)
        assert data["category"] == "支付问题"
        assert data["priority"] == "高"

    @pytest.mark.asyncio
    async def test_member_keyword(self, provider):
        messages = [
            LLMMessage(role="system", content="test"),
            LLMMessage(role="user", content="<ticket>\n会员等级显示错误\n</ticket>"),
        ]
        response = await provider.analyze(messages)
        data = json.loads(response.content)
        assert data["category"] == "账号问题"

    @pytest.mark.asyncio
    async def test_login_keyword(self, provider):
        messages = [
            LLMMessage(role="system", content="test"),
            LLMMessage(role="user", content="<ticket>\n忘记了密码无法登录\n</ticket>"),
        ]
        response = await provider.analyze(messages)
        data = json.loads(response.content)
        assert data["category"] == "登录问题"

    @pytest.mark.asyncio
    async def test_refund_keyword(self, provider):
        messages = [
            LLMMessage(role="system", content="test"),
            LLMMessage(role="user", content="<ticket>\n我要退款\n</ticket>"),
        ]
        response = await provider.analyze(messages)
        data = json.loads(response.content)
        assert data["category"] == "退款问题"
        assert data["need_human_review"] is True

    @pytest.mark.asyncio
    async def test_default_result(self, provider):
        messages = [
            LLMMessage(role="system", content="test"),
            LLMMessage(role="user", content="<ticket>\n未知问题\n</ticket>"),
        ]
        response = await provider.analyze(messages)
        data = json.loads(response.content)
        assert data["category"] == "一般咨询"

    @pytest.mark.asyncio
    async def test_model_name(self, provider):
        assert provider.model_name == "mock"
