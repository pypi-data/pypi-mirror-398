"""Service registry for MCP server discovery and management."""

from typing import Callable, Awaitable
from dataclasses import dataclass, field

from fastmcp import FastMCP

import structlog

logger = structlog.get_logger()

# Type alias for service factory functions
ServiceFactory = Callable[[], Awaitable[FastMCP]]


@dataclass
class ServiceInfo:
    """Metadata about a registered service."""

    name: str
    description: str
    factory: ServiceFactory
    tags: list[str] = field(default_factory=list)


class ServiceRegistry:
    """Registry for discovering and managing MCP services.

    The registry allows services to self-register using the @register_service
    decorator, enabling dynamic discovery by the CLI.

    Example:
        >>> from yirifi_mcp.server import register_service
        >>>
        >>> @register_service("auth", description="Auth service MCP")
        ... async def create_auth_server():
        ...     factory = MCPServerFactory(AUTH_CATALOG, AuthServiceConfig())
        ...     return await factory.build()
        >>>
        >>> # Later, in CLI:
        >>> registry = ServiceRegistry()
        >>> server = await registry.create("auth")
        >>> server.run()
    """

    _instance: "ServiceRegistry | None" = None
    _services: dict[str, ServiceInfo]

    def __new__(cls) -> "ServiceRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
        return cls._instance

    def register(
        self,
        name: str,
        factory: ServiceFactory,
        *,
        description: str = "",
        tags: list[str] | None = None,
    ) -> None:
        """Register a service factory.

        Args:
            name: Unique service identifier (e.g., "auth", "crm")
            factory: Async function that creates a FastMCP instance
            description: Human-readable description
            tags: Optional tags for categorization
        """
        if name in self._services:
            logger.warning("service_already_registered", name=name)

        self._services[name] = ServiceInfo(
            name=name,
            description=description,
            factory=factory,
            tags=tags or [],
        )
        logger.debug("service_registered", name=name)

    def unregister(self, name: str) -> bool:
        """Remove a service from the registry.

        Returns:
            True if service was removed, False if not found
        """
        if name in self._services:
            del self._services[name]
            return True
        return False

    async def create(self, name: str) -> FastMCP:
        """Create an MCP server instance for a registered service.

        Args:
            name: Service identifier

        Returns:
            FastMCP server instance

        Raises:
            KeyError: If service is not registered
        """
        if name not in self._services:
            available = list(self._services.keys())
            raise KeyError(f"Unknown service: {name}. Available: {available}")

        info = self._services[name]
        logger.info("creating_service", name=name)
        return await info.factory()

    def list_services(self) -> list[ServiceInfo]:
        """Get all registered services."""
        return list(self._services.values())

    def get_service(self, name: str) -> ServiceInfo | None:
        """Get service info by name."""
        return self._services.get(name)

    def __contains__(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services

    def __len__(self) -> int:
        """Number of registered services."""
        return len(self._services)


# Global registry instance
_registry = ServiceRegistry()


def register_service(
    name: str,
    *,
    description: str = "",
    tags: list[str] | None = None,
):
    """Decorator to register a service factory function.

    Example:
        >>> @register_service("auth", description="Auth service MCP")
        ... async def create_auth_server():
        ...     factory = MCPServerFactory(AUTH_CATALOG, AuthServiceConfig())
        ...     return await factory.build()
    """

    def decorator(factory: ServiceFactory) -> ServiceFactory:
        _registry.register(name, factory, description=description, tags=tags)
        return factory

    return decorator


def get_registry() -> ServiceRegistry:
    """Get the global service registry."""
    return _registry
