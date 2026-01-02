"""Generic MCP server factory for any service catalog.

This module provides MCPServerFactory which builds FastMCP servers from
ServiceCatalog definitions. It handles:

- OpenAPI spec fetching and filtering
- HTTP client creation with authentication
- Direct tool registration from OpenAPI
- Gateway tools for dynamic API access
- Health check tool for monitoring
- Batch operations tool
- Resource lifecycle management

Supports two catalog modes:
1. Explicit catalog (legacy): Pass a ServiceCatalog with all endpoints defined
2. Spec-driven (new): Pass tier/risk overrides, catalog is built from OpenAPI spec
"""

from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import AsyncIterator, Callable, Type

import httpx
import structlog
from fastmcp import FastMCP

from yirifi_mcp.catalog.base import BaseCatalog, ServiceCatalog, Tier
from yirifi_mcp.catalog.policy import CatalogPolicy, PolicyViolationError, validate_catalog
from yirifi_mcp.catalog.spec_driven import SpecDrivenCatalog
from yirifi_mcp.core.config import ServiceConfig
from yirifi_mcp.core.exceptions import (
    ActionNotFoundError,
    GatewayError,
    MissingPathParamError,
    UpstreamError,
)
from yirifi_mcp.core.environment_middleware import EnvironmentMiddleware
from yirifi_mcp.core.http_client import create_passthrough_client
from yirifi_mcp.core.observability import metrics
from yirifi_mcp.core.openapi_utils import (
    fetch_openapi_spec,
    get_spec_info,
    patch_openapi_spec,
)
from yirifi_mcp.core.resilience import ResilienceConfig
from yirifi_mcp.core.route_filters import filter_openapi_paths
from yirifi_mcp.core.tool_optimizer import optimize_component_descriptions
from yirifi_mcp.gateway.base import BaseGateway
from yirifi_mcp.gateway.dynamic import BatchCallItem, DynamicGateway

logger = structlog.get_logger()

# Type aliases for dependency injection
ClientFactory = Callable[[str, float, float, str], httpx.AsyncClient]


class MCPServerFactory:
    """Generic factory for creating MCP servers from any ServiceCatalog.

    This factory encapsulates the common logic for building MCP servers:
    - Fetching and filtering OpenAPI specs
    - Creating HTTP clients with authentication
    - Registering direct tools from OpenAPI
    - Adding gateway tools for dynamic API access
    - Health check and batch operation tools
    - Managing resource lifecycle

    Supports two catalog modes:
    1. Explicit catalog (legacy): Pass a ServiceCatalog with all endpoints defined
    2. Spec-driven (new): Pass tier/risk overrides, catalog is built from OpenAPI spec

    Supports dependency injection for testing:
    - client_factory: Custom HTTP client creation
    - gateway_class: Custom gateway implementation

    Example (explicit catalog):
        >>> from yirifi_mcp.catalog.auth_service import AUTH_CATALOG
        >>> from yirifi_mcp.core.config import AuthServiceConfig
        >>>
        >>> factory = MCPServerFactory(AUTH_CATALOG, AuthServiceConfig())
        >>> mcp = await factory.build()
        >>> mcp.run()

    Example (spec-driven):
        >>> from yirifi_mcp.catalog.overrides.auth import (
        ...     DIRECT_ENDPOINTS, RISK_OVERRIDES, EXCLUDE_PATTERNS
        ... )
        >>> factory = MCPServerFactory(
        ...     config=AuthServiceConfig(),
        ...     gateway_prefix="auth",
        ...     tier_overrides={ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS},
        ...     risk_overrides=RISK_OVERRIDES,
        ...     exclude_patterns=EXCLUDE_PATTERNS,
        ... )
        >>> mcp = await factory.build()
    """

    def __init__(
        self,
        catalog: BaseCatalog | None = None,
        config: ServiceConfig | None = None,
        *,
        gateway_prefix: str | None = None,
        client_factory: ClientFactory | None = None,
        gateway_class: Type[BaseGateway] | None = None,
        resilience_config: ResilienceConfig | None = None,
        # Spec-driven mode options
        tier_overrides: dict[str, Tier] | None = None,
        risk_overrides: dict[str, str] | None = None,
        name_overrides: dict[str, str] | None = None,
        description_overrides: dict[str, str] | None = None,
        idempotent_overrides: dict[str, bool] | None = None,
        exclude_patterns: list[str] | None = None,
        policy: CatalogPolicy | None = None,
    ):
        """Initialize the factory with a catalog and config.

        Args:
            catalog: ServiceCatalog defining available endpoints (optional in spec-driven mode)
            config: ServiceConfig with connection and server settings
            gateway_prefix: Optional prefix for gateway tool names (default: derived from server_name)
            client_factory: Custom HTTP client factory for testing (default: create_passthrough_client)
            gateway_class: Custom gateway class for testing (default: DynamicGateway)
            resilience_config: Optional resilience configuration (overrides config settings)

            Spec-driven mode options (used when catalog is None):
            tier_overrides: Map of operationId to Tier override
            risk_overrides: Map of operationId to risk level override
            name_overrides: Map of operationId to tool name override
            description_overrides: Map of operationId to description override
            idempotent_overrides: Map of operationId to idempotency override
            exclude_patterns: Regex patterns for paths to exclude entirely
            policy: Optional CatalogPolicy for validation (raises PolicyViolationError if violated)
        """
        if config is None:
            raise ValueError("config is required")

        self.catalog = catalog
        self.config = config
        self.gateway_prefix = gateway_prefix or self._derive_prefix(config.server_name)

        # Dependency injection
        self._client_factory = client_factory or create_passthrough_client
        self._gateway_class = gateway_class or DynamicGateway
        self._resilience_config = resilience_config

        # Spec-driven mode options
        self._tier_overrides = tier_overrides
        self._risk_overrides = risk_overrides
        self._name_overrides = name_overrides
        self._description_overrides = description_overrides
        self._idempotent_overrides = idempotent_overrides
        self._exclude_patterns = exclude_patterns
        self._policy = policy

        self._client: httpx.AsyncClient | None = None
        self._gateway: BaseGateway | None = None

    @staticmethod
    def _derive_prefix(server_name: str) -> str:
        """Derive gateway prefix from server name.

        Examples:
            yirifi-auth -> auth
            my-cool-service -> my_cool_service
        """
        # Remove common prefixes
        name = server_name.lower()
        for prefix in ("yirifi-", "mcp-", "service-"):
            if name.startswith(prefix):
                name = name[len(prefix) :]
                break
        # Replace hyphens with underscores
        return name.replace("-", "_")

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[FastMCP]:
        """Async context manager for resource lifecycle.

        Ensures HTTP client is properly closed when server exits.

        Yields:
            Configured FastMCP server instance
        """
        try:
            mcp = await self.build()
            yield mcp
        finally:
            if self._client:
                await self._client.aclose()
                self._client = None
                logger.debug("http_client_closed", server=self.config.server_name)

    async def build(self) -> FastMCP:
        """Build the MCP server instance.

        Returns:
            Configured FastMCP server with direct tools, gateway, health check, and batch

        Raises:
            PolicyViolationError: If catalog violates the configured policy
        """
        logger.info(
            "building_mcp_server",
            server_name=self.config.server_name,
            base_url=self.config.base_url,
            catalog_mode="explicit" if self.catalog else "spec-driven",
        )

        # Fetch and convert OpenAPI spec
        # Some services require auth even for swagger endpoint
        static_api_key = getattr(self.config, "api_key", None) or ""
        spec = await fetch_openapi_spec(
            base_url=self.config.base_url,
            openapi_path=self.config.openapi_path,
            api_key=static_api_key,
        )
        spec = patch_openapi_spec(spec, self.config.base_url)

        # Create catalog from spec if not provided (spec-driven mode)
        if self.catalog is None:
            logger.info(
                "creating_spec_driven_catalog",
                tier_overrides=len(self._tier_overrides or {}),
                risk_overrides=len(self._risk_overrides or {}),
                exclude_patterns=len(self._exclude_patterns or []),
            )
            self.catalog = SpecDrivenCatalog(
                spec=spec,
                tier_overrides=self._tier_overrides,
                risk_overrides=self._risk_overrides,
                name_overrides=self._name_overrides,
                description_overrides=self._description_overrides,
                idempotent_overrides=self._idempotent_overrides,
                exclude_patterns=self._exclude_patterns,
            )

        # Validate catalog against policy if provided
        if self._policy:
            violations = validate_catalog(self.catalog, self._policy)
            if violations:
                logger.error(
                    "catalog_policy_violation",
                    violation_count=len(violations),
                    violations=[str(v) for v in violations],
                )
                raise PolicyViolationError(violations)

        # Generate route maps from catalog and filter spec
        route_maps = self.catalog.to_route_maps()
        filtered_spec = filter_openapi_paths(spec, route_maps)
        spec_info = get_spec_info(filtered_spec)

        logger.info(
            "spec_filtered",
            server=self.config.server_name,
            endpoints=spec_info["endpoints_count"],
            direct_tools=self.catalog.direct_count,
            gateway_actions=self.catalog.gateway_count,
        )

        # Get base URL from spec (may include /api/v1 prefix)
        api_base_url = filtered_spec.get("servers", [{}])[0].get(
            "url", self.config.base_url
        )

        # Create HTTP client with passthrough authentication
        # The client uses PassthroughAuth to inject X-API-Key from context variable
        # For STDIO transport, static_api_key is used as fallback
        static_api_key = getattr(self.config, "api_key", None) or ""
        self._client = self._client_factory(
            api_base_url,
            self.config.request_timeout,
            self.config.connect_timeout,
            static_api_key,
        )

        # Create MCP server from filtered OpenAPI spec
        mcp = FastMCP.from_openapi(
            openapi_spec=filtered_spec,
            client=self._client,
            name=self.config.server_name,
            mcp_component_fn=optimize_component_descriptions,
        )

        # Add environment middleware to wrap all tool responses
        # This ensures AI agents always know which database (DEV/UAT/PRD) they're operating against
        mcp.add_middleware(EnvironmentMiddleware(self.config))

        # Create gateway with resilience
        resilience_config = self._resilience_config
        if resilience_config is None:
            resilience_config = self.config.get_resilience_config()

        self._gateway = self._gateway_class(
            self._client,
            self.catalog,
            config=self.config,
            resilience_config=resilience_config,
        )

        # Register all tools
        self._register_gateway_tools(mcp)
        self._register_health_tool(mcp)
        self._register_batch_tool(mcp)

        # Log final stats
        stats = self.catalog.get_stats()
        logger.info(
            "mcp_server_built",
            server_name=self.config.server_name,
            direct_tools=stats["direct"],
            gateway_actions=stats["gateway"],
            high_risk_actions=stats["high_risk"],
            resilience_enabled=self.config.resilience_enabled,
        )

        return mcp

    def _register_gateway_tools(self, mcp: FastMCP) -> None:
        """Register gateway tools on the MCP server.

        Creates two tools:
        - {prefix}_api_catalog: Lists available actions
        - {prefix}_api_call: Executes any action dynamically

        Args:
            mcp: FastMCP server instance
        """
        gateway = self._gateway
        prefix = self.gateway_prefix

        # Create catalog tool
        # output_schema=None allows middleware to transform response to TOON
        @mcp.tool(name=f"{prefix}_api_catalog", output_schema=None)
        async def api_catalog() -> dict:
            f"""List all available {prefix} API actions.
            Use with {prefix}_api_call to execute any action.
            """
            return await gateway.catalog()

        # Create call tool
        # output_schema=None allows middleware to transform response to TOON
        @mcp.tool(name=f"{prefix}_api_call", output_schema=None)
        async def api_call(
            action: str,
            path_params: dict | None = None,
            query_params: dict | None = None,
            body: dict | None = None,
        ) -> dict:
            f"""Execute any {prefix} API action dynamically.

            Args:
                action: Action name from {prefix}_api_catalog (e.g., "get_user_list", "delete_role_detail")
                path_params: URL path parameters (e.g., {{"user_id": 1}})
                query_params: Query string parameters
                body: Request body for POST/PUT/PATCH

            Returns:
                API response as dict
            """
            try:
                return await gateway.call(action, path_params, query_params, body)
            except ActionNotFoundError as e:
                return {
                    "error": str(e),
                    "available_actions": e.available[:20],
                }
            except MissingPathParamError as e:
                return {
                    "error": str(e),
                    "required_params": e.params,
                    "path": e.path,
                }
            except UpstreamError as e:
                return {
                    "error": f"HTTP {e.status_code}",
                    "detail": e.detail,
                }
            except GatewayError as e:
                return {"error": str(e)}
            except Exception as e:
                logger.exception(
                    "gateway_error", action=action, server=self.config.server_name
                )
                return {"error": str(e)}

    def _register_health_tool(self, mcp: FastMCP) -> None:
        """Register health check tool for monitoring.

        The health tool provides:
        - Server status information
        - Upstream service connectivity check
        - Metrics statistics

        Args:
            mcp: FastMCP server instance
        """
        config = self.config
        client = self._client
        gateway = self._gateway
        prefix = self.gateway_prefix

        @mcp.tool(name=f"{prefix}_health", output_schema=None)
        async def health_check() -> dict:
            f"""Check {prefix} MCP server health and upstream connectivity.

            Returns:
                Health status including server info, upstream connectivity, and metrics
            """
            health = {
                "status": "healthy",
                "server": config.server_name,
                "mode": getattr(config, "mode", "unknown"),
                "base_url": config.base_url,
                "upstream": {"status": "unknown"},
                "resilience": {
                    "enabled": config.resilience_enabled,
                    "circuit_state": None,
                },
                "metrics": metrics.get_stats(),
            }

            # Add circuit breaker state if available
            if hasattr(gateway, "circuit_state") and gateway.circuit_state:
                health["resilience"]["circuit_state"] = gateway.circuit_state.value

            # Check upstream connectivity
            try:
                # Try to ping health endpoint
                response = await client.get("/health/live")
                health["upstream"] = {
                    "status": "connected" if response.status_code == 200 else "degraded",
                    "status_code": response.status_code,
                }
            except httpx.RequestError as e:
                health["status"] = "degraded"
                health["upstream"] = {
                    "status": "unreachable",
                    "error": str(e)[:100],
                }

            return health

    def _register_batch_tool(self, mcp: FastMCP) -> None:
        """Register batch operations tool.

        Allows executing multiple API calls in a single request,
        optionally concurrently.

        Args:
            mcp: FastMCP server instance
        """
        gateway = self._gateway
        prefix = self.gateway_prefix

        @mcp.tool(name=f"{prefix}_api_call_batch", output_schema=None)
        async def api_call_batch(
            calls: list[dict],
            concurrent: bool = True,
            max_concurrency: int = 5,
        ) -> dict:
            f"""Execute multiple {prefix} API calls in a batch.

            Args:
                calls: List of call specifications, each with:
                    - action: Action name from {prefix}_api_catalog
                    - path_params: URL path parameters (optional)
                    - query_params: Query parameters (optional)
                    - body: Request body (optional)
                    - id: Client correlation ID (optional)
                concurrent: Execute concurrently (default: true)
                max_concurrency: Max concurrent requests (default: 5)

            Returns:
                Batch results with success/failure for each call
            """
            # Convert dicts to BatchCallItem
            items = []
            for call_spec in calls:
                items.append(
                    BatchCallItem(
                        action=call_spec.get("action", ""),
                        path_params=call_spec.get("path_params"),
                        query_params=call_spec.get("query_params"),
                        body=call_spec.get("body"),
                        id=call_spec.get("id"),
                    )
                )

            # Execute batch
            results = await gateway.call_batch(
                items,
                concurrent=concurrent,
                max_concurrency=max_concurrency,
            )

            # Convert results to dicts
            return {
                "results": [asdict(r) for r in results],
                "total": len(results),
                "succeeded": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
            }

    @property
    def gateway(self) -> BaseGateway | None:
        """Access to the gateway instance for testing."""
        return self._gateway

    @property
    def client(self) -> httpx.AsyncClient | None:
        """Access to the HTTP client for testing."""
        return self._client
