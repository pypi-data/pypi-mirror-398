"""Configuration management for Yirifi MCP servers."""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Literal

from yirifi_mcp.core.toon_encoder import OutputFormat

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from yirifi_mcp.core.resilience import ResilienceConfig

# Environment-specific URLs for auth service
AUTH_SERVICE_URLS: dict[str, str] = {
    "dev": "http://localhost:5100",
    "prd": "https://auth.ops.yirifi.ai",
}

# Environment-specific URLs for reg service
REG_SERVICE_URLS: dict[str, str] = {
    "dev": "http://localhost:5008",
    "prd": "https://reg.ops.yirifi.ai",
}


def get_api_key() -> str:
    """Get API key from environment.

    Checks in order:
    1. YIRIFI_API_KEY (unified key for all services)
    2. Returns empty string if not found

    Returns:
        API key string or empty string
    """
    return os.environ.get("YIRIFI_API_KEY", "")


class ServiceConfig(BaseSettings):
    """Base configuration for any service MCP server.

    Authentication: Uses API key passthrough. Clients provide their X-API-Key
    header, which is forwarded to the upstream service for validation.
    """

    # Service connection
    base_url: str = Field(default="", description="Base URL of the service API")

    # OpenAPI spec
    openapi_path: str = Field(
        default="/api/v1/swagger.json",
        description="Path to OpenAPI/Swagger spec",
    )

    # MCP Server settings
    server_name: str = Field(description="Name of the MCP server")
    server_description: str = Field(default="", description="Description of the MCP server")

    # Timeouts
    request_timeout: float = Field(default=30.0, description="Request timeout in seconds")
    connect_timeout: float = Field(default=10.0, description="Connection timeout in seconds")

    # Resilience settings
    resilience_enabled: bool = Field(
        default=True,
        description="Enable resilience patterns (circuit breaker, retry, rate limit)",
    )

    # Circuit breaker settings
    circuit_failure_threshold: int = Field(
        default=5,
        description="Consecutive failures before circuit opens",
    )
    circuit_recovery_timeout: float = Field(
        default=30.0,
        description="Seconds before circuit tries to recover (half-open)",
    )
    circuit_success_threshold: int = Field(
        default=2,
        description="Successes needed to close circuit from half-open",
    )

    # Rate limiting settings
    rate_limit_high_risk: float = Field(
        default=10.0,
        description="Requests per minute for high-risk operations",
    )
    rate_limit_default: float = Field(
        default=60.0,
        description="Requests per minute for low/medium risk operations",
    )

    # Retry settings
    retry_max_attempts: int = Field(
        default=3,
        description="Maximum retry attempts for idempotent operations",
    )
    retry_min_wait: float = Field(
        default=1.0,
        description="Minimum wait between retries (seconds)",
    )
    retry_max_wait: float = Field(
        default=10.0,
        description="Maximum wait between retries (seconds)",
    )

    # Response limits
    max_response_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum response size in bytes before truncation",
    )
    response_truncation_enabled: bool = Field(
        default=True,
        description="Truncate oversized responses instead of raising error",
    )

    # Output format settings
    output_format: OutputFormat = Field(
        default=OutputFormat.AUTO,
        description="Response format: auto (detect best), json, or toon",
    )

    model_config = {"extra": "ignore"}

    @field_validator("base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate base_url is a valid HTTP(S) URL if provided."""
        if v and not re.match(r"^https?://", v):
            raise ValueError("base_url must start with http:// or https://")
        return v

    @field_validator("request_timeout", "connect_timeout")
    @classmethod
    def validate_positive_timeout(cls, v: float) -> float:
        """Validate timeout values are positive."""
        if v <= 0:
            raise ValueError("Timeout must be a positive number")
        return v

    @field_validator("openapi_path")
    @classmethod
    def validate_openapi_path(cls, v: str) -> str:
        """Validate openapi_path starts with /."""
        if not v.startswith("/"):
            raise ValueError("openapi_path must start with /")
        return v

    def get_resilience_config(self) -> "ResilienceConfig | None":
        """Build ResilienceConfig from settings.

        Returns:
            ResilienceConfig if enabled, None if disabled
        """
        from yirifi_mcp.core.resilience import (
            CircuitBreakerConfig,
            RateLimitConfig,
            ResilienceConfig,
            RetryConfig,
        )

        if not self.resilience_enabled:
            return ResilienceConfig(
                enable_circuit_breaker=False,
                enable_rate_limiting=False,
                enable_retry=False,
            )

        return ResilienceConfig(
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=self.circuit_failure_threshold,
                recovery_timeout=self.circuit_recovery_timeout,
                success_threshold=self.circuit_success_threshold,
            ),
            rate_limit=RateLimitConfig(
                high_risk_rate=self.rate_limit_high_risk,
                default_rate=self.rate_limit_default,
            ),
            retry=RetryConfig(
                max_attempts=self.retry_max_attempts,
                min_wait=self.retry_min_wait,
                max_wait=self.retry_max_wait,
            ),
            enable_circuit_breaker=True,
            enable_rate_limiting=True,
            enable_retry=True,
        )


class AuthServiceConfig(ServiceConfig):
    """Configuration for auth-service MCP server.

    URLs are determined by mode (dev/prod), not environment variables.
    Authentication: For STDIO transport, uses API key from environment:
    - YIRIFI_API_KEY (unified, recommended)
    - AUTH_SERVICE_API_KEY (service-specific fallback)
    For HTTP transport, client's X-API-Key header is passed through.
    """

    mode: Literal["dev", "prd"] = Field(
        default="prd",
        description="Environment mode: dev (localhost) or prd (remote)",
    )
    base_url: str = Field(
        default="",
        description="Auth service base URL (computed from mode)",
    )
    api_key: str = Field(
        default="",
        description="API key for authenticating with upstream service (STDIO mode)",
    )
    server_name: str = Field(default="yirifi-auth")
    server_description: str = Field(default="MCP server for Yirifi Auth Service")
    openapi_path: str = Field(default="/api/v1/swagger.json")

    model_config = {
        "env_prefix": "AUTH_SERVICE_",
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def set_defaults_from_environment(self) -> "AuthServiceConfig":
        """Set base_url and api_key from environment if not explicitly provided."""
        if not self.base_url:
            self.base_url = AUTH_SERVICE_URLS[self.mode]
        # Use unified YIRIFI_API_KEY if service-specific key not set
        if not self.api_key:
            self.api_key = get_api_key()
        return self


class RegServiceConfig(ServiceConfig):
    """Configuration for reg-service MCP server.

    URLs are determined by mode (dev/prod), not environment variables.
    Authentication: For STDIO transport, uses API key from environment:
    - YIRIFI_API_KEY (unified, recommended)
    - REG_SERVICE_API_KEY (service-specific fallback)
    For HTTP transport, client's X-API-Key header is passed through.
    """

    mode: Literal["dev", "prd"] = Field(
        default="prd",
        description="Environment mode: dev (localhost) or prd (remote)",
    )
    base_url: str = Field(
        default="",
        description="Reg service base URL (computed from mode)",
    )
    api_key: str = Field(
        default="",
        description="API key for authenticating with upstream service (STDIO mode)",
    )
    server_name: str = Field(default="yirifi-reg")
    server_description: str = Field(default="MCP server for Yirifi Reg Service")
    openapi_path: str = Field(default="/api/v1/swagger.json")

    model_config = {
        "env_prefix": "REG_SERVICE_",
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def set_defaults_from_environment(self) -> "RegServiceConfig":
        """Set base_url and api_key from environment if not explicitly provided."""
        if not self.base_url:
            self.base_url = REG_SERVICE_URLS[self.mode]
        # Use unified YIRIFI_API_KEY if service-specific key not set
        if not self.api_key:
            self.api_key = get_api_key()
        return self
