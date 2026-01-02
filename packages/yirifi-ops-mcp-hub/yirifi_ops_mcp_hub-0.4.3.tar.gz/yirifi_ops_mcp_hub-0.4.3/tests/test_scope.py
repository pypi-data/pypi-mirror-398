"""Tests for service scope registry and MCP scope middleware."""

import pytest

from yirifi_mcp.catalog.base import Endpoint, ServiceCatalog, Tier
from yirifi_mcp.core.scope import (
    ScopeRegistry,
    build_default_registry,
    current_scope_tools,
    get_current_scope_tools,
    get_default_registry,
    set_current_scope_tools,
)
from yirifi_mcp.core.scope_middleware import (
    MCP_PROTOCOL_PATHS,
    SERVICE_PATH_PATTERN,
    _normalize_path,
    _parse_scope_from_path,
)


# =============================================================================
# ScopeRegistry Tests
# =============================================================================


class TestScopeRegistry:
    """Tests for the ScopeRegistry class."""

    @pytest.fixture
    def empty_registry(self):
        """Create an empty registry."""
        return ScopeRegistry()

    @pytest.fixture
    def sample_catalog(self):
        """Create a sample catalog for testing."""
        return ServiceCatalog(
            [
                Endpoint("get_user_list", "GET", "/users/", "List users", Tier.DIRECT),
                Endpoint("get_user_detail", "GET", "/users/{id}", "Get user", Tier.DIRECT),
                Endpoint("delete_user", "DELETE", "/users/{id}", "Delete", Tier.GATEWAY),
                Endpoint("health_check", "GET", "/health", "Health", Tier.EXCLUDE),
            ]
        )

    def test_empty_registry(self, empty_registry):
        """Empty registry should have no services or tools."""
        assert empty_registry.get_registered_services() == []
        assert empty_registry.get_all_tools() == set()

    def test_register_service(self, empty_registry, sample_catalog):
        """Registering a service should add its tools."""
        empty_registry.register_service("test", sample_catalog)

        assert "test" in empty_registry
        services = empty_registry.get_registered_services()
        assert "test" in services

    def test_registered_tools_include_direct_and_gateway(self, empty_registry, sample_catalog):
        """Registered tools should include DIRECT and GATEWAY endpoints."""
        empty_registry.register_service("test", sample_catalog)

        tools = empty_registry.get_tools_for_scope(["test"])
        assert "get_user_list" in tools
        assert "get_user_detail" in tools
        assert "delete_user" in tools  # GATEWAY tier included
        assert "health_check" not in tools  # EXCLUDE tier not included

    def test_gateway_tools_added(self, empty_registry, sample_catalog):
        """Gateway tools (api_call, api_catalog, etc.) should be added."""
        empty_registry.register_service("test", sample_catalog)

        tools = empty_registry.get_tools_for_scope(["test"])
        assert "test_api_call" in tools
        assert "test_api_catalog" in tools
        assert "test_health" in tools
        assert "test_api_call_batch" in tools

    def test_get_service_for_tool(self, empty_registry, sample_catalog):
        """Should return the service that owns a tool."""
        empty_registry.register_service("test", sample_catalog)

        assert empty_registry.get_service_for_tool("get_user_list") == "test"
        assert empty_registry.get_service_for_tool("test_api_call") == "test"
        assert empty_registry.get_service_for_tool("unknown_tool") is None

    def test_multiple_services(self, empty_registry):
        """Multiple services should be isolated."""
        catalog1 = ServiceCatalog(
            [Endpoint("get_users", "GET", "/users", "Users", Tier.DIRECT)]
        )
        catalog2 = ServiceCatalog(
            [Endpoint("get_orders", "GET", "/orders", "Orders", Tier.DIRECT)]
        )

        empty_registry.register_service("users", catalog1)
        empty_registry.register_service("orders", catalog2)

        users_tools = empty_registry.get_tools_for_scope(["users"])
        orders_tools = empty_registry.get_tools_for_scope(["orders"])

        assert "get_users" in users_tools
        assert "get_users" not in orders_tools
        assert "get_orders" in orders_tools
        assert "get_orders" not in users_tools

    def test_combined_scope(self, empty_registry):
        """Should combine tools from multiple services."""
        catalog1 = ServiceCatalog(
            [Endpoint("get_users", "GET", "/users", "Users", Tier.DIRECT)]
        )
        catalog2 = ServiceCatalog(
            [Endpoint("get_orders", "GET", "/orders", "Orders", Tier.DIRECT)]
        )

        empty_registry.register_service("users", catalog1)
        empty_registry.register_service("orders", catalog2)

        combined = empty_registry.get_tools_for_scope(["users", "orders"])

        assert "get_users" in combined
        assert "get_orders" in combined
        assert "users_api_call" in combined
        assert "orders_api_call" in combined


class TestDefaultRegistry:
    """Tests for the default registry with real catalogs."""

    def test_build_default_registry(self):
        """Default registry should include auth, reg, and risk services."""
        registry = build_default_registry()

        assert "auth" in registry
        assert "reg" in registry
        assert "risk" in registry
        assert len(registry.get_registered_services()) == 3

    def test_auth_tools_registered(self):
        """Auth service tools should be registered."""
        registry = build_default_registry()
        auth_tools = registry.get_tools_for_scope(["auth"])

        # Check some known auth tools
        assert "get_user_list" in auth_tools
        assert "get_auth_me" in auth_tools
        assert "auth_api_call" in auth_tools
        assert "auth_api_catalog" in auth_tools

    def test_reg_tools_registered(self):
        """Reg service tools should be registered."""
        registry = build_default_registry()
        reg_tools = registry.get_tools_for_scope(["reg"])

        # Check some known reg tools
        assert "get_country_list" in reg_tools
        assert "get_organization_list" in reg_tools
        assert "reg_api_call" in reg_tools
        assert "reg_api_catalog" in reg_tools

    def test_risk_tools_registered(self):
        """Risk service tools should be registered."""
        registry = build_default_registry()
        risk_tools = registry.get_tools_for_scope(["risk"])

        # Check some known risk tools
        assert "get_risk_item_list" in risk_tools
        assert "get_risk_category_list" in risk_tools
        assert "get_risk_hierarchy_list" in risk_tools
        assert "risk_api_call" in risk_tools
        assert "risk_api_catalog" in risk_tools

    def test_services_are_isolated(self):
        """Auth, reg, and risk tools should not overlap."""
        registry = build_default_registry()
        auth_tools = registry.get_tools_for_scope(["auth"])
        reg_tools = registry.get_tools_for_scope(["reg"])
        risk_tools = registry.get_tools_for_scope(["risk"])

        # Auth-specific tools
        assert "get_user_list" in auth_tools
        assert "get_user_list" not in reg_tools
        assert "get_user_list" not in risk_tools

        # Reg-specific tools
        assert "get_country_list" in reg_tools
        assert "get_country_list" not in auth_tools
        assert "get_country_list" not in risk_tools

        # Risk-specific tools
        assert "get_risk_item_list" in risk_tools
        assert "get_risk_item_list" not in auth_tools
        assert "get_risk_item_list" not in reg_tools

    def test_singleton_behavior(self):
        """get_default_registry should return the same instance."""
        registry1 = get_default_registry()
        registry2 = get_default_registry()
        assert registry1 is registry2


# =============================================================================
# MCPScopeMiddleware Tests
# =============================================================================


class TestServicePathPattern:
    """Tests for the SERVICE_PATH_PATTERN regex."""

    def test_matches_single_service(self):
        """Pattern should match /mcp/auth, /mcp/reg, etc."""
        match = SERVICE_PATH_PATTERN.match("/mcp/auth")
        assert match is not None
        assert match.group(1) == "auth"

        match = SERVICE_PATH_PATTERN.match("/mcp/reg")
        assert match is not None
        assert match.group(1) == "reg"

    def test_matches_multiple_services(self):
        """Pattern should match comma-separated services."""
        match = SERVICE_PATH_PATTERN.match("/mcp/auth,reg")
        assert match is not None
        assert match.group(1) == "auth,reg"

    def test_matches_with_trailing_path(self):
        """Pattern should match with trailing path."""
        match = SERVICE_PATH_PATTERN.match("/mcp/auth/message")
        assert match is not None
        assert match.group(1) == "auth"

    def test_no_match_for_root_mcp(self):
        """Pattern should NOT match /mcp or /mcp/."""
        assert SERVICE_PATH_PATTERN.match("/mcp") is None
        assert SERVICE_PATH_PATTERN.match("/mcp/") is None

    def test_no_match_for_non_mcp_paths(self):
        """Pattern should NOT match non-MCP paths."""
        assert SERVICE_PATH_PATTERN.match("/health") is None
        assert SERVICE_PATH_PATTERN.match("/api/auth") is None

    def test_mcp_protocol_paths_defined(self):
        """MCP protocol paths should be defined for exclusion."""
        assert "message" in MCP_PROTOCOL_PATHS
        assert "sse" in MCP_PROTOCOL_PATHS
        assert "events" in MCP_PROTOCOL_PATHS


class TestPathNormalization:
    """Tests for path normalization functions."""

    def test_normalize_auth_path(self):
        """Should normalize /mcp/auth/message to /mcp/message."""
        assert _normalize_path("/mcp/auth/message") == "/mcp/message"

    def test_normalize_reg_path(self):
        """Should normalize /mcp/reg/message to /mcp/message."""
        assert _normalize_path("/mcp/reg/message") == "/mcp/message"

    def test_normalize_combined_path(self):
        """Should normalize /mcp/auth,reg/message to /mcp/message."""
        assert _normalize_path("/mcp/auth,reg/message") == "/mcp/message"

    def test_no_normalize_base_mcp(self):
        """Should NOT normalize /mcp/message (already base path)."""
        assert _normalize_path("/mcp/message") == "/mcp/message"

    def test_no_normalize_health(self):
        """Should NOT normalize non-MCP paths."""
        assert _normalize_path("/health") == "/health"

    def test_normalize_preserves_subpath(self):
        """Should preserve paths after service segment."""
        assert _normalize_path("/mcp/auth/sse") == "/mcp/sse"


class TestScopeContextVar:
    """Tests for scope ContextVar functionality."""

    def test_default_scope_is_none(self):
        """Default scope should be None (all tools allowed)."""
        assert get_current_scope_tools() is None

    def test_set_and_get_scope(self):
        """Should be able to set and get scope."""
        token = set_current_scope_tools({"tool1", "tool2"})
        try:
            assert get_current_scope_tools() == {"tool1", "tool2"}
        finally:
            current_scope_tools.reset(token)

    def test_reset_scope(self):
        """Should reset scope after token reset."""
        original = get_current_scope_tools()
        token = set_current_scope_tools({"tool1"})
        current_scope_tools.reset(token)
        assert get_current_scope_tools() == original


class TestParseScopeFromPath:
    """Tests for _parse_scope_from_path function."""

    @pytest.fixture
    def registry(self):
        """Create a test registry."""
        registry = ScopeRegistry()
        registry.register_service(
            "auth",
            ServiceCatalog(
                [
                    Endpoint("get_user_list", "GET", "/users", "Users", Tier.DIRECT),
                    Endpoint("get_auth_me", "GET", "/auth/me", "Me", Tier.DIRECT),
                ]
            ),
        )
        registry.register_service(
            "reg",
            ServiceCatalog(
                [
                    Endpoint("get_country_list", "GET", "/countries", "Countries", Tier.DIRECT),
                ]
            ),
        )
        return registry

    def test_base_path_returns_none(self, registry):
        """Base /mcp path should return None (all tools)."""
        assert _parse_scope_from_path("/mcp", registry) is None
        assert _parse_scope_from_path("/mcp/", registry) is None

    def test_message_path_returns_none(self, registry):
        """Protocol paths like /mcp/message should return None."""
        assert _parse_scope_from_path("/mcp/message", registry) is None

    def test_auth_path_returns_auth_tools(self, registry):
        """Auth path should return auth tools."""
        tools = _parse_scope_from_path("/mcp/auth/message", registry)
        assert tools is not None
        assert "get_user_list" in tools
        assert "get_auth_me" in tools
        assert "auth_api_call" in tools
        assert "get_country_list" not in tools

    def test_reg_path_returns_reg_tools(self, registry):
        """Reg path should return reg tools."""
        tools = _parse_scope_from_path("/mcp/reg/message", registry)
        assert tools is not None
        assert "get_country_list" in tools
        assert "reg_api_call" in tools
        assert "get_user_list" not in tools

    def test_combined_path_returns_both(self, registry):
        """Combined path should return both services' tools."""
        tools = _parse_scope_from_path("/mcp/auth,reg/message", registry)
        assert tools is not None
        assert "get_user_list" in tools
        assert "get_country_list" in tools

    def test_invalid_service_returns_empty_set(self, registry):
        """Invalid service should return empty set."""
        tools = _parse_scope_from_path("/mcp/invalid/message", registry)
        assert tools == set()


# Integration tests for the full scope filtering system (MCPScopeWrapper + ScopeFilterMiddleware)
# have been moved to tests/test_scope_filter_middleware.py which tests the FastMCP middleware directly.
