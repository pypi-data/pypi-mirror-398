"""Service descriptor for unified service registration.

This module provides the ServiceDescriptor dataclass which captures ALL
metadata needed to register, configure, and discover MCP services.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Awaitable, Literal

if TYPE_CHECKING:
    from fastmcp import FastMCP


@dataclass
class ServiceURLs:
    """Environment-specific URLs for a service.

    Attributes:
        dev: URL for development environment (typically localhost)
        prd: URL for production environment (remote deployment)
    """

    dev: str
    prd: str

    def get(self, mode: str) -> str:
        """Get URL for the specified mode.

        Args:
            mode: Environment mode ('dev' or 'prd')

        Returns:
            URL for the specified mode

        Raises:
            ValueError: If mode is not 'dev' or 'prd'
        """
        if mode == "dev":
            return self.dev
        elif mode == "prd":
            return self.prd
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'dev' or 'prd'")


@dataclass
class ServiceDescriptor:
    """Complete metadata for a service - single source of truth.

    This dataclass captures ALL information needed to:
    - Create the MCP server (factory function)
    - Generate CLI choices (name, description)
    - Build scope registry (catalog/tool mappings)
    - Configure HTTP client (URLs, API key env vars)
    - Filter tools for HTTP mode (catalog reference)

    Attributes:
        name: Unique service identifier (e.g., "auth", "reg", "risk")
        description: Human-readable description for CLI help
        factory: Async function that creates FastMCP instance
        urls: Environment-specific base URLs
        openapi_path: Path to OpenAPI/Swagger spec
        api_key_env: Environment variable name for API key (fallback)
        gateway_prefix: Prefix for gateway tools (default: name)
        tags: Tags for categorization (e.g., ["core"], ["experimental"])
        catalog_mode: "spec-driven" (auto from OpenAPI) or "explicit" (manual catalog)
        overrides_module: Module path for tier/risk overrides (spec-driven mode)
        catalog_module: Module path for explicit catalog (explicit mode)
        catalog_attr: Attribute name for catalog in module (default: {NAME}_CATALOG)

    Example (spec-driven mode):
        >>> descriptor = ServiceDescriptor(
        ...     name="risk",
        ...     description="Risk service MCP server",
        ...     factory=create_risk_server,
        ...     urls=ServiceURLs(dev="http://localhost:5012", prd="https://risk.ops.yirifi.ai"),
        ...     overrides_module="yirifi_mcp.catalog.overrides.risk",
        ... )

    Example (explicit catalog mode):
        >>> descriptor = ServiceDescriptor(
        ...     name="auth",
        ...     description="Auth service MCP server",
        ...     factory=create_auth_server,
        ...     urls=ServiceURLs(dev="http://localhost:5100", prd="https://auth.ops.yirifi.ai"),
        ...     catalog_mode="explicit",
        ...     catalog_module="yirifi_mcp.catalog.auth_service",
        ... )
    """

    name: str
    description: str
    factory: Callable[..., Awaitable["FastMCP"]]
    urls: ServiceURLs
    openapi_path: str = "/api/v1/swagger.json"
    api_key_env: str | None = None  # Falls back to YIRIFI_API_KEY
    gateway_prefix: str | None = None  # Defaults to name
    tags: list[str] = field(default_factory=list)
    catalog_mode: Literal["spec-driven", "explicit"] = "spec-driven"
    overrides_module: str | None = None  # e.g., "yirifi_mcp.catalog.overrides.risk"
    catalog_module: str | None = None  # e.g., "yirifi_mcp.catalog.risk_service"
    catalog_attr: str | None = None  # e.g., "RISK_CATALOG" (defaults to {NAME}_CATALOG)

    def __post_init__(self):
        """Set default values for optional fields."""
        if self.gateway_prefix is None:
            self.gateway_prefix = self.name
        if self.api_key_env is None:
            self.api_key_env = f"{self.name.upper()}_SERVICE_API_KEY"
        if self.catalog_attr is None:
            self.catalog_attr = f"{self.name.upper()}_CATALOG"

    def get_base_url(self, mode: str) -> str:
        """Get base URL for the specified mode.

        Args:
            mode: Environment mode ('dev' or 'prd')

        Returns:
            Base URL for the service
        """
        return self.urls.get(mode)

    def get_api_key(self) -> str:
        """Get API key from environment.

        Tries unified YIRIFI_API_KEY first, then service-specific.

        Returns:
            API key string (empty if not found)
        """
        import os

        # Try unified key first
        key = os.environ.get("YIRIFI_API_KEY", "")
        if key:
            return key

        # Try service-specific key
        if self.api_key_env:
            key = os.environ.get(self.api_key_env, "")

        return key
