"""Resilience patterns: circuit breaker, rate limiting, and retry logic.

This module provides production-grade resilience patterns:
- CircuitBreaker: Fail-fast when upstream is degraded
- RateLimiterRegistry: Per-risk-level request throttling
- ResilienceCoordinator: Combines all patterns for gateway integration

Usage:
    coordinator = ResilienceCoordinator("auth", config)

    result = await coordinator.execute(
        lambda: gateway.call("delete_user", ...),
        action="delete_user",
        risk_level="high",
        idempotent=True,
    )
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, TypeVar

import httpx
import structlog
from aiolimiter import AsyncLimiter
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from yirifi_mcp.core.exceptions import CircuitBreakerOpenError

logger = structlog.get_logger()

T = TypeVar("T")


# =============================================================================
# Circuit Breaker
# =============================================================================


class CircuitState(Enum):
    """Circuit breaker states.

    CLOSED: Normal operation, requests pass through
    OPEN: Circuit tripped, all requests fail fast
    HALF_OPEN: Testing if upstream has recovered
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration.

    Attributes:
        failure_threshold: Consecutive failures before opening circuit
        recovery_timeout: Seconds before trying to recover (half-open)
        success_threshold: Successes needed to close from half-open
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 2


class CircuitBreaker:
    """Async circuit breaker for upstream service protection.

    Prevents cascading failures by failing fast when upstream is degraded.

    State transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After recovery_timeout seconds
    - HALF_OPEN -> CLOSED: After success_threshold successes
    - HALF_OPEN -> OPEN: On any failure

    Thread-safe via asyncio.Lock.

    Example:
        circuit = CircuitBreaker("auth-service")

        if await circuit.can_execute():
            try:
                result = await call_upstream()
                await circuit.record_success()
            except Exception:
                await circuit.record_failure()
                raise
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None):
        """Initialize circuit breaker.

        Args:
            name: Service name for logging
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Whether circuit is in closed (normal) state."""
        return self._state == CircuitState.CLOSED

    @property
    def failure_count(self) -> int:
        """Current consecutive failure count."""
        return self._failure_count

    async def can_execute(self) -> bool:
        """Check if request can proceed through the circuit.

        Returns:
            True if request should proceed, False if circuit is open
        """
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time is not None:
                    elapsed = time.monotonic() - self._last_failure_time
                    if elapsed >= self.config.recovery_timeout:
                        self._state = CircuitState.HALF_OPEN
                        self._success_count = 0
                        logger.info(
                            "circuit_half_open",
                            circuit=self.name,
                            elapsed_seconds=round(elapsed, 1),
                        )
                        return True
                return False

            # HALF_OPEN: allow request through for testing
            return True

    async def record_success(self) -> None:
        """Record a successful request."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(
                        "circuit_closed",
                        circuit=self.name,
                        after_successes=self._success_count,
                    )
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    async def record_failure(self) -> None:
        """Record a failed request."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open returns to open
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_reopened",
                    circuit=self.name,
                    reason="failure_in_half_open",
                )
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        "circuit_opened",
                        circuit=self.name,
                        failures=self._failure_count,
                        threshold=self.config.failure_threshold,
                    )

    def get_retry_after(self) -> float:
        """Get seconds until circuit might recover.

        Returns:
            Seconds until HALF_OPEN state, or 0 if not applicable
        """
        if self._state != CircuitState.OPEN or self._last_failure_time is None:
            return 0.0
        elapsed = time.monotonic() - self._last_failure_time
        return max(0.0, self.config.recovery_timeout - elapsed)

    def reset(self) -> None:
        """Reset circuit to initial state (for testing)."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None


# =============================================================================
# Rate Limiter
# =============================================================================


@dataclass
class RateLimitConfig:
    """Rate limit configuration.

    Attributes:
        high_risk_rate: Requests per minute for high-risk operations
        high_risk_burst: Burst capacity for high-risk
        default_rate: Requests per minute for low/medium risk
        default_burst: Burst capacity for default
    """

    high_risk_rate: float = 10.0  # 10 per minute
    high_risk_burst: int = 2
    default_rate: float = 60.0  # 60 per minute
    default_burst: int = 10


class RateLimiterRegistry:
    """Manages rate limiters for different risk levels.

    Uses aiolimiter for async-native token bucket rate limiting.
    Lazily creates limiters per risk level.

    Example:
        registry = RateLimiterRegistry(config)
        await registry.acquire("high")  # Blocks if limit exceeded
    """

    def __init__(self, config: RateLimitConfig | None = None):
        """Initialize rate limiter registry.

        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self._limiters: dict[str, AsyncLimiter] = {}
        self._lock = asyncio.Lock()

    def _create_limiter(self, risk_level: str) -> AsyncLimiter:
        """Create limiter for risk level.

        AsyncLimiter(max_rate, time_period) creates a leaky bucket with:
        - max_rate: bucket capacity (max tokens)
        - time_period: time to refill all tokens

        Args:
            risk_level: Risk level (high, medium, low)

        Returns:
            Configured AsyncLimiter
        """
        if risk_level == "high":
            # High-risk: stricter limits (e.g., 10 requests per minute)
            max_rate = self.config.high_risk_rate
            time_period = 60.0
        else:
            # Low/medium: more permissive (e.g., 60 requests per minute)
            max_rate = self.config.default_rate
            time_period = 60.0

        return AsyncLimiter(max_rate, time_period)

    async def get_limiter(self, risk_level: str) -> AsyncLimiter:
        """Get or create limiter for risk level.

        Args:
            risk_level: Risk level (high, medium, low)

        Returns:
            AsyncLimiter for the risk level
        """
        async with self._lock:
            if risk_level not in self._limiters:
                self._limiters[risk_level] = self._create_limiter(risk_level)
                logger.debug(
                    "rate_limiter_created",
                    risk_level=risk_level,
                    rate_per_minute=(
                        self.config.high_risk_rate
                        if risk_level == "high"
                        else self.config.default_rate
                    ),
                )
            return self._limiters[risk_level]

    async def acquire(self, risk_level: str) -> None:
        """Acquire rate limit permit, blocking if necessary.

        Args:
            risk_level: Risk level for the operation
        """
        limiter = await self.get_limiter(risk_level)
        await limiter.acquire()


# =============================================================================
# Retry Configuration
# =============================================================================


@dataclass
class RetryConfig:
    """Retry configuration for transient failures.

    Attributes:
        max_attempts: Maximum retry attempts (including initial)
        min_wait: Minimum wait between retries (seconds)
        max_wait: Maximum wait between retries (seconds)
        exponential_base: Base for exponential backoff
        retryable_status_codes: HTTP status codes to retry
    """

    max_attempts: int = 3
    min_wait: float = 1.0
    max_wait: float = 10.0
    exponential_base: float = 2.0
    retryable_status_codes: tuple[int, ...] = (429, 502, 503, 504)


def is_retryable_error(exception: BaseException) -> bool:
    """Check if exception is retryable.

    Retryable errors:
    - Network/connection errors (httpx.RequestError)
    - Specific HTTP status codes (429, 502, 503, 504)

    Args:
        exception: Exception to check

    Returns:
        True if error should be retried
    """
    if isinstance(exception, httpx.RequestError):
        # Network errors are retryable
        return True

    if isinstance(exception, httpx.HTTPStatusError):
        # Only retry specific status codes
        return exception.response.status_code in (429, 502, 503, 504)

    return False


# =============================================================================
# Resilience Coordinator
# =============================================================================


@dataclass
class ResilienceConfig:
    """Combined resilience configuration.

    Attributes:
        circuit_breaker: Circuit breaker settings
        rate_limit: Rate limiting settings
        retry: Retry settings
        enable_circuit_breaker: Whether to use circuit breaker
        enable_rate_limiting: Whether to use rate limiting
        enable_retry: Whether to use retry logic
    """

    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)

    # Feature flags
    enable_circuit_breaker: bool = True
    enable_rate_limiting: bool = True
    enable_retry: bool = True


class ResilienceCoordinator:
    """Coordinates all resilience patterns for a service.

    Applies patterns in order:
    1. Circuit breaker check (fail fast if open)
    2. Rate limiting (block if limit exceeded)
    3. Retry with exponential backoff (for idempotent operations)

    Records success/failure for circuit breaker state management.

    Example:
        coordinator = ResilienceCoordinator("auth", config)

        result = await coordinator.execute(
            lambda: client.request("DELETE", "/users/123"),
            action="delete_user",
            risk_level="high",
            idempotent=True,
        )
    """

    def __init__(
        self,
        service_name: str,
        config: ResilienceConfig | None = None,
    ):
        """Initialize resilience coordinator.

        Args:
            service_name: Service name for logging and circuit naming
            config: Resilience configuration
        """
        self.service_name = service_name
        self.config = config or ResilienceConfig()

        # Initialize components based on config
        self._circuit: CircuitBreaker | None = None
        if self.config.enable_circuit_breaker:
            self._circuit = CircuitBreaker(
                service_name,
                self.config.circuit_breaker,
            )

        self._rate_limiters: RateLimiterRegistry | None = None
        if self.config.enable_rate_limiting:
            self._rate_limiters = RateLimiterRegistry(self.config.rate_limit)

    @property
    def circuit_state(self) -> CircuitState | None:
        """Current circuit breaker state."""
        return self._circuit.state if self._circuit else None

    @property
    def circuit(self) -> CircuitBreaker | None:
        """Access to circuit breaker for inspection."""
        return self._circuit

    async def execute(
        self,
        func: Callable[[], T],
        *,
        action: str,
        risk_level: str = "low",
        idempotent: bool = False,
    ) -> T:
        """Execute function with resilience patterns applied.

        Order of operations:
        1. Check circuit breaker (fail fast if open)
        2. Acquire rate limit permit (blocks if exceeded)
        3. Execute with retry if idempotent
        4. Record success/failure for circuit breaker

        Args:
            func: Async function to execute (should be a coroutine function)
            action: Action name for logging
            risk_level: Risk level for rate limiting (low, medium, high)
            idempotent: Whether operation can be safely retried

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: Circuit is open
            Exception: From underlying operation (after retries exhausted)
        """
        # 1. Circuit breaker check
        if self._circuit:
            if not await self._circuit.can_execute():
                retry_after = self._circuit.get_retry_after()
                logger.warning(
                    "circuit_blocked_request",
                    service=self.service_name,
                    action=action,
                    retry_after=round(retry_after, 1),
                )
                raise CircuitBreakerOpenError(self.service_name, retry_after)

        # 2. Rate limiting
        if self._rate_limiters:
            await self._rate_limiters.acquire(risk_level)

        # 3. Execute with optional retry
        try:
            if self.config.enable_retry and idempotent:
                result = await self._execute_with_retry(func, action)
            else:
                result = await func()

            # 4. Record success
            if self._circuit:
                await self._circuit.record_success()

            return result

        except Exception as e:
            # 4. Record failure for circuit breaker (only for circuit-relevant errors)
            if self._circuit and self._is_circuit_failure(e):
                await self._circuit.record_failure()
            raise

    async def _execute_with_retry(
        self,
        func: Callable[[], T],
        action: str,
    ) -> T:
        """Execute with tenacity retry logic.

        Args:
            func: Async function to execute
            action: Action name for logging

        Returns:
            Result from func

        Raises:
            Exception: Last error if all retries exhausted
        """
        retry_config = self.config.retry
        attempt_count = 0

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retry_config.max_attempts),
            wait=wait_exponential(
                multiplier=retry_config.min_wait,
                max=retry_config.max_wait,
                exp_base=retry_config.exponential_base,
            ),
            retry=retry_if_exception(is_retryable_error),
            reraise=True,
        ):
            with attempt:
                attempt_count += 1
                try:
                    return await func()
                except Exception as e:
                    if is_retryable_error(e) and attempt_count < retry_config.max_attempts:
                        logger.warning(
                            "retry_attempt",
                            action=action,
                            attempt=attempt_count,
                            max_attempts=retry_config.max_attempts,
                            error_type=type(e).__name__,
                            error=str(e)[:100],
                        )
                    raise

        # This should never be reached due to reraise=True
        raise RuntimeError("Retry loop exited unexpectedly")

    def _is_circuit_failure(self, error: Exception) -> bool:
        """Check if error should count toward circuit breaker.

        Only count upstream failures (5xx, network errors), not client errors.

        Args:
            error: Exception to check

        Returns:
            True if error should trip circuit breaker
        """
        # Network errors always count
        if isinstance(error, httpx.RequestError):
            return True

        # Server errors count (5xx)
        if isinstance(error, httpx.HTTPStatusError):
            return error.response.status_code >= 500

        return False
