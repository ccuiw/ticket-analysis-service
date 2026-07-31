"""Provider 工厂测试。"""

import os
import pytest
from app.llm.provider_factory import create_provider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_compatible import OpenAICompatibleLLMProvider
from app.domain.exceptions import LLMConfigurationError


class TestProviderFactory:
    def test_default_is_mock(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        provider = create_provider()
        assert isinstance(provider, MockLLMProvider)
        assert provider.model_name == "mock"

    def test_explicit_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        provider = create_provider()
        assert isinstance(provider, MockLLMProvider)

    def test_openai_compatible_requires_api_key(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        with pytest.raises(LLMConfigurationError, match="LLM_API_KEY"):
            create_provider()

    def test_openai_compatible_requires_base_url(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
        monkeypatch.setenv("LLM_API_KEY", "sk-test")
        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        with pytest.raises(LLMConfigurationError, match="LLM_BASE_URL"):
            create_provider()

    def test_openai_compatible_requires_model(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
        monkeypatch.setenv("LLM_API_KEY", "sk-test")
        monkeypatch.setenv("LLM_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.delenv("LLM_MODEL", raising=False)
        with pytest.raises(LLMConfigurationError, match="LLM_MODEL"):
            create_provider()

    def test_openai_compatible_full_config(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
        monkeypatch.setenv("LLM_API_KEY", "sk-test")
        monkeypatch.setenv("LLM_BASE_URL", "https://api.example.com/v1")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "60")
        provider = create_provider()
        assert isinstance(provider, OpenAICompatibleLLMProvider)
        assert provider.model_name == "gpt-4o"

    def test_invalid_provider_name(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "invalid_provider_xyz")
        with pytest.raises(LLMConfigurationError, match="不支持"):
            create_provider()

    def test_invalid_timeout_value(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
        monkeypatch.setenv("LLM_API_KEY", "sk-test")
        monkeypatch.setenv("LLM_BASE_URL", "https://api.example.com/v1")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "not_a_number")
        with pytest.raises(LLMConfigurationError, match="LLM_TIMEOUT_SECONDS"):
            create_provider()
