"""Base classes for unified service catalogs.

This module provides the core abstractions for defining API endpoint catalogs:

- Tier: Exposure level enum (DIRECT, GATEWAY, EXCLUDE)
- Endpoint: Single endpoint definition dataclass
- BaseCatalog: Protocol/interface for all catalog implementations
- ServiceCatalog: Concrete catalog with explicit endpoint definitions

For auto-discovery from OpenAPI specs, see SpecDrivenCatalog in spec_driven.py.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from yirifi_mcp.core.route_filters import RouteMap


@runtime_checkable
class BaseCatalog(Protocol):
    """Protocol defining the interface for all catalog implementations.

    This protocol allows both ServiceCatalog (explicit definitions) and
    SpecDrivenCatalog (auto-discovery) to be used interchangeably.

    All catalog implementations must provide:
    - Endpoint queries (get_direct_endpoints, get_gateway_endpoints, etc.)
    - Route map generation (to_route_maps)
    - Gateway catalog generation (to_gateway_catalog)
    - Statistics (get_stats, direct_count, gateway_count)
    """

    def get_direct_endpoints(self) -> list["Endpoint"]:
        """Get endpoints exposed as direct MCP tools."""
        ...

    def get_gateway_endpoints(self) -> list["Endpoint"]:
        """Get endpoints accessible via gateway only."""
        ...

    def get_all_endpoints(self) -> list["Endpoint"]:
        """Get all endpoints (excluding EXCLUDE tier)."""
        ...

    def get_endpoint(self, name: str) -> "Endpoint | None":
        """Look up an endpoint by name."""
        ...

    def to_route_maps(self) -> list["RouteMap"]:
        """Generate RouteMap list for OpenAPI filtering."""
        ...

    def to_gateway_catalog(self) -> dict[str, dict]:
        """Generate runtime catalog dict for gateway tool."""
        ...

    def get_stats(self) -> dict[str, int]:
        """Get statistics about the catalog."""
        ...

    @property
    def direct_count(self) -> int:
        """Number of direct tool endpoints."""
        ...

    @property
    def gateway_count(self) -> int:
        """Number of gateway-only endpoints."""
        ...


class Tier(Enum):
    """Exposure tier for endpoints.

    DIRECT: Exposed as individual MCP tool (frequent, safe operations)
    GATEWAY: Only via gateway tool (admin, dangerous, infrequent)
    EXCLUDE: Never exposed via MCP
    """

    DIRECT = "direct"
    GATEWAY = "gateway"
    EXCLUDE = "exclude"


@dataclass
class Endpoint:
    """Single endpoint definition - the source of truth.

    This dataclass defines an API endpoint with all metadata needed
    to generate both RouteMap entries (for OpenAPI filtering) and
    API_CATALOG entries (for gateway tool).

    Attributes:
        name: Unique action name matching OpenAPI operationId
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        path: URL path pattern with placeholders (e.g., "/users/{user_id}")
        description: Short description for MCP tool/catalog
        tier: Exposure level (DIRECT, GATEWAY, or EXCLUDE)
        tags: OpenAPI tags for grouping
        risk_level: Risk assessment (low, medium, high) for gateway ops
        idempotent: Whether operation can be safely retried (None = auto-detect)
    """

    name: str
    method: str
    path: str
    description: str
    tier: Tier
    tags: list[str] = field(default_factory=list)
    risk_level: str = "low"
    idempotent: bool | None = None

    def __post_init__(self):
        """Validate endpoint definition and set defaults."""
        self.method = self.method.upper()
        if self.method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
            raise ValueError(f"Invalid HTTP method: {self.method}")
        if self.risk_level not in ("low", "medium", "high"):
            raise ValueError(f"Invalid risk level: {self.risk_level}")

        # Auto-detect idempotency from HTTP method if not specified
        # GET, PUT, DELETE are idempotent by HTTP spec
        # POST, PATCH are NOT idempotent by default
        if self.idempotent is None:
            self.idempotent = self.method in ("GET", "PUT", "DELETE")

    @property
    def is_retryable(self) -> bool:
        """Whether this endpoint can be safely retried."""
        return self.idempotent is True


class ServiceCatalog:
    """Unified service catalog with route map and gateway catalog generation.

    A catalog is a collection of endpoints that define all available
    operations for a service. It provides methods to:
    - Query endpoints by tier
    - Generate RouteMap entries for OpenAPI filtering
    - Generate gateway catalog for dynamic API access

    Example:
        >>> catalog = ServiceCatalog([
        ...     Endpoint("get_user_list", "GET", "/users/", "List users", Tier.DIRECT),
        ...     Endpoint("delete_user_detail", "DELETE", "/users/{id}", "Delete", Tier.GATEWAY),
        ... ])
        >>> route_maps = catalog.to_route_maps()
        >>> gateway_catalog = catalog.to_gateway_catalog()
    """

    def __init__(self, endpoints: list[Endpoint]):
        """Initialize catalog with endpoint definitions.

        Args:
            endpoints: List of Endpoint definitions
        """
        self._endpoints = endpoints
        self._by_name = {e.name: e for e in endpoints}
        self._validate()

    def _validate(self) -> None:
        """Validate catalog for duplicate names."""
        names = [e.name for e in self._endpoints]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            raise ValueError(f"Duplicate endpoint names: {set(duplicates)}")

    # -------------------------------------------------------------------------
    # Endpoint queries
    # -------------------------------------------------------------------------

    def get_direct_endpoints(self) -> list[Endpoint]:
        """Get endpoints exposed as direct MCP tools."""
        return [e for e in self._endpoints if e.tier == Tier.DIRECT]

    def get_gateway_endpoints(self) -> list[Endpoint]:
        """Get endpoints accessible via gateway only."""
        return [e for e in self._endpoints if e.tier == Tier.GATEWAY]

    def get_all_endpoints(self) -> list[Endpoint]:
        """Get all endpoints (excluding EXCLUDE tier)."""
        return [e for e in self._endpoints if e.tier != Tier.EXCLUDE]

    def get_endpoint(self, name: str) -> Endpoint | None:
        """Look up an endpoint by name."""
        return self._by_name.get(name)

    # -------------------------------------------------------------------------
    # Route map generation (for OpenAPI filtering)
    # -------------------------------------------------------------------------

    def to_route_maps(self) -> list["RouteMap"]:
        """Generate RouteMap list for OpenAPI filtering.

        Creates RouteMap entries for each DIRECT endpoint, plus
        a catch-all exclusion rule at the end.

        Returns:
            List of RouteMap configurations for filter_openapi_paths()
        """
        from yirifi_mcp.core.route_filters import MCPType, RouteMap

        route_maps = []

        for endpoint in self.get_direct_endpoints():
            pattern = self._path_to_pattern(endpoint.path)
            route_maps.append(
                RouteMap(
                    pattern=pattern,
                    methods=[endpoint.method],
                    mcp_type=MCPType.TOOL,
                )
            )

        # Add catch-all exclusion (MUST be last - first match wins)
        route_maps.append(RouteMap(pattern=r".*", mcp_type=MCPType.EXCLUDE))

        return route_maps

    @staticmethod
    def _path_to_pattern(path: str) -> str:
        """Convert URL path pattern to regex for RouteMap.

        Examples:
            /users/ -> ^/users/$
            /users/{user_id} -> ^/users/[^/]+$
            /users/{user_id}/access -> ^/users/[^/]+/access$
        """
        pattern = re.sub(r"\{[^}]+\}", "[^/]+", path)
        return f"^{pattern}$"

    # -------------------------------------------------------------------------
    # Gateway catalog generation
    # -------------------------------------------------------------------------

    def to_gateway_catalog(self) -> dict[str, dict]:
        """Generate runtime catalog dict for gateway tool.

        Returns all non-excluded endpoints in the format expected
        by DynamicGateway.

        Returns:
            Dict mapping action names to endpoint info:
            {"action_name": {"method": "GET", "path": "/...", "desc": "...", "risk_level": "...", "idempotent": bool}}
        """
        return {
            e.name: {
                "method": e.method,
                "path": e.path,
                "desc": e.description,
                "risk_level": e.risk_level,
                "idempotent": e.idempotent,
            }
            for e in self.get_all_endpoints()
        }

    def to_api_catalog(self) -> dict[str, dict]:
        """Generate API catalog for backward compatibility.

        Alias for to_gateway_catalog() - same format used by gateway tools.
        """
        return self.to_gateway_catalog()

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> dict[str, int]:
        """Get statistics about the catalog.

        Returns:
            Dict with counts by tier and risk level
        """
        gateway_endpoints = self.get_gateway_endpoints()
        return {
            "total": len(self._endpoints),
            "direct": self.direct_count,
            "gateway": self.gateway_count,
            "excluded": len(self._endpoints) - len(self.get_all_endpoints()),
            "high_risk": sum(1 for e in gateway_endpoints if e.risk_level == "high"),
            "medium_risk": sum(1 for e in gateway_endpoints if e.risk_level == "medium"),
            "low_risk": sum(1 for e in gateway_endpoints if e.risk_level == "low"),
        }

    @property
    def direct_count(self) -> int:
        """Number of direct tool endpoints."""
        return len(self.get_direct_endpoints())

    @property
    def gateway_count(self) -> int:
        """Number of gateway-only endpoints."""
        return len(self.get_gateway_endpoints())

    def __len__(self) -> int:
        """Total number of endpoints (all tiers)."""
        return len(self._endpoints)

    def __repr__(self) -> str:
        return f"ServiceCatalog(direct={self.direct_count}, gateway={self.gateway_count})"
