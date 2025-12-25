"""HTTP middleware for MCP server authentication.

Provides API key passthrough for MCP clients connecting over HTTP.
Client's X-API-Key is extracted and forwarded to upstream services.
"""

from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger()

# Header name for client API key (passthrough to upstream)
CLIENT_API_KEY_HEADER = "X-API-Key"

# Context variable to store client API key for the current request
# This allows tools to access the client's key without explicit passing
client_api_key_var: ContextVar[str] = ContextVar("client_api_key", default="")

# Paths that don't require authentication
PUBLIC_PATHS = frozenset({"/health", "/health/live", "/health/ready"})


def get_client_api_key() -> str:
    """Get the client API key for the current request context.

    Returns:
        The client's API key or empty string if not set
    """
    return client_api_key_var.get()


class APIKeyPassthroughMiddleware(BaseHTTPMiddleware):
    """Middleware to extract client API key for passthrough to upstream services.

    Extracts X-API-Key from incoming requests and stores in context variable.
    The key is then forwarded to upstream services, preserving client identity.
    Health check endpoints are exempt from authentication.

    Example:
        >>> from starlette.applications import Starlette
        >>> app = Starlette()
        >>> app.add_middleware(APIKeyPassthroughMiddleware)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and extract API key for passthrough.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response from next handler or 401 error
        """
        # Allow public paths without auth
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Extract client's API key
        api_key = request.headers.get(CLIENT_API_KEY_HEADER)

        if not api_key:
            logger.warning(
                "client_api_key_missing",
                path=request.url.path,
                client_ip=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                {
                    "error": "missing_api_key",
                    "message": f"Missing {CLIENT_API_KEY_HEADER} header",
                },
                status_code=401,
            )

        # Store in context variable for downstream access
        token = client_api_key_var.set(api_key)
        logger.debug(
            "client_api_key_extracted",
            path=request.url.path,
            key_prefix=api_key[:8] + "..." if len(api_key) > 8 else "***",
        )

        try:
            return await call_next(request)
        finally:
            # Reset context variable after request completes
            client_api_key_var.reset(token)
