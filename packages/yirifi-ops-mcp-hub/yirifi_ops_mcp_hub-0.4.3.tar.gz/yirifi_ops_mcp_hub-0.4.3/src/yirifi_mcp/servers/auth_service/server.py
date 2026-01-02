"""Auth Service MCP Server.

This module provides the MCP server for the auth service using the
generic MCPServerFactory. It registers itself with the service registry
for CLI discovery.

Uses spec-driven catalog mode:
- Tier/risk metadata derived from x-mcp-* OpenAPI extensions in auth-service
- Override files provide fallback values if x-mcp attributes are missing
- Priority: x-mcp-* extensions in spec > overrides > safe defaults (GATEWAY/medium)
"""

import asyncio

import structlog
from fastmcp import FastMCP

from yirifi_mcp.catalog.base import Tier
from yirifi_mcp.catalog.overrides.auth import (
    DESCRIPTION_OVERRIDES,
    DIRECT_ENDPOINTS,
    EXCLUDE_PATTERNS,
    IDEMPOTENT_OVERRIDES,
    NAME_OVERRIDES,
    RISK_OVERRIDES,
)
from yirifi_mcp.catalog.policy import DEFAULT_POLICY
from yirifi_mcp.core.config import AuthServiceConfig
from yirifi_mcp.server.factory import MCPServerFactory
from yirifi_mcp.core.decorators import register_service

logger = structlog.get_logger()


@register_service(
    "auth",
    description="Auth service MCP server",
    urls={"dev": "http://localhost:5100", "prd": "https://auth.ops.yirifi.ai"},
    tags=["core", "auth"],
    catalog_mode="spec-driven",
    overrides_module="yirifi_mcp.catalog.overrides.auth",
)
async def create_auth_server(
    config: AuthServiceConfig | None = None,
    *,
    validate_policy: bool = False,
) -> FastMCP:
    """Create auth service MCP server.

    This factory function is registered with the service registry
    and can be invoked via CLI: yirifi-mcp serve auth

    Uses spec-driven catalog mode where tier/risk metadata is derived from
    x-mcp-* OpenAPI extensions in the auth-service, with fallbacks to the
    overrides module for any endpoints missing the extensions.

    Args:
        config: Optional config override. If not provided, creates default config.
        validate_policy: If True, validates catalog against DEFAULT_POLICY.

    Returns:
        Configured FastMCP server instance
    """
    if config is None:
        config = AuthServiceConfig()

    factory = MCPServerFactory(
        config=config,
        gateway_prefix="auth",  # Creates auth_api_catalog and auth_api_call
        # Spec-driven mode: derive catalog from OpenAPI spec with fallback overrides
        tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        risk_overrides=RISK_OVERRIDES,
        name_overrides=NAME_OVERRIDES,
        description_overrides=DESCRIPTION_OVERRIDES,
        idempotent_overrides=IDEMPOTENT_OVERRIDES,
        exclude_patterns=EXCLUDE_PATTERNS,
        # Optional policy validation
        policy=DEFAULT_POLICY if validate_policy else None,
    )
    return await factory.build()


async def create_auth_server_with_lifespan():
    """Create auth server with proper resource lifecycle.

    Use this when you need automatic cleanup of HTTP clients.

    Example:
        >>> async with create_auth_server_with_lifespan() as mcp:
        ...     mcp.run()
    """
    config = AuthServiceConfig()
    factory = MCPServerFactory(
        config=config,
        gateway_prefix="auth",
        tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        risk_overrides=RISK_OVERRIDES,
        name_overrides=NAME_OVERRIDES,
        description_overrides=DESCRIPTION_OVERRIDES,
        idempotent_overrides=IDEMPOTENT_OVERRIDES,
        exclude_patterns=EXCLUDE_PATTERNS,
    )
    return factory.lifespan()


# Backward compatibility alias
create_auth_server_spec_driven = create_auth_server


async def create_auth_service_mcp(config: AuthServiceConfig | None = None) -> FastMCP:
    """Factory function for creating auth service MCP.

    DEPRECATED: Use create_auth_server() instead.

    Args:
        config: Optional config override.

    Returns:
        Configured FastMCP server instance
    """
    return await create_auth_server(config=config)


def main():
    """Entry point for running auth-service MCP server."""

    async def run():
        config = AuthServiceConfig()
        factory = MCPServerFactory(
            config=config,
            gateway_prefix="auth",
            tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
            risk_overrides=RISK_OVERRIDES,
            name_overrides=NAME_OVERRIDES,
            description_overrides=DESCRIPTION_OVERRIDES,
            idempotent_overrides=IDEMPOTENT_OVERRIDES,
            exclude_patterns=EXCLUDE_PATTERNS,
        )
        async with factory.lifespan() as mcp:
            mcp.run()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
