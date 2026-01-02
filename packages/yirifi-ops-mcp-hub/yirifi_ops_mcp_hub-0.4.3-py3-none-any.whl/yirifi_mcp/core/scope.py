"""Service scope registry for URL-based tool filtering.

Provides automatic tool→service mapping derived from ServiceCatalog definitions.
This enables path-based filtering in HTTP mode: /mcp/auth, /mcp/reg, etc.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field

from yirifi_mcp.catalog.base import ServiceCatalog, Tier

# ContextVar to store allowed tools for current request scope
# None means all tools allowed (no scope restriction)
current_scope_tools: ContextVar[set[str] | None] = ContextVar(
    "current_scope_tools", default=None
)


def get_current_scope_tools() -> set[str] | None:
    """Get allowed tools for current request context.

    Returns:
        Set of allowed tool names, or None if all tools are allowed.
    """
    return current_scope_tools.get()


def set_current_scope_tools(tools: set[str] | None) -> object:
    """Set allowed tools for current request context.

    Args:
        tools: Set of allowed tool names, or None to allow all.

    Returns:
        Token that can be used to reset the ContextVar.
    """
    return current_scope_tools.set(tools)


@dataclass
class ServiceScope:
    """Defines the tool scope for a service.

    Attributes:
        name: Service identifier (e.g., 'auth', 'reg')
        tools: Set of tool names that belong to this service
    """

    name: str
    tools: set[str] = field(default_factory=set)


class ScopeRegistry:
    """Registry that maps tools to services for URL-based filtering.

    The registry is built from ServiceCatalog definitions, ensuring a single
    source of truth. Gateway tools (e.g., auth_api_call, auth_api_catalog)
    are automatically included.

    Example:
        >>> registry = ScopeRegistry()
        >>> registry.register_service("auth", AUTH_CATALOG)
        >>> registry.get_tools_for_scope(["auth"])
        {'get_user_list', 'auth_api_call', 'auth_api_catalog', ...}
    """

    # Gateway tool suffixes that are added for each service
    GATEWAY_TOOL_SUFFIXES = ["_api_call", "_api_catalog", "_health", "_api_call_batch"]

    def __init__(self):
        self._services: dict[str, ServiceScope] = {}
        self._tool_to_service: dict[str, str] = {}

    def register_service(self, name: str, catalog: ServiceCatalog) -> None:
        """Register a service with its catalog.

        Args:
            name: Service identifier (e.g., 'auth', 'reg')
            catalog: ServiceCatalog defining endpoints for this service
        """
        tools = set()

        # Add direct and gateway tools from catalog
        for endpoint in catalog.get_all_endpoints():
            if endpoint.tier != Tier.EXCLUDE:
                tools.add(endpoint.name)

        # Add gateway tools (prefixed with service name)
        for suffix in self.GATEWAY_TOOL_SUFFIXES:
            tools.add(f"{name}{suffix}")

        scope = ServiceScope(name=name, tools=tools)
        self._services[name] = scope

        # Build reverse mapping
        for tool in tools:
            self._tool_to_service[tool] = name

    def get_tools_for_scope(self, services: list[str]) -> set[str]:
        """Get all tools for the specified service scope.

        Args:
            services: List of service names to include

        Returns:
            Set of tool names from all specified services
        """
        result = set()
        for service in services:
            if service in self._services:
                result.update(self._services[service].tools)
        return result

    def get_all_tools(self) -> set[str]:
        """Get all registered tools across all services."""
        return set(self._tool_to_service.keys())

    def get_service_for_tool(self, tool_name: str) -> str | None:
        """Get the service that owns a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Service name or None if not found
        """
        return self._tool_to_service.get(tool_name)

    def get_registered_services(self) -> list[str]:
        """Get list of all registered service names."""
        return list(self._services.keys())

    def __contains__(self, service: str) -> bool:
        return service in self._services

    def __repr__(self) -> str:
        services = ", ".join(self._services.keys())
        return f"ScopeRegistry(services=[{services}], tools={len(self._tool_to_service)})"


def build_default_registry() -> ScopeRegistry:
    """Build registry with all discovered services.

    Uses UnifiedServiceRegistry instead of hardcoded imports.
    For services with explicit catalogs, registers them directly.
    For spec-driven services, attempts to import catalog if available.

    Returns:
        ScopeRegistry populated with catalogs from unified registry
    """
    from yirifi_mcp.core.unified_registry import get_unified_registry

    unified = get_unified_registry()
    unified.discover()

    # Try unified registry first
    try:
        return unified.build_scope_registry()
    except Exception:
        pass

    # Fallback to hardcoded imports for backward compatibility
    # This ensures the system works even if services aren't registered via entry points yet
    registry = ScopeRegistry()

    try:
        from yirifi_mcp.catalog.auth_service import AUTH_CATALOG
        registry.register_service("auth", AUTH_CATALOG)
    except ImportError:
        pass

    try:
        from yirifi_mcp.catalog.reg_service import REG_CATALOG
        registry.register_service("reg", REG_CATALOG)
    except ImportError:
        pass

    try:
        from yirifi_mcp.catalog.risk_service import RISK_CATALOG
        registry.register_service("risk", RISK_CATALOG)
    except ImportError:
        pass

    return registry


# Global singleton for convenience
_default_registry: ScopeRegistry | None = None


def get_default_registry() -> ScopeRegistry:
    """Get the default scope registry (singleton)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = build_default_registry()
    return _default_registry
