"""RetryPolicy 测试。"""

import pytest
from app.repair.retry_policy import RetryPolicy
from app.domain.exceptions import (
    LLMTimeoutError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMServerError,
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMRequestError,
    RetryConfigurationError,
)


class TestRetryPolicyShouldRetry:
    @pytest.fixture
    def policy(self):
        return RetryPolicy(max_attempts=3)

    def test_timeout_is_retryable(self, policy):
        assert policy.should_retry(LLMTimeoutError("timeout"), 1) is True

    def test_connection_error_is_retryable(self, policy):
        assert policy.should_retry(LLMConnectionError("conn"), 1) is True

    def test_rate_limit_is_retryable(self, policy):
        assert policy.should_retry(LLMRateLimitError("429"), 1) is True

    def test_server_error_is_retryable(self, policy):
        assert policy.should_retry(LLMServerError("500"), 1) is True

    def test_401_is_not_retryable(self, policy):
        assert policy.should_retry(LLMAuthenticationError("401"), 1) is False

    def test_config_error_is_not_retryable(self, policy):
        assert policy.should_retry(LLMConfigurationError("cfg"), 1) is False

    def test_request_error_is_not_retryable(self, policy):
        assert policy.should_retry(LLMRequestError("req"), 1) is False

    def test_stops_at_max_attempts(self, policy):
        """达到最大次数后不应重试。"""
        assert policy.should_retry(LLMTimeoutError("t"), 1) is True   # attempt 1 < 3
        assert policy.should_retry(LLMTimeoutError("t"), 2) is True   # attempt 2 < 3
        assert policy.should_retry(LLMTimeoutError("t"), 3) is False  # attempt 3 >= 3
        assert policy.should_retry(LLMTimeoutError("t"), 4) is False

    def test_llmservererror_is_retryable_for_all_4_codes(self, policy):
        """500/502/503/504 均可重试。"""
        assert policy.should_retry(LLMServerError("500"), 1) is True
        assert policy.should_retry(LLMServerError("502"), 1) is True
        assert policy.should_retry(LLMServerError("503"), 1) is True
        assert policy.should_retry(LLMServerError("504"), 1) is True

    def test_request_error_not_retryable_includes_501(self, policy):
        """501 Not Implemented 映射为 LLMRequestError，不可重试。"""
        assert policy.should_retry(LLMRequestError("501"), 1) is False

    def test_non_llm_error_is_not_retryable(self, policy):
        assert policy.should_retry(ValueError("random"), 1) is False
        assert policy.should_retry(RuntimeError("random"), 1) is False


class TestRetryPolicyExecute:
    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        policy = RetryPolicy(max_attempts=3)
        call_count = 0

        async def op():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await policy.execute_with_retry(op)
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self):
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0, backoff_multiplier=0)
        call_count = 0

        async def op():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise LLMTimeoutError("timeout")
            return "ok"

        result = await policy.execute_with_retry(op)
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_stops_at_max_attempts(self):
        policy = RetryPolicy(max_attempts=2, base_delay_seconds=0, backoff_multiplier=0)
        call_count = 0

        async def op():
            nonlocal call_count
            call_count += 1
            raise LLMTimeoutError("timeout")

        with pytest.raises(LLMTimeoutError):
            await policy.execute_with_retry(op)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_does_not_retry_non_retryable(self):
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0, backoff_multiplier=0)
        call_count = 0

        async def op():
            nonlocal call_count
            call_count += 1
            raise LLMAuthenticationError("bad key")

        with pytest.raises(LLMAuthenticationError):
            await policy.execute_with_retry(op)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_delay_calculation(self):
        policy = RetryPolicy(
            max_attempts=5,
            base_delay_seconds=1.0,
            max_delay_seconds=10.0,
            backoff_multiplier=2.0,
        )
        assert policy.delay_for(1) == 1.0   # 1.0 * 2^0
        assert policy.delay_for(2) == 2.0   # 1.0 * 2^1
        assert policy.delay_for(3) == 4.0   # 1.0 * 2^2
        assert policy.delay_for(4) == 8.0   # 1.0 * 2^3
        assert policy.delay_for(5) == 10.0  # capped at max

    @pytest.mark.asyncio
    async def test_default_delay_is_minimal(self):
        """Tests should not experience real delays by default. Default delay is 0.5s."""
        policy = RetryPolicy()
        assert policy.delay_for(1) == 0.5


class TestRetryPolicyConfiguration:
    def test_default_values(self):
        policy = RetryPolicy()
        assert policy.max_attempts == 2
        assert policy.base_delay_seconds == 0.5

    def test_invalid_max_attempts(self):
        with pytest.raises(RetryConfigurationError):
            RetryPolicy(max_attempts=0)

    def test_negative_delay(self):
        with pytest.raises(RetryConfigurationError):
            RetryPolicy(base_delay_seconds=-0.1)
