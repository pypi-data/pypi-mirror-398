"""Tests for the gateway module."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx

from yirifi_mcp.gateway.dynamic import DynamicGateway
from yirifi_mcp.catalog.base import Endpoint, ServiceCatalog, Tier
from yirifi_mcp.core.exceptions import (
    ActionNotFoundError,
    MissingPathParamError,
    UpstreamError,
    GatewayError,
)


class TestDynamicGateway:
    """Tests for DynamicGateway class."""

    @pytest.fixture
    def sample_catalog(self):
        """Sample catalog for gateway testing."""
        return ServiceCatalog([
            Endpoint("list_users", "GET", "/users/", "List users", Tier.DIRECT),
            Endpoint("get_user", "GET", "/users/{user_id}", "Get user", Tier.DIRECT),
            Endpoint("create_user", "POST", "/users/", "Create user", Tier.DIRECT),
            Endpoint("update_user", "PUT", "/users/{user_id}", "Update user", Tier.GATEWAY),
            Endpoint("delete_user", "DELETE", "/users/{user_id}", "Delete user", Tier.GATEWAY, risk_level="high"),
            Endpoint("get_perms", "GET", "/rbac/users/{user_id}/permissions/{app_id}", "Get perms", Tier.DIRECT),
        ])

    @pytest.fixture
    def mock_client(self):
        """Mock HTTP client."""
        client = MagicMock(spec=httpx.AsyncClient)
        return client

    @pytest.fixture
    def gateway(self, mock_client, sample_catalog):
        """Gateway instance for testing."""
        return DynamicGateway(mock_client, sample_catalog)

    @pytest.mark.asyncio
    async def test_catalog_returns_all_actions(self, gateway):
        """Test that catalog returns all non-excluded endpoints."""
        catalog = await gateway.catalog()
        assert len(catalog) == 6
        assert "list_users" in catalog
        assert "delete_user" in catalog
        assert catalog["list_users"] == "List users"

    @pytest.mark.asyncio
    async def test_call_simple_get(self, gateway, mock_client):
        """Test calling a simple GET endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"users": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)

        result = await gateway.call("list_users")

        mock_client.request.assert_called_once_with(
            method="GET",
            url="/users/",
            params=None,
            json=None,
        )
        assert result == {"users": []}

    @pytest.mark.asyncio
    async def test_call_with_path_params(self, gateway, mock_client):
        """Test calling endpoint with path parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "name": "Test"}
        mock_response.raise_for_status = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)

        result = await gateway.call("get_user", path_params={"user_id": 123})

        mock_client.request.assert_called_once_with(
            method="GET",
            url="/users/123",
            params=None,
            json=None,
        )
        assert result["id"] == 123

    @pytest.mark.asyncio
    async def test_call_with_multiple_path_params(self, gateway, mock_client):
        """Test calling endpoint with multiple path parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"permissions": ["read", "write"]}
        mock_response.raise_for_status = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)

        result = await gateway.call(
            "get_perms",
            path_params={"user_id": 123, "app_id": "my-app"}
        )

        mock_client.request.assert_called_once_with(
            method="GET",
            url="/rbac/users/123/permissions/my-app",
            params=None,
            json=None,
        )

    @pytest.mark.asyncio
    async def test_call_with_query_params(self, gateway, mock_client):
        """Test calling endpoint with query parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"users": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)

        result = await gateway.call("list_users", query_params={"limit": 10, "offset": 0})

        mock_client.request.assert_called_once_with(
            method="GET",
            url="/users/",
            params={"limit": 10, "offset": 0},
            json=None,
        )

    @pytest.mark.asyncio
    async def test_call_post_with_body(self, gateway, mock_client):
        """Test calling POST endpoint with body."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 456, "email": "test@example.com"}
        mock_response.raise_for_status = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)

        body = {"email": "test@example.com", "password": "secret"}
        result = await gateway.call("create_user", body=body)

        mock_client.request.assert_called_once_with(
            method="POST",
            url="/users/",
            params=None,
            json=body,
        )

    @pytest.mark.asyncio
    async def test_call_unknown_action_raises(self, gateway):
        """Test that unknown action raises ActionNotFoundError."""
        with pytest.raises(ActionNotFoundError) as exc_info:
            await gateway.call("nonexistent_action")

        assert exc_info.value.action == "nonexistent_action"
        assert "list_users" in exc_info.value.available

    @pytest.mark.asyncio
    async def test_call_missing_path_param_raises(self, gateway):
        """Test that missing path parameter raises MissingPathParamError."""
        with pytest.raises(MissingPathParamError) as exc_info:
            await gateway.call("get_user")  # No path_params provided

        assert "user_id" in exc_info.value.params
        assert exc_info.value.path == "/users/{user_id}"

    @pytest.mark.asyncio
    async def test_call_partial_path_params_raises(self, gateway):
        """Test that partial path parameters raise error."""
        with pytest.raises(MissingPathParamError) as exc_info:
            await gateway.call("get_perms", path_params={"user_id": 123})
            # Missing app_id

        assert "app_id" in exc_info.value.params

    @pytest.mark.asyncio
    async def test_call_http_error_raises_upstream_error(self, gateway, mock_client):
        """Test that HTTP errors raise UpstreamError."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "User not found"

        error = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response
        )
        mock_client.request = AsyncMock(side_effect=error)

        with pytest.raises(UpstreamError) as exc_info:
            await gateway.call("get_user", path_params={"user_id": 999})

        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_call_request_error_raises_gateway_error(self, gateway, mock_client):
        """Test that request errors raise GatewayError."""
        mock_client.request = AsyncMock(
            side_effect=httpx.RequestError("Connection refused")
        )

        with pytest.raises(GatewayError) as exc_info:
            await gateway.call("list_users")

        assert "Request failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_empty_response(self, gateway, mock_client):
        """Test handling of 204 No Content response."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_response.raise_for_status = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)

        result = await gateway.call("delete_user", path_params={"user_id": 123})

        assert result == {"success": True, "status_code": 204}

    def test_get_action_info(self, gateway):
        """Test getting action info."""
        info = gateway.get_action_info("delete_user")
        assert info is not None
        assert info["method"] == "DELETE"
        assert info["path"] == "/users/{user_id}"
        assert info["risk_level"] == "high"

    def test_get_action_info_not_found(self, gateway):
        """Test getting info for non-existent action."""
        assert gateway.get_action_info("nonexistent") is None

    def test_get_high_risk_actions(self, gateway):
        """Test getting list of high-risk actions."""
        high_risk = gateway.get_high_risk_actions()
        assert "delete_user" in high_risk
        assert "list_users" not in high_risk


class TestExceptions:
    """Tests for gateway exceptions."""

    def test_action_not_found_error(self):
        """Test ActionNotFoundError attributes."""
        error = ActionNotFoundError("bad_action", ["good_action", "other_action"])
        assert error.action == "bad_action"
        assert "good_action" in error.available
        assert "Unknown action: bad_action" in str(error)

    def test_missing_path_param_error(self):
        """Test MissingPathParamError attributes."""
        error = MissingPathParamError(["user_id", "app_id"], "/users/{user_id}/apps/{app_id}")
        assert error.params == ["user_id", "app_id"]
        assert error.path == "/users/{user_id}/apps/{app_id}"
        assert "Missing path parameters" in str(error)

    def test_upstream_error(self):
        """Test UpstreamError attributes."""
        detail = "Internal server error"
        error = UpstreamError(500, detail)
        assert error.status_code == 500
        assert error.detail == detail  # Stored as-is
        assert "HTTP 500" in str(error)
        assert detail in str(error)  # Short detail appears in message

    def test_upstream_error_truncates_detail(self):
        """Test that UpstreamError truncates long details in message."""
        long_detail = "x" * 1000
        error = UpstreamError(500, long_detail)
        # Message should be truncated at 200 chars
        assert len(str(error)) < 300
