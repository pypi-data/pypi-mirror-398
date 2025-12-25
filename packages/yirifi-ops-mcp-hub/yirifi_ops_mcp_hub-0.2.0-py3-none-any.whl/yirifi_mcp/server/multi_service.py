"""Multi-service MCP server that combines multiple service servers into one."""

from typing import Literal

import structlog
from fastmcp import FastMCP

from yirifi_mcp.core.config import AuthServiceConfig, RegServiceConfig

logger = structlog.get_logger()

# Service registry - add new services here
AVAILABLE_SERVICES = ["auth", "reg"]

ServiceName = Literal["auth", "reg"]
ModeName = Literal["dev", "prd"]


async def create_service_server(
    service: ServiceName,
    mode: ModeName,
) -> FastMCP:
    """Create a single service server.

    Args:
        service: Service name (auth, reg, etc.)
        mode: Environment mode (dev, prd)

    Returns:
        FastMCP server instance for the service
    """
    if service == "auth":
        from yirifi_mcp.servers.auth_service.server import create_auth_server

        config = AuthServiceConfig(mode=mode)
        return await create_auth_server(config=config)

    elif service == "reg":
        from yirifi_mcp.servers.reg_service.server import create_reg_server

        config = RegServiceConfig(mode=mode)
        return await create_reg_server(config=config)

    else:
        raise ValueError(f"Unknown service: {service}")


async def create_multi_service_server(
    services: list[ServiceName] | None = None,
    mode: ModeName = "prd",
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

    Returns:
        Combined FastMCP server with all service tools
    """
    if services is None:
        services = AVAILABLE_SERVICES

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

    # Import each service
    imported_count = 0
    for service in services:
        try:
            logger.info("importing_service", service=service, mode=mode)
            service_server = await create_service_server(service, mode)

            # Import without prefix - each service already has prefixed gateway tools
            # (auth_api_call, reg_api_call, etc.)
            await main_server.import_server(service_server, prefix=None)

            # Count tools
            tools = await service_server._tool_manager.get_tools()
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

    logger.info(
        "multi_service_server_ready",
        services=services,
        total_tools=imported_count,
        mode=mode,
    )

    return main_server


def get_available_services() -> list[str]:
    """Get list of available service names."""
    return AVAILABLE_SERVICES.copy()
