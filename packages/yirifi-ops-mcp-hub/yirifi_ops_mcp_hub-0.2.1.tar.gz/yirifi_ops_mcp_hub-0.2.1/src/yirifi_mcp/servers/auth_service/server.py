"""Auth Service MCP Server.

This module provides the MCP server for the auth service using the
generic MCPServerFactory. It registers itself with the service registry
for CLI discovery.
"""

import asyncio

import structlog
from fastmcp import FastMCP

from yirifi_mcp.catalog.auth_service import AUTH_CATALOG
from yirifi_mcp.core.config import AuthServiceConfig
from yirifi_mcp.server.factory import MCPServerFactory
from yirifi_mcp.server.registry import register_service

logger = structlog.get_logger()


@register_service("auth", description="Auth service MCP server", tags=["core", "auth"])
async def create_auth_server(config: AuthServiceConfig | None = None) -> FastMCP:
    """Create auth service MCP server.

    This factory function is registered with the service registry
    and can be invoked via CLI: yirifi-mcp serve auth

    Args:
        config: Optional config override. If not provided, creates default config.

    Returns:
        Configured FastMCP server instance
    """
    if config is None:
        config = AuthServiceConfig()
    factory = MCPServerFactory(
        catalog=AUTH_CATALOG,
        config=config,
        gateway_prefix="auth",  # Creates auth_api_catalog and auth_api_call
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
        catalog=AUTH_CATALOG,
        config=config,
        gateway_prefix="auth",
    )
    return factory.lifespan()


# Legacy class for backward compatibility
class AuthServiceMCP:
    """Auth service MCP server wrapper.

    DEPRECATED: Use create_auth_server() or MCPServerFactory directly.

    This class is kept for backward compatibility but will be removed
    in a future version.
    """

    def __init__(self, config: AuthServiceConfig | None = None):
        """Initialize auth service MCP.

        Args:
            config: Optional config override. Uses env vars if not provided.
        """
        self.config = config or AuthServiceConfig()
        self.catalog = AUTH_CATALOG
        self._factory = MCPServerFactory(
            catalog=self.catalog,
            config=self.config,
            gateway_prefix="auth",
        )

    def lifespan(self):
        """Async context manager for resource lifecycle."""
        return self._factory.lifespan()


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
            catalog=AUTH_CATALOG,
            config=config,
            gateway_prefix="auth",
        )
        async with factory.lifespan() as mcp:
            mcp.run()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
