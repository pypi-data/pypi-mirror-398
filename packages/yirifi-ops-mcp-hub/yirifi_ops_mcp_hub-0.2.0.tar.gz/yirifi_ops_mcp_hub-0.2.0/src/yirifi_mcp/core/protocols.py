"""Protocol definitions for dependency injection and testing."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class MCPServerProtocol(Protocol):
    """Protocol for MCP server implementations."""

    async def get_tools(self) -> dict:
        """Get available tools from the server."""
        ...

    def run(self) -> None:
        """Run the MCP server."""
        ...


@runtime_checkable
class GatewayProtocol(Protocol):
    """Protocol for gateway implementations."""

    async def catalog(self) -> dict[str, str]:
        """Return available actions as {name: description}."""
        ...

    async def call(
        self,
        action: str,
        path_params: dict | None = None,
        query_params: dict | None = None,
        body: dict | None = None,
    ) -> dict:
        """Execute an action and return the result."""
        ...


@runtime_checkable
class CatalogProtocol(Protocol):
    """Protocol for service catalogs."""

    def get_direct_endpoints(self) -> list:
        """Get endpoints exposed as direct MCP tools."""
        ...

    def get_gateway_endpoints(self) -> list:
        """Get endpoints accessible via gateway only."""
        ...

    def get_gateway_catalog(self) -> dict[str, str]:
        """Get gateway catalog as {action_name: description}."""
        ...
