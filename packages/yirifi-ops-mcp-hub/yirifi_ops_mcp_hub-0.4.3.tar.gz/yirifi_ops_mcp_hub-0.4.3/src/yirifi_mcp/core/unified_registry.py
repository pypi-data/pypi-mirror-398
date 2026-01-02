"""Unified service registry for MCP service discovery and management.

This module provides the UnifiedServiceRegistry which serves as the single
source of truth for all service metadata. It supports:
- Decorator-based self-registration
- Entry point-based auto-discovery
- Dynamic CLI choice generation
- Scope registry building for HTTP filtering
"""

from importlib import import_module
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

import structlog

from .service_descriptor import ServiceDescriptor

if TYPE_CHECKING:
    from yirifi_mcp.catalog.base import ServiceCatalog
    from yirifi_mcp.core.scope import ScopeRegistry

logger = structlog.get_logger()


class UnifiedServiceRegistry:
    """Central registry for all service metadata.

    This registry:
    1. Stores ServiceDescriptor instances
    2. Auto-discovers services via entry points
    3. Provides dynamic access to service lists for CLI
    4. Builds scope mappings for HTTP filtering
    5. Supports both explicit and spec-driven catalogs

    Singleton pattern ensures consistent global state.

    Example:
        >>> registry = get_unified_registry()
        >>> registry.discover()  # Load from entry points
        >>> names = registry.get_available_names()  # ["auth", "reg", "risk"]
        >>> descriptor = registry.get("auth")
        >>> server = await descriptor.factory(config=config)
    """

    _instance: "UnifiedServiceRegistry | None" = None
    _services: dict[str, ServiceDescriptor]
    _loaded: bool

    # Entry point group name for service discovery
    ENTRY_POINT_GROUP = "yirifi_mcp.services"

    def __new__(cls) -> "UnifiedServiceRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
            cls._instance._loaded = False
        return cls._instance

    def register(self, descriptor: ServiceDescriptor) -> None:
        """Register a service descriptor.

        Args:
            descriptor: ServiceDescriptor with complete service metadata
        """
        if descriptor.name in self._services:
            logger.warning("service_already_registered", name=descriptor.name)

        self._services[descriptor.name] = descriptor
        logger.debug("service_registered", name=descriptor.name)

    def unregister(self, name: str) -> bool:
        """Remove a service from the registry.

        Args:
            name: Service identifier

        Returns:
            True if service was removed, False if not found
        """
        if name in self._services:
            del self._services[name]
            return True
        return False

    def discover(self, force: bool = False) -> None:
        """Discover and load services from entry points.

        This method:
        1. Reads entry points from yirifi_mcp.services group
        2. Imports each entry point module (which triggers @register_service)
        3. Sets _loaded to prevent redundant discovery

        Args:
            force: If True, re-discover even if already loaded
        """
        if self._loaded and not force:
            return

        # Get entry points for our group
        try:
            eps = entry_points(group=self.ENTRY_POINT_GROUP)
        except TypeError:
            # Python < 3.10 compatibility
            all_eps = entry_points()
            eps = all_eps.get(self.ENTRY_POINT_GROUP, [])

        for ep in eps:
            try:
                # Loading the entry point imports the module,
                # which triggers @register_service decorator
                ep.load()
                logger.debug("service_discovered", name=ep.name)
            except Exception as e:
                logger.error("service_discovery_failed", name=ep.name, error=str(e))

        self._loaded = True
        logger.info(
            "service_discovery_complete",
            count=len(self._services),
            services=list(self._services.keys()),
        )

    def get(self, name: str) -> ServiceDescriptor | None:
        """Get service descriptor by name.

        Args:
            name: Service identifier

        Returns:
            ServiceDescriptor or None if not found
        """
        self.discover()
        return self._services.get(name)

    def list_services(self) -> list[ServiceDescriptor]:
        """Get all registered service descriptors.

        Returns:
            List of all ServiceDescriptor instances
        """
        self.discover()
        return list(self._services.values())

    def get_available_names(self) -> list[str]:
        """Get list of service names for CLI choices.

        Returns:
            Sorted list of service names
        """
        self.discover()
        return sorted(self._services.keys())

    def get_catalog(self, name: str) -> "ServiceCatalog":
        """Get or build the catalog for a service.

        For explicit mode, imports and returns the catalog module.
        For spec-driven mode, raises an error (catalog is built during server creation).

        Args:
            name: Service identifier

        Returns:
            ServiceCatalog instance

        Raises:
            KeyError: If service not found
            ValueError: If service uses spec-driven mode
        """
        descriptor = self.get(name)
        if descriptor is None:
            raise KeyError(f"Unknown service: {name}")

        if descriptor.catalog_mode == "explicit" and descriptor.catalog_module:
            # Import explicit catalog
            module = import_module(descriptor.catalog_module)
            return getattr(module, descriptor.catalog_attr)

        # For spec-driven, we can't pre-build (needs async fetch)
        raise ValueError(
            f"Service '{name}' uses spec-driven catalog. "
            "Catalog is built during server creation."
        )

    def build_scope_registry(self) -> "ScopeRegistry":
        """Build ScopeRegistry from all registered services.

        For services with explicit or spec-driven catalogs, registers them
        if a catalog_module is available.

        Returns:
            Populated ScopeRegistry for HTTP filtering
        """
        from yirifi_mcp.core.scope import ScopeRegistry

        self.discover()
        registry = ScopeRegistry()

        for descriptor in self._services.values():
            # Try to import catalog if catalog_module is specified
            if descriptor.catalog_module:
                try:
                    module = import_module(descriptor.catalog_module)
                    catalog = getattr(module, descriptor.catalog_attr)
                    registry.register_service(descriptor.name, catalog)
                except Exception as e:
                    logger.debug(
                        "catalog_import_failed",
                        service=descriptor.name,
                        catalog_module=descriptor.catalog_module,
                        error=str(e),
                    )

        return registry

    def __contains__(self, name: str) -> bool:
        """Check if a service is registered."""
        self.discover()
        return name in self._services

    def __len__(self) -> int:
        """Number of registered services."""
        self.discover()
        return len(self._services)

    def __repr__(self) -> str:
        services = ", ".join(sorted(self._services.keys()))
        return f"UnifiedServiceRegistry(services=[{services}], count={len(self._services)})"


# Global instance
_unified_registry = UnifiedServiceRegistry()


def get_unified_registry() -> UnifiedServiceRegistry:
    """Get the global unified service registry.

    Returns:
        The singleton UnifiedServiceRegistry instance
    """
    return _unified_registry


def reset_unified_registry() -> None:
    """Reset the unified registry (primarily for testing).

    This clears all registered services and resets the loaded state.
    """
    global _unified_registry
    UnifiedServiceRegistry._instance = None
    _unified_registry = UnifiedServiceRegistry()
