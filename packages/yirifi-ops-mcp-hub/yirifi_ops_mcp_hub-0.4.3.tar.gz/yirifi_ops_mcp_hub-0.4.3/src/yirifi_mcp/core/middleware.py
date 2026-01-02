"""HTTP middleware for MCP server authentication.

Provides API key passthrough for MCP clients connecting over HTTP.
Client's X-API-Key is extracted and forwarded to upstream services.
"""

import json
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger()

# Header name for client API key (passthrough to upstream)
CLIENT_API_KEY_HEADER = "X-API-Key"

# Context variable to store client API key for the current request
# This allows tools to access the client's key without explicit passing
client_api_key_var: ContextVar[str] = ContextVar("client_api_key", default="")

# Paths that don't require authentication
PUBLIC_PATHS = frozenset({"/health", "/health/live", "/health/ready"})

# Path prefixes that don't require authentication (OAuth discovery, etc.)
PUBLIC_PATH_PREFIXES = ("/.well-known/", "/register")


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
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PATH_PREFIXES):
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


class APIKeyPassthroughASGIMiddleware:
    """Pure ASGI middleware for API key passthrough.

    This version works correctly with raw ASGI apps and streaming responses,
    unlike BaseHTTPMiddleware which can have issues with ASGI apps that
    send responses directly via the send callable.

    Use this when wrapping apps that include raw ASGI components.
    """

    def __init__(self, app: ASGIApp):
        """Initialize the middleware.

        Args:
            app: The ASGI application to wrap
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process ASGI request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get path from scope
        path = scope.get("path", "")

        # Allow public paths without auth
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PATH_PREFIXES):
            await self.app(scope, receive, send)
            return

        # Extract API key from headers
        headers = dict(scope.get("headers", []))
        api_key = headers.get(b"x-api-key", b"").decode("utf-8")

        if not api_key:
            # Get client IP from scope
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"
            logger.warning(
                "client_api_key_missing",
                path=path,
                client_ip=client_ip,
            )
            # Send 401 response
            await self._send_error_response(
                send,
                status=401,
                error="missing_api_key",
                message=f"Missing {CLIENT_API_KEY_HEADER} header",
            )
            return

        # Store in context variable for downstream access
        token = client_api_key_var.set(api_key)
        logger.debug(
            "client_api_key_extracted",
            path=path,
            key_prefix=api_key[:8] + "..." if len(api_key) > 8 else "***",
        )

        try:
            await self.app(scope, receive, send)
        finally:
            # Reset context variable after request completes
            client_api_key_var.reset(token)

    async def _send_error_response(
        self,
        send: Send,
        status: int,
        error: str,
        message: str,
    ) -> None:
        """Send a JSON error response."""
        body = json.dumps({"error": error, "message": message}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
                "more_body": False,
            }
        )
