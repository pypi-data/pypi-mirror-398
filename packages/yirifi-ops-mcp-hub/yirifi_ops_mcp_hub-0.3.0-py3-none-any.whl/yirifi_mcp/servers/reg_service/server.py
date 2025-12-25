"""Reg Service MCP Server.

This module provides the MCP server for the reg service using the
generic MCPServerFactory. It registers itself with the service registry
for CLI discovery.
"""

import asyncio

import structlog
from fastmcp import FastMCP

from yirifi_mcp.catalog.reg_service import REG_CATALOG
from yirifi_mcp.core.config import RegServiceConfig
from yirifi_mcp.server.factory import MCPServerFactory
from yirifi_mcp.server.registry import register_service

logger = structlog.get_logger()


@register_service("reg", description="Reg service MCP server", tags=["core", "reg"])
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
