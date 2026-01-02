"""Enhanced decorators for service registration.

This module provides the enhanced @register_service decorator which captures
ALL service metadata in a single registration point.
"""

from functools import wraps
from typing import Callable, Awaitable, Literal, overload

from fastmcp import FastMCP

from .service_descriptor import ServiceDescriptor, ServiceURLs
from .unified_registry import get_unified_registry


def register_service(
    name: str,
    *,
    description: str = "",
    urls: dict[str, str] | ServiceURLs | None = None,
    openapi_path: str = "/api/v1/swagger.json",
    api_key_env: str | None = None,
    gateway_prefix: str | None = None,
    tags: list[str] | None = None,
    catalog_mode: Literal["spec-driven", "explicit"] = "spec-driven",
    overrides_module: str | None = None,
    catalog_module: str | None = None,
    catalog_attr: str | None = None,
):
    """Decorator to register a service with full metadata.

    This is the SINGLE registration point for a service. The decorated
    factory function and all metadata are captured in a ServiceDescriptor
    and registered with the UnifiedServiceRegistry.

    Example (spec-driven mode - recommended for new services):
        >>> @register_service(
        ...     "risk",
        ...     description="Risk service MCP server",
        ...     urls={"dev": "http://localhost:5012", "prd": "https://risk.ops.yirifi.ai"},
        ...     tags=["core", "risk"],
        ...     overrides_module="yirifi_mcp.catalog.overrides.risk",
        ... )
        ... async def create_risk_server(config=None):
        ...     # Factory implementation
        ...     pass

    Example (explicit catalog mode - for services without OpenAPI x-mcp extensions):
        >>> @register_service(
        ...     "auth",
        ...     description="Auth service MCP server",
        ...     urls={"dev": "http://localhost:5100", "prd": "https://auth.ops.yirifi.ai"},
        ...     catalog_mode="explicit",
        ...     catalog_module="yirifi_mcp.catalog.auth_service",
        ... )
        ... async def create_auth_server(config=None):
        ...     pass

    Args:
        name: Unique service identifier (e.g., "auth", "reg", "risk")
        description: Human-readable description for CLI help text
        urls: Dict with 'dev' and 'prd' keys, or ServiceURLs instance.
              If None, defaults are inferred from service name.
        openapi_path: Path to OpenAPI/Swagger spec (default: /api/v1/swagger.json)
        api_key_env: Environment variable name for service-specific API key.
                     Falls back to YIRIFI_API_KEY if not set.
        gateway_prefix: Prefix for gateway tools (default: service name)
        tags: Categorization tags (e.g., ["core", "experimental"])
        catalog_mode: "spec-driven" (auto from OpenAPI) or "explicit" (manual catalog)
        overrides_module: Module path for tier/risk overrides (spec-driven mode)
                          e.g., "yirifi_mcp.catalog.overrides.risk"
        catalog_module: Module path for explicit catalog (explicit mode)
                        e.g., "yirifi_mcp.catalog.auth_service"
        catalog_attr: Attribute name for catalog in module (default: {NAME}_CATALOG)

    Returns:
        Decorator function that wraps the service factory
    """

    def decorator(factory: Callable[..., Awaitable[FastMCP]]):
        # Convert urls dict to ServiceURLs if needed
        if isinstance(urls, dict):
            service_urls = ServiceURLs(dev=urls["dev"], prd=urls["prd"])
        elif urls is None:
            # Infer default URLs from name
            service_urls = ServiceURLs(
                dev=f"http://localhost:5000",
                prd=f"https://{name}.ops.yirifi.ai",
            )
        else:
            service_urls = urls

        # Create descriptor with full metadata
        descriptor = ServiceDescriptor(
            name=name,
            description=description or f"{name.title()} service MCP server",
            factory=factory,
            urls=service_urls,
            openapi_path=openapi_path,
            api_key_env=api_key_env,
            gateway_prefix=gateway_prefix,
            tags=tags or [],
            catalog_mode=catalog_mode,
            overrides_module=overrides_module,
            catalog_module=catalog_module,
            catalog_attr=catalog_attr,
        )

        # Register with global registry
        get_unified_registry().register(descriptor)

        @wraps(factory)
        async def wrapper(*args, **kwargs):
            return await factory(*args, **kwargs)

        # Attach descriptor for introspection
        wrapper._service_descriptor = descriptor

        return wrapper

    return decorator


# Backward compatibility alias
# This allows existing code using the old registry.register_service to work
def legacy_register_service(
    name: str,
    *,
    description: str = "",
    tags: list[str] | None = None,
):
    """Legacy decorator for backward compatibility.

    This provides the same interface as the old @register_service from
    server/registry.py but internally uses the unified registry.

    Note: This decorator captures less metadata than the enhanced version.
    New services should use the full @register_service decorator.
    """

    def decorator(factory: Callable[..., Awaitable[FastMCP]]):
        # Create descriptor with minimal metadata (legacy mode)
        # URLs will need to be inferred or looked up elsewhere
        descriptor = ServiceDescriptor(
            name=name,
            description=description or f"{name.title()} service MCP server",
            factory=factory,
            urls=ServiceURLs(
                dev=f"http://localhost:5000",
                prd=f"https://{name}.ops.yirifi.ai",
            ),
            tags=tags or [],
            # Mark as explicit since we don't have overrides info
            catalog_mode="explicit",
        )

        get_unified_registry().register(descriptor)

        @wraps(factory)
        async def wrapper(*args, **kwargs):
            return await factory(*args, **kwargs)

        wrapper._service_descriptor = descriptor
        return wrapper

    return decorator
