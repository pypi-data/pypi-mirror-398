"""Reg Service MCP Server.

This module provides the MCP server for the reg service using the
generic MCPServerFactory. It registers itself with the service registry
for CLI discovery.

Supports two catalog modes:
1. Explicit catalog (legacy): Uses REG_CATALOG with all endpoints defined
2. Spec-driven (new): Uses override files, catalog derived from OpenAPI spec

Use create_reg_server() for legacy mode (stable, default)
Use create_reg_server_spec_driven() for spec-driven mode (experimental)
"""

import asyncio

import structlog
from fastmcp import FastMCP

from yirifi_mcp.catalog.base import Tier
from yirifi_mcp.catalog.overrides.reg import (
    DESCRIPTION_OVERRIDES,
    DIRECT_ENDPOINTS,
    EXCLUDE_PATTERNS,
    IDEMPOTENT_OVERRIDES,
    NAME_OVERRIDES,
    RISK_OVERRIDES,
)
from yirifi_mcp.catalog.policy import DEFAULT_POLICY
from yirifi_mcp.catalog.reg_service import REG_CATALOG
from yirifi_mcp.core.config import RegServiceConfig
from yirifi_mcp.server.factory import MCPServerFactory
from yirifi_mcp.core.decorators import register_service

logger = structlog.get_logger()


@register_service(
    "reg",
    description="Reg service MCP server",
    urls={"dev": "http://localhost:5008", "prd": "https://reg.ops.yirifi.ai"},
    tags=["core", "reg"],
    catalog_mode="explicit",
    catalog_module="yirifi_mcp.catalog.reg_service",
)
async def create_reg_server(config: RegServiceConfig | None = None) -> FastMCP:
    """Create reg service MCP server.

    This factory function is registered with the service registry
    and can be invoked via CLI: yirifi-mcp serve reg

    Args:
        config: Optional config override. If not provided, creates default config.

    Returns:
        Configured FastMCP server instance
    """
    if config is None:
        config = RegServiceConfig()
    factory = MCPServerFactory(
        catalog=REG_CATALOG,
        config=config,
        gateway_prefix="reg",  # Creates reg_api_catalog and reg_api_call
    )
    return await factory.build()


async def create_reg_server_spec_driven(
    config: RegServiceConfig | None = None,
    *,
    validate_policy: bool = False,
) -> FastMCP:
    """Create reg service MCP server using spec-driven catalog.

    This is the new approach that derives the catalog from the OpenAPI spec
    with minimal overrides. It eliminates manual endpoint definitions while
    maintaining the same safety guarantees.

    Args:
        config: Optional config override. If not provided, creates default config.
        validate_policy: If True, validates catalog against DEFAULT_POLICY.

    Returns:
        Configured FastMCP server instance

    Example:
        >>> mcp = await create_reg_server_spec_driven(validate_policy=True)
        >>> mcp.run()
    """
    if config is None:
        config = RegServiceConfig()

    factory = MCPServerFactory(
        config=config,
        gateway_prefix="reg",
        # Spec-driven mode: derive catalog from OpenAPI spec with these overrides
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


async def create_reg_server_with_lifespan():
    """Create reg server with proper resource lifecycle.

    Use this when you need automatic cleanup of HTTP clients.

    Example:
        >>> async with create_reg_server_with_lifespan() as mcp:
        ...     mcp.run()
    """
    config = RegServiceConfig()
    factory = MCPServerFactory(
        catalog=REG_CATALOG,
        config=config,
        gateway_prefix="reg",
    )
    return factory.lifespan()


def main():
    """Entry point for running reg-service MCP server."""

    async def run():
        config = RegServiceConfig()
        factory = MCPServerFactory(
            catalog=REG_CATALOG,
            config=config,
            gateway_prefix="reg",
        )
        async with factory.lifespan() as mcp:
            mcp.run()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
