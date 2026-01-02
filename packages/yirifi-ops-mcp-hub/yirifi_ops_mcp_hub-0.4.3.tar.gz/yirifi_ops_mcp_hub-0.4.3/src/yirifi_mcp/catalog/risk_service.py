"""Risk service catalog - SINGLE SOURCE OF TRUTH.

This module defines all endpoints for the risk service in a unified format.
The catalog is used to generate both:
1. RouteMap entries for OpenAPI filtering (direct tools)
2. API_CATALOG entries for gateway tool (all accessible endpoints)

NAMING CONVENTION:
- Endpoint names MUST match the OpenAPI operationId from the upstream service
- FastMCP generates MCP tool names from operationId
- This ensures: catalog name == MCP tool name == gateway action name
- Pattern: {method}_{resource}_{action} e.g., get_risk_item_list, post_risk_category_list

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
# RISK SERVICE ENDPOINTS
# Names match OpenAPI operationId from risk-service Swagger spec
# =============================================================================

RISK_ENDPOINTS = [
    # -------------------------------------------------------------------------
    # Environment (1 direct, 1 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_environment_list",  # operationId: get_environment_list
        "GET",
        "/environment",
        "Get current environment status",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "post_environment_switch",  # operationId: post_environment_switch
        "POST",
        "/environment/switch/{env}",
        "Switch environment at runtime (DEV/UAT/PRD)",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Risk Items - Read Operations (6 direct)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_risk_item_list",  # operationId: get_risk_item_list
        "GET",
        "/risk-items",
        "List all risk items with pagination",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_item_detail",  # operationId: get_risk_item_detail
        "GET",
        "/risk-items/{id}",
        "Get risk item by ID",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_item_by_yid",  # operationId: get_risk_item_by_yid
        "GET",
        "/risk-items/yid/{yid}",
        "Get risk item by YID",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_items_by_hierarchy",  # operationId: get_risk_items_by_hierarchy
        "GET",
        "/risk-items/hierarchy/{hierarchy_id}",
        "Get risk items by hierarchy",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_items_by_level",  # operationId: get_risk_items_by_level
        "GET",
        "/risk-items/level/{level}",
        "Get risk items by level",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_high_risk_items",  # operationId: get_high_risk_items
        "GET",
        "/risk-items/high-risk",
        "Get high risk items",
        Tier.DIRECT,
        risk_level="low",
    ),
    # -------------------------------------------------------------------------
    # Risk Items - Write Operations (2 direct, 1 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "post_risk_item_list",  # operationId: post_risk_item_list
        "POST",
        "/risk-items",
        "Create a new risk item",
        Tier.DIRECT,
        risk_level="medium",
    ),
    Endpoint(
        "put_risk_item_detail",  # operationId: put_risk_item_detail
        "PUT",
        "/risk-items/{id}",
        "Update a risk item",
        Tier.DIRECT,
        risk_level="medium",
    ),
    Endpoint(
        "delete_risk_item_detail",  # operationId: delete_risk_item_detail
        "DELETE",
        "/risk-items/{id}",
        "Delete a risk item",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Risk Categories - Read Operations (5 direct)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_risk_category_list",  # operationId: get_risk_category_list
        "GET",
        "/risk-categories",
        "List all risk categories with pagination",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_category_detail",  # operationId: get_risk_category_detail
        "GET",
        "/risk-categories/{id}",
        "Get risk category by ID",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_category_by_yid",  # operationId: get_risk_category_by_yid
        "GET",
        "/risk-categories/yid/{yid}",
        "Get risk category by YID",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_category_roots",  # operationId: get_risk_category_roots
        "GET",
        "/risk-categories/roots",
        "Get root risk categories",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_category_children",  # operationId: get_risk_category_children
        "GET",
        "/risk-categories/{id}/children",
        "Get children of a risk category",
        Tier.DIRECT,
        risk_level="low",
    ),
    # -------------------------------------------------------------------------
    # Risk Categories - Write Operations (2 direct, 1 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "post_risk_category_list",  # operationId: post_risk_category_list
        "POST",
        "/risk-categories",
        "Create a new risk category",
        Tier.DIRECT,
        risk_level="medium",
    ),
    Endpoint(
        "put_risk_category_detail",  # operationId: put_risk_category_detail
        "PUT",
        "/risk-categories/{id}",
        "Update a risk category",
        Tier.DIRECT,
        risk_level="medium",
    ),
    Endpoint(
        "delete_risk_category_detail",  # operationId: delete_risk_category_detail
        "DELETE",
        "/risk-categories/{id}",
        "Delete a risk category",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Risk Hierarchies - Read Operations (5 direct)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_risk_hierarchy_list",  # operationId: get_risk_hierarchy_list
        "GET",
        "/risk-hierarchies",
        "List all risk hierarchies with pagination",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_hierarchy_detail",  # operationId: get_risk_hierarchy_detail
        "GET",
        "/risk-hierarchies/{id}",
        "Get risk hierarchy by ID",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_hierarchy_by_yid",  # operationId: get_risk_hierarchy_by_yid
        "GET",
        "/risk-hierarchies/yid/{yid}",
        "Get risk hierarchy by YID",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_hierarchy_roots",  # operationId: get_risk_hierarchy_roots
        "GET",
        "/risk-hierarchies/roots",
        "Get root risk hierarchies",
        Tier.DIRECT,
        risk_level="low",
    ),
    Endpoint(
        "get_risk_hierarchy_children",  # operationId: get_risk_hierarchy_children
        "GET",
        "/risk-hierarchies/{id}/children",
        "Get children of a risk hierarchy",
        Tier.DIRECT,
        risk_level="low",
    ),
    # -------------------------------------------------------------------------
    # Risk Hierarchies - Write Operations (2 direct, 1 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "post_risk_hierarchy_list",  # operationId: post_risk_hierarchy_list
        "POST",
        "/risk-hierarchies",
        "Create a new risk hierarchy",
        Tier.DIRECT,
        risk_level="medium",
    ),
    Endpoint(
        "put_risk_hierarchy_detail",  # operationId: put_risk_hierarchy_detail
        "PUT",
        "/risk-hierarchies/{id}",
        "Update a risk hierarchy",
        Tier.DIRECT,
        risk_level="medium",
    ),
    Endpoint(
        "delete_risk_hierarchy_detail",  # operationId: delete_risk_hierarchy_detail
        "DELETE",
        "/risk-hierarchies/{id}",
        "Delete a risk hierarchy",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Health (excluded - infrastructure endpoints)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_live_check",  # operationId: get_live_check
        "GET",
        "/health/live",
        "Liveness probe",
        Tier.EXCLUDE,
    ),
    Endpoint(
        "get_ready_check",  # operationId: get_ready_check
        "GET",
        "/health/ready",
        "Readiness probe",
        Tier.EXCLUDE,
    ),
    Endpoint(
        "get_info_check",  # operationId: get_info_check
        "GET",
        "/health/info",
        "Application info",
        Tier.EXCLUDE,
    ),
]

# Create the catalog singleton
RISK_CATALOG = ServiceCatalog(RISK_ENDPOINTS)
