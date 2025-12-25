"""Auth service catalog - SINGLE SOURCE OF TRUTH.

This module defines all endpoints for the auth service in a unified format.
The catalog is used to generate both:
1. RouteMap entries for OpenAPI filtering (direct tools)
2. API_CATALOG entries for gateway tool (all accessible endpoints)

NAMING CONVENTION:
- Endpoint names MUST match the OpenAPI operationId from the upstream service
- FastMCP generates MCP tool names from operationId
- This ensures: catalog name == MCP tool name == gateway action name
- Pattern: {method}_{resource}_{action} e.g., get_user_list, post_api_key_list

Tier Guidelines:
- DIRECT: Frequent, safe operations that benefit from individual MCP tools
- GATEWAY: Admin/dangerous operations that should require explicit naming
- EXCLUDE: Never expose via MCP (health checks, internal endpoints)

Risk Level (for GATEWAY tier):
- low: Read-only admin operations (audit logs, listing)
- medium: Operations that modify non-critical data
- high: Destructive or security-sensitive operations
"""

from .base import Endpoint, ServiceCatalog, Tier

# =============================================================================
# AUTH SERVICE ENDPOINTS
# Names match OpenAPI operationId from auth-service Swagger spec
# =============================================================================

AUTH_ENDPOINTS = [
    # -------------------------------------------------------------------------
    # Auth (2 direct)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_auth_me",  # operationId: get_auth_me
        "GET",
        "/auth/me",
        "Get current user info",
        Tier.DIRECT,
    ),
    Endpoint(
        "post_auth_verify",  # operationId: post_auth_verify
        "POST",
        "/auth/verify",
        "Verify session/API key",
        Tier.DIRECT,
    ),
    # -------------------------------------------------------------------------
    # Users (7 direct, 2 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_user_list",  # operationId: get_user_list
        "GET",
        "/users/",
        "List all users",
        Tier.DIRECT,
    ),
    Endpoint(
        "post_user_list",  # operationId: post_user_list
        "POST",
        "/users/",
        "Create new user",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_user_me",  # operationId: get_user_me
        "GET",
        "/users/me",
        "Get current user details",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_user_detail",  # operationId: get_user_detail
        "GET",
        "/users/{user_id}",
        "Get user by ID",
        Tier.DIRECT,
    ),
    Endpoint(
        "put_user_detail",  # operationId: put_user_detail
        "PUT",
        "/users/{user_id}",
        "Update user",
        Tier.DIRECT,
    ),
    Endpoint(
        "delete_user_detail",  # operationId: delete_user_detail
        "DELETE",
        "/users/{user_id}",
        "Deactivate user",
        Tier.GATEWAY,
        risk_level="high",
    ),
    Endpoint(
        "get_user_access",  # operationId: get_user_access
        "GET",
        "/users/{user_id}/access",
        "Get user microsite access",
        Tier.DIRECT,
    ),
    Endpoint(
        "put_user_access",  # operationId: put_user_access
        "PUT",
        "/users/{user_id}/access",
        "Set user microsite access",
        Tier.DIRECT,
    ),
    Endpoint(
        "put_user_password",  # operationId: put_user_password
        "PUT",
        "/users/{user_id}/password",
        "Change user password",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Microsites (2 direct, 2 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_microsite_list",  # operationId: get_microsite_list
        "GET",
        "/microsites/",
        "List all microsites",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_microsite_detail",  # operationId: get_microsite_detail
        "GET",
        "/microsites/{microsite_id}",
        "Get microsite details",
        Tier.DIRECT,
    ),
    Endpoint(
        "post_microsite_list",  # operationId: post_microsite_list
        "POST",
        "/microsites/",
        "Create microsite",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "put_microsite_detail",  # operationId: put_microsite_detail
        "PUT",
        "/microsites/{microsite_id}",
        "Update microsite",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    # -------------------------------------------------------------------------
    # API Keys (3 direct)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_api_key_list",  # operationId: get_api_key_list
        "GET",
        "/api-keys/",
        "List API keys",
        Tier.DIRECT,
    ),
    Endpoint(
        "post_api_key_list",  # operationId: post_api_key_list
        "POST",
        "/api-keys/",
        "Create API key",
        Tier.DIRECT,
    ),
    Endpoint(
        "delete_api_key_detail",  # operationId: delete_api_key_detail
        "DELETE",
        "/api-keys/{key_id}",
        "Revoke API key",
        Tier.DIRECT,
    ),
    # -------------------------------------------------------------------------
    # Sessions (1 direct, 2 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_current_user_sessions",  # operationId: get_current_user_sessions
        "GET",
        "/sessions/me",
        "List my sessions",
        Tier.DIRECT,
    ),
    Endpoint(
        "delete_session_detail",  # operationId: delete_session_detail
        "DELETE",
        "/sessions/me/{session_id}",
        "Revoke session",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "get_session_list",  # operationId: get_session_list
        "GET",
        "/sessions/",
        "List all sessions (admin)",
        Tier.GATEWAY,
        risk_level="low",
    ),
    # -------------------------------------------------------------------------
    # RBAC - User Permissions (2 direct)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_user_permissions",  # operationId: get_user_permissions
        "GET",
        "/rbac/users/{user_id}/permissions/{app_id}",
        "Get user permissions",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_user_roles",  # operationId: get_user_roles
        "GET",
        "/rbac/users/{user_id}/roles",
        "Get user roles",
        Tier.DIRECT,
    ),
    # -------------------------------------------------------------------------
    # RBAC - Roles (gateway only - admin operations)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_role_list",  # operationId: get_role_list
        "GET",
        "/rbac/roles",
        "List all roles",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "get_role_detail",  # operationId: get_role_detail
        "GET",
        "/rbac/roles/{role_id}",
        "Get role details",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "post_application_roles",  # operationId: post_application_roles
        "POST",
        "/rbac/applications/{app_id}/roles",
        "Create role",
        Tier.GATEWAY,
        risk_level="high",
    ),
    Endpoint(
        "put_role_detail",  # operationId: put_role_detail
        "PUT",
        "/rbac/roles/{role_id}",
        "Update role",
        Tier.GATEWAY,
        risk_level="high",
    ),
    Endpoint(
        "delete_role_detail",  # operationId: delete_role_detail
        "DELETE",
        "/rbac/roles/{role_id}",
        "Delete role",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # RBAC - Permissions (gateway only)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_permission_list",  # operationId: get_permission_list
        "GET",
        "/rbac/permissions",
        "List all permissions",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "get_permission_detail",  # operationId: get_permission_detail
        "GET",
        "/rbac/permissions/{permission_id}",
        "Get permission",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "post_permission_list",  # operationId: post_permission_list
        "POST",
        "/rbac/permissions",
        "Create permission",
        Tier.GATEWAY,
        risk_level="high",
    ),
    Endpoint(
        "post_permission_batch",  # operationId: post_permission_batch
        "POST",
        "/rbac/permissions/batch",
        "Batch create permissions (supports ?dry_run=true)",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # RBAC - User Role Assignment (gateway only)
    # -------------------------------------------------------------------------
    Endpoint(
        "post_user_roles",  # operationId: post_user_roles
        "POST",
        "/rbac/users/{user_id}/roles",
        "Assign role to user",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # RBAC - Role Permissions (gateway only)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_role_permissions",  # operationId: get_role_permissions
        "GET",
        "/rbac/roles/{role_id}/permissions",
        "Get role permissions",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "put_role_permissions",  # operationId: put_role_permissions
        "PUT",
        "/rbac/roles/{role_id}/permissions",
        "Set role permissions",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # RBAC - Combined Role Creation (gateway only)
    # -------------------------------------------------------------------------
    Endpoint(
        "post_role_with_permissions",  # operationId: post_role_with_permissions
        "POST",
        "/rbac/roles/with-permissions",
        "Create role with permissions (supports ?dry_run=true)",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # RBAC - Global Roles (gateway only)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_global_role_list",  # operationId: get_global_role_list
        "GET",
        "/rbac/global/roles",
        "List global roles",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "post_global_role_list",  # operationId: post_global_role_list
        "POST",
        "/rbac/global/roles",
        "Create global role (supports ?dry_run=true)",
        Tier.GATEWAY,
        risk_level="high",
    ),
    Endpoint(
        "get_global_role_detail",  # operationId: get_global_role_detail
        "GET",
        "/rbac/global/roles/{role_id}",
        "Get global role",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "put_global_role_detail",  # operationId: put_global_role_detail
        "PUT",
        "/rbac/global/roles/{role_id}",
        "Update global role",
        Tier.GATEWAY,
        risk_level="high",
    ),
    Endpoint(
        "delete_global_role_detail",  # operationId: delete_global_role_detail
        "DELETE",
        "/rbac/global/roles/{role_id}",
        "Delete global role",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Audit (gateway only)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_audit_list",  # operationId: get_audit_list
        "GET",
        "/audit/",
        "List audit logs",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "get_audit_event_types",  # operationId: get_audit_event_types
        "GET",
        "/audit/event-types",
        "Get audit event types",
        Tier.GATEWAY,
        risk_level="low",
    ),
    # -------------------------------------------------------------------------
    # Applications (gateway only)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_application_list",  # operationId: get_application_list
        "GET",
        "/rbac/applications",
        "List applications",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "get_application_detail",  # operationId: get_application_detail
        "GET",
        "/rbac/applications/{app_id}",
        "Get application",
        Tier.GATEWAY,
        risk_level="low",
    ),
]

# Create the catalog singleton
AUTH_CATALOG = ServiceCatalog(AUTH_ENDPOINTS)
