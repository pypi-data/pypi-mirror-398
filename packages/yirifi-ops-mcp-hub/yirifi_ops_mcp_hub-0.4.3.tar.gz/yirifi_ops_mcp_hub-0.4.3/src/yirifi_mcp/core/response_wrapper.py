"""Response wrapper for environment context.

Wraps all MCP tool responses with environment metadata to ensure
AI agents always know which database (DEV/UAT/PRD) they're operating against.
"""

from typing import Any

from yirifi_mcp.core.config import ServiceConfig


def wrap_response(
    response: Any,
    config: ServiceConfig,
    is_mutation: bool = False,
) -> dict:
    """Wrap API response with environment context.

    Args:
        response: The raw API response (dict, list, or any JSON-serializable)
        config: Service configuration containing mode and server info
        is_mutation: Whether this is a mutating operation (POST/PUT/DELETE)

    Returns:
        Wrapped response with _environment metadata
    """
    warning = None
    if config.mode == "prd" and is_mutation:
        warning = "PRODUCTION: This operation modifies live data"

    return {
        "_environment": {
            "database": config.mode.upper(),
            "mode": config.mode,
            "server": config.server_name,
            "base_url": config.base_url,
            "warning": warning,
        },
        "data": response,
    }


def is_mutation_method(method: str) -> bool:
    """Check if HTTP method is a mutation (modifies data).

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)

    Returns:
        True if the method modifies data
    """
    return method.upper() in ("POST", "PUT", "DELETE", "PATCH")
