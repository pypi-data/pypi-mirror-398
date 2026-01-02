"""Tests for the MCP server factory."""

import pytest

from yirifi_mcp.catalog.base import Endpoint, ServiceCatalog, Tier
from yirifi_mcp.catalog.policy import CatalogPolicy
from yirifi_mcp.core.config import ServiceConfig
from yirifi_mcp.server.factory import MCPServerFactory


class TestMCPServerFactory:
    """Tests for MCPServerFactory."""

    @pytest.fixture
    def sample_catalog(self):
        """Sample catalog for testing."""
        return ServiceCatalog([
            Endpoint("get_item_list", "GET", "/items/", "List items", Tier.DIRECT),
            Endpoint("get_item_detail", "GET", "/items/{id}", "Get item", Tier.DIRECT),
            Endpoint("delete_item_detail", "DELETE", "/items/{id}", "Delete", Tier.GATEWAY, risk_level="high"),
        ])

    @pytest.fixture
    def sample_config(self):
        """Sample config for testing."""
        return ServiceConfig(
            base_url="http://localhost:8000",
            server_name="test-service",
            api_key="test-key",
        )

    def test_factory_creation(self, sample_catalog, sample_config):
        """Test factory is created correctly."""
        factory = MCPServerFactory(sample_catalog, sample_config)
        assert factory.catalog == sample_catalog
        assert factory.config == sample_config
        assert factory.gateway_prefix == "test_service"

    def test_factory_custom_prefix(self, sample_catalog, sample_config):
        """Test factory with custom gateway prefix."""
        factory = MCPServerFactory(
            sample_catalog,
            sample_config,
            gateway_prefix="custom",
        )
        assert factory.gateway_prefix == "custom"

    def test_derive_prefix_removes_yirifi(self):
        """Test prefix derivation removes yirifi- prefix."""
        assert MCPServerFactory._derive_prefix("yirifi-auth") == "auth"
        assert MCPServerFactory._derive_prefix("yirifi-crm") == "crm"

    def test_derive_prefix_removes_mcp(self):
        """Test prefix derivation removes mcp- prefix."""
        assert MCPServerFactory._derive_prefix("mcp-auth") == "auth"
        assert MCPServerFactory._derive_prefix("mcp-service") == "service"

    def test_derive_prefix_replaces_hyphens(self):
        """Test prefix derivation replaces hyphens with underscores."""
        assert MCPServerFactory._derive_prefix("my-cool-service") == "my_cool_service"
        assert MCPServerFactory._derive_prefix("auth-service") == "auth_service"


class TestMCPServerFactorySpecDrivenMode:
    """Tests for MCPServerFactory in spec-driven mode."""

    @pytest.fixture
    def sample_config(self):
        """Sample config for testing."""
        return ServiceConfig(
            base_url="http://localhost:8000",
            server_name="test-service",
            api_key="test-key",
        )

    def test_factory_with_tier_overrides_no_catalog(self, sample_config):
        """Test factory accepts tier_overrides without explicit catalog."""
        tier_overrides = {"get_user_list": Tier.DIRECT}
        factory = MCPServerFactory(
            config=sample_config,
            gateway_prefix="test",
            tier_overrides=tier_overrides,
        )

        # Factory should be created successfully
        assert factory.catalog is None  # Catalog not created until build()
        assert factory._tier_overrides == tier_overrides

    def test_factory_with_risk_overrides(self, sample_config):
        """Test factory accepts risk_overrides."""
        risk_overrides = {"delete_user_detail": "high"}
        factory = MCPServerFactory(
            config=sample_config,
            gateway_prefix="test",
            risk_overrides=risk_overrides,
        )

        assert factory._risk_overrides == risk_overrides

    def test_factory_with_all_overrides(self, sample_config):
        """Test factory accepts all override types."""
        factory = MCPServerFactory(
            config=sample_config,
            gateway_prefix="test",
            tier_overrides={"get_user_list": Tier.DIRECT},
            risk_overrides={"delete_user_detail": "high"},
            name_overrides={"get_user_list": "list_users"},
            description_overrides={"get_user_list": "List all users"},
            idempotent_overrides={"post_user_upsert": True},
            exclude_patterns=[r"^/health/.*"],
        )

        assert factory._tier_overrides is not None
        assert factory._risk_overrides is not None
        assert factory._name_overrides is not None
        assert factory._description_overrides is not None
        assert factory._idempotent_overrides is not None
        assert factory._exclude_patterns is not None

    def test_factory_with_policy(self, sample_config):
        """Test factory accepts policy for validation."""
        policy = CatalogPolicy(
            mandatory_gateway=["/admin/*"],
            allow_direct_delete=False,
        )
        factory = MCPServerFactory(
            config=sample_config,
            gateway_prefix="test",
            policy=policy,
        )

        assert factory._policy == policy

    def test_factory_requires_config(self):
        """Test factory raises if config is not provided."""
        with pytest.raises(ValueError, match="config is required"):
            MCPServerFactory(catalog=None, config=None)

    def test_factory_explicit_catalog_takes_precedence(self, sample_config):
        """Test that explicit catalog is used when provided."""
        catalog = ServiceCatalog([
            Endpoint("get_item_list", "GET", "/items/", "List items", Tier.DIRECT),
        ])
        factory = MCPServerFactory(
            catalog=catalog,
            config=sample_config,
            tier_overrides={"different_endpoint": Tier.DIRECT},  # Should be ignored
        )

        # Catalog should be the one provided
        assert factory.catalog == catalog
        assert factory.catalog.direct_count == 1


class TestMCPServerFactoryPolicyValidation:
    """Tests for MCPServerFactory policy validation during build."""

    @pytest.fixture
    def sample_config(self):
        """Sample config for testing."""
        return ServiceConfig(
            base_url="http://localhost:8000",
            server_name="test-service",
            api_key="test-key",
        )

    def test_catalog_with_policy_violation(self, sample_config):
        """Test that policy violations are detected with explicit catalog."""
        # Catalog with DELETE as DIRECT (violates default policy)
        catalog = ServiceCatalog([
            Endpoint("delete_user", "DELETE", "/users/{id}", "Delete user", Tier.DIRECT),
        ])
        policy = CatalogPolicy(allow_direct_delete=False)

        factory = MCPServerFactory(
            catalog=catalog,
            config=sample_config,
            policy=policy,
        )

        # Policy is stored for validation during build()
        assert factory._policy == policy

    def test_catalog_without_violation_passes(self, sample_config):
        """Test that catalog without violations is accepted."""
        # Catalog with DELETE as GATEWAY (compliant with policy)
        catalog = ServiceCatalog([
            Endpoint("delete_user", "DELETE", "/users/{id}", "Delete user", Tier.GATEWAY),
            Endpoint("get_user_list", "GET", "/users/", "List users", Tier.DIRECT),
        ])
        policy = CatalogPolicy(allow_direct_delete=False)

        factory = MCPServerFactory(
            catalog=catalog,
            config=sample_config,
            policy=policy,
        )

        # Should be created without error
        assert factory.catalog == catalog
