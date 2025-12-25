"""Tests for the observability module."""

import time
from unittest.mock import MagicMock

import httpx
import pytest

from yirifi_mcp.core.observability import (
    HTTPRequestMetric,
    MetricsCollector,
    clear_request_id,
    get_request_id,
    log_request,
    log_response,
    metrics,
    new_request_id,
    request_id_var,
    sanitize_headers,
)


class TestRequestId:
    """Tests for request ID generation and context."""

    def test_new_request_id_generates_uuid(self):
        """Test that new_request_id generates a valid short UUID."""
        request_id = new_request_id()
        assert len(request_id) == 8
        assert request_id.isalnum()

    def test_new_request_id_sets_context_var(self):
        """Test that new_request_id sets the context variable."""
        request_id = new_request_id()
        assert get_request_id() == request_id

    def test_get_request_id_returns_current(self):
        """Test that get_request_id returns the current request ID."""
        request_id = new_request_id()
        assert get_request_id() == request_id

    def test_get_request_id_generates_if_empty(self):
        """Test that get_request_id generates new ID when not set."""
        clear_request_id()
        request_id = get_request_id()
        assert len(request_id) == 8
        # Should be set now
        assert get_request_id() == request_id

    def test_clear_request_id(self):
        """Test clearing the request ID."""
        new_request_id()
        clear_request_id()
        # Next get should generate a new one
        new_id = get_request_id()
        assert len(new_id) == 8

    def test_request_ids_are_unique(self):
        """Test that multiple request IDs are unique."""
        ids = {new_request_id() for _ in range(100)}
        assert len(ids) == 100


class TestHTTPRequestMetric:
    """Tests for HTTPRequestMetric dataclass."""

    def test_metric_creation(self):
        """Test creating a metric."""
        metric = HTTPRequestMetric(
            timestamp=time.time(),
            request_id="abc12345",
            method="GET",
            url="/api/users",
            status_code=200,
            duration_ms=50.5,
            success=True,
        )
        assert metric.method == "GET"
        assert metric.status_code == 200
        assert metric.success is True

    def test_metric_with_optional_fields(self):
        """Test metric with optional action and service."""
        metric = HTTPRequestMetric(
            timestamp=time.time(),
            request_id="abc12345",
            method="POST",
            url="/api/users",
            status_code=201,
            duration_ms=100.0,
            success=True,
            action="create_user",
            service="auth-service",
        )
        assert metric.action == "create_user"
        assert metric.service == "auth-service"


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    @pytest.fixture
    def collector(self):
        """Fresh metrics collector for each test."""
        collector = MetricsCollector()
        collector.reset()
        return collector

    def test_record_metric(self, collector):
        """Test recording a metric."""
        metric = HTTPRequestMetric(
            timestamp=time.time(),
            request_id="test123",
            method="GET",
            url="/test",
            status_code=200,
            duration_ms=10.0,
            success=True,
        )
        collector.record(metric)

        stats = collector.get_stats()
        assert stats["total_requests"] == 1
        assert stats["total_errors"] == 0

    def test_record_failure(self, collector):
        """Test recording a failed request."""
        metric = HTTPRequestMetric(
            timestamp=time.time(),
            request_id="test123",
            method="GET",
            url="/test",
            status_code=500,
            duration_ms=10.0,
            success=False,
        )
        collector.record(metric)

        stats = collector.get_stats()
        assert stats["total_errors"] == 1

    def test_action_counts(self, collector):
        """Test per-action counting."""
        for status, success in [(200, True), (200, True), (500, False)]:
            metric = HTTPRequestMetric(
                timestamp=time.time(),
                request_id="test",
                method="GET",
                url="/test",
                status_code=status,
                duration_ms=10.0,
                success=success,
                action="get_users",
            )
            collector.record(metric)

        stats = collector.get_stats()
        assert stats["actions"]["get_users"]["count"] == 3
        assert stats["actions"]["get_users"]["errors"] == 1

    def test_ring_buffer_limit(self, collector):
        """Test that ring buffer respects size limit."""
        # Record more than buffer size
        for i in range(15000):
            metric = HTTPRequestMetric(
                timestamp=time.time(),
                request_id=f"req{i}",
                method="GET",
                url="/test",
                status_code=200,
                duration_ms=10.0,
                success=True,
            )
            collector.record(metric)

        # Should still only have buffer_size recent metrics
        assert len(collector.requests) <= 10000

    def test_get_prometheus_metrics(self, collector):
        """Test Prometheus format export."""
        metric = HTTPRequestMetric(
            timestamp=time.time(),
            request_id="test",
            method="GET",
            url="/test",
            status_code=200,
            duration_ms=100.0,
            success=True,
            action="get_users",
            service="test-service",
        )
        collector.record(metric)

        output = collector.get_prometheus_metrics()
        assert "yirifi_mcp_http_requests_total" in output
        assert "yirifi_mcp_http_errors_total" in output
        assert "yirifi_mcp_http_duration_ms_sum" in output

    def test_reset(self, collector):
        """Test resetting metrics."""
        metric = HTTPRequestMetric(
            timestamp=time.time(),
            request_id="test",
            method="GET",
            url="/test",
            status_code=200,
            duration_ms=10.0,
            success=True,
        )
        collector.record(metric)

        collector.reset()
        stats = collector.get_stats()
        assert stats["total_requests"] == 0


class TestSanitizeHeaders:
    """Tests for header sanitization."""

    def test_sanitize_api_key(self):
        """Test that API keys are masked."""
        headers = httpx.Headers({
            "Content-Type": "application/json",
            "X-API-Key": "secret-key-12345",
        })
        sanitized = sanitize_headers(headers)
        assert sanitized["x-api-key"] == "***"
        assert sanitized["content-type"] == "application/json"

    def test_sanitize_authorization(self):
        """Test that Authorization header is masked."""
        headers = httpx.Headers({
            "Authorization": "Bearer secret-token",
        })
        sanitized = sanitize_headers(headers)
        assert sanitized["authorization"] == "***"

    def test_preserve_safe_headers(self):
        """Test that safe headers are preserved."""
        headers = httpx.Headers({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "test-client",
        })
        sanitized = sanitize_headers(headers)
        assert sanitized["content-type"] == "application/json"
        assert sanitized["accept"] == "application/json"
        assert sanitized["user-agent"] == "test-client"


class TestEventHooks:
    """Tests for httpx event hooks."""

    @pytest.mark.asyncio
    async def test_log_request(self):
        """Test request logging hook."""
        request = MagicMock(spec=httpx.Request)
        request.method = "GET"
        request.url = httpx.URL("https://example.com/api/test")
        request.headers = httpx.Headers({"Content-Type": "application/json"})
        request.extensions = {}
        request.content = b""

        # Should not raise
        await log_request(request)

        # Check extensions were set
        assert "start_time" in request.extensions
        assert "request_id" in request.extensions

    @pytest.mark.asyncio
    async def test_log_response(self):
        """Test response logging hook."""
        request = MagicMock()
        request.extensions = {
            "start_time": time.perf_counter() - 0.05,
            "request_id": "test123",
        }
        request.method = "GET"
        request.url = httpx.URL("https://example.com/api/test")

        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.headers = httpx.Headers({"Content-Type": "application/json"})
        response.request = request

        # Should not raise
        await log_response(response)


class TestGlobalMetrics:
    """Tests for the global metrics instance."""

    def test_global_metrics_exists(self):
        """Test that global metrics collector exists."""
        assert metrics is not None
        assert isinstance(metrics, MetricsCollector)

    def test_global_metrics_can_record(self):
        """Test that global metrics can record."""
        initial_count = metrics.get_stats()["total_requests"]

        metric = HTTPRequestMetric(
            timestamp=time.time(),
            request_id="global-test",
            method="GET",
            url="/global-test",
            status_code=200,
            duration_ms=10.0,
            success=True,
        )
        metrics.record(metric)

        new_count = metrics.get_stats()["total_requests"]
        assert new_count == initial_count + 1
