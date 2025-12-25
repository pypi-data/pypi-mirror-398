"""Route filtering utilities for MCP server generation."""

from dataclasses import dataclass
from enum import Enum
import re


class MCPType(Enum):
    """MCP component types for route mapping."""

    TOOL = "tool"
    RESOURCE = "resource"
    EXCLUDE = "exclude"


@dataclass
class RouteMap:
    """
    Route mapping configuration for OpenAPI to MCP conversion.

    Attributes:
        pattern: Regex pattern to match route paths
        methods: HTTP methods to match (None matches all)
        mcp_type: Target MCP component type
        tags: OpenAPI tags to match (None matches all)
    """

    pattern: str
    mcp_type: MCPType = MCPType.TOOL
    methods: list[str] | None = None
    tags: list[str] | None = None

    def matches(self, path: str, method: str = None, route_tags: list[str] = None) -> bool:
        """Check if this route map matches the given path/method/tags."""
        # Check pattern
        if not re.match(self.pattern, path):
            return False

        # Check method if specified
        if self.methods and method:
            if method.upper() not in [m.upper() for m in self.methods]:
                return False

        # Check tags if specified
        if self.tags and route_tags:
            if not any(tag in self.tags for tag in route_tags):
                return False

        return True


def exclude_health_checks() -> RouteMap:
    """Exclude health check endpoints from MCP tools."""
    return RouteMap(
        pattern=r".*/health(/.*)?$",
        mcp_type=MCPType.EXCLUDE,
    )


def exclude_docs() -> RouteMap:
    """Exclude documentation endpoints."""
    return RouteMap(
        pattern=r".*/docs.*",
        mcp_type=MCPType.EXCLUDE,
    )


def exclude_swagger() -> RouteMap:
    """Exclude swagger endpoints."""
    return RouteMap(
        pattern=r".*/swagger.*",
        mcp_type=MCPType.EXCLUDE,
    )


def exclude_by_patterns(patterns: list[str]) -> list[RouteMap]:
    """Create exclusion RouteMaps for multiple patterns."""
    return [RouteMap(pattern=pattern, mcp_type=MCPType.EXCLUDE) for pattern in patterns]


# Common route map presets used across all services
STANDARD_EXCLUSIONS = [
    exclude_health_checks(),
    exclude_docs(),
    exclude_swagger(),
]


def should_exclude_route(
    path: str,
    method: str,
    route_maps: list[RouteMap],
    tags: list[str] = None,
) -> bool:
    """
    Check if a route should be excluded based on route maps.

    Args:
        path: API endpoint path
        method: HTTP method
        route_maps: List of RouteMap configurations
        tags: OpenAPI tags for the route

    Returns:
        True if the route should be excluded
    """
    for route_map in route_maps:
        if route_map.matches(path, method, tags):
            if route_map.mcp_type == MCPType.EXCLUDE:
                return True
    return False


def get_route_mcp_type(
    path: str,
    method: str,
    route_maps: list[RouteMap],
    tags: list[str] = None,
) -> MCPType | None:
    """
    Get the MCP type for a route based on route maps.

    First matching route map wins (order matters!).

    Args:
        path: API endpoint path
        method: HTTP method
        route_maps: List of RouteMap configurations (first match wins)
        tags: OpenAPI tags for the route

    Returns:
        MCPType if matched, None if no match
    """
    for route_map in route_maps:
        if route_map.matches(path, method, tags):
            return route_map.mcp_type
    return None


def filter_openapi_paths(spec: dict, route_maps: list[RouteMap]) -> dict:
    """
    Filter OpenAPI spec paths based on route maps.

    Uses first-match-wins semantics:
    - Routes matching a TOOL pattern are included
    - Routes matching an EXCLUDE pattern are excluded
    - Routes matching no pattern are excluded (conservative default)

    Args:
        spec: OpenAPI specification dict
        route_maps: List of RouteMap configurations

    Returns:
        Filtered OpenAPI specification
    """
    filtered_paths = {}
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        filtered_methods = {}
        for method, details in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue

            tags = details.get("tags", [])
            mcp_type = get_route_mcp_type(path, method, route_maps, tags)

            # Include only if explicitly matched as TOOL
            if mcp_type == MCPType.TOOL:
                filtered_methods[method] = details

        if filtered_methods:
            filtered_paths[path] = filtered_methods

    spec = spec.copy()
    spec["paths"] = filtered_paths
    return spec
