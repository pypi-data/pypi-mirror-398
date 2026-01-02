"""Tests for core utilities."""

import pytest

from yirifi_mcp.core.http_client import (
    create_passthrough_client,
    create_unauthenticated_client,
)
from yirifi_mcp.core.openapi_utils import patch_openapi_spec, get_spec_info
from yirifi_mcp.core.route_filters import (
    RouteMap,
    MCPType,
    should_exclude_route,
    filter_openapi_paths,
    STANDARD_EXCLUSIONS,
)


class TestHttpClient:
    """Tests for HTTP client factory."""

    def test_passthrough_client_has_json_headers(self):
        """Test that passthrough client has JSON content headers."""
        client = create_passthrough_client(base_url="http://localhost:5000")
        assert client.headers["Accept"] == "application/json"
        assert client.headers["Content-Type"] == "application/json"

    def test_unauthenticated_client_has_json_headers(self):
        """Test that unauthenticated client has JSON content headers."""
        client = create_unauthenticated_client(base_url="http://localhost:5000")
        assert client.headers["Accept"] == "application/json"
        assert client.headers["Content-Type"] == "application/json"

    def test_passthrough_client_custom_timeout(self):
        """Test that custom timeouts are applied."""
        client = create_passthrough_client(
            base_url="http://localhost:5000",
            timeout=60.0,
            connect_timeout=5.0,
        )
        assert client.timeout.read == 60.0
        assert client.timeout.connect == 5.0

    def test_unauthenticated_client_follows_redirects(self):
        """Test that unauthenticated client follows redirects."""
        client = create_unauthenticated_client(base_url="http://localhost:5000")
        assert client.follow_redirects is True


class TestOpenAPIUtils:
    """Tests for OpenAPI utilities."""

    def test_patch_swagger_spec_converts_to_openapi3(self, sample_openapi_spec):
        """Test that Swagger 2.0 spec is converted to OpenAPI 3.0."""
        patched = patch_openapi_spec(sample_openapi_spec, "http://api.example.com")

        # Should be converted to OpenAPI 3.0
        assert patched["openapi"] == "3.0.3"
        assert "servers" in patched
        assert patched["servers"][0]["url"] == "http://api.example.com/api/v1"

    def test_patch_swagger_spec_https(self, sample_openapi_spec):
        """Test patching with HTTPS URL."""
        patched = patch_openapi_spec(sample_openapi_spec, "https://api.example.com")

        # Should use HTTPS in server URL
        assert "https://" in patched["servers"][0]["url"]

    def test_get_spec_info(self, sample_openapi_spec):
        """Test extracting spec info."""
        info = get_spec_info(sample_openapi_spec)

        assert info["title"] == "Test API"
        assert info["version"] == "1.0"
        assert info["paths_count"] == 5
        assert info["endpoints_count"] == 6


class TestRouteFilters:
    """Tests for route filtering."""

    def test_route_map_matches_pattern(self):
        """Test RouteMap pattern matching."""
        route_map = RouteMap(pattern=r".*/health.*", mcp_type=MCPType.EXCLUDE)

        assert route_map.matches("/api/v1/health/live")
        assert route_map.matches("/health")
        assert not route_map.matches("/api/v1/users")

    def test_route_map_matches_method(self):
        """Test RouteMap method matching."""
        route_map = RouteMap(
            pattern=r".*",
            methods=["GET"],
            mcp_type=MCPType.TOOL,
        )

        assert route_map.matches("/users", "GET")
        assert not route_map.matches("/users", "POST")

    def test_should_exclude_health_routes(self):
        """Test that health routes are excluded."""
        assert should_exclude_route(
            "/api/v1/health/live",
            "GET",
            STANDARD_EXCLUSIONS,
        )

    def test_should_exclude_docs_routes(self):
        """Test that docs routes are excluded."""
        assert should_exclude_route(
            "/api/v1/docs",
            "GET",
            STANDARD_EXCLUSIONS,
        )

    def test_should_not_exclude_api_routes(self):
        """Test that regular API routes are not excluded."""
        assert not should_exclude_route(
            "/api/v1/users",
            "GET",
            STANDARD_EXCLUSIONS,
        )

    def test_filter_openapi_paths(self, sample_openapi_spec):
        """Test filtering OpenAPI paths with allow-list approach."""
        # filter_openapi_paths uses first-match-wins, only includes if matched as TOOL
        # Create a route map that allows users and auth, excludes everything else
        route_maps = [
            RouteMap(pattern=r"^/users/.*", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/users/$", methods=["GET", "POST"], mcp_type=MCPType.TOOL),
            RouteMap(pattern=r"^/auth/.*", mcp_type=MCPType.TOOL),
            RouteMap(pattern=r".*", mcp_type=MCPType.EXCLUDE),  # Catch-all
        ]
        filtered = filter_openapi_paths(sample_openapi_spec, route_maps)

        paths = filtered["paths"]
        assert "/health/live" not in paths  # Excluded by catch-all
        assert "/docs" not in paths  # Excluded by catch-all
        assert "/users/" in paths  # Allowed by route map
        assert "/auth/login" in paths  # Allowed by route map
