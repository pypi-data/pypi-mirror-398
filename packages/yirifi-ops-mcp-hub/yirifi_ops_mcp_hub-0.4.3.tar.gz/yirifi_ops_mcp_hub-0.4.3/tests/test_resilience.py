"""Tests for the resilience module."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from yirifi_mcp.core.exceptions import CircuitBreakerOpenError
from yirifi_mcp.core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    RateLimitConfig,
    RateLimiterRegistry,
    ResilienceConfig,
    ResilienceCoordinator,
    RetryConfig,
    is_retryable_error,
)


class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 30.0
        assert config.success_threshold == 2

    def test_custom_values(self):
        """Test custom configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60.0,
            success_threshold=1,
        )
        assert config.failure_threshold == 3
        assert config.recovery_timeout == 60.0


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    @pytest.fixture
    def config(self):
        """Circuit breaker config for testing."""
        return CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,  # Fast timeout for tests
            success_threshold=1,
        )

    @pytest.fixture
    def breaker(self, config):
        """Fresh circuit breaker for each test."""
        return CircuitBreaker("test-service", config)

    def test_initial_state_closed(self, breaker):
        """Test that circuit starts closed."""
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed is True

    @pytest.mark.asyncio
    async def test_can_execute_when_closed(self, breaker):
        """Test can_execute returns True when closed."""
        assert await breaker.can_execute() is True

    @pytest.mark.asyncio
    async def test_record_success(self, breaker):
        """Test recording successful calls."""
        await breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_record_failure_below_threshold(self, breaker):
        """Test failures below threshold keep circuit closed."""
        await breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_record_failure_opens_circuit(self, breaker):
        """Test reaching threshold opens circuit."""
        await breaker.record_failure()
        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        assert await breaker.can_execute() is False

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open(self, breaker):
        """Test circuit transitions to half-open after timeout."""
        # Open the circuit
        await breaker.record_failure()
        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Should transition to half-open
        assert await breaker.can_execute() is True
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self, breaker):
        """Test success in half-open state closes circuit."""
        # Get to half-open state
        await breaker.record_failure()
        await breaker.record_failure()
        await asyncio.sleep(0.15)
        await breaker.can_execute()  # Transitions to half-open

        # Record success
        await breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self, breaker):
        """Test failure in half-open state reopens circuit."""
        # Get to half-open state
        await breaker.record_failure()
        await breaker.record_failure()
        await asyncio.sleep(0.15)
        await breaker.can_execute()  # Transitions to half-open

        # Record failure
        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_reset(self, breaker):
        """Test resetting circuit breaker."""
        await breaker.record_failure()
        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        breaker.reset()  # reset is synchronous
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_values(self):
        """Test default rate limit values."""
        config = RateLimitConfig()
        assert config.high_risk_rate == 10.0
        assert config.default_rate == 60.0

    def test_custom_values(self):
        """Test custom rate limits."""
        config = RateLimitConfig(high_risk_rate=5.0, default_rate=100.0)
        assert config.high_risk_rate == 5.0
        assert config.default_rate == 100.0


class TestRateLimiterRegistry:
    """Tests for RateLimiterRegistry."""

    @pytest.fixture
    def registry(self):
        """Fresh registry for each test."""
        config = RateLimitConfig(high_risk_rate=100.0, default_rate=200.0)
        return RateLimiterRegistry(config)

    @pytest.mark.asyncio
    async def test_get_limiter_creates_limiter(self, registry):
        """Test that get_limiter creates a limiter."""
        limiter = await registry.get_limiter("high")
        assert limiter is not None

    @pytest.mark.asyncio
    async def test_get_limiter_reuses_limiter(self, registry):
        """Test that get_limiter reuses existing limiter."""
        limiter1 = await registry.get_limiter("high")
        limiter2 = await registry.get_limiter("high")
        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_different_risk_levels_different_limiters(self, registry):
        """Test that different risk levels get different limiters."""
        high = await registry.get_limiter("high")
        low = await registry.get_limiter("low")
        assert high is not low

    @pytest.mark.asyncio
    async def test_acquire_succeeds(self, registry):
        """Test that acquire succeeds for normal rate."""
        await registry.acquire("low")  # Should not raise


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.min_wait == 1.0
        assert config.max_wait == 10.0
        assert 429 in config.retryable_status_codes
        assert 503 in config.retryable_status_codes


class TestIsRetryableError:
    """Tests for is_retryable_error function."""

    def test_request_error_is_retryable(self):
        """Test that network errors are retryable."""
        error = httpx.ConnectError("Connection failed")
        assert is_retryable_error(error) is True

    def test_timeout_is_retryable(self):
        """Test that timeouts are retryable."""
        error = httpx.TimeoutException("Request timed out")
        assert is_retryable_error(error) is True

    def test_503_is_retryable(self):
        """Test that 503 is retryable."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 503
        error = httpx.HTTPStatusError("", request=MagicMock(), response=response)
        assert is_retryable_error(error) is True

    def test_429_is_retryable(self):
        """Test that 429 (rate limit) is retryable."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 429
        error = httpx.HTTPStatusError("", request=MagicMock(), response=response)
        assert is_retryable_error(error) is True

    def test_400_is_not_retryable(self):
        """Test that 400 is not retryable."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 400
        error = httpx.HTTPStatusError("", request=MagicMock(), response=response)
        assert is_retryable_error(error) is False

    def test_404_is_not_retryable(self):
        """Test that 404 is not retryable."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 404
        error = httpx.HTTPStatusError("", request=MagicMock(), response=response)
        assert is_retryable_error(error) is False

    def test_value_error_is_not_retryable(self):
        """Test that ValueError is not retryable."""
        error = ValueError("Invalid value")
        assert is_retryable_error(error) is False


class TestResilienceConfig:
    """Tests for ResilienceConfig."""

    def test_default_config(self):
        """Test default resilience configuration."""
        config = ResilienceConfig()
        assert config.enable_circuit_breaker is True
        assert config.enable_rate_limiting is True
        assert config.enable_retry is True
        assert config.circuit_breaker is not None
        assert config.rate_limit is not None
        assert config.retry is not None

    def test_disabled_config(self):
        """Test disabling individual resilience features."""
        config = ResilienceConfig(
            enable_circuit_breaker=False,
            enable_rate_limiting=False,
            enable_retry=False,
        )
        assert config.enable_circuit_breaker is False
        assert config.enable_rate_limiting is False
        assert config.enable_retry is False


class TestResilienceCoordinator:
    """Tests for ResilienceCoordinator."""

    @pytest.fixture
    def config(self):
        """Fast resilience config for testing."""
        return ResilienceConfig(
            enable_circuit_breaker=True,
            enable_rate_limiting=True,
            enable_retry=True,
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=0.1,
            ),
            rate_limit=RateLimitConfig(
                high_risk_rate=100.0,  # High for tests
                default_rate=200.0,
            ),
            retry=RetryConfig(
                max_attempts=2,
                min_wait=0.01,
                max_wait=0.1,
            ),
        )

    @pytest.fixture
    def coordinator(self, config):
        """Fresh coordinator for each test."""
        return ResilienceCoordinator("test-service", config)

    @pytest.mark.asyncio
    async def test_execute_success(self, coordinator):
        """Test successful execution."""
        async def success_fn():
            return {"result": "ok"}

        result = await coordinator.execute(
            success_fn,
            action="test_action",
            risk_level="low",
            idempotent=True,
        )
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_execute_failure(self, coordinator):
        """Test execution failure."""
        async def fail_fn():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await coordinator.execute(
                fail_fn,
                action="test_action",
                risk_level="low",
                idempotent=False,
            )

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self, coordinator):
        """Test that circuit opens after repeated failures."""
        async def fail_fn():
            response = MagicMock(spec=httpx.Response)
            response.status_code = 500
            raise httpx.HTTPStatusError("", request=MagicMock(), response=response)

        # First failure
        with pytest.raises(httpx.HTTPStatusError):
            await coordinator.execute(
                fail_fn, action="test", risk_level="low", idempotent=False
            )

        # Second failure - should open circuit
        with pytest.raises(httpx.HTTPStatusError):
            await coordinator.execute(
                fail_fn, action="test", risk_level="low", idempotent=False
            )

        # Circuit should now be open
        assert coordinator.circuit_state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self, coordinator):
        """Test retry on transient failure."""
        call_count = 0

        async def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Connection failed")
            return {"result": "ok"}

        result = await coordinator.execute(
            flaky_fn,
            action="test",
            risk_level="low",
            idempotent=True,  # Only retries idempotent
        )
        assert result == {"result": "ok"}
        assert call_count == 2  # First fail, then success

    @pytest.mark.asyncio
    async def test_no_retry_for_non_idempotent(self, coordinator):
        """Test no retry for non-idempotent operations."""
        call_count = 0

        async def fail_fn():
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("Connection failed")

        with pytest.raises(httpx.ConnectError):
            await coordinator.execute(
                fail_fn,
                action="test",
                risk_level="low",
                idempotent=False,  # No retry
            )
        assert call_count == 1  # Only one attempt

    @pytest.mark.asyncio
    async def test_disabled_resilience_bypasses_all(self):
        """Test that disabled resilience bypasses all patterns."""
        config = ResilienceConfig(
            enable_circuit_breaker=False,
            enable_rate_limiting=False,
            enable_retry=False,
        )
        coordinator = ResilienceCoordinator("test", config)

        async def success_fn():
            return {"result": "ok"}

        result = await coordinator.execute(
            success_fn,
            action="test",
            risk_level="high",
            idempotent=True,
        )
        assert result == {"result": "ok"}

    def test_circuit_state_property(self, coordinator):
        """Test circuit_state property."""
        assert coordinator.circuit_state == CircuitState.CLOSED

    def test_circuit_can_be_reset(self, coordinator):
        """Test that the internal circuit can be reset."""
        # Access the internal circuit breaker
        circuit = coordinator.circuit
        assert circuit is not None
        circuit.reset()
        assert coordinator.circuit_state == CircuitState.CLOSED
