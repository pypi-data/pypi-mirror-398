"""Reg service MCP catalog overrides.

This file defines the minimal configuration needed to expose reg API
endpoints as MCP tools. Only specify overrides - everything else is
derived from the OpenAPI spec.

Priority: x-mcp-* extensions in spec > these overrides > safe defaults

NAMING CONVENTION:
- Endpoint names match the OpenAPI operationId from the upstream service
- Pattern: {method}_{resource}_{action} e.g., get_country_list, post_source_list

Tier Guidelines:
- DIRECT: Frequent, safe operations that benefit from individual MCP tools
- GATEWAY (default): Admin/dangerous operations that should require explicit naming
- EXCLUDE: Never expose via MCP (health checks, internal endpoints)

Risk Level (for observability and rate limiting):
- low: Read-only admin operations (audit logs, listing)
- medium (default): Operations that modify non-critical data
- high: Destructive or security-sensitive operations
"""

from yirifi_mcp.catalog.base import Tier

# =============================================================================
# TIER OVERRIDES - The main value-add
# Default: GATEWAY (safe - requires explicit action naming)
# Only list endpoints to PROMOTE to DIRECT tier
# =============================================================================

DIRECT_ENDPOINTS: list[str] = [
    # Countries - read operations
    "get_country_list",
    "get_country_resource",
    "get_country_by_code",
    # Organizations - read operations
    "get_organization_list",
    "get_organization_resource",
    # Sources - read operations
    "get_source_list",
    "get_source_resource",
    # Source Types - read operations
    "get_source_type_list",
    "get_source_type_resource",
]

# Endpoints to exclude entirely (health checks, docs)
EXCLUDE_PATTERNS: list[str] = [
    r"^/health/.*",
    r"^/api/v1/docs.*",
    r"^/swagger.*",
]

# =============================================================================
# RISK OVERRIDES - For observability and rate limiting
# Default: "medium"
# Only specify non-medium risk levels
# =============================================================================

RISK_OVERRIDES: dict[str, str] = {
    # High risk - destructive operations
    "delete_country_resource": "high",
    "delete_organization_resource": "high",
    "delete_source_resource": "high",
    "delete_source_type_resource": "high",
    "post_environment_switch": "high",
    # Low risk - read-only admin operations
    "get_environment_resource": "low",
}

# =============================================================================
# OPTIONAL: Name/Description/Idempotent overrides
# Use when OpenAPI names/descriptions are not ideal for LLM context
# =============================================================================

NAME_OVERRIDES: dict[str, str] = {
    # Example: "get_country_list": "list_countries",
}

DESCRIPTION_OVERRIDES: dict[str, str] = {
    # Example: "get_country_list": "List all countries",
}

IDEMPOTENT_OVERRIDES: dict[str, bool] = {
    # Example: "post_country_upsert": True,  # POST that is actually idempotent
}


def get_tier_overrides() -> dict[str, Tier]:
    """Build tier overrides dict from DIRECT_ENDPOINTS list.

    Returns:
        Dict mapping operationId to Tier.DIRECT
    """
    return {ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS}
