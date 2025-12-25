"""Base gateway implementation."""

from abc import ABC, abstractmethod

import httpx


class BaseGateway(ABC):
    """Abstract base class for gateway implementations.

    A gateway provides dynamic API access through a catalog of
    available actions. This allows Claude to execute API calls
    without needing individual MCP tools for each endpoint.

    Subclasses must implement:
    - catalog(): Return available actions
    - call(): Execute an action

    Example:
        >>> gateway = MyGateway(http_client)
        >>> actions = await gateway.catalog()
        >>> result = await gateway.call("delete_user", path_params={"user_id": 123})
    """

    def __init__(self, client: httpx.AsyncClient):
        """Initialize gateway with HTTP client.

        Args:
            client: Configured httpx.AsyncClient for API requests
        """
        self.client = client

    @abstractmethod
    async def catalog(self) -> dict[str, str]:
        """Return available actions as {name: description}.

        Returns:
            Dict mapping action names to their descriptions
        """
        ...

    @abstractmethod
    async def call(
        self,
        action: str,
        path_params: dict | None = None,
        query_params: dict | None = None,
        body: dict | None = None,
    ) -> dict:
        """Execute an action and return the result.

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
            UpstreamError: HTTP error from upstream service
            GatewayError: Other gateway errors
        """
        ...
