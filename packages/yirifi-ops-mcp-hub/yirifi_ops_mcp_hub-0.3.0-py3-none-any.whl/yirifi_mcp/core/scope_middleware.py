"""MCP Protocol Scope Handling for URL-based tool filtering.

MCPScopeWrapper: ASGI wrapper that normalizes paths and sets scope in ContextVar.
Tool filtering is handled by ScopeFilterMiddleware at the FastMCP protocol layer.

URL path patterns:
- /mcp/message → all tools
- /mcp/auth/message → only auth service tools
- /mcp/reg/message → only reg service tools
- /mcp/auth,reg/message → auth + reg tools (composable)
"""

import re

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send

from yirifi_mcp.core.scope import (
    ScopeRegistry,
    current_scope_tools,
    set_current_scope_tools,
)

logger = structlog.get_logger()

# Regex to parse service scope from URL path
# Matches: /mcp/auth, /mcp/reg, /mcp/auth,reg, etc.
# But NOT /mcp/message or /mcp/sse (MCP protocol paths)
SERVICE_PATH_PATTERN = re.compile(r"^/mcp/([a-z,]+)(?:/|$)")

# MCP protocol path segments that should NOT be treated as service names
MCP_PROTOCOL_PATHS = frozenset({"message", "sse", "events"})


def _parse_scope_from_path(path: str, registry: ScopeRegistry) -> set[str] | None:
    """Extract service scope from URL path.

    Args:
        path: Request URL path
        registry: ScopeRegistry with service→tools mapping

    Returns:
        Set of allowed tool names, or None for all tools
    """
    match = SERVICE_PATH_PATTERN.match(path)
    if not match:
        # /mcp or /mcp/ → all tools
        return None

    # Parse comma-separated services: /mcp/auth,reg → ["auth", "reg"]
    services_str = match.group(1)
    services = [s.strip() for s in services_str.split(",") if s.strip()]

    # Check if this is actually an MCP protocol path like /mcp/message
    # If any segment is an MCP protocol path, treat as "all tools"
    if any(s in MCP_PROTOCOL_PATHS for s in services):
        return None

    # Validate services exist
    valid_services = [s for s in services if s in registry]
    if not valid_services:
        logger.warning(
            "mcp_scope_no_valid_services",
            requested=services,
            available=registry.get_registered_services(),
        )
        return set()  # Empty set = no tools allowed

    return registry.get_tools_for_scope(valid_services)


def _normalize_path(path: str) -> str:
    """Normalize scoped path to base MCP path.

    Removes service scope segment from path so MCP app receives expected path.

    Examples:
        /mcp/auth/message -> /mcp/message
        /mcp/reg/message -> /mcp/message
        /mcp/auth,reg/message -> /mcp/message
        /mcp/message -> /mcp/message (unchanged)
    """
    match = SERVICE_PATH_PATTERN.match(path)
    if not match:
        return path

    services_str = match.group(1)
    # Check if this is actually a service scope (not MCP protocol path)
    services = [s.strip() for s in services_str.split(",") if s.strip()]
    if any(s in MCP_PROTOCOL_PATHS for s in services):
        return path  # Not a scope, don't rewrite

    # Remove the service segment: /mcp/auth/message -> /mcp/message
    # match.end() gives us the position after the service segment
    remainder = path[match.end():]
    if remainder.startswith("/"):
        return f"/mcp{remainder}"
    elif remainder:
        return f"/mcp/{remainder}"
    else:
        return "/mcp/message"  # Default to /mcp/message for base scoped path


class MCPScopeWrapper:
    """ASGI wrapper for path normalization and scope extraction.

    This wrapper:
    1. Parses URL path to extract service scope (e.g., /mcp/auth/message → auth)
    2. Stores allowed tools in ContextVar for ScopeFilterMiddleware to read
    3. Normalizes path for FastMCP (e.g., /mcp/auth/message → /mcp/message)

    Tool filtering is handled by ScopeFilterMiddleware at the FastMCP layer,
    which works correctly with streamable-http transport (SSE format).

    Example:
        >>> mcp_app = mcp.http_app(path="/mcp/message")
        >>> registry = get_default_registry()
        >>> wrapped = MCPScopeWrapper(mcp_app, registry)
        >>> # Mount wrapped app in Starlette
        >>> routes = [Mount("/", app=wrapped)]
    """

    def __init__(self, mcp_app: ASGIApp, registry: ScopeRegistry):
        """Initialize the wrapper.

        Args:
            mcp_app: The MCP ASGI application to wrap
            registry: ScopeRegistry with service→tools mapping
        """
        self.mcp_app = mcp_app
        self.registry = registry
        # Store lifespan for Starlette compatibility
        self.lifespan = getattr(mcp_app, "lifespan", None)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process ASGI request."""
        if scope["type"] != "http":
            await self.mcp_app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Determine allowed tools for this path
        allowed_tools = _parse_scope_from_path(path, self.registry)

        # Normalize path for MCP app
        # /mcp/auth/message -> /mcp/message
        normalized_path = _normalize_path(path)
        if normalized_path != path:
            scope = dict(scope)
            scope["path"] = normalized_path
            logger.debug(
                "mcp_path_normalized",
                original=path,
                normalized=normalized_path,
            )

        # Store scope in ContextVar for ScopeFilterMiddleware
        token = set_current_scope_tools(allowed_tools)

        try:
            # Pass through to MCP app - no response interception needed
            # Tool filtering is handled by ScopeFilterMiddleware
            await self.mcp_app(scope, receive, send)
        finally:
            # Reset ContextVar to prevent leakage between requests
            current_scope_tools.reset(token)


# MCPScopeMiddleware has been removed.
# Tool filtering is now handled by ScopeFilterMiddleware at the FastMCP layer.
# Use MCPScopeWrapper for ASGI-level path normalization and scope extraction.
