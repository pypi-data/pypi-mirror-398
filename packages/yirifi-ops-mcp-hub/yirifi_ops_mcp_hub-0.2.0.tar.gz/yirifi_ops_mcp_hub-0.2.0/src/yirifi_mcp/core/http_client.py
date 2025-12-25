"""HTTP client factory with API key passthrough authentication."""

import httpx
import structlog

from yirifi_mcp.core.middleware import get_client_api_key
from yirifi_mcp.core.observability import log_request, log_response

logger = structlog.get_logger()


class PassthroughAuth(httpx.Auth):
    """HTTPX Auth that injects API key into requests.

    For HTTP transport: Reads API key from request context (set by middleware).
    For STDIO transport: Uses static_api_key provided at construction time.

    This enables both passthrough (HTTP) and static key (STDIO) authentication modes.
    """

    def __init__(self, static_api_key: str = ""):
        """Initialize with optional static API key for STDIO mode.

        Args:
            static_api_key: Fallback API key when context variable is empty
        """
        self._static_api_key = static_api_key

    def auth_flow(self, request: httpx.Request):
        """Add X-API-Key header from context variable or static key."""
        # Try context variable first (HTTP transport with middleware)
        api_key = get_client_api_key()
        # Fall back to static key (STDIO transport)
        if not api_key:
            api_key = self._static_api_key
        if api_key:
            request.headers["X-API-Key"] = api_key
        yield request


def create_passthrough_client(
    base_url: str,
    timeout: float = 30.0,
    connect_timeout: float = 10.0,
    static_api_key: str = "",
) -> httpx.AsyncClient:
    """
    Create an httpx AsyncClient with API key authentication.

    For HTTP transport: API key is read from request context (set by middleware).
    For STDIO transport: Uses static_api_key as the authentication credential.

    Args:
        base_url: Base URL for all requests
        timeout: Request timeout in seconds
        connect_timeout: Connection timeout in seconds
        static_api_key: API key for STDIO transport (fallback when context is empty)

    Returns:
        Configured httpx.AsyncClient instance with auth
    """
    logger.debug(
        "passthrough_http_client_created",
        base_url=base_url,
        has_static_key=bool(static_api_key),
    )

    return httpx.AsyncClient(
        base_url=base_url,
        auth=PassthroughAuth(static_api_key=static_api_key),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(
            timeout=timeout,
            connect=connect_timeout,
        ),
        follow_redirects=True,
        event_hooks={
            "request": [log_request],
            "response": [log_response],
        },
    )


def create_unauthenticated_client(
    base_url: str,
    timeout: float = 30.0,
    connect_timeout: float = 10.0,
) -> httpx.AsyncClient:
    """
    Create an httpx AsyncClient without authentication.

    Used for fetching OpenAPI specs and other public endpoints.

    Args:
        base_url: Base URL for all requests
        timeout: Request timeout in seconds
        connect_timeout: Connection timeout in seconds

    Returns:
        Configured httpx.AsyncClient instance without auth
    """
    logger.debug("unauthenticated_http_client_created", base_url=base_url)

    return httpx.AsyncClient(
        base_url=base_url,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=httpx.Timeout(
            timeout=timeout,
            connect=connect_timeout,
        ),
        follow_redirects=True,
    )
