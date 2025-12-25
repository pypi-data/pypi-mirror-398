"""FastMCP middleware for wrapping all tool responses with environment context."""

from typing import TYPE_CHECKING

import structlog
from fastmcp.server.middleware import Middleware
from fastmcp.server.middleware.middleware import CallNext, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from mcp import types as mt

from yirifi_mcp.core.response_wrapper import wrap_response
from yirifi_mcp.core.toon_encoder import encode_response

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

        tool_name = context.message.name

        # Gateway tools already wrap with _environment, just need encoding
        is_gateway_tool = tool_name.endswith("_api_catalog") or tool_name.endswith(
            "_api_call"
        )

        # Process each content item
        wrapped_content = []
        for item in result.content:
            if item.type == "text":
                # Try to parse as JSON and wrap/encode
                import json

                try:
                    data = json.loads(item.text)

                    if is_gateway_tool:
                        # Gateway tools already wrapped, just encode
                        encoded_text, _format_used = encode_response(
                            data, self._config.output_format
                        )
                    else:
                        # Regular tools need wrapping first
                        is_mutation = self._is_mutation_tool(tool_name)
                        wrapped = wrap_response(
                            data, self._config, is_mutation=is_mutation
                        )
                        encoded_text, _format_used = encode_response(
                            wrapped, self._config.output_format
                        )

                    wrapped_content.append(
                        mt.TextContent(type="text", text=encoded_text)
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


class MultiServiceEnvironmentMiddleware(Middleware):
    """Middleware for multi-service hub that routes tools to their correct service config.

    When tools from multiple services are imported into a single main_server,
    the original per-service middleware is lost. This middleware maintains a
    mapping of tool names to their original service configs, ensuring each
    tool's response includes the correct _environment metadata and encoding.

    Example:
        >>> tool_configs = {
        ...     "get_user_list": auth_config,
        ...     "auth_api_call": auth_config,
        ...     "get_country_list": reg_config,
        ...     "reg_api_call": reg_config,
        ... }
        >>> middleware = MultiServiceEnvironmentMiddleware(tool_configs, default_config)
        >>> main_server.add_middleware(middleware)
    """

    def __init__(
        self,
        tool_configs: dict[str, "ServiceConfig"],
        default_config: "ServiceConfig",
    ):
        """Initialize with tool-to-config mapping.

        Args:
            tool_configs: Mapping of tool names to their service configs
            default_config: Fallback config for tools not in the mapping
        """
        self._tool_configs = tool_configs
        self._default_config = default_config

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        """Wrap tool responses with correct service environment context.

        Args:
            context: Middleware context containing request params
            call_next: Function to call the next middleware/handler

        Returns:
            ToolResult with wrapped content containing _environment metadata
        """
        # Execute the tool
        result = await call_next(context)

        tool_name = context.message.name

        # Look up the config for this tool
        config = self._tool_configs.get(tool_name, self._default_config)

        # Gateway tools already wrap with _environment, just need encoding
        is_gateway_tool = tool_name.endswith("_api_catalog") or tool_name.endswith(
            "_api_call"
        )

        # Process each content item
        wrapped_content = []
        for item in result.content:
            if item.type == "text":
                # Try to parse as JSON and wrap/encode
                import json

                try:
                    data = json.loads(item.text)

                    if is_gateway_tool:
                        # Gateway tools already wrapped, just encode
                        encoded_text, _format_used = encode_response(
                            data, config.output_format
                        )
                    else:
                        # Regular tools need wrapping first
                        is_mutation = self._is_mutation_tool(tool_name)
                        wrapped = wrap_response(
                            data, config, is_mutation=is_mutation
                        )
                        encoded_text, _format_used = encode_response(
                            wrapped, config.output_format
                        )

                    wrapped_content.append(
                        mt.TextContent(type="text", text=encoded_text)
                    )
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, pass through unchanged
                    wrapped_content.append(item)
            else:
                # Non-text content, pass through unchanged
                wrapped_content.append(item)

        return ToolResult(content=wrapped_content)

    def _is_mutation_tool(self, tool_name: str) -> bool:
        """Check if tool name indicates a mutation operation."""
        mutation_prefixes = ("post_", "put_", "delete_", "patch_")
        return tool_name.lower().startswith(mutation_prefixes)
