"""Auth service MCP catalog overrides (FALLBACK ONLY).

This file provides FALLBACK values for endpoints that are missing x-mcp-*
extensions in the upstream auth-service OpenAPI spec.

Priority order:
1. x-mcp-tier / x-mcp-risk-level in OpenAPI spec (primary source of truth)
2. These override values (fallback if spec lacks extensions)
3. Safe defaults: GATEWAY tier, medium risk (if neither spec nor override)

With x-mcp attributes now added to all auth-service endpoints, these values
mainly serve as documentation and provide a safety net for any missed endpoints.

NAMING CONVENTION:
- Endpoint names match the OpenAPI operationId from the upstream service
- Pattern: {method}_{resource}_{action} e.g., get_user_list, post_api_key_list

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
    # Auth
    "get_auth_me",
    "post_auth_verify",
    # Users - common operations
    "get_user_list",
    "post_user_list",
    "get_user_me",
    "get_user_detail",
    "put_user_detail",
    "get_user_access",
    "put_user_access",
    # Microsites - read operations
    "get_microsite_list",
    "get_microsite_detail",
    # API Keys - self-service operations
    "get_api_key_list",
    "post_api_key_list",
    "delete_api_key_detail",
    # Sessions - self-service
    "get_current_user_sessions",
    # RBAC - read-only user queries
    "get_user_permissions",
    "get_user_roles",
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
    # High risk - destructive or security-sensitive
    "delete_user_detail": "high",
    "put_user_password": "high",
    "post_application_roles": "high",
    "put_role_detail": "high",
    "delete_role_detail": "high",
    "post_permission_list": "high",
    "post_permission_batch": "high",
    "post_user_roles": "high",
    "put_role_permissions": "high",
    "post_role_with_permissions": "high",
    "post_global_role_list": "high",
    "put_global_role_detail": "high",
    "delete_global_role_detail": "high",
    # Low risk - read-only admin operations
    "get_session_list": "low",
    "get_role_list": "low",
    "get_role_detail": "low",
    "get_permission_list": "low",
    "get_permission_detail": "low",
    "get_role_permissions": "low",
    "get_global_role_list": "low",
    "get_global_role_detail": "low",
    "get_audit_list": "low",
    "get_audit_event_types": "low",
    "get_application_list": "low",
    "get_application_detail": "low",
}

# =============================================================================
# OPTIONAL: Name/Description/Idempotent overrides
# Use when OpenAPI names/descriptions are not ideal for LLM context
# =============================================================================

NAME_OVERRIDES: dict[str, str] = {
    # Example: "get_user_list": "list_users",
}

DESCRIPTION_OVERRIDES: dict[str, str] = {
    # Example: "get_user_list": "List all users",
}

IDEMPOTENT_OVERRIDES: dict[str, bool] = {
    # Example: "post_user_upsert": True,  # POST that is actually idempotent
}


def get_tier_overrides() -> dict[str, Tier]:
    """Build tier overrides dict from DIRECT_ENDPOINTS list.

    Returns:
        Dict mapping operationId to Tier.DIRECT
    """
    return {ep: Tier.DIRECT for ep in DIRECT_ENDPOINTS}
