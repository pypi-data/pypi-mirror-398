"""FastMCP middleware for wrapping all tool responses with environment context."""

from typing import TYPE_CHECKING

import structlog
from fastmcp.server.middleware import Middleware
from fastmcp.server.middleware.middleware import CallNext, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from mcp import types as mt

from yirifi_mcp.core.response_wrapper import wrap_response

if TYPE_CHECKING:
    from yirifi_mcp.core.config import ServiceConfig

logger = structlog.get_logger()


class EnvironmentMiddleware(Middleware):
    """Middleware that wraps all tool responses with environment context.

    Adds _environment metadata to all tool responses, ensuring AI agents
    always know which database (DEV/UAT/PRD) they're operating against.

    For mutations in production, includes a warning message.

    Example output:
        {
            "_environment": {
                "database": "PRD",
                "mode": "prd",
                "server": "yirifi-reg",
                "base_url": "https://reg.ops.yirifi.ai",
                "warning": "PRODUCTION: This operation modifies live data"
            },
            "data": { ... actual response ... }
        }
    """

    def __init__(self, config: "ServiceConfig"):
        """Initialize with service configuration.

        Args:
            config: Service configuration containing mode, server_name, base_url
        """
        self._config = config

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Wrap tool responses with environment context.

        Args:
            context: Middleware context containing request params
            call_next: Function to call the next middleware/handler

        Returns:
            ToolResult with wrapped content containing _environment metadata
        """
        # Execute the tool
        result = await call_next(context)

        # Skip wrapping for gateway tools - they already wrap responses
        tool_name = context.message.name
        if tool_name.endswith("_api_catalog") or tool_name.endswith("_api_call"):
            return result

        # Wrap each content item
        wrapped_content = []
        for item in result.content:
            if item.type == "text":
                # Try to parse as JSON and wrap
                import json

                try:
                    data = json.loads(item.text)
                    # Determine if this is a mutation based on tool name
                    is_mutation = self._is_mutation_tool(tool_name)
                    wrapped = wrap_response(data, self._config, is_mutation=is_mutation)
                    wrapped_content.append(
                        mt.TextContent(type="text", text=json.dumps(wrapped, indent=2))
                    )
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, pass through unchanged
                    wrapped_content.append(item)
            else:
                # Non-text content, pass through unchanged
                wrapped_content.append(item)

        return ToolResult(content=wrapped_content)

    def _is_mutation_tool(self, tool_name: str) -> bool:
        """Check if tool name indicates a mutation operation.

        Args:
            tool_name: Name of the tool being called

        Returns:
            True if the tool is likely a mutation (post, put, delete, patch)
        """
        mutation_prefixes = ("post_", "put_", "delete_", "patch_")
        return tool_name.lower().startswith(mutation_prefixes)
