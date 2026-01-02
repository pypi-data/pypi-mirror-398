"""Policy validation for MCP catalogs.

This module provides security policy definitions and validation to prevent
accidental exposure of dangerous operations as DIRECT MCP tools.

Example usage:
    from yirifi_mcp.catalog.policy import CatalogPolicy, validate_catalog

    policy = CatalogPolicy(
        mandatory_gateway=["/rbac/roles/*", "*/password*"],
        mandatory_exclude=["/health/*", "/internal/*"],
    )

    violations = validate_catalog(catalog, policy)
    if violations:
        for v in violations:
            print(f"VIOLATION: {v}")
        raise PolicyViolationError(violations)
"""

import fnmatch
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseCatalog, Endpoint, Tier


@dataclass
class PolicyViolation:
    """A single policy violation found during validation.

    Attributes:
        endpoint_name: Name of the endpoint that violated policy
        violation_type: Type of violation (e.g., "mandatory_gateway", "mandatory_exclude")
        rule: The policy rule that was violated
        message: Human-readable description of the violation
    """

    endpoint_name: str
    violation_type: str
    rule: str
    message: str

    def __str__(self) -> str:
        return f"[{self.violation_type}] {self.endpoint_name}: {self.message}"


@dataclass
class CatalogPolicy:
    """Security policy for catalog validation.

    This policy defines constraints on which endpoints can be exposed at
    which tier. It's used for CI-time validation to prevent accidental
    exposure of dangerous operations.

    Attributes:
        mandatory_exclude: Path patterns that MUST be EXCLUDE tier (never exposed)
        mandatory_gateway: Path patterns that MUST be GATEWAY tier (never DIRECT)
        gateway_by_default_methods: HTTP methods that should default to GATEWAY
        allow_direct_delete: Whether DELETE operations can be DIRECT (default: False)
        allow_direct_patch: Whether PATCH operations can be DIRECT (default: False)

    Example:
        >>> policy = CatalogPolicy(
        ...     mandatory_gateway=["/rbac/roles/*", "*/password*"],
        ...     mandatory_exclude=["/health/*", "/internal/*"],
        ... )
    """

    # Paths that MUST be EXCLUDE (never exposed)
    mandatory_exclude: list[str] = field(
        default_factory=lambda: [
            "/health/*",
            "/internal/*",
            "/swagger*",
            "/docs*",
        ]
    )

    # Paths that MUST be GATEWAY (never DIRECT)
    mandatory_gateway: list[str] = field(
        default_factory=lambda: [
            "/rbac/roles/*",
            "/rbac/permissions/*",
            "*/password*",
            "/rbac/global/*",
            "/admin/*",
        ]
    )

    # HTTP methods that should be GATEWAY by default
    # (warn if they're DIRECT without explicit override)
    gateway_by_default_methods: list[str] = field(
        default_factory=lambda: ["DELETE", "PATCH"]
    )

    # Whether to allow DELETE operations as DIRECT tools
    allow_direct_delete: bool = False

    # Whether to allow PATCH operations as DIRECT tools
    allow_direct_patch: bool = False


class PolicyViolationError(Exception):
    """Raised when catalog validation fails against policy."""

    def __init__(self, violations: list[PolicyViolation]):
        self.violations = violations
        messages = [str(v) for v in violations]
        super().__init__(f"Policy validation failed with {len(violations)} violations:\n" + "\n".join(messages))


def validate_catalog(
    catalog: "BaseCatalog",
    policy: CatalogPolicy,
) -> list[PolicyViolation]:
    """Validate a catalog against a security policy.

    Checks all endpoints in the catalog against the policy rules and
    returns a list of violations. An empty list means the catalog passes.

    Args:
        catalog: The catalog to validate (ServiceCatalog or SpecDrivenCatalog)
        policy: The policy to validate against

    Returns:
        List of PolicyViolation objects (empty if validation passes)

    Example:
        >>> violations = validate_catalog(auth_catalog, DEFAULT_POLICY)
        >>> if violations:
        ...     raise PolicyViolationError(violations)
    """
    from .base import Tier

    violations = []

    # Check DIRECT endpoints against policy
    for endpoint in catalog.get_direct_endpoints():
        # Check mandatory_gateway paths
        for pattern in policy.mandatory_gateway:
            if _path_matches(endpoint.path, pattern):
                violations.append(
                    PolicyViolation(
                        endpoint_name=endpoint.name,
                        violation_type="mandatory_gateway",
                        rule=pattern,
                        message=f"Path '{endpoint.path}' matches mandatory_gateway pattern '{pattern}' but is DIRECT",
                    )
                )

        # Check DELETE method
        if endpoint.method == "DELETE" and not policy.allow_direct_delete:
            violations.append(
                PolicyViolation(
                    endpoint_name=endpoint.name,
                    violation_type="disallowed_method",
                    rule="DELETE",
                    message="DELETE operations should not be DIRECT unless allow_direct_delete=True",
                )
            )

        # Check PATCH method
        if endpoint.method == "PATCH" and not policy.allow_direct_patch:
            violations.append(
                PolicyViolation(
                    endpoint_name=endpoint.name,
                    violation_type="disallowed_method",
                    rule="PATCH",
                    message="PATCH operations should not be DIRECT unless allow_direct_patch=True",
                )
            )

    # Check all endpoints for mandatory_exclude violations
    for endpoint in catalog.get_all_endpoints():
        for pattern in policy.mandatory_exclude:
            if _path_matches(endpoint.path, pattern):
                violations.append(
                    PolicyViolation(
                        endpoint_name=endpoint.name,
                        violation_type="mandatory_exclude",
                        rule=pattern,
                        message=f"Path '{endpoint.path}' matches mandatory_exclude pattern '{pattern}' but is exposed",
                    )
                )

    return violations


def _path_matches(path: str, pattern: str) -> bool:
    """Check if a path matches a pattern.

    Supports both glob patterns (using fnmatch) and simple contains checks.

    Args:
        path: The URL path to check
        pattern: The pattern to match against

    Returns:
        True if the path matches the pattern

    Examples:
        >>> _path_matches("/users/123", "/users/*")
        True
        >>> _path_matches("/users/123/password", "*/password*")
        True
        >>> _path_matches("/health/live", "/health/*")
        True
    """
    # Normalize path (remove trailing slashes for consistency)
    path = path.rstrip("/")
    pattern = pattern.rstrip("/")

    # Use fnmatch for glob-style matching
    return fnmatch.fnmatch(path, pattern)


# Default policy for general use
DEFAULT_POLICY = CatalogPolicy()


# Strict policy for production-critical systems
STRICT_POLICY = CatalogPolicy(
    mandatory_exclude=[
        "/health/*",
        "/internal/*",
        "/swagger*",
        "/docs*",
        "/debug/*",
        "/metrics*",
    ],
    mandatory_gateway=[
        "/rbac/*",
        "*/password*",
        "*/admin/*",
        "/audit/*",
        "/sessions/*",
        "/environment/*",
    ],
    allow_direct_delete=False,
    allow_direct_patch=False,
)
