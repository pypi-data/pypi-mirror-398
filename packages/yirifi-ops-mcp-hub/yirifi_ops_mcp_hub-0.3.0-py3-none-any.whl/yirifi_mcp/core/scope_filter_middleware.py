"""FastMCP middleware for scope-based tool filtering.

This middleware filters tools at the MCP protocol level, not HTTP level.
It reads allowed tools from a ContextVar set by the ASGI wrapper.

This approach works correctly with streamable-http transport because
filtering happens before responses are serialized to SSE format.
"""

from typing import Sequence

import structlog
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware
from fastmcp.server.middleware.middleware import CallNext, MiddlewareContext
from fastmcp.tools.tool import Tool, ToolResult
from mcp import types as mt

from yirifi_mcp.core.scope import get_current_scope_tools

logger = structlog.get_logger()


class ScopeFilterMiddleware(Middleware):
    """FastMCP middleware that filters tools based on URL path scope.

    Reads allowed tools from ContextVar (set by ASGI wrapper) and:
    1. Filters tools/list responses to only include allowed tools
    2. Rejects tools/call requests for tools outside scope

    When scope is None (ContextVar not set), all tools are allowed.
    This supports the base /mcp path which shows all tools.

    Example:
        >>> from yirifi_mcp.core.scope import set_current_scope_tools
        >>> # In ASGI layer, set the scope
        >>> token = set_current_scope_tools({"get_user_list", "auth_api_call"})
        >>> # Now tools/list will only return those 2 tools
    """

    async def on_list_tools(
        self,
        context: MiddlewareContext[mt.ListToolsRequest],
        call_next: CallNext[mt.ListToolsRequest, Sequence[Tool]],
    ) -> Sequence[Tool]:
        """Filter tools based on current scope.

        Args:
            context: Middleware context containing request params
            call_next: Function to call the next middleware/handler

        Returns:
            Sequence of tools, filtered by scope if set
        """
        # Get all tools from the server
        all_tools = await call_next(context)

        # Check scope restriction
        allowed_tools = get_current_scope_tools()

        if allowed_tools is None:
            # No scope restriction - return all tools
            logger.debug(
                "scope_filter_tools_list",
                scope="all",
                count=len(all_tools),
            )
            return all_tools

        # Filter to only allowed tools
        filtered = [t for t in all_tools if t.name in allowed_tools]

        logger.info(
            "scope_filter_tools_filtered",
            original=len(all_tools),
            filtered=len(filtered),
            allowed_scope=len(allowed_tools),
        )

        return filtered

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Validate tool call is within scope.

        Args:
            context: Middleware context containing request params
            call_next: Function to call the next middleware/handler

        Returns:
            ToolResult from the tool, or error if out of scope
        """
        tool_name = context.message.name
        allowed_tools = get_current_scope_tools()

        if allowed_tools is not None and tool_name not in allowed_tools:
            # Tool not in scope - reject
            logger.warning(
                "scope_filter_tool_rejected",
                tool=tool_name,
                allowed_count=len(allowed_tools),
            )

            # Raise ToolError - will be converted to MCP error response
            raise ToolError(
                f"Tool '{tool_name}' is not available in this scope. "
                "Use /mcp for all tools or check the service path."
            )

        # Tool is allowed - proceed
        return await call_next(context)
