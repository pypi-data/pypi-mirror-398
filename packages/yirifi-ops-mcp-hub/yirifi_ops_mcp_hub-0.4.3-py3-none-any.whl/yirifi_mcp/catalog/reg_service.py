"""Reg service catalog - SINGLE SOURCE OF TRUTH.

This module defines all endpoints for the reg service in a unified format.
The catalog is used to generate both:
1. RouteMap entries for OpenAPI filtering (direct tools)
2. API_CATALOG entries for gateway tool (all accessible endpoints)

NAMING CONVENTION:
- Endpoint names MUST match the OpenAPI operationId from the upstream service
- FastMCP generates MCP tool names from operationId
- This ensures: catalog name == MCP tool name == gateway action name
- Pattern: {method}_{resource}_{action} e.g., get_country_list, post_source_list

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
# REG SERVICE ENDPOINTS
# Names match OpenAPI operationId from reg-service Swagger spec
# =============================================================================

REG_ENDPOINTS = [
    # -------------------------------------------------------------------------
    # Countries (3 direct, 3 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_country_list",  # operationId: get_country_list
        "GET",
        "/countries",
        "List all countries with pagination",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_country_resource",  # operationId: get_country_resource
        "GET",
        "/countries/{id}",
        "Get country by ID",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_country_by_code",  # operationId: get_country_by_code
        "GET",
        "/countries/code/{code}",
        "Get country by ISO alpha-2 or alpha-3 code",
        Tier.DIRECT,
    ),
    Endpoint(
        "post_country_list",  # operationId: post_country_list
        "POST",
        "/countries",
        "Create a new country",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "put_country_resource",  # operationId: put_country_resource
        "PUT",
        "/countries/{id}",
        "Update a country",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "delete_country_resource",  # operationId: delete_country_resource
        "DELETE",
        "/countries/{id}",
        "Delete a country",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Organizations (2 direct, 3 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_organization_list",  # operationId: get_organization_list
        "GET",
        "/organizations",
        "List all organizations with pagination",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_organization_resource",  # operationId: get_organization_resource
        "GET",
        "/organizations/{id}",
        "Get organization by ID",
        Tier.DIRECT,
    ),
    Endpoint(
        "post_organization_list",  # operationId: post_organization_list
        "POST",
        "/organizations",
        "Create a new organization",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "put_organization_resource",  # operationId: put_organization_resource
        "PUT",
        "/organizations/{id}",
        "Update an organization",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "delete_organization_resource",  # operationId: delete_organization_resource
        "DELETE",
        "/organizations/{id}",
        "Delete an organization",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Sources (2 direct, 3 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_source_list",  # operationId: get_source_list
        "GET",
        "/sources",
        "List all sources with pagination",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_source_resource",  # operationId: get_source_resource
        "GET",
        "/sources/{id}",
        "Get source by ID",
        Tier.DIRECT,
    ),
    Endpoint(
        "post_source_list",  # operationId: post_source_list
        "POST",
        "/sources",
        "Create a new source",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "put_source_resource",  # operationId: put_source_resource
        "PUT",
        "/sources/{id}",
        "Update a source",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "delete_source_resource",  # operationId: delete_source_resource
        "DELETE",
        "/sources/{id}",
        "Delete a source",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Source Types (2 direct, 3 gateway)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_source_type_list",  # operationId: get_source_type_list
        "GET",
        "/sourcetypes",
        "List all source types with pagination",
        Tier.DIRECT,
    ),
    Endpoint(
        "get_source_type_resource",  # operationId: get_source_type_resource
        "GET",
        "/sourcetypes/{id}",
        "Get source type by ID",
        Tier.DIRECT,
    ),
    Endpoint(
        "post_source_type_list",  # operationId: post_source_type_list
        "POST",
        "/sourcetypes",
        "Create a new source type",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "put_source_type_resource",  # operationId: put_source_type_resource
        "PUT",
        "/sourcetypes/{id}",
        "Update a source type",
        Tier.GATEWAY,
        risk_level="medium",
    ),
    Endpoint(
        "delete_source_type_resource",  # operationId: delete_source_type_resource
        "DELETE",
        "/sourcetypes/{id}",
        "Delete a source type",
        Tier.GATEWAY,
        risk_level="high",
    ),
    # -------------------------------------------------------------------------
    # Environment (2 gateway - admin operations)
    # -------------------------------------------------------------------------
    Endpoint(
        "get_environment_resource",  # operationId: get_environment_resource
        "GET",
        "/environment",
        "Get current MongoDB environment status",
        Tier.GATEWAY,
        risk_level="low",
    ),
    Endpoint(
        "post_environment_switch",  # operationId: post_environment_switch
        "POST",
        "/environment/switch/{env}",
        "Switch MongoDB environment at runtime (DEV/UAT/PRD)",
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
REG_CATALOG = ServiceCatalog(REG_ENDPOINTS)
