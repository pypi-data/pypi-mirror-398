"""Risk Service MCP Server.

This module provides the MCP server for the risk service using the
generic MCPServerFactory. It registers itself with the service registry
for CLI discovery.

Uses spec-driven mode: catalog derived from OpenAPI spec with overrides.
No explicit catalog file needed - endpoints are discovered from the API spec.
"""

import asyncio

import structlog
from fastmcp import FastMCP

from yirifi_mcp.catalog.base import Tier
from yirifi_mcp.catalog.overrides.risk import (
    DESCRIPTION_OVERRIDES,
    DIRECT_ENDPOINTS,
    EXCLUDE_PATTERNS,
    IDEMPOTENT_OVERRIDES,
    NAME_OVERRIDES,
    RISK_OVERRIDES,
)
from yirifi_mcp.catalog.policy import DEFAULT_POLICY
from yirifi_mcp.core.config import RiskServiceConfig
from yirifi_mcp.server.factory import MCPServerFactory
from yirifi_mcp.core.decorators import register_service

logger = structlog.get_logger()


@register_service(
    "risk",
    description="Risk service MCP server",
    urls={"dev": "http://localhost:5012", "prd": "https://risk.ops.yirifi.ai"},
    tags=["core", "risk"],
    catalog_mode="spec-driven",
    overrides_module="yirifi_mcp.catalog.overrides.risk",
    # For HTTP mode scope filtering, risk also needs a catalog
    catalog_module="yirifi_mcp.catalog.risk_service",
)
async def create_risk_server(config: RiskServiceConfig | None = None) -> FastMCP:
    """Create risk service MCP server using spec-driven catalog.

    This factory function is registered with the service registry
    and can be invoked via CLI: yirifi-ops-mcp-hub -s risk

    The catalog is derived from the OpenAPI spec with minimal overrides,
    eliminating manual endpoint definitions while maintaining safety.

    Args:
        config: Optional config override. If not provided, creates default config.

    Returns:
        Configured FastMCP server instance
    """
    if config is None:
        config = RiskServiceConfig()

    factory = MCPServerFactory(
        config=config,
        gateway_prefix="risk",  # Creates risk_api_catalog and risk_api_call
        # Spec-driven mode: derive catalog from OpenAPI spec with these overrides
        tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        risk_overrides=RISK_OVERRIDES,
        name_overrides=NAME_OVERRIDES,
        description_overrides=DESCRIPTION_OVERRIDES,
        idempotent_overrides=IDEMPOTENT_OVERRIDES,
        exclude_patterns=EXCLUDE_PATTERNS,
    )
    return await factory.build()


async def create_risk_server_spec_driven(
    config: RiskServiceConfig | None = None,
    *,
    validate_policy: bool = False,
) -> FastMCP:
    """Create risk service MCP server with optional policy validation.

    Args:
        config: Optional config override. If not provided, creates default config.
        validate_policy: If True, validates catalog against DEFAULT_POLICY.

    Returns:
        Configured FastMCP server instance
    """
    if config is None:
        config = RiskServiceConfig()

    factory = MCPServerFactory(
        config=config,
        gateway_prefix="risk",
        tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        risk_overrides=RISK_OVERRIDES,
        name_overrides=NAME_OVERRIDES,
        description_overrides=DESCRIPTION_OVERRIDES,
        idempotent_overrides=IDEMPOTENT_OVERRIDES,
        exclude_patterns=EXCLUDE_PATTERNS,
        policy=DEFAULT_POLICY if validate_policy else None,
    )
    return await factory.build()


async def create_risk_server_with_lifespan():
    """Create risk server with proper resource lifecycle.

    Use this when you need automatic cleanup of HTTP clients.

    Example:
        >>> async with create_risk_server_with_lifespan() as mcp:
        ...     mcp.run()
    """
    config = RiskServiceConfig()
    factory = MCPServerFactory(
        config=config,
        gateway_prefix="risk",
        tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        risk_overrides=RISK_OVERRIDES,
        exclude_patterns=EXCLUDE_PATTERNS,
    )
    return factory.lifespan()


def main():
    """Entry point for running risk-service MCP server."""

    async def run():
        config = RiskServiceConfig()
        factory = MCPServerFactory(
            config=config,
            gateway_prefix="risk",
            tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
            risk_overrides=RISK_OVERRIDES,
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
