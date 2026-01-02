"""Scaffolding tool for creating new MCP servers.

Generates catalog-based MCP server scaffolds using the unified
endpoint definition pattern.
"""

from pathlib import Path

# =============================================================================
# TEMPLATES
# =============================================================================

SERVER_TEMPLATE = '''"""
{name} MCP Server

Auto-generates MCP tools from the {name} OpenAPI specification.
Uses unified catalog pattern for endpoint management.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
import structlog
from fastmcp import FastMCP

from yirifi_mcp.catalog.{name_lower} import {name_upper}_CATALOG
from yirifi_mcp.catalog.builder import CatalogBuilder
from yirifi_mcp.core.config import ServiceConfig
from yirifi_mcp.core.exceptions import (
    ActionNotFoundError,
    MissingPathParamError,
    UpstreamError,
)
from yirifi_mcp.core.http_client import create_authenticated_client
from yirifi_mcp.core.openapi_utils import (
    fetch_openapi_spec,
    get_spec_info,
    patch_openapi_spec,
)
from yirifi_mcp.core.route_filters import filter_openapi_paths
from yirifi_mcp.core.tool_optimizer import optimize_component_descriptions
from yirifi_mcp.gateway.dynamic import DynamicGateway

logger = structlog.get_logger()


class {name_camel}Config(ServiceConfig):
    """{name} service configuration."""

    base_url: str = "{base_url}"
    server_name: str = "yirifi-{name_lower}"
    server_description: str = "MCP server for {name}"
    openapi_path: str = "{openapi_path}"

    model_config = {{
        "env_prefix": "{name_upper}_",
        "env_file": ".env",
        "extra": "ignore",
    }}


class {name_camel}MCP:
    """{name} MCP server with proper resource management."""

    def __init__(self, config: {name_camel}Config | None = None):
        self.config = config or {name_camel}Config()
        self._client: httpx.AsyncClient | None = None
        self._mcp: FastMCP | None = None
        self._gateway: DynamicGateway | None = None
        self._builder = CatalogBuilder({name_upper}_CATALOG)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[FastMCP]:
        """Async context manager for resource lifecycle."""
        try:
            self._mcp = await self._build_mcp()
            yield self._mcp
        finally:
            if self._client:
                await self._client.aclose()
                self._client = None

    async def _build_mcp(self) -> FastMCP:
        """Build the MCP server instance."""
        logger.info(
            "building_{name_lower}_mcp",
            base_url=self.config.base_url,
            has_api_key=bool(self.config.api_key),
        )

        # Fetch and convert OpenAPI spec
        spec = await fetch_openapi_spec(
            base_url=self.config.base_url,
            openapi_path=self.config.openapi_path,
            api_key=self.config.api_key,
        )
        spec = patch_openapi_spec(spec, self.config.base_url)

        # Build route maps from unified catalog
        route_maps = self._builder.build_route_maps()
        filtered_spec = filter_openapi_paths(spec, route_maps)
        spec_info = get_spec_info(filtered_spec)

        logger.info(
            "spec_filtered",
            endpoints=spec_info["endpoints_count"],
            direct_tools=self._builder.catalog.direct_count,
            gateway_actions=self._builder.catalog.gateway_count,
        )

        # Get base URL from spec
        api_base_url = filtered_spec.get("servers", [{{}}])[0].get(
            "url", self.config.base_url
        )

        # Create authenticated HTTP client
        self._client = create_authenticated_client(
            base_url=api_base_url,
            api_key=self.config.api_key,
            timeout=self.config.request_timeout,
            connect_timeout=self.config.connect_timeout,
        )

        # Create MCP server from filtered OpenAPI spec
        mcp = FastMCP.from_openapi(
            openapi_spec=filtered_spec,
            client=self._client,
            name=self.config.server_name,
            mcp_component_fn=optimize_component_descriptions,
        )

        # Add gateway tools
        self._gateway = DynamicGateway(self._client, {name_upper}_CATALOG)
        self._register_gateway_tools(mcp)

        logger.info("{name_lower}_mcp_built", server_name=self.config.server_name)
        return mcp

    def _register_gateway_tools(self, mcp: FastMCP) -> None:
        """Register gateway tools on the MCP server."""
        gateway = self._gateway

        @mcp.tool()
        async def {name_lower}_api_catalog() -> dict:
            """List all available {name} API actions."""
            return await gateway.catalog()

        @mcp.tool()
        async def {name_lower}_api_call(
            action: str,
            path_params: dict | None = None,
            query_params: dict | None = None,
            body: dict | None = None,
        ) -> dict:
            """Execute any {name} API action dynamically."""
            try:
                return await gateway.call(action, path_params, query_params, body)
            except ActionNotFoundError as e:
                return {{"error": str(e), "available_actions": e.available[:20]}}
            except MissingPathParamError as e:
                return {{"error": str(e), "required_params": e.params, "path": e.path}}
            except UpstreamError as e:
                return {{"error": f"HTTP {{e.status_code}}", "detail": e.detail}}
            except Exception as e:
                logger.exception("gateway_error", action=action)
                return {{"error": str(e)}}


async def create_{name_lower}_mcp() -> FastMCP:
    """Factory function for creating {name} MCP server."""
    server = {name_camel}MCP()
    return await server._build_mcp()


def main():
    """Entry point for running {name} MCP server."""
    async def run():
        server = {name_camel}MCP()
        async with server.lifespan() as mcp:
            mcp.run()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\\nShutting down...")


if __name__ == "__main__":
    main()
'''

CATALOG_TEMPLATE = '''"""{name} service catalog - SINGLE SOURCE OF TRUTH.

Define all endpoints here with their exposure tiers.
This catalog is used to generate both RouteMap entries and API catalog.

Tier Guidelines:
- DIRECT: Frequent, safe operations (individual MCP tools)
- GATEWAY: Admin/dangerous operations (via gateway only)
- EXCLUDE: Never expose via MCP
"""

from yirifi_mcp.catalog.base import Endpoint, ServiceCatalog, Tier

{name_upper}_ENDPOINTS = [
    # Example endpoints - customize for your service
    # Endpoint("list_items", "GET", "/items/", "List all items", Tier.DIRECT),
    # Endpoint("get_item", "GET", "/items/{{item_id}}", "Get item by ID", Tier.DIRECT),
    # Endpoint("create_item", "POST", "/items/", "Create new item", Tier.DIRECT),
    # Endpoint("delete_item", "DELETE", "/items/{{item_id}}", "Delete item", Tier.GATEWAY, risk_level="high"),
]

{name_upper}_CATALOG = ServiceCatalog({name_upper}_ENDPOINTS)
'''

ROUTES_TEMPLATE = '''"""Route configuration for {name} MCP server.

Thin wrapper around the unified catalog for backward compatibility.
"""

from yirifi_mcp.catalog.{name_lower} import {name_upper}_CATALOG
from yirifi_mcp.catalog.builder import CatalogBuilder
from yirifi_mcp.core.route_filters import RouteMap

_builder = CatalogBuilder({name_upper}_CATALOG)


def get_route_maps() -> list[RouteMap]:
    """Get route maps generated from unified catalog."""
    return _builder.build_route_maps()


def get_api_catalog() -> dict[str, dict]:
    """Get API catalog for gateway tool."""
    return _builder.build_api_catalog()
'''

INIT_TEMPLATE = '''"""MCP server for {name}."""

from yirifi_mcp.servers.{name_lower}.server import create_{name_lower}_mcp, {name_camel}MCP

__all__ = ["create_{name_lower}_mcp", "{name_camel}MCP"]
'''


def create_server_scaffold(name: str, base_url: str, openapi_path: str) -> None:
    """
    Create a new server scaffold from templates.

    Args:
        name: Service name (e.g., "social", "dataqa")
        base_url: Base URL of the service
        openapi_path: Path to OpenAPI spec
    """
    # Normalize name
    name_lower = name.lower().replace("-", "_").replace(" ", "_")
    name_upper = name_lower.upper()
    name_camel = "".join(word.capitalize() for word in name_lower.split("_"))

    # Create server directory
    server_dir = Path(__file__).parent.parent / "servers" / name_lower
    server_dir.mkdir(parents=True, exist_ok=True)

    # Create catalog directory entry
    catalog_dir = Path(__file__).parent.parent / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    init_file = server_dir / "__init__.py"
    init_file.write_text(
        INIT_TEMPLATE.format(
            name=name,
            name_lower=name_lower,
            name_camel=name_camel,
        )
    )
    print(f"Created: {init_file}")

    # Create server.py
    server_file = server_dir / "server.py"
    server_file.write_text(
        SERVER_TEMPLATE.format(
            name=name,
            name_lower=name_lower,
            name_upper=name_upper,
            name_camel=name_camel,
            base_url=base_url,
            openapi_path=openapi_path,
        )
    )
    print(f"Created: {server_file}")

    # Create routes.py (backward compatibility)
    routes_file = server_dir / "routes.py"
    routes_file.write_text(
        ROUTES_TEMPLATE.format(
            name=name,
            name_lower=name_lower,
            name_upper=name_upper,
        )
    )
    print(f"Created: {routes_file}")

    # Create catalog file
    catalog_file = catalog_dir / f"{name_lower}.py"
    catalog_file.write_text(
        CATALOG_TEMPLATE.format(
            name=name,
            name_lower=name_lower,
            name_upper=name_upper,
        )
    )
    print(f"Created: {catalog_file}")
