"""HTTP server utilities for MCP deployment.

Provides functions to create ASGI applications from FastMCP servers
for deployment with uvicorn or other ASGI servers.

Supports path-based service scoping:
- /mcp → All services (all tools)
- /mcp/auth → Auth service only
- /mcp/reg → Reg service only
- /mcp/auth,reg → Auth + Reg (composable)
"""

import asyncio

import structlog
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from yirifi_mcp.core.middleware import (
    APIKeyPassthroughASGIMiddleware,
    APIKeyPassthroughMiddleware,
)
from yirifi_mcp.core.scope import get_default_registry
from yirifi_mcp.core.scope_middleware import MCPScopeWrapper
from yirifi_mcp.core.toon_encoder import OutputFormat
from yirifi_mcp.core.transport import HTTPTransportConfig

logger = structlog.get_logger()


async def health_check(request):
    """Health check endpoint for load balancers and orchestrators."""
    return JSONResponse({"status": "healthy", "service": "yirifi-mcp"})


def create_http_app(
    mcp: FastMCP,
    config: HTTPTransportConfig,
) -> Starlette:
    """Create ASGI application from FastMCP server.

    Wraps the FastMCP HTTP app with:
    - Health check endpoints at /health
    - API key passthrough middleware (X-API-Key -> upstream)

    Args:
        mcp: FastMCP server instance (must be built)
        config: HTTP transport configuration

    Returns:
        Starlette ASGI application ready for uvicorn

    Example:
        >>> mcp = await factory.build()
        >>> config = HTTPTransportConfig(port=8000)
        >>> app = create_http_app(mcp, config)
        >>> # Run with: uvicorn module:app --host 0.0.0.0 --port 8000
    """
    # Get FastMCP's HTTP app with streamable-http transport (MCP 2025-03-26+)
    mcp_asgi_app = mcp.http_app(
        path=config.path,
        transport="streamable-http",
    )

    # Create Starlette app with health routes and mounted MCP app
    # IMPORTANT: Pass the lifespan from the MCP app to enable proper task group initialization
    routes = [
        Route("/health", health_check, methods=["GET"]),
        Route("/health/live", health_check, methods=["GET"]),
        Route("/health/ready", health_check, methods=["GET"]),
        Mount("/", app=mcp_asgi_app),
    ]

    app = Starlette(routes=routes, lifespan=mcp_asgi_app.lifespan)

    # Add passthrough middleware - extracts X-API-Key and passes to upstream
    app.add_middleware(APIKeyPassthroughMiddleware)
    logger.info("http_passthrough_auth_enabled", header="X-API-Key")

    logger.info(
        "http_app_created",
        host=config.host,
        port=config.port,
        path=config.path,
        stateless=config.stateless,
    )

    return app


def create_scoped_http_app(
    mcp: FastMCP,
    config: HTTPTransportConfig,
) -> Starlette:
    """Create ASGI application with path-based service scoping.

    This version supports filtering tools based on URL path:
    - /mcp/message → All tools from all services
    - /mcp/auth/message → Only auth service tools
    - /mcp/reg/message → Only reg service tools
    - /mcp/auth,reg/message → Auth + Reg tools (composable)

    The MCP server contains ALL tools, but responses are filtered
    based on the request path. The MCPScopeWrapper normalizes paths
    (e.g., /mcp/auth/message → /mcp/message) before they reach FastMCP.

    Args:
        mcp: FastMCP server instance with all services
        config: HTTP transport configuration

    Returns:
        Starlette ASGI application with scope filtering

    Example:
        >>> mcp = await create_multi_service_server()
        >>> config = HTTPTransportConfig(port=8000)
        >>> app = create_scoped_http_app(mcp, config)
    """
    # Get FastMCP's HTTP app
    # The path="/mcp/message" is the full path for MCP protocol messages
    mcp_asgi_app = mcp.http_app(
        path="/mcp/message",
        transport="streamable-http",
    )

    # Build scope registry from catalogs
    registry = get_default_registry()

    # Wrap MCP app with scope handler
    # This wrapper normalizes paths (/mcp/auth/message → /mcp/message)
    # and filters tools based on the original path scope.
    # The wrapper sits directly in front of FastMCP - no routing in between.
    scoped_mcp_app = MCPScopeWrapper(mcp_asgi_app, registry)

    # Create Starlette app
    # Mount the wrapped MCP app at root
    routes = [
        Route("/health", health_check, methods=["GET"]),
        Route("/health/live", health_check, methods=["GET"]),
        Route("/health/ready", health_check, methods=["GET"]),
        # Mount the scope wrapper - it handles path normalization
        Mount("/", app=scoped_mcp_app),
    ]

    # Use the original MCP app's lifespan for proper initialization
    starlette_app = Starlette(routes=routes, lifespan=mcp_asgi_app.lifespan)

    # Wrap with pure ASGI middleware for API key passthrough
    # We use the ASGI version instead of BaseHTTPMiddleware because
    # our scope wrapper sends responses directly via send() which
    # doesn't work with Starlette's BaseHTTPMiddleware.
    app = APIKeyPassthroughASGIMiddleware(starlette_app)

    logger.info("http_passthrough_auth_enabled", header="X-API-Key")
    # Generate dynamic paths based on registered services
    services = registry.get_registered_services()
    dynamic_paths = ["/mcp/message"] + [f"/mcp/{svc}/message" for svc in services]
    if len(services) >= 2:
        # Add example composite path
        dynamic_paths.append(f"/mcp/{','.join(services[:2])}/message")

    logger.info(
        "http_scoped_app_created",
        host=config.host,
        port=config.port,
        services=services,
        total_tools=len(registry.get_all_tools()),
        paths=dynamic_paths,
    )

    return app


async def create_scoped_http_app_async(
    mode: str = "prd",
    output_format: OutputFormat = OutputFormat.AUTO,
    config: HTTPTransportConfig | None = None,
) -> Starlette:
    """Create scoped HTTP app with multi-service MCP server.

    Convenience function that creates the MCP server and wraps it
    with scoped HTTP middleware.

    Args:
        mode: Environment mode ('dev' or 'prd')
        output_format: Response output format
        config: HTTP transport configuration (optional)

    Returns:
        Starlette ASGI application ready for uvicorn
    """
    from yirifi_mcp.server.multi_service import create_multi_service_server

    if config is None:
        config = HTTPTransportConfig()

    # Create multi-service server with ALL tools
    mcp = await create_multi_service_server(
        services=None,  # All services
        mode=mode,
        output_format=output_format,
    )

    return create_scoped_http_app(mcp, config)


def run_http_server(
    mcp: FastMCP,
    config: HTTPTransportConfig,
) -> None:
    """Run the MCP server with HTTP transport using uvicorn.

    This is a convenience function that creates the ASGI app and
    runs it with uvicorn in the current process.

    Args:
        mcp: FastMCP server instance (must be built)
        config: HTTP transport configuration
    """
    import uvicorn

    app = create_http_app(mcp, config)

    logger.info(
        "starting_http_server",
        host=config.host,
        port=config.port,
        path=config.path,
    )

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
    )


def run_scoped_http_server(
    mode: str = "prd",
    output_format: OutputFormat = OutputFormat.AUTO,
    config: HTTPTransportConfig | None = None,
) -> None:
    """Run the MCP server with path-based service scoping.

    Creates a multi-service MCP server and runs it with scope
    filtering middleware. Supports paths like:
    - /mcp → All tools
    - /mcp/auth → Auth tools only
    - /mcp/reg → Reg tools only

    Args:
        mode: Environment mode ('dev' or 'prd')
        output_format: Response output format
        config: HTTP transport configuration (optional)
    """
    import uvicorn

    if config is None:
        config = HTTPTransportConfig()

    # Create app asynchronously
    app = asyncio.run(
        create_scoped_http_app_async(
            mode=mode,
            output_format=output_format,
            config=config,
        )
    )

    registry = get_default_registry()

    # Generate dynamic endpoints based on registered services
    services = registry.get_registered_services()
    dynamic_endpoints = [f"http://{config.host}:{config.port}/mcp/message"]
    dynamic_endpoints.extend(
        f"http://{config.host}:{config.port}/mcp/{svc}/message" for svc in services
    )

    logger.info(
        "starting_scoped_http_server",
        host=config.host,
        port=config.port,
        services=services,
        endpoints=dynamic_endpoints,
    )

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
    )
