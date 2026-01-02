"""Custom exception hierarchy for MCP Hub."""


class MCPHubError(Exception):
    """Base exception for all MCP Hub errors."""

    pass


class ConfigurationError(MCPHubError):
    """Configuration/environment errors."""

    pass


class OpenAPIError(MCPHubError):
    """OpenAPI spec fetch/parse errors."""

    pass


class CatalogError(MCPHubError):
    """Catalog definition errors."""

    pass


class GatewayError(MCPHubError):
    """Gateway execution errors."""

    pass


class ActionNotFoundError(GatewayError):
    """Unknown action requested."""

    def __init__(self, action: str, available: list[str]):
        self.action = action
        self.available = available
        super().__init__(f"Unknown action: {action}")


class MissingPathParamError(GatewayError):
    """Required path parameter not provided."""

    def __init__(self, params: list[str], path: str):
        self.params = params
        self.path = path
        super().__init__(f"Missing path parameters {params} for {path}")


class UpstreamError(GatewayError):
    """Error from upstream service."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail[:200]}")


# ---------------------------------------------------------------------------
# Resilience Exceptions
# ---------------------------------------------------------------------------


class ResilienceError(MCPHubError):
    """Base exception for resilience-related errors."""

    pass


class CircuitBreakerOpenError(ResilienceError):
    """Circuit breaker is open, failing fast.

    This exception is raised when the circuit breaker has detected
    too many failures and is preventing further requests to protect
    the upstream service.
    """

    def __init__(self, service: str, retry_after: float):
        self.service = service
        self.retry_after = retry_after
        super().__init__(
            f"Service '{service}' circuit is open. Retry after {retry_after:.1f}s"
        )


class RateLimitError(ResilienceError):
    """Rate limit exceeded.

    Raised when a client has exceeded the configured rate limit
    for a particular action or risk level.
    """

    def __init__(self, action: str, limit: float):
        self.action = action
        self.limit = limit
        super().__init__(f"Rate limit exceeded for '{action}'. Limit: {limit}/min")


class RetryExhaustedError(ResilienceError):
    """All retry attempts failed.

    Raised when an operation has been retried the maximum number
    of times and all attempts have failed.
    """

    def __init__(self, action: str, attempts: int, last_error: Exception):
        self.action = action
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Action '{action}' failed after {attempts} attempts: {last_error}"
        )


# ---------------------------------------------------------------------------
# Validation Exceptions
# ---------------------------------------------------------------------------


class ValidationError(GatewayError):
    """Parameter validation failed.

    Raised when input parameters don't match the expected schema
    or fail validation rules.
    """

    def __init__(self, message: str, param_name: str | None = None):
        self.param_name = param_name
        super().__init__(message)


class SpecValidationError(OpenAPIError):
    """OpenAPI spec validation failed.

    Raised when a fetched OpenAPI spec is missing required fields
    or is malformed.
    """

    pass


# ---------------------------------------------------------------------------
# Efficiency Exceptions
# ---------------------------------------------------------------------------


class ResponseTooLargeError(GatewayError):
    """Response exceeds size limit.

    Raised when an upstream response exceeds the configured
    maximum response size.
    """

    def __init__(self, actual_size: int, max_size: int):
        self.actual_size = actual_size
        self.max_size = max_size
        super().__init__(f"Response too large: {actual_size} bytes (max: {max_size})")
