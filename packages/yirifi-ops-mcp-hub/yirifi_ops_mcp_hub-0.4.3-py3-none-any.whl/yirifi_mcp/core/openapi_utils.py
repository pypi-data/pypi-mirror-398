"""OpenAPI specification utilities.

This module provides utilities for working with OpenAPI specifications:
- Fetching specs from services
- Converting Swagger 2.0 to OpenAPI 3.0
- Patching specs for MCP compatibility
- Validating spec structure and content
"""

import copy
from typing import TYPE_CHECKING

import httpx
import structlog

from yirifi_mcp.core.exceptions import SpecValidationError

if TYPE_CHECKING:
    from yirifi_mcp.catalog.base import ServiceCatalog

logger = structlog.get_logger()


def convert_swagger2_to_openapi3(swagger_spec: dict) -> dict:
    """
    Convert Swagger 2.0 specification to OpenAPI 3.0 format.

    FastMCP requires OpenAPI 3.x format, but Flask-RESTX generates Swagger 2.0.
    This function performs the conversion.

    Args:
        swagger_spec: Swagger 2.0 specification dict

    Returns:
        OpenAPI 3.0 specification dict
    """
    spec = copy.deepcopy(swagger_spec)

    # Build server URL from Swagger 2.0 fields
    schemes = spec.get("schemes", ["http"])
    host = spec.get("host", "localhost")
    base_path = spec.get("basePath", "")
    server_url = f"{schemes[0]}://{host}{base_path}"

    # Start building OpenAPI 3.0 spec
    openapi_spec = {
        "openapi": "3.0.3",
        "info": spec.get("info", {"title": "API", "version": "1.0"}),
        "servers": [{"url": server_url}],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {},
        },
    }

    # Convert definitions to components/schemas
    if "definitions" in spec:
        openapi_spec["components"]["schemas"] = spec["definitions"]

    # Convert securityDefinitions to components/securitySchemes
    if "securityDefinitions" in spec:
        for name, security_def in spec["securityDefinitions"].items():
            if security_def.get("type") == "apiKey":
                openapi_spec["components"]["securitySchemes"][name] = {
                    "type": "apiKey",
                    "in": security_def.get("in", "header"),
                    "name": security_def.get("name", name),
                }

    # Convert paths
    for path, path_item in spec.get("paths", {}).items():
        openapi_spec["paths"][path] = {}

        for method, operation in path_item.items():
            if method in ("get", "post", "put", "patch", "delete", "options", "head"):
                openapi_spec["paths"][path][method] = convert_operation(operation, spec)
            elif method == "parameters":
                # Path-level parameters
                openapi_spec["paths"][path]["parameters"] = [
                    convert_parameter(p, spec) for p in operation
                ]

    return openapi_spec


def convert_operation(operation: dict, spec: dict) -> dict:
    """Convert a Swagger 2.0 operation to OpenAPI 3.0 format."""
    converted = {
        "summary": operation.get("summary", ""),
        "description": operation.get("description", ""),
        "operationId": operation.get("operationId", ""),
        "tags": operation.get("tags", []),
        "parameters": [],
        "responses": {},
    }

    # Convert parameters
    for param in operation.get("parameters", []):
        if param.get("in") == "body":
            # Convert body parameter to requestBody
            converted["requestBody"] = convert_body_parameter(param, spec)
        else:
            converted["parameters"].append(convert_parameter(param, spec))

    # Convert responses
    for status_code, response in operation.get("responses", {}).items():
        converted["responses"][status_code] = convert_response(response, spec)

    # Ensure at least a default response
    if not converted["responses"]:
        converted["responses"]["200"] = {"description": "Success"}

    # Remove empty parameters list
    if not converted["parameters"]:
        del converted["parameters"]

    return converted


def convert_parameter(param: dict, spec: dict) -> dict:
    """Convert a Swagger 2.0 parameter to OpenAPI 3.0 format."""
    converted = {
        "name": param.get("name", ""),
        "in": param.get("in", "query"),
        "required": param.get("required", False),
        "description": param.get("description", ""),
    }

    # Convert schema
    if "type" in param:
        converted["schema"] = {
            "type": param.get("type", "string"),
        }
        if "format" in param:
            converted["schema"]["format"] = param["format"]
        if "enum" in param:
            converted["schema"]["enum"] = param["enum"]
        if "default" in param:
            converted["schema"]["default"] = param["default"]
    elif "$ref" in param:
        converted["schema"] = {"$ref": param["$ref"].replace("#/definitions/", "#/components/schemas/")}

    return converted


def convert_body_parameter(param: dict, spec: dict) -> dict:
    """Convert a Swagger 2.0 body parameter to OpenAPI 3.0 requestBody."""
    request_body = {
        "required": param.get("required", False),
        "description": param.get("description", ""),
        "content": {
            "application/json": {
                "schema": {}
            }
        }
    }

    schema = param.get("schema", {})
    if "$ref" in schema:
        request_body["content"]["application/json"]["schema"] = {
            "$ref": schema["$ref"].replace("#/definitions/", "#/components/schemas/")
        }
    else:
        request_body["content"]["application/json"]["schema"] = schema

    return request_body


def convert_response(response: dict, spec: dict) -> dict:
    """Convert a Swagger 2.0 response to OpenAPI 3.0 format."""
    converted = {
        "description": response.get("description", "Response"),
    }

    if "schema" in response:
        schema = response["schema"]
        if "$ref" in schema:
            schema = {"$ref": schema["$ref"].replace("#/definitions/", "#/components/schemas/")}

        converted["content"] = {
            "application/json": {
                "schema": schema
            }
        }

    return converted


async def fetch_openapi_spec(
    base_url: str,
    openapi_path: str = "/api/v1/docs/swagger.json",
    api_key: str | None = None,
) -> dict:
    """
    Fetch OpenAPI specification from a service.

    Flask-RESTX serves Swagger 2.0 spec at /api/v1/docs/swagger.json

    Args:
        base_url: Base URL of the service
        openapi_path: Path to the OpenAPI spec endpoint
        api_key: Optional API key for authentication

    Returns:
        Parsed OpenAPI specification as dict
    """
    url = f"{base_url.rstrip('/')}{openapi_path}"

    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        logger.info("fetching_openapi_spec", url=url)
        response = await client.get(url)
        response.raise_for_status()

        spec = response.json()
        logger.info(
            "openapi_spec_fetched",
            title=spec.get("info", {}).get("title"),
            paths_count=len(spec.get("paths", {})),
        )
        return spec


def patch_openapi_spec(spec: dict, server_url: str) -> dict:
    """
    Patch OpenAPI spec for MCP compatibility.

    Converts Swagger 2.0 to OpenAPI 3.0 (required by FastMCP).
    Ensures servers points to the correct URL.

    Args:
        spec: OpenAPI specification dict
        server_url: Target server URL

    Returns:
        Patched OpenAPI 3.0 specification
    """
    # For Swagger 2.0 specs - convert to OpenAPI 3.0
    if "swagger" in spec:
        # First set the host/schemes so conversion uses correct URL
        host = server_url.replace("http://", "").replace("https://", "").split("/")[0]
        spec["host"] = host
        spec["basePath"] = spec.get("basePath", "/api/v1")
        spec["schemes"] = ["https" if "https" in server_url else "http"]

        # Convert to OpenAPI 3.0
        logger.info("converting_swagger2_to_openapi3")
        spec = convert_swagger2_to_openapi3(spec)

    # For OpenAPI 3.x specs - just update server URL
    elif "openapi" in spec:
        spec["servers"] = [{"url": server_url}]

    return spec


def get_spec_info(spec: dict) -> dict:
    """
    Extract summary information from OpenAPI spec.

    Args:
        spec: OpenAPI specification dict

    Returns:
        Dict with title, version, paths count, and endpoint list
    """
    info = spec.get("info", {})
    paths = spec.get("paths", {})

    endpoints = []
    for path, methods in paths.items():
        for method in methods:
            if method in ("get", "post", "put", "patch", "delete"):
                endpoints.append(f"{method.upper()} {path}")

    return {
        "title": info.get("title", "Unknown"),
        "version": info.get("version", "Unknown"),
        "paths_count": len(paths),
        "endpoints_count": len(endpoints),
        "endpoints": endpoints,
    }


# =============================================================================
# Spec Validation
# =============================================================================


def validate_openapi_spec(spec: dict) -> list[str]:
    """Validate OpenAPI spec has required fields.

    Performs structural validation to ensure the spec is well-formed.

    Args:
        spec: OpenAPI specification dict

    Returns:
        List of warning messages (empty if fully valid)

    Raises:
        SpecValidationError: If spec is malformed (missing critical fields)
    """
    errors = []
    warnings = []

    # Check for version field (required - either openapi or swagger)
    if "openapi" not in spec and "swagger" not in spec:
        errors.append("Missing 'openapi' or 'swagger' version field")

    # Check for info field (required)
    if "info" not in spec:
        errors.append("Missing 'info' field")
    else:
        info = spec["info"]
        if not info.get("title"):
            warnings.append("Missing info.title")
        if not info.get("version"):
            warnings.append("Missing info.version")

    # Check for paths field (required)
    if "paths" not in spec:
        errors.append("Missing 'paths' field")
    elif not spec["paths"]:
        warnings.append("No paths defined in spec")

    # Raise error for critical issues
    if errors:
        raise SpecValidationError(f"Invalid spec: {'; '.join(errors)}")

    return warnings


def validate_catalog_against_spec(
    catalog: "ServiceCatalog",
    spec: dict,
) -> list[str]:
    """Check catalog endpoint names match spec operationIds.

    This validation ensures that catalog endpoint names correspond to
    actual operations defined in the OpenAPI spec.

    Args:
        catalog: ServiceCatalog to validate
        spec: OpenAPI specification dict

    Returns:
        List of warning messages for mismatches
    """
    warnings = []

    # Collect all operationIds from spec
    spec_operation_ids = set()
    for path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if isinstance(operation, dict) and "operationId" in operation:
                spec_operation_ids.add(operation["operationId"])

    # Check catalog endpoints against spec
    for endpoint in catalog.get_all_endpoints():
        if endpoint.name not in spec_operation_ids:
            warnings.append(
                f"Catalog endpoint '{endpoint.name}' not found in spec operationIds"
            )

    # Check for spec operations not in catalog (info only)
    catalog_names = {e.name for e in catalog.get_all_endpoints()}
    for op_id in spec_operation_ids:
        if op_id not in catalog_names:
            logger.debug(
                "spec_operation_not_in_catalog",
                operation_id=op_id,
            )

    return warnings


def get_spec_operation_ids(spec: dict) -> set[str]:
    """Extract all operationIds from an OpenAPI spec.

    Args:
        spec: OpenAPI specification dict

    Returns:
        Set of operationId strings
    """
    operation_ids = set()

    for path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if isinstance(operation, dict) and "operationId" in operation:
                operation_ids.add(operation["operationId"])

    return operation_ids
