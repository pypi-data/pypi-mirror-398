"""Parameter validation utilities.

This module provides validation functions for API parameters including:
- Type validation (string, integer, uuid, email, boolean)
- Pattern matching with regex
- Range validation for numeric types
- Required field checking

Validation is optional - endpoints without param_schema are not validated.
"""

import re
import uuid as uuid_module
from dataclasses import dataclass, field
from typing import Any, Literal

from yirifi_mcp.core.exceptions import ValidationError

# Supported parameter types
ParamType = Literal["string", "integer", "uuid", "email", "boolean"]

# Predefined regex patterns
PATTERNS = {
    "uuid": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "slug": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
}


@dataclass
class ParamSpec:
    """Parameter validation specification.

    Attributes:
        name: Parameter name
        param_type: Type of parameter (string, integer, uuid, email, boolean)
        required: Whether parameter is required (default: True)
        pattern: Optional regex pattern for string validation
        min_value: Minimum value for integers
        max_value: Maximum value for integers
        min_length: Minimum length for strings
        max_length: Maximum length for strings
        allowed_values: Optional list of allowed values (enum)
    """

    name: str
    param_type: ParamType = "string"
    required: bool = True
    pattern: str | None = None
    min_value: int | None = None
    max_value: int | None = None
    min_length: int | None = None
    max_length: int | None = None
    allowed_values: list[Any] | None = None


def validate_param(name: str, value: Any, spec: ParamSpec) -> Any:
    """Validate and coerce a single parameter.

    Args:
        name: Parameter name (for error messages)
        value: Parameter value to validate
        spec: ParamSpec defining validation rules

    Returns:
        Validated and coerced value

    Raises:
        ValidationError: If validation fails
    """
    # Handle missing required values
    if value is None:
        if spec.required:
            raise ValidationError(f"Missing required parameter: {name}", name)
        return None

    # Type-specific validation
    if spec.param_type == "integer":
        return _validate_integer(name, value, spec)
    elif spec.param_type == "uuid":
        return _validate_uuid(name, value)
    elif spec.param_type == "email":
        return _validate_email(name, value)
    elif spec.param_type == "boolean":
        return _validate_boolean(name, value)
    else:  # string
        return _validate_string(name, value, spec)


def _validate_integer(name: str, value: Any, spec: ParamSpec) -> int:
    """Validate integer parameter."""
    # Coerce to int
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Parameter '{name}' must be an integer, got: {type(value).__name__}",
            name,
        )

    # Range validation
    if spec.min_value is not None and int_value < spec.min_value:
        raise ValidationError(
            f"Parameter '{name}' must be >= {spec.min_value}, got: {int_value}",
            name,
        )
    if spec.max_value is not None and int_value > spec.max_value:
        raise ValidationError(
            f"Parameter '{name}' must be <= {spec.max_value}, got: {int_value}",
            name,
        )

    return int_value


def _validate_uuid(name: str, value: Any) -> str:
    """Validate UUID parameter."""
    str_value = str(value)

    # Try to parse as UUID
    try:
        parsed = uuid_module.UUID(str_value)
        return str(parsed)  # Normalized format
    except ValueError:
        raise ValidationError(
            f"Parameter '{name}' must be a valid UUID, got: {str_value[:50]}",
            name,
        )


def _validate_email(name: str, value: Any) -> str:
    """Validate email parameter."""
    str_value = str(value)

    if not re.match(PATTERNS["email"], str_value):
        raise ValidationError(
            f"Parameter '{name}' must be a valid email address, got: {str_value[:50]}",
            name,
        )

    return str_value.lower()  # Normalize to lowercase


def _validate_boolean(name: str, value: Any) -> bool:
    """Validate boolean parameter."""
    if isinstance(value, bool):
        return value

    # String coercion
    if isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ("true", "1", "yes", "on"):
            return True
        if lower_value in ("false", "0", "no", "off"):
            return False

    # Integer coercion
    if isinstance(value, int):
        return bool(value)

    raise ValidationError(
        f"Parameter '{name}' must be a boolean, got: {type(value).__name__}",
        name,
    )


def _validate_string(name: str, value: Any, spec: ParamSpec) -> str:
    """Validate string parameter."""
    str_value = str(value)

    # Length validation
    if spec.min_length is not None and len(str_value) < spec.min_length:
        raise ValidationError(
            f"Parameter '{name}' must be at least {spec.min_length} characters",
            name,
        )
    if spec.max_length is not None and len(str_value) > spec.max_length:
        raise ValidationError(
            f"Parameter '{name}' must be at most {spec.max_length} characters",
            name,
        )

    # Pattern validation
    if spec.pattern:
        # Check if pattern is a predefined one
        pattern = PATTERNS.get(spec.pattern, spec.pattern)
        if not re.match(pattern, str_value):
            raise ValidationError(
                f"Parameter '{name}' does not match required pattern",
                name,
            )

    # Allowed values validation (enum)
    if spec.allowed_values is not None and str_value not in spec.allowed_values:
        raise ValidationError(
            f"Parameter '{name}' must be one of: {spec.allowed_values}",
            name,
        )

    return str_value


def validate_params(
    params: dict | None,
    param_schema: list[ParamSpec] | None,
) -> dict | None:
    """Validate all parameters against schema.

    If no schema is provided, returns params unchanged (backward compatible).

    Args:
        params: Dict of parameter names to values
        param_schema: List of ParamSpec definitions

    Returns:
        Validated and coerced params dict

    Raises:
        ValidationError: If any validation fails
    """
    # No schema = no validation (backward compatible)
    if not param_schema:
        return params

    # No params provided
    if params is None:
        params = {}

    validated = {}
    schema_by_name = {spec.name: spec for spec in param_schema}

    # Validate parameters defined in schema
    for spec in param_schema:
        value = params.get(spec.name)
        validated_value = validate_param(spec.name, value, spec)
        if validated_value is not None:
            validated[spec.name] = validated_value

    # Include extra params not in schema (passthrough)
    for key, value in params.items():
        if key not in schema_by_name:
            validated[key] = value

    return validated if validated else None
