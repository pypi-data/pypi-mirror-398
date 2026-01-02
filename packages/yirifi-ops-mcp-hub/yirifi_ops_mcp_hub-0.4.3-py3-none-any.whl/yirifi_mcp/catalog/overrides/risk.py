"""Risk service MCP catalog overrides.

This file defines the minimal configuration needed to expose risk API
endpoints as MCP tools. Only specify overrides - everything else is
derived from the OpenAPI spec.

Priority: x-mcp-* extensions in spec > these overrides > safe defaults

NAMING CONVENTION:
- Endpoint names match the OpenAPI operationId from the upstream service
- Pattern: {method}_{resource}_{action} e.g., get_risk_item_list, post_risk_category_list

Tier Guidelines:
- DIRECT: Frequent, safe operations that benefit from individual MCP tools
- GATEWAY (default): Admin/dangerous operations that should require explicit naming
- EXCLUDE: Never expose via MCP (health checks, internal endpoints)

Risk Level (for observability and rate limiting):
- low: Read-only operations
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
    # Environment - read only
    "get_environment_list",
    # Risk Items - read operations
    "get_risk_item_list",
    "get_risk_item_detail",
    "get_risk_item_by_yid",
    "get_risk_items_by_hierarchy",
    "get_risk_items_by_level",
    "get_high_risk_items",
    # Risk Items - write operations (medium risk)
    "post_risk_item_list",
    "put_risk_item_detail",
    # Risk Categories - read operations
    "get_risk_category_list",
    "get_risk_category_detail",
    "get_risk_category_by_yid",
    "get_risk_category_roots",
    "get_risk_category_children",
    # Risk Categories - write operations (medium risk)
    "post_risk_category_list",
    "put_risk_category_detail",
    # Risk Hierarchies - read operations
    "get_risk_hierarchy_list",
    "get_risk_hierarchy_detail",
    "get_risk_hierarchy_by_yid",
    "get_risk_hierarchy_roots",
    "get_risk_hierarchy_children",
    # Risk Hierarchies - write operations (medium risk)
    "post_risk_hierarchy_list",
    "put_risk_hierarchy_detail",
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
    # High risk - destructive or dangerous operations
    "delete_risk_item_detail": "high",
    "delete_risk_category_detail": "high",
    "delete_risk_hierarchy_detail": "high",
    "post_environment_switch": "high",
    # Low risk - read-only operations
    "get_environment_list": "low",
    "get_risk_item_list": "low",
    "get_risk_item_detail": "low",
    "get_risk_item_by_yid": "low",
    "get_risk_items_by_hierarchy": "low",
    "get_risk_items_by_level": "low",
    "get_high_risk_items": "low",
    "get_risk_category_list": "low",
    "get_risk_category_detail": "low",
    "get_risk_category_by_yid": "low",
    "get_risk_category_roots": "low",
    "get_risk_category_children": "low",
    "get_risk_hierarchy_list": "low",
    "get_risk_hierarchy_detail": "low",
    "get_risk_hierarchy_by_yid": "low",
    "get_risk_hierarchy_roots": "low",
    "get_risk_hierarchy_children": "low",
}

# =============================================================================
# OPTIONAL: Name/Description/Idempotent overrides
# Use when OpenAPI names/descriptions are not ideal for LLM context
# =============================================================================

NAME_OVERRIDES: dict[str, str] = {
    # Example: "get_risk_item_list": "list_risk_items",
}

DESCRIPTION_OVERRIDES: dict[str, str] = {
    # Example: "get_risk_item_list": "List all risk items with pagination",
}

IDEMPOTENT_OVERRIDES: dict[str, bool] = {
    # Example: "post_risk_item_upsert": True,
}


def get_tier_overrides() -> dict[str, Tier]:
    """Build tier overrides dict from DIRECT_ENDPOINTS list.

    Returns:
        Dict mapping operationId to Tier.DIRECT
    """
    return {ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS}
