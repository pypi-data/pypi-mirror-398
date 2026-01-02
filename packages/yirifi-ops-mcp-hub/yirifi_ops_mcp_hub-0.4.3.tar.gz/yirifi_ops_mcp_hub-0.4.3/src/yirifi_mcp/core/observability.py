"""Observability utilities for request/response logging and metrics collection.

This module provides:
- Request correlation IDs for distributed tracing
- HTTPX event hooks for request/response logging
- Metrics collection with VictoriaMetrics/Prometheus-compatible export
"""

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx
import structlog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Request Correlation IDs
# ---------------------------------------------------------------------------

# Context variable for request correlation ID (thread-safe)
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get current request correlation ID, or generate a new one if not set.

    Returns:
        8-character request ID for correlation
    """
    request_id = request_id_var.get()
    if not request_id:
        request_id = str(uuid.uuid4())[:8]
        request_id_var.set(request_id)
    return request_id


def new_request_id() -> str:
    """Generate and set a new request correlation ID.

    Call this at the start of each gateway action to ensure
    unique correlation IDs per operation.

    Returns:
        8-character request ID
    """
    request_id = str(uuid.uuid4())[:8]
    request_id_var.set(request_id)
    return request_id


def clear_request_id() -> None:
    """Clear the current request ID (for cleanup between requests)."""
    request_id_var.set("")


# ---------------------------------------------------------------------------
# Metrics Data Structures (VictoriaMetrics/Prometheus compatible)
# ---------------------------------------------------------------------------


@dataclass
class HTTPRequestMetric:
    """Single HTTP request metric record.

    Attributes:
        timestamp: Unix timestamp of the request
        request_id: Correlation ID for tracing
        method: HTTP method (GET, POST, etc.)
        url: Request URL path (not full URL for grouping)
        status_code: HTTP response status code
        duration_ms: Request duration in milliseconds
        success: Whether request was successful (2xx/3xx)
        action: Gateway action name (for gateway calls)
        service: Service name (auth, reg, etc.)
    """

    timestamp: float
    request_id: str
    method: str
    url: str
    status_code: int
    duration_ms: float
    success: bool
    action: str = ""
    service: str = ""


@dataclass
class MetricsCollector:
    """Thread-safe metrics collector for HTTP requests.

    Collects request metrics in a ring buffer and provides
    aggregated statistics and Prometheus/VictoriaMetrics export.

    The ring buffer prevents unbounded memory growth while
    maintaining recent history for debugging.

    Attributes:
        requests: Ring buffer of recent request metrics
        total_requests: Total requests since startup
        total_errors: Total error responses (4xx/5xx)
        total_duration_ms: Cumulative request duration
    """

    requests: list[HTTPRequestMetric] = field(default_factory=list)
    _max_size: int = 10000  # Limit memory usage (~2MB max)

    # Aggregated counters (for quick stats without iterating)
    total_requests: int = 0
    total_errors: int = 0
    total_duration_ms: float = 0.0

    # Per-action stats for gateway calls
    action_counts: dict[str, int] = field(default_factory=dict)
    action_errors: dict[str, int] = field(default_factory=dict)
    action_durations: dict[str, float] = field(default_factory=dict)

    def record(self, metric: HTTPRequestMetric) -> None:
        """Record a request metric.

        Args:
            metric: HTTPRequestMetric to record
        """
        self.total_requests += 1
        self.total_duration_ms += metric.duration_ms

        if not metric.success:
            self.total_errors += 1

        # Track per-action metrics
        if metric.action:
            self.action_counts[metric.action] = self.action_counts.get(metric.action, 0) + 1
            self.action_durations[metric.action] = (
                self.action_durations.get(metric.action, 0.0) + metric.duration_ms
            )
            if not metric.success:
                self.action_errors[metric.action] = (
                    self.action_errors.get(metric.action, 0) + 1
                )

        # Ring buffer behavior - drop oldest when full
        if len(self.requests) >= self._max_size:
            self.requests.pop(0)
        self.requests.append(metric)

    def get_stats(self) -> dict:
        """Get aggregated statistics.

        Returns:
            Dict with total counts, error rate, and average duration
        """
        avg_duration = self.total_duration_ms / max(self.total_requests, 1)
        error_rate = self.total_errors / max(self.total_requests, 1)

        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": round(error_rate, 4),
            "avg_duration_ms": round(avg_duration, 2),
            "buffer_size": len(self.requests),
            "actions": {
                action: {
                    "count": self.action_counts.get(action, 0),
                    "errors": self.action_errors.get(action, 0),
                    "avg_ms": round(
                        self.action_durations.get(action, 0.0)
                        / max(self.action_counts.get(action, 1), 1),
                        2,
                    ),
                }
                for action in self.action_counts
            },
        }

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus/VictoriaMetrics text format.

        Returns:
            Prometheus text exposition format string
        """
        lines = [
            "# HELP yirifi_mcp_http_requests_total Total HTTP requests",
            "# TYPE yirifi_mcp_http_requests_total counter",
            f"yirifi_mcp_http_requests_total {self.total_requests}",
            "",
            "# HELP yirifi_mcp_http_errors_total Total HTTP errors (4xx/5xx)",
            "# TYPE yirifi_mcp_http_errors_total counter",
            f"yirifi_mcp_http_errors_total {self.total_errors}",
            "",
            "# HELP yirifi_mcp_http_duration_ms_sum Total HTTP duration in milliseconds",
            "# TYPE yirifi_mcp_http_duration_ms_sum counter",
            f"yirifi_mcp_http_duration_ms_sum {self.total_duration_ms:.2f}",
        ]

        # Per-action metrics
        if self.action_counts:
            lines.extend([
                "",
                "# HELP yirifi_mcp_action_requests_total Requests per action",
                "# TYPE yirifi_mcp_action_requests_total counter",
            ])
            for action, count in self.action_counts.items():
                lines.append(f'yirifi_mcp_action_requests_total{{action="{action}"}} {count}')

            lines.extend([
                "",
                "# HELP yirifi_mcp_action_errors_total Errors per action",
                "# TYPE yirifi_mcp_action_errors_total counter",
            ])
            for action, errors in self.action_errors.items():
                lines.append(f'yirifi_mcp_action_errors_total{{action="{action}"}} {errors}')

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all metrics (for testing)."""
        self.requests.clear()
        self.total_requests = 0
        self.total_errors = 0
        self.total_duration_ms = 0.0
        self.action_counts.clear()
        self.action_errors.clear()
        self.action_durations.clear()


# Global metrics collector instance
metrics = MetricsCollector()


# ---------------------------------------------------------------------------
# HTTPX Event Hooks for Request/Response Logging
# ---------------------------------------------------------------------------

# Headers that should be masked in logs
SENSITIVE_HEADERS = frozenset({
    "x-api-key",
    "authorization",
    "cookie",
    "set-cookie",
    "x-auth-token",
})


def sanitize_headers(headers: httpx.Headers) -> dict[str, str]:
    """Sanitize headers for logging, masking sensitive values.

    Args:
        headers: HTTPX headers object

    Returns:
        Dict with sensitive values replaced by "***"
    """
    return {
        k: "***" if k.lower() in SENSITIVE_HEADERS else v
        for k, v in headers.items()
    }


async def log_request(request: httpx.Request) -> None:
    """HTTPX event hook to log outgoing HTTP requests.

    This hook:
    - Stores start time for duration calculation
    - Adds X-Request-ID header for upstream tracing
    - Logs sanitized request details

    Args:
        request: HTTPX Request object (modified in place)
    """
    request_id = get_request_id()

    # Store start time and request ID in extensions for response hook
    request.extensions["start_time"] = time.perf_counter()
    request.extensions["request_id"] = request_id

    # Add correlation ID header for upstream tracing
    request.headers["X-Request-ID"] = request_id

    # Calculate body size safely
    body_size = 0
    if request.content:
        body_size = len(request.content)

    logger.debug(
        "http_request_out",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        headers=sanitize_headers(request.headers),
        body_size=body_size,
    )


async def log_response(response: httpx.Response) -> None:
    """HTTPX event hook to log incoming HTTP responses.

    This hook:
    - Calculates request duration
    - Logs response details
    - Records metrics for monitoring

    Args:
        response: HTTPX Response object
    """
    request = response.request
    request_id = request.extensions.get("request_id", "unknown")
    start_time = request.extensions.get("start_time", time.perf_counter())

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Calculate content length
    content_length = int(response.headers.get("content-length", 0))

    success = 200 <= response.status_code < 400

    # Use appropriate log level based on status
    log_method = logger.info if success else logger.warning
    log_method(
        "http_response_in",
        request_id=request_id,
        status_code=response.status_code,
        content_length=content_length,
        elapsed_ms=round(elapsed_ms, 2),
        url=str(request.url),
    )

    # Record metric (HTTP-level, action set later in gateway)
    metric = HTTPRequestMetric(
        timestamp=time.time(),
        request_id=request_id,
        method=request.method,
        url=str(request.url.path),  # Path only for grouping
        status_code=response.status_code,
        duration_ms=elapsed_ms,
        success=success,
    )
    metrics.record(metric)
