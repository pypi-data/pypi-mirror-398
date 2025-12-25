"""HTTP server utilities for MCP deployment.

Provides functions to create ASGI applications from FastMCP servers
for deployment with uvicorn or other ASGI servers.
"""

import structlog
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from yirifi_mcp.core.middleware import APIKeyPassthroughMiddleware
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
    # Get FastMCP's streamable HTTP app
    mcp_asgi_app = mcp.http_app(path=config.path)

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
