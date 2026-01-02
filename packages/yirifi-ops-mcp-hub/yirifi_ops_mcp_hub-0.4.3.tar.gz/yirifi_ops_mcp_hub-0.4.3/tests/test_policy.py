"""Tests for catalog policy validation."""

import pytest

from yirifi_mcp.catalog.base import Endpoint, ServiceCatalog, Tier
from yirifi_mcp.catalog.policy import (
    CatalogPolicy,
    PolicyViolation,
    PolicyViolationError,
    DEFAULT_POLICY,
    STRICT_POLICY,
    validate_catalog,
)


class TestCatalogPolicy:
    """Tests for CatalogPolicy configuration."""

    def test_default_policy_has_expected_rules(self):
        """Test that DEFAULT_POLICY has sensible defaults."""
        policy = DEFAULT_POLICY

        # Should have mandatory exclusions
        assert "/health/*" in policy.mandatory_exclude
        assert "/internal/*" in policy.mandatory_exclude

        # Should have mandatory gateway paths
        assert "/rbac/roles/*" in policy.mandatory_gateway
        assert "*/password*" in policy.mandatory_gateway

        # DELETE and PATCH should not be allowed as DIRECT
        assert not policy.allow_direct_delete
        assert not policy.allow_direct_patch

    def test_strict_policy_is_more_restrictive(self):
        """Test that STRICT_POLICY is more restrictive than DEFAULT_POLICY."""
        # Strict policy should have more mandatory_gateway patterns
        assert len(STRICT_POLICY.mandatory_gateway) >= len(DEFAULT_POLICY.mandatory_gateway)

        # Strict policy should have more mandatory_exclude patterns
        assert len(STRICT_POLICY.mandatory_exclude) >= len(DEFAULT_POLICY.mandatory_exclude)

    def test_custom_policy_creation(self):
        """Test creating a custom policy."""
        policy = CatalogPolicy(
            mandatory_exclude=["/admin/*"],
            mandatory_gateway=["/users/*/delete"],
            allow_direct_delete=True,
        )

        assert "/admin/*" in policy.mandatory_exclude
        assert "/users/*/delete" in policy.mandatory_gateway
        assert policy.allow_direct_delete is True


class TestValidateCatalog:
    """Tests for validate_catalog function."""

    def test_valid_catalog_passes(self):
        """Test that a valid catalog passes validation."""
        endpoints = [
            Endpoint("get_user_list", "GET", "/users/", "List users", Tier.DIRECT),
            Endpoint("delete_user_detail", "DELETE", "/users/{id}", "Delete", Tier.GATEWAY, risk_level="high"),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(allow_direct_delete=False)

        violations = validate_catalog(catalog, policy)
        assert len(violations) == 0

    def test_direct_delete_violation(self):
        """Test that DIRECT DELETE operations are flagged."""
        endpoints = [
            Endpoint("delete_user_detail", "DELETE", "/users/{id}", "Delete", Tier.DIRECT),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(allow_direct_delete=False)

        violations = validate_catalog(catalog, policy)

        assert len(violations) == 1
        assert violations[0].violation_type == "disallowed_method"
        assert violations[0].rule == "DELETE"

    def test_direct_patch_violation(self):
        """Test that DIRECT PATCH operations are flagged."""
        endpoints = [
            Endpoint("patch_user_detail", "PATCH", "/users/{id}", "Patch", Tier.DIRECT),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(allow_direct_patch=False)

        violations = validate_catalog(catalog, policy)

        assert len(violations) == 1
        assert violations[0].violation_type == "disallowed_method"
        assert violations[0].rule == "PATCH"

    def test_mandatory_gateway_violation(self):
        """Test that mandatory_gateway paths as DIRECT are flagged."""
        endpoints = [
            Endpoint("post_role_list", "POST", "/rbac/roles", "Create role", Tier.DIRECT),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(
            mandatory_gateway=["/rbac/roles/*", "/rbac/roles"],
        )

        violations = validate_catalog(catalog, policy)

        assert len(violations) >= 1
        mandatory_violations = [v for v in violations if v.violation_type == "mandatory_gateway"]
        assert len(mandatory_violations) >= 1

    def test_mandatory_exclude_violation(self):
        """Test that mandatory_exclude paths that are exposed are flagged."""
        endpoints = [
            Endpoint("get_health_live", "GET", "/health/live", "Liveness", Tier.DIRECT),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(mandatory_exclude=["/health/*"])

        violations = validate_catalog(catalog, policy)

        assert len(violations) >= 1
        exclude_violations = [v for v in violations if v.violation_type == "mandatory_exclude"]
        assert len(exclude_violations) >= 1

    def test_allow_direct_delete_flag(self):
        """Test that allow_direct_delete=True allows DELETE as DIRECT."""
        endpoints = [
            Endpoint("delete_api_key", "DELETE", "/api-keys/{id}", "Delete", Tier.DIRECT),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(allow_direct_delete=True)

        violations = validate_catalog(catalog, policy)

        # Should not have a disallowed_method violation
        method_violations = [v for v in violations if v.violation_type == "disallowed_method"]
        assert len(method_violations) == 0

    def test_multiple_violations(self):
        """Test that multiple violations are all reported."""
        endpoints = [
            Endpoint("delete_user", "DELETE", "/users/{id}", "Delete", Tier.DIRECT),
            Endpoint("post_role", "POST", "/rbac/roles", "Create role", Tier.DIRECT),
            Endpoint("get_health", "GET", "/health/live", "Health", Tier.DIRECT),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(
            mandatory_gateway=["/rbac/roles"],
            mandatory_exclude=["/health/*"],
            allow_direct_delete=False,
        )

        violations = validate_catalog(catalog, policy)

        # Should have at least 3 violations
        assert len(violations) >= 3


class TestPolicyViolation:
    """Tests for PolicyViolation class."""

    def test_violation_string_representation(self):
        """Test that violations have readable string representation."""
        violation = PolicyViolation(
            endpoint_name="delete_user_detail",
            violation_type="disallowed_method",
            rule="DELETE",
            message="DELETE operations should not be DIRECT",
        )

        str_repr = str(violation)
        assert "delete_user_detail" in str_repr
        assert "disallowed_method" in str_repr
        assert "DELETE" in str_repr


class TestPolicyViolationError:
    """Tests for PolicyViolationError exception."""

    def test_error_message_includes_count(self):
        """Test that error message includes violation count."""
        violations = [
            PolicyViolation("ep1", "type1", "rule1", "message1"),
            PolicyViolation("ep2", "type2", "rule2", "message2"),
        ]
        error = PolicyViolationError(violations)

        assert "2 violations" in str(error)

    def test_error_stores_violations(self):
        """Test that error stores violations for programmatic access."""
        violations = [
            PolicyViolation("ep1", "type1", "rule1", "message1"),
        ]
        error = PolicyViolationError(violations)

        assert len(error.violations) == 1
        assert error.violations[0].endpoint_name == "ep1"


class TestPathMatching:
    """Tests for path pattern matching."""

    def test_glob_pattern_matching(self):
        """Test that glob patterns work correctly."""
        endpoints = [
            Endpoint("get_health_live", "GET", "/health/live", "Health", Tier.DIRECT),
            Endpoint("get_health_ready", "GET", "/health/ready", "Health", Tier.DIRECT),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(mandatory_exclude=["/health/*"])

        violations = validate_catalog(catalog, policy)

        # Both health endpoints should be flagged
        assert len(violations) == 2

    def test_contains_pattern_matching(self):
        """Test that contains-style patterns work."""
        endpoints = [
            Endpoint("put_password", "PUT", "/users/{id}/password", "Password", Tier.DIRECT),
        ]
        catalog = ServiceCatalog(endpoints)
        policy = CatalogPolicy(mandatory_gateway=["*/password*"])

        violations = validate_catalog(catalog, policy)

        assert len(violations) >= 1
