"""Tests for API key passthrough middleware."""

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from yirifi_mcp.core.middleware import (
    APIKeyPassthroughMiddleware,
    CLIENT_API_KEY_HEADER,
    PUBLIC_PATHS,
    client_api_key_var,
    get_client_api_key,
)


@pytest.fixture
def app_with_middleware():
    """Create a test app with the APIKeyPassthroughMiddleware."""

    async def protected_endpoint(request):
        """Endpoint that returns the extracted API key."""
        return JSONResponse({"api_key": get_client_api_key()})

    async def health_endpoint(request):
        """Public health check endpoint."""
        return JSONResponse({"status": "ok"})

    async def health_live_endpoint(request):
        """Public liveness check endpoint."""
        return JSONResponse({"status": "live"})

    async def health_ready_endpoint(request):
        """Public readiness check endpoint."""
        return JSONResponse({"status": "ready"})

    app = Starlette(
        routes=[
            Route("/protected", protected_endpoint),
            Route("/health", health_endpoint),
            Route("/health/live", health_live_endpoint),
            Route("/health/ready", health_ready_endpoint),
        ]
    )
    app.add_middleware(APIKeyPassthroughMiddleware)
    return app


@pytest.fixture
def client(app_with_middleware):
    """Create a test client for the app."""
    return TestClient(app_with_middleware)


class TestAPIKeyExtraction:
    """Tests for API key extraction from headers."""

    def test_api_key_extracted_from_header(self, client):
        """API key should be extracted from X-API-Key header."""
        response = client.get(
            "/protected",
            headers={CLIENT_API_KEY_HEADER: "test-api-key-12345"},
        )
        assert response.status_code == 200
        assert response.json()["api_key"] == "test-api-key-12345"

    def test_api_key_with_prefix(self, client):
        """API keys with various formats should be preserved."""
        test_key = "yirifi_ops_ABC123xyz"
        response = client.get(
            "/protected",
            headers={CLIENT_API_KEY_HEADER: test_key},
        )
        assert response.status_code == 200
        assert response.json()["api_key"] == test_key

    def test_long_api_key(self, client):
        """Long API keys should be handled correctly."""
        long_key = "a" * 100
        response = client.get(
            "/protected",
            headers={CLIENT_API_KEY_HEADER: long_key},
        )
        assert response.status_code == 200
        assert response.json()["api_key"] == long_key


class TestMissingAPIKey:
    """Tests for missing API key handling."""

    def test_missing_api_key_returns_401(self, client):
        """Request without API key should return 401."""
        response = client.get("/protected")
        assert response.status_code == 401
        assert response.json()["error"] == "missing_api_key"

    def test_empty_api_key_returns_401(self, client):
        """Request with empty API key should return 401."""
        response = client.get(
            "/protected",
            headers={CLIENT_API_KEY_HEADER: ""},
        )
        assert response.status_code == 401

    def test_401_response_includes_message(self, client):
        """401 response should include helpful message."""
        response = client.get("/protected")
        assert response.status_code == 401
        json_response = response.json()
        assert "message" in json_response
        assert CLIENT_API_KEY_HEADER in json_response["message"]


class TestPublicPaths:
    """Tests for public path exemptions."""

    def test_health_endpoint_no_auth_required(self, client):
        """Health endpoint should not require authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_live_endpoint_no_auth_required(self, client):
        """Health/live endpoint should not require authentication."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "live"

    def test_health_ready_endpoint_no_auth_required(self, client):
        """Health/ready endpoint should not require authentication."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_all_public_paths_defined(self):
        """Verify all expected public paths are in PUBLIC_PATHS."""
        expected_paths = {"/health", "/health/live", "/health/ready"}
        assert PUBLIC_PATHS == expected_paths


class TestContextVariableCleanup:
    """Tests for context variable lifecycle management."""

    def test_context_variable_default_empty(self):
        """Context variable should default to empty string."""
        # Access in a fresh context (no request in progress)
        assert client_api_key_var.get() == ""

    def test_get_client_api_key_helper(self):
        """get_client_api_key helper should return context variable value."""
        # In a fresh context, should be empty
        assert get_client_api_key() == ""

    def test_api_key_not_leaked_between_requests(self, client):
        """API key from one request should not leak to another."""
        # First request with a key
        response1 = client.get(
            "/protected",
            headers={CLIENT_API_KEY_HEADER: "first-key"},
        )
        assert response1.status_code == 200
        assert response1.json()["api_key"] == "first-key"

        # Second request with different key
        response2 = client.get(
            "/protected",
            headers={CLIENT_API_KEY_HEADER: "second-key"},
        )
        assert response2.status_code == 200
        assert response2.json()["api_key"] == "second-key"


class TestHeaderNameConstant:
    """Tests for header name configuration."""

    def test_client_api_key_header_value(self):
        """CLIENT_API_KEY_HEADER should be X-API-Key."""
        assert CLIENT_API_KEY_HEADER == "X-API-Key"

    def test_case_insensitive_header(self, client):
        """HTTP headers should be case-insensitive."""
        # Note: Starlette normalizes headers, so this tests the flow
        response = client.get(
            "/protected",
            headers={"x-api-key": "test-key"},
        )
        assert response.status_code == 200
        assert response.json()["api_key"] == "test-key"
