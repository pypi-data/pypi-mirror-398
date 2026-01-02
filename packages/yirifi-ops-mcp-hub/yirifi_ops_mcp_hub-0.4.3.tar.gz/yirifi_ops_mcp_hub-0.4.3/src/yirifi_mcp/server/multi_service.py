"""Multi-service MCP server that combines multiple service servers into one."""

from typing import Literal

import structlog
from fastmcp import FastMCP

from yirifi_mcp.core.config import ServiceConfig, create_service_config
from yirifi_mcp.core.environment_middleware import MultiServiceEnvironmentMiddleware
from yirifi_mcp.core.scope_filter_middleware import ScopeFilterMiddleware
from yirifi_mcp.core.toon_encoder import OutputFormat

logger = structlog.get_logger()

ModeName = Literal["dev", "prd"]


def get_available_services() -> list[str]:
    """Get list of available service names from unified registry.

    This replaces the hardcoded AVAILABLE_SERVICES list.

    Returns:
        Sorted list of service names
    """
    from yirifi_mcp.core.unified_registry import get_unified_registry

    registry = get_unified_registry()
    registry.discover()
    return registry.get_available_names()


async def create_service_server(
    service: str,
    mode: ModeName,
    output_format: OutputFormat = OutputFormat.AUTO,
) -> FastMCP:
    """Create a single service server using unified registry.

    This replaces the hardcoded if/elif chains.

    Args:
        service: Service name (auth, reg, risk, etc.)
        mode: Environment mode (dev, prd)
        output_format: Response output format (auto, json, toon)

    Returns:
        FastMCP server instance for the service

    Raises:
        ValueError: If service is not found in registry
    """
    from yirifi_mcp.core.unified_registry import get_unified_registry

    registry = get_unified_registry()
    registry.discover()

    descriptor = registry.get(service)
    if descriptor is None:
        available = registry.get_available_names()
        raise ValueError(f"Unknown service: {service}. Available: {available}")

    # Create config using the dynamic config factory
    config = create_service_config(service, mode=mode, output_format=output_format)

    # Call the service's factory function
    return await descriptor.factory(config=config)


async def create_multi_service_server(
    services: list[str] | None = None,
    mode: ModeName = "prd",
    output_format: OutputFormat = OutputFormat.AUTO,
) -> FastMCP:
    """Create a combined MCP server with multiple services.

    Each service's tools are imported with a prefix to avoid conflicts.
    For example:
    - auth service: get_user_list, auth_api_call, auth_api_catalog
    - reg service: get_country_list, reg_api_call, reg_api_catalog

    Since each service already uses prefixed gateway tools (auth_api_call, reg_api_call),
    we don't add an additional prefix - tools are imported as-is.

    Args:
        services: List of services to include. Defaults to all available services.
        mode: Environment mode (dev, prd)
        output_format: Response output format (auto, json, toon)

    Returns:
        Combined FastMCP server with all service tools
    """
    if services is None:
        services = get_available_services()

    # Create the main server
    main_server = FastMCP(
        name="yirifi-ops-hub",
        instructions=f"""Yirifi Ops MCP Hub - Multi-Service Gateway

This server provides access to multiple Yirifi microservices:
{chr(10).join(f'- {svc}: Use {svc}_api_catalog to see available actions' for svc in services)}

Environment: {mode.upper()}

Each service has:
- Direct tools for common read operations (e.g., get_user_list, get_country_list)
- Gateway tools for all operations ({', '.join(f'{svc}_api_call' for svc in services)})
- Catalog tools to list available actions ({', '.join(f'{svc}_api_catalog' for svc in services)})

All responses include _environment metadata showing the database context.
""",
    )

    # Build tool→config mapping for multi-service middleware
    # This ensures each tool's response uses the correct service config for encoding
    tool_configs: dict[str, ServiceConfig] = {}

    # Import each service
    imported_count = 0
    for service in services:
        try:
            logger.info("importing_service", service=service, mode=mode)

            # Create service config using dynamic factory
            service_config = create_service_config(service, mode=mode, output_format=output_format)

            # Create service server using registry-driven dispatch
            service_server = await create_service_server(service, mode, output_format)

            # Map tool names to service config BEFORE import
            tools = await service_server._tool_manager.get_tools()
            for tool_name in tools.keys():
                tool_configs[tool_name] = service_config

            # Import without prefix - each service already has prefixed gateway tools
            # (auth_api_call, reg_api_call, etc.)
            await main_server.import_server(service_server, prefix=None)

            tool_count = len(tools)
            imported_count += tool_count

            logger.info(
                "service_imported",
                service=service,
                tools=tool_count,
            )

        except Exception as e:
            logger.error("service_import_failed", service=service, error=str(e))
            raise

    # Add scope filter middleware FIRST - filters tools based on URL path scope
    # This middleware reads allowed_tools from ContextVar (set by MCPScopeWrapper)
    # and filters on_list_tools/on_call_tool at the MCP protocol level
    main_server.add_middleware(ScopeFilterMiddleware())

    # Add multi-service middleware to main_server with tool→config mapping
    # This is needed because import_server() copies tools but NOT middleware
    # Use first service's config as default fallback
    default_config = create_service_config(
        services[0] if services else "auth",
        mode=mode,
        output_format=output_format,
    )
    main_server.add_middleware(MultiServiceEnvironmentMiddleware(tool_configs, default_config))

    logger.info(
        "multi_service_server_ready",
        services=services,
        total_tools=imported_count,
        mode=mode,
    )

    return main_server
