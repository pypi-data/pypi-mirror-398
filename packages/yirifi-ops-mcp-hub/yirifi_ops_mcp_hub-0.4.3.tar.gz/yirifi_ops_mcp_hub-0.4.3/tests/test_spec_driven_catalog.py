"""Tests for SpecDrivenCatalog."""

import pytest

from yirifi_mcp.catalog.base import Tier
from yirifi_mcp.catalog.spec_driven import SpecDrivenCatalog


# Sample OpenAPI spec for testing
SAMPLE_SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {
                "operationId": "get_user_list",
                "summary": "List all users",
                "tags": ["users"],
            },
            "post": {
                "operationId": "post_user_list",
                "summary": "Create a new user",
                "tags": ["users"],
            },
        },
        "/users/{user_id}": {
            "get": {
                "operationId": "get_user_detail",
                "summary": "Get user by ID",
                "tags": ["users"],
            },
            "delete": {
                "operationId": "delete_user_detail",
                "summary": "Delete a user",
                "tags": ["users"],
            },
        },
        "/health/live": {
            "get": {
                "operationId": "get_health_live",
                "summary": "Liveness probe",
                "tags": ["health"],
            },
        },
    },
}


# Sample spec with x-mcp-* extensions
SPEC_WITH_EXTENSIONS = {
    "openapi": "3.0.3",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {
                "operationId": "get_user_list",
                "summary": "List all users with pagination",
                "x-mcp-tier": "direct",
                "x-mcp-risk-level": "low",
                "x-mcp-name": "list_users",
                "x-mcp-description": "List all users",
            },
            "post": {
                "operationId": "post_user_list",
                "summary": "Create a new user",
                "x-mcp-tier": "direct",
                "x-mcp-risk-level": "medium",
            },
        },
        "/users/{user_id}": {
            "delete": {
                "operationId": "delete_user_detail",
                "summary": "Delete a user",
                "x-mcp-tier": "gateway",
                "x-mcp-risk-level": "high",
                "x-mcp-description": "Permanently delete a user",
            },
        },
        "/health/live": {
            "get": {
                "operationId": "get_health_live",
                "summary": "Liveness probe",
                "x-mcp-tier": "exclude",
            },
        },
    },
}


class TestSpecDrivenCatalog:
    """Tests for SpecDrivenCatalog initialization and parsing."""

    def test_creates_catalog_from_spec(self):
        """Test that catalog is created from OpenAPI spec."""
        catalog = SpecDrivenCatalog(SAMPLE_SPEC)

        # Should have 4 endpoints (health excluded by default in exclude_patterns)
        assert len(catalog.get_all_endpoints()) >= 4

    def test_default_tier_is_gateway(self):
        """Test that default tier is GATEWAY for safety."""
        catalog = SpecDrivenCatalog(SAMPLE_SPEC)

        # Without overrides, all endpoints should be GATEWAY
        for endpoint in catalog.get_all_endpoints():
            assert endpoint.tier == Tier.GATEWAY

    def test_tier_overrides_applied(self):
        """Test that tier overrides are correctly applied."""
        tier_overrides = {
            "get_user_list": Tier.DIRECT,
            "get_user_detail": Tier.DIRECT,
        }
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, tier_overrides=tier_overrides)

        # Check direct endpoints
        direct = {e.name for e in catalog.get_direct_endpoints()}
        assert "get_user_list" in direct
        assert "get_user_detail" in direct

        # Check gateway endpoints
        gateway = {e.name for e in catalog.get_gateway_endpoints()}
        assert "post_user_list" in gateway
        assert "delete_user_detail" in gateway

    def test_risk_overrides_applied(self):
        """Test that risk level overrides are correctly applied."""
        risk_overrides = {"delete_user_detail": "high"}
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, risk_overrides=risk_overrides)

        endpoint = catalog.get_endpoint("delete_user_detail")
        assert endpoint is not None
        assert endpoint.risk_level == "high"

    def test_exclude_patterns_filter_paths(self):
        """Test that exclude patterns filter out matching paths."""
        exclude_patterns = [r"^/health/.*"]
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, exclude_patterns=exclude_patterns)

        # Health endpoints should be excluded
        names = {e.name for e in catalog.get_all_endpoints()}
        assert "get_health_live" not in names

    def test_idempotent_auto_detection(self):
        """Test that idempotency is auto-detected from HTTP method."""
        catalog = SpecDrivenCatalog(SAMPLE_SPEC)

        # GET, PUT, DELETE should be idempotent
        get_endpoint = catalog.get_endpoint("get_user_list")
        assert get_endpoint is not None
        assert get_endpoint.idempotent is True

        delete_endpoint = catalog.get_endpoint("delete_user_detail")
        assert delete_endpoint is not None
        assert delete_endpoint.idempotent is True

        # POST should not be idempotent
        post_endpoint = catalog.get_endpoint("post_user_list")
        assert post_endpoint is not None
        assert post_endpoint.idempotent is False

    def test_idempotent_override(self):
        """Test that idempotency can be overridden."""
        idempotent_overrides = {"post_user_list": True}  # POST that is idempotent
        catalog = SpecDrivenCatalog(
            SAMPLE_SPEC, idempotent_overrides=idempotent_overrides
        )

        endpoint = catalog.get_endpoint("post_user_list")
        assert endpoint is not None
        assert endpoint.idempotent is True


class TestXMcpExtensions:
    """Tests for x-mcp-* OpenAPI extension parsing."""

    def test_x_mcp_tier_parsed(self):
        """Test that x-mcp-tier extension is parsed."""
        catalog = SpecDrivenCatalog(SPEC_WITH_EXTENSIONS)

        # Direct from extension
        # Note: get_user_list is renamed to list_users via x-mcp-name
        direct = {e.name for e in catalog.get_direct_endpoints()}
        assert "list_users" in direct  # Renamed via x-mcp-name
        assert "post_user_list" in direct

        # Gateway from extension
        gateway = {e.name for e in catalog.get_gateway_endpoints()}
        assert "delete_user_detail" in gateway

        # Exclude from extension
        all_names = {e.name for e in catalog.get_all_endpoints()}
        assert "get_health_live" not in all_names

    def test_x_mcp_risk_level_parsed(self):
        """Test that x-mcp-risk-level extension is parsed."""
        catalog = SpecDrivenCatalog(SPEC_WITH_EXTENSIONS)

        # Note: get_user_list is renamed to list_users via x-mcp-name
        get_endpoint = catalog.get_endpoint("list_users")
        assert get_endpoint is not None
        assert get_endpoint.risk_level == "low"

        delete_endpoint = catalog.get_endpoint("delete_user_detail")
        assert delete_endpoint is not None
        assert delete_endpoint.risk_level == "high"

    def test_x_mcp_name_parsed(self):
        """Test that x-mcp-name extension overrides operationId."""
        catalog = SpecDrivenCatalog(SPEC_WITH_EXTENSIONS)

        # The name should be from x-mcp-name, not operationId
        endpoint = catalog.get_endpoint("list_users")
        assert endpoint is not None
        assert endpoint.name == "list_users"

    def test_x_mcp_description_parsed(self):
        """Test that x-mcp-description extension overrides summary."""
        catalog = SpecDrivenCatalog(SPEC_WITH_EXTENSIONS)

        endpoint = catalog.get_endpoint("list_users")
        assert endpoint is not None
        assert endpoint.description == "List all users"

        # Without x-mcp-description, should use summary
        post_endpoint = catalog.get_endpoint("post_user_list")
        assert post_endpoint is not None
        assert post_endpoint.description == "Create a new user"

    def test_extension_priority_over_overrides(self):
        """Test that x-mcp-* extensions take priority over override files."""
        # Override says DIRECT, but extension says GATEWAY
        tier_overrides = {"delete_user_detail": Tier.DIRECT}
        catalog = SpecDrivenCatalog(
            SPEC_WITH_EXTENSIONS, tier_overrides=tier_overrides
        )

        # Extension should win
        endpoint = catalog.get_endpoint("delete_user_detail")
        assert endpoint is not None
        assert endpoint.tier == Tier.GATEWAY


class TestCatalogInterface:
    """Tests for catalog interface methods."""

    def test_to_route_maps(self):
        """Test route map generation for DIRECT endpoints."""
        tier_overrides = {"get_user_list": Tier.DIRECT}
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, tier_overrides=tier_overrides)

        route_maps = catalog.to_route_maps()

        # Should have at least one route map for DIRECT endpoint
        # Plus catch-all exclusion at the end
        assert len(route_maps) >= 2

        # Last one should be catch-all exclusion
        from yirifi_mcp.core.route_filters import MCPType
        assert route_maps[-1].mcp_type == MCPType.EXCLUDE
        assert route_maps[-1].pattern == r".*"

    def test_to_gateway_catalog(self):
        """Test gateway catalog generation."""
        tier_overrides = {"get_user_list": Tier.DIRECT}
        risk_overrides = {"delete_user_detail": "high"}
        catalog = SpecDrivenCatalog(
            SAMPLE_SPEC,
            tier_overrides=tier_overrides,
            risk_overrides=risk_overrides,
        )

        gateway_catalog = catalog.to_gateway_catalog()

        # Should include all non-excluded endpoints
        assert "get_user_list" in gateway_catalog
        assert "delete_user_detail" in gateway_catalog

        # Check structure
        entry = gateway_catalog["delete_user_detail"]
        assert entry["method"] == "DELETE"
        assert entry["path"] == "/users/{user_id}"
        assert entry["risk_level"] == "high"

    def test_get_stats(self):
        """Test statistics generation."""
        tier_overrides = {"get_user_list": Tier.DIRECT, "get_user_detail": Tier.DIRECT}
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, tier_overrides=tier_overrides)

        stats = catalog.get_stats()

        assert stats["direct"] == 2
        assert stats["gateway"] >= 2  # post_user_list, delete_user_detail
        assert "tier_overrides" in stats
        assert stats["tier_overrides"] == 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_spec(self):
        """Test handling of empty OpenAPI spec."""
        empty_spec = {"openapi": "3.0.3", "info": {"title": "Empty", "version": "1.0.0"}, "paths": {}}
        catalog = SpecDrivenCatalog(empty_spec)

        assert len(catalog.get_all_endpoints()) == 0
        assert catalog.direct_count == 0
        assert catalog.gateway_count == 0

    def test_missing_operation_id(self):
        """Test handling of operations without operationId."""
        spec_without_id = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {"summary": "List items"},  # No operationId
                }
            },
        }
        catalog = SpecDrivenCatalog(spec_without_id)

        # Should generate an operation ID
        endpoints = catalog.get_all_endpoints()
        assert len(endpoints) == 1
        assert endpoints[0].name == "get_items"

    def test_invalid_tier_extension_ignored(self):
        """Test that invalid x-mcp-tier values are ignored."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "operationId": "get_items",
                        "x-mcp-tier": "invalid_tier",  # Invalid value
                    }
                }
            },
        }
        catalog = SpecDrivenCatalog(spec)

        # Should fall back to default tier
        endpoint = catalog.get_endpoint("get_items")
        assert endpoint is not None
        assert endpoint.tier == Tier.GATEWAY

    def test_invalid_risk_level_extension_ignored(self):
        """Test that invalid x-mcp-risk-level values are ignored."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "operationId": "get_items",
                        "x-mcp-risk-level": "critical",  # Invalid - should be low/medium/high
                    }
                }
            },
        }
        catalog = SpecDrivenCatalog(spec)

        # Should fall back to default risk level
        endpoint = catalog.get_endpoint("get_items")
        assert endpoint is not None
        assert endpoint.risk_level == "medium"


class TestXMcpTagsExtension:
    """Tests for x-mcp-tags OpenAPI extension parsing."""

    def test_x_mcp_tags_parsed(self):
        """Test that x-mcp-tags extension overrides OpenAPI tags."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "operationId": "get_items",
                        "tags": ["items", "crud"],
                        "x-mcp-tags": ["custom", "mcp-specific"],
                    }
                }
            },
        }
        catalog = SpecDrivenCatalog(spec)

        endpoint = catalog.get_endpoint("get_items")
        assert endpoint is not None
        assert endpoint.tags == ["custom", "mcp-specific"]

    def test_openapi_tags_used_without_x_mcp_tags(self):
        """Test that OpenAPI tags are used when x-mcp-tags is not present."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "operationId": "get_items",
                        "tags": ["items", "crud"],
                    }
                }
            },
        }
        catalog = SpecDrivenCatalog(spec)

        endpoint = catalog.get_endpoint("get_items")
        assert endpoint is not None
        assert endpoint.tags == ["items", "crud"]

    def test_empty_tags_when_none_specified(self):
        """Test that tags default to empty list when none specified."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "operationId": "get_items",
                    }
                }
            },
        }
        catalog = SpecDrivenCatalog(spec)

        endpoint = catalog.get_endpoint("get_items")
        assert endpoint is not None
        assert endpoint.tags == []


class TestXMcpIdempotentExtension:
    """Tests for x-mcp-idempotent OpenAPI extension parsing."""

    def test_x_mcp_idempotent_true_on_post(self):
        """Test that x-mcp-idempotent=true makes POST idempotent."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "post": {
                        "operationId": "post_items",
                        "x-mcp-idempotent": True,  # Upsert-style POST
                    }
                }
            },
        }
        catalog = SpecDrivenCatalog(spec)

        endpoint = catalog.get_endpoint("post_items")
        assert endpoint is not None
        assert endpoint.idempotent is True

    def test_x_mcp_idempotent_false_on_get(self):
        """Test that x-mcp-idempotent=false overrides auto-detection."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/random": {
                    "get": {
                        "operationId": "get_random",
                        "summary": "Get random data",
                        "x-mcp-idempotent": False,  # Non-idempotent GET (e.g., returns random data)
                    }
                }
            },
        }
        catalog = SpecDrivenCatalog(spec)

        endpoint = catalog.get_endpoint("get_random")
        assert endpoint is not None
        assert endpoint.idempotent is False

    def test_x_mcp_idempotent_priority_over_override(self):
        """Test that x-mcp-idempotent takes priority over idempotent_overrides."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "post": {
                        "operationId": "post_items",
                        "x-mcp-idempotent": True,  # Extension says idempotent
                    }
                }
            },
        }
        # Override says non-idempotent
        idempotent_overrides = {"post_items": False}
        catalog = SpecDrivenCatalog(spec, idempotent_overrides=idempotent_overrides)

        # Extension should win
        endpoint = catalog.get_endpoint("post_items")
        assert endpoint is not None
        assert endpoint.idempotent is True


class TestOverrideFiles:
    """Tests for name/description override files (not x-mcp-* extensions)."""

    def test_name_overrides_applied(self):
        """Test that name overrides change endpoint names."""
        name_overrides = {"get_user_list": "list_all_users"}
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, name_overrides=name_overrides)

        # Old name should not exist
        assert catalog.get_endpoint("get_user_list") is None

        # New name should exist
        endpoint = catalog.get_endpoint("list_all_users")
        assert endpoint is not None
        assert endpoint.name == "list_all_users"

    def test_description_overrides_applied(self):
        """Test that description overrides change endpoint descriptions."""
        description_overrides = {"get_user_list": "Fetch all users with pagination support"}
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, description_overrides=description_overrides)

        endpoint = catalog.get_endpoint("get_user_list")
        assert endpoint is not None
        assert endpoint.description == "Fetch all users with pagination support"

    def test_x_mcp_name_priority_over_name_override(self):
        """Test that x-mcp-name takes priority over name_overrides."""
        # Spec has x-mcp-name: list_users
        name_overrides = {"get_user_list": "different_name"}
        catalog = SpecDrivenCatalog(SPEC_WITH_EXTENSIONS, name_overrides=name_overrides)

        # x-mcp-name should win
        endpoint = catalog.get_endpoint("list_users")
        assert endpoint is not None
        assert endpoint.name == "list_users"

    def test_x_mcp_description_priority_over_description_override(self):
        """Test that x-mcp-description takes priority over description_overrides."""
        # Spec has x-mcp-description: "List all users"
        description_overrides = {"get_user_list": "A different description"}
        catalog = SpecDrivenCatalog(SPEC_WITH_EXTENSIONS, description_overrides=description_overrides)

        # x-mcp-description should win (note: endpoint is renamed to list_users)
        endpoint = catalog.get_endpoint("list_users")
        assert endpoint is not None
        assert endpoint.description == "List all users"


class TestDefaultParameters:
    """Tests for default parameter handling."""

    def test_default_risk_level_parameter(self):
        """Test that default_risk_level parameter is applied."""
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, default_risk_level="low")

        # All endpoints should have "low" risk level (unless overridden)
        for endpoint in catalog.get_all_endpoints():
            assert endpoint.risk_level == "low"

    def test_default_tier_parameter(self):
        """Test that default_tier parameter is applied."""
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, default_tier=Tier.DIRECT)

        # All endpoints should be DIRECT (unless overridden)
        for endpoint in catalog.get_all_endpoints():
            assert endpoint.tier == Tier.DIRECT

    def test_stats_include_all_override_types(self):
        """Test that stats include counts for all override types."""
        catalog = SpecDrivenCatalog(
            SAMPLE_SPEC,
            tier_overrides={"get_user_list": Tier.DIRECT},
            risk_overrides={"delete_user_detail": "high"},
            name_overrides={"post_user_list": "create_user"},
            description_overrides={"get_user_detail": "Get single user"},
            exclude_patterns=[r"^/health/.*"],
        )

        stats = catalog.get_stats()

        assert stats["tier_overrides"] == 1
        assert stats["risk_overrides"] == 1
        assert stats["name_overrides"] == 1
        assert stats["description_overrides"] == 1
        assert stats["exclude_patterns"] == 1


class TestSpecProperties:
    """Tests for SpecDrivenCatalog properties."""

    def test_spec_property_returns_original_spec(self):
        """Test that spec property returns the original OpenAPI spec."""
        catalog = SpecDrivenCatalog(SAMPLE_SPEC)

        assert catalog.spec == SAMPLE_SPEC
        assert catalog.spec["info"]["title"] == "Test API"

    def test_default_tier_property(self):
        """Test that default_tier property returns configured default."""
        catalog = SpecDrivenCatalog(SAMPLE_SPEC, default_tier=Tier.DIRECT)

        assert catalog.default_tier == Tier.DIRECT

    def test_repr_format(self):
        """Test that __repr__ returns useful information."""
        catalog = SpecDrivenCatalog(
            SAMPLE_SPEC,
            tier_overrides={"get_user_list": Tier.DIRECT},
        )

        repr_str = repr(catalog)
        assert "SpecDrivenCatalog" in repr_str
        assert "direct=" in repr_str
        assert "gateway=" in repr_str
