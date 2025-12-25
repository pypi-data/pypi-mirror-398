"""Dynamic gateway for executing catalog actions with resilience patterns.

This module provides the DynamicGateway class that executes API actions
from a ServiceCatalog with full observability, resilience, and efficiency features:

- Request correlation IDs for distributed tracing
- High-risk action logging and monitoring
- Circuit breaker for upstream protection
- Rate limiting per risk level
- Retry logic for idempotent operations
- Response size limits
- Catalog caching
- Batch operations
"""

import asyncio
import re
import time
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

import httpx
import structlog

from yirifi_mcp.catalog.base import ServiceCatalog
from yirifi_mcp.core.exceptions import (
    ActionNotFoundError,
    CircuitBreakerOpenError,
    GatewayError,
    MissingPathParamError,
    ResponseTooLargeError,
    UpstreamError,
)
from yirifi_mcp.core.observability import (
    HTTPRequestMetric,
    get_request_id,
    metrics,
    new_request_id,
)
from yirifi_mcp.core.resilience import ResilienceConfig, ResilienceCoordinator
from yirifi_mcp.core.response_wrapper import is_mutation_method, wrap_response

from .base import BaseGateway

if TYPE_CHECKING:
    from yirifi_mcp.core.config import ServiceConfig

logger = structlog.get_logger()


# =============================================================================
# Batch Operation Data Structures
# =============================================================================


@dataclass
class BatchCallItem:
    """Single call specification in a batch operation.

    Attributes:
        action: Action name from catalog
        path_params: URL path parameters (e.g., {"user_id": 123})
        query_params: Query string parameters
        body: Request body for POST/PUT/PATCH
        id: Optional client-provided ID for correlation
    """

    action: str
    path_params: dict | None = None
    query_params: dict | None = None
    body: dict | None = None
    id: str | None = None


@dataclass
class BatchResult:
    """Result of a single call in a batch operation.

    Attributes:
        id: Client correlation ID (if provided)
        action: Action name
        success: Whether call succeeded
        data: Response data (if success)
        error: Error message (if failed)
        status_code: HTTP status code (if available)
    """

    id: str | None
    action: str
    success: bool
    data: dict | None = None
    error: str | None = None
    status_code: int | None = None


# =============================================================================
# Dynamic Gateway
# =============================================================================


class DynamicGateway(BaseGateway):
    """Gateway that executes actions from a service catalog with resilience.

    This gateway provides dynamic access to API endpoints defined in a
    ServiceCatalog with full production features:

    - **Observability**: Request IDs, timing, high-risk action logging
    - **Resilience**: Circuit breaker, rate limiting, retry logic
    - **Efficiency**: Catalog caching, response size limits, batch operations

    Example:
        >>> from yirifi_mcp.catalog.auth_service import AUTH_CATALOG
        >>> gateway = DynamicGateway(http_client, AUTH_CATALOG, config=config)
        >>> await gateway.call("delete_user_detail", path_params={"user_id": 123})
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        catalog: ServiceCatalog,
        config: "ServiceConfig | None" = None,
        resilience_config: ResilienceConfig | None = None,
    ):
        """Initialize gateway with HTTP client and service catalog.

        Args:
            client: Configured httpx.AsyncClient for API requests
            catalog: ServiceCatalog defining available endpoints
            config: Optional service config for environment context and limits
            resilience_config: Optional resilience configuration (overrides config)
        """
        super().__init__(client)
        self._catalog = catalog
        self._config = config
        self._api_catalog = catalog.to_gateway_catalog()

        # Catalog caching
        self._catalog_cache: dict | None = None

        # Response size limits from config
        self._max_response_size = (
            config.max_response_size if config else 10 * 1024 * 1024
        )
        self._response_truncation_enabled = (
            config.response_truncation_enabled if config else True
        )

        # Initialize resilience coordinator
        service_name = config.server_name if config else "unknown"

        # Use provided resilience_config, or build from service config, or use defaults
        if resilience_config is None and config is not None:
            resilience_config = config.get_resilience_config()

        self._resilience = ResilienceCoordinator(
            service_name,
            resilience_config,
        )

    # -------------------------------------------------------------------------
    # Catalog Operations (with caching)
    # -------------------------------------------------------------------------

    async def catalog(self) -> dict:
        """Return available actions as {name: description} with environment context.

        Results are cached for efficiency. Call invalidate_cache() to refresh.

        Returns:
            Dict with environment metadata and action mappings
        """
        if self._catalog_cache is None:
            actions = {name: info["desc"] for name, info in self._api_catalog.items()}

            # Wrap with environment context if config available
            if self._config:
                self._catalog_cache = wrap_response(
                    actions, self._config, is_mutation=False
                )
            else:
                self._catalog_cache = actions

        return self._catalog_cache

    def invalidate_cache(self) -> None:
        """Invalidate catalog cache (call after config change)."""
        self._catalog_cache = None

    # -------------------------------------------------------------------------
    # Single Action Execution
    # -------------------------------------------------------------------------

    async def call(
        self,
        action: str,
        path_params: dict | None = None,
        query_params: dict | None = None,
        body: dict | None = None,
    ) -> dict:
        """Execute an action from the catalog with full resilience.

        This method applies:
        1. Request correlation ID generation
        2. High-risk action logging
        3. Circuit breaker check
        4. Rate limiting
        5. Retry logic (for idempotent operations)
        6. Response size limits

        Args:
            action: Action name from catalog()
            path_params: URL path parameters (e.g., {"user_id": 123})
            query_params: Query string parameters
            body: Request body for POST/PUT/PATCH

        Returns:
            API response as dict

        Raises:
            ActionNotFoundError: Unknown action name
            MissingPathParamError: Required path param not provided
            CircuitBreakerOpenError: Circuit is open, failing fast
            ResponseTooLargeError: Response exceeds size limit
            UpstreamError: HTTP error from upstream service
            GatewayError: Other gateway errors
        """
        # Generate new request ID for this gateway call
        request_id = new_request_id()
        start_time = time.perf_counter()

        # Validate action exists
        if action not in self._api_catalog:
            logger.warning("action_not_found", action=action, request_id=request_id)
            raise ActionNotFoundError(action, list(self._api_catalog.keys()))

        endpoint = self._api_catalog[action]
        method = endpoint["method"]
        path = endpoint["path"]
        risk_level = endpoint.get("risk_level", "low")
        idempotent = endpoint.get("idempotent", method in ("GET", "PUT", "DELETE"))

        # Log warning for high-risk actions
        if risk_level == "high":
            logger.warning(
                "high_risk_action_invoked",
                request_id=request_id,
                action=action,
                method=method,
                path=path,
                path_params=path_params,
                risk_level=risk_level,
            )

        # Substitute path parameters
        if path_params:
            for key, value in path_params.items():
                path = path.replace(f"{{{key}}}", str(value))

        # Check for unsubstituted path params
        missing = re.findall(r"\{(\w+)\}", path)
        if missing:
            logger.warning(
                "missing_path_params",
                action=action,
                missing=missing,
                path=endpoint["path"],
                request_id=request_id,
            )
            raise MissingPathParamError(missing, endpoint["path"])

        # Define the actual HTTP request as a callable for resilience
        async def execute_request() -> httpx.Response:
            response = await self.client.request(
                method=method,
                url=path,
                params=query_params,
                json=body if method in ("POST", "PUT", "PATCH") else None,
            )
            response.raise_for_status()
            return response

        # Execute with resilience patterns
        logger.debug(
            "gateway_call",
            request_id=request_id,
            action=action,
            method=method,
            path=path,
            has_body=body is not None,
            idempotent=idempotent,
            risk_level=risk_level,
        )

        try:
            response = await self._resilience.execute(
                execute_request,
                action=action,
                risk_level=risk_level,
                idempotent=idempotent,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Check response size
            content_length = int(response.headers.get("content-length", 0))
            if content_length > self._max_response_size:
                logger.warning(
                    "response_size_exceeded",
                    request_id=request_id,
                    action=action,
                    size=content_length,
                    max_size=self._max_response_size,
                )
                if not self._response_truncation_enabled:
                    raise ResponseTooLargeError(content_length, self._max_response_size)
                # Return truncation warning
                result = {
                    "_truncated": True,
                    "_warning": (
                        f"Response truncated: {content_length} bytes > "
                        f"{self._max_response_size} limit"
                    ),
                }
            elif response.status_code == 204 or not response.content:
                result = {"success": True, "status_code": response.status_code}
            else:
                result = response.json()

            # Record gateway-level metric
            metric = HTTPRequestMetric(
                timestamp=time.time(),
                request_id=request_id,
                method=method,
                url=path,
                status_code=response.status_code,
                duration_ms=elapsed_ms,
                success=True,
                action=action,
                service=self._config.server_name if self._config else "",
            )
            metrics.record(metric)

            # Log successful execution
            logger.info(
                "gateway_call_success",
                request_id=request_id,
                action=action,
                status_code=response.status_code,
                elapsed_ms=round(elapsed_ms, 2),
            )

            # Wrap with environment context if config available
            if self._config:
                return wrap_response(
                    result,
                    self._config,
                    is_mutation=is_mutation_method(method),
                )
            return result

        except CircuitBreakerOpenError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                "circuit_open",
                request_id=request_id,
                action=action,
                circuit=e.service,
                retry_after=e.retry_after,
                elapsed_ms=round(elapsed_ms, 2),
            )
            raise GatewayError(
                f"Service temporarily unavailable. Retry after {e.retry_after:.0f}s"
            )

        except httpx.HTTPStatusError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Record failure metric
            metric = HTTPRequestMetric(
                timestamp=time.time(),
                request_id=request_id,
                method=method,
                url=path,
                status_code=e.response.status_code,
                duration_ms=elapsed_ms,
                success=False,
                action=action,
                service=self._config.server_name if self._config else "",
            )
            metrics.record(metric)

            logger.error(
                "upstream_error",
                request_id=request_id,
                action=action,
                status_code=e.response.status_code,
                elapsed_ms=round(elapsed_ms, 2),
                detail=e.response.text[:200],
            )
            raise UpstreamError(e.response.status_code, e.response.text[:500])

        except httpx.RequestError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "request_error",
                request_id=request_id,
                action=action,
                elapsed_ms=round(elapsed_ms, 2),
                error=str(e),
            )
            raise GatewayError(f"Request failed: {e}")

    # -------------------------------------------------------------------------
    # Batch Operations
    # -------------------------------------------------------------------------

    async def call_batch(
        self,
        calls: list[BatchCallItem],
        *,
        concurrent: bool = True,
        max_concurrency: int = 5,
        fail_fast: bool = False,
    ) -> list[BatchResult]:
        """Execute multiple calls, optionally concurrently.

        Args:
            calls: List of BatchCallItem to execute
            concurrent: Whether to execute concurrently (vs. sequentially)
            max_concurrency: Maximum concurrent requests (semaphore limit)
            fail_fast: Stop on first error (only for sequential mode)

        Returns:
            List of BatchResult in same order as input calls
        """
        if concurrent:
            return await self._batch_concurrent(calls, max_concurrency)
        else:
            return await self._batch_sequential(calls, fail_fast)

    async def _batch_concurrent(
        self,
        calls: list[BatchCallItem],
        max_concurrency: int,
    ) -> list[BatchResult]:
        """Execute calls concurrently with semaphore."""
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_with_semaphore(
            item: BatchCallItem, index: int
        ) -> tuple[int, BatchResult]:
            async with semaphore:
                result = await self._execute_single(item)
                return index, result

        tasks = [execute_with_semaphore(item, i) for i, item in enumerate(calls)]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Sort by original index and extract results
        sorted_results = sorted(results, key=lambda x: x[0])
        return [r[1] for r in sorted_results]

    async def _batch_sequential(
        self,
        calls: list[BatchCallItem],
        fail_fast: bool,
    ) -> list[BatchResult]:
        """Execute calls sequentially."""
        results = []
        for item in calls:
            result = await self._execute_single(item)
            results.append(result)
            if fail_fast and not result.success:
                break
        return results

    async def _execute_single(self, item: BatchCallItem) -> BatchResult:
        """Execute a single batch item and wrap result."""
        try:
            data = await self.call(
                item.action,
                path_params=item.path_params,
                query_params=item.query_params,
                body=item.body,
            )
            return BatchResult(
                id=item.id,
                action=item.action,
                success=True,
                data=data,
            )
        except UpstreamError as e:
            return BatchResult(
                id=item.id,
                action=item.action,
                success=False,
                error=e.detail,
                status_code=e.status_code,
            )
        except GatewayError as e:
            return BatchResult(
                id=item.id,
                action=item.action,
                success=False,
                error=str(e),
            )

    # -------------------------------------------------------------------------
    # Inspection Methods
    # -------------------------------------------------------------------------

    def get_action_info(self, action: str) -> dict | None:
        """Get detailed info about an action.

        Args:
            action: Action name

        Returns:
            Dict with method, path, desc, risk_level, idempotent or None
        """
        return self._api_catalog.get(action)

    def get_high_risk_actions(self) -> list[str]:
        """Get list of high-risk action names.

        Returns:
            List of action names with risk_level="high"
        """
        return [
            name
            for name, info in self._api_catalog.items()
            if info.get("risk_level") == "high"
        ]

    @property
    def circuit_state(self):
        """Current circuit breaker state for monitoring."""
        return self._resilience.circuit_state

    @property
    def resilience(self) -> ResilienceCoordinator:
        """Access to resilience coordinator for inspection."""
        return self._resilience
