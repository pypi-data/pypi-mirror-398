"""Tests for the MCP server factory and registry."""

import pytest

from yirifi_mcp.catalog.base import Endpoint, ServiceCatalog, Tier
from yirifi_mcp.core.config import ServiceConfig
from yirifi_mcp.server.factory import MCPServerFactory
from yirifi_mcp.server.registry import ServiceRegistry, register_service, get_registry


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


class TestServiceRegistry:
    """Tests for ServiceRegistry."""

    @pytest.fixture
    def fresh_registry(self):
        """Create a fresh registry for testing."""
        registry = ServiceRegistry()
        # Clear any existing registrations
        registry._services.clear()
        return registry

    def test_registry_singleton(self):
        """Test that ServiceRegistry is a singleton."""
        r1 = ServiceRegistry()
        r2 = ServiceRegistry()
        assert r1 is r2

    def test_register_service(self, fresh_registry):
        """Test registering a service."""
        async def factory():
            pass

        fresh_registry.register("test", factory, description="Test service")
        assert "test" in fresh_registry
        assert len(fresh_registry) == 1

    def test_register_with_tags(self, fresh_registry):
        """Test registering a service with tags."""
        async def factory():
            pass

        fresh_registry.register("test", factory, tags=["core", "auth"])
        info = fresh_registry.get_service("test")
        assert info.tags == ["core", "auth"]

    def test_list_services(self, fresh_registry):
        """Test listing services."""
        async def factory1():
            pass

        async def factory2():
            pass

        fresh_registry.register("svc1", factory1)
        fresh_registry.register("svc2", factory2)

        services = fresh_registry.list_services()
        assert len(services) == 2

    def test_unregister_service(self, fresh_registry):
        """Test unregistering a service."""
        async def factory():
            pass

        fresh_registry.register("test", factory)
        assert fresh_registry.unregister("test") is True
        assert "test" not in fresh_registry

    def test_unregister_nonexistent(self, fresh_registry):
        """Test unregistering nonexistent service returns False."""
        assert fresh_registry.unregister("nonexistent") is False

    @pytest.mark.asyncio
    async def test_create_service(self, fresh_registry):
        """Test creating a service instance."""
        created = False

        async def factory():
            nonlocal created
            created = True
            return "mcp_instance"

        fresh_registry.register("test", factory)
        result = await fresh_registry.create("test")

        assert created is True
        assert result == "mcp_instance"

    @pytest.mark.asyncio
    async def test_create_unknown_service_raises(self, fresh_registry):
        """Test creating unknown service raises KeyError."""
        with pytest.raises(KeyError, match="Unknown service"):
            await fresh_registry.create("nonexistent")


class TestRegisterServiceDecorator:
    """Tests for @register_service decorator."""

    def test_decorator_registers_service(self):
        """Test that decorator registers the service."""
        registry = get_registry()
        original_count = len(registry)

        @register_service("decorator_test", description="Test")
        async def my_factory():
            return "instance"

        assert len(registry) == original_count + 1
        assert "decorator_test" in registry

        # Cleanup
        registry.unregister("decorator_test")

    def test_decorator_preserves_function(self):
        """Test that decorator preserves the original function."""
        @register_service("preserve_test")
        async def my_factory():
            return "preserved"

        # Function should still be callable
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(my_factory())
        assert result == "preserved"

        # Cleanup
        get_registry().unregister("preserve_test")
