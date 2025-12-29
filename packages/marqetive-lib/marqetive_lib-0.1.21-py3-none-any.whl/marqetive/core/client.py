"""API client implementation for MarqetiveLib."""

from typing import Any

import httpx
from pydantic import BaseModel

# Default connection pool limits for optimal performance
DEFAULT_MAX_CONNECTIONS = 100
DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20
DEFAULT_KEEPALIVE_EXPIRY = 30.0


class APIResponse(BaseModel):
    """Response model for API calls."""

    status_code: int
    data: dict[str, Any]
    headers: dict[str, str]


class APIClient:
    """A simple HTTP API client with type hints.

    This client provides a clean interface for making HTTP requests
    with automatic response parsing and error handling.

    Args:
        base_url: The base URL for API requests
        timeout: Request timeout in seconds (default: 30)
        headers: Optional default headers for all requests
        max_connections: Maximum total connections in pool (default: 100)
        max_keepalive_connections: Maximum persistent connections (default: 20)

    Example:
        >>> client = APIClient(base_url="https://api.example.com")
        >>> response = await client.get("/users/1")
        >>> print(response.data)
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        max_keepalive_connections: int = DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
    ) -> None:
        """Initialize the API client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = headers or {}
        self._client: httpx.AsyncClient | None = None
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=DEFAULT_KEEPALIVE_EXPIRY,
        )

    async def __aenter__(self) -> "APIClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self.default_headers,
            limits=self._limits,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> APIResponse:
        """Make a GET request.

        Args:
            path: The endpoint path
            params: Optional query parameters

        Returns:
            APIResponse object containing status, data, and headers

        Raises:
            httpx.HTTPError: If the request fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        response = await self._client.get(path, params=params)
        response.raise_for_status()

        return APIResponse(
            status_code=response.status_code,
            data=response.json() if response.content else {},
            headers=dict(response.headers),
        )

    async def post(self, path: str, data: dict[str, Any] | None = None) -> APIResponse:
        """Make a POST request.

        Args:
            path: The endpoint path
            data: Optional request body data

        Returns:
            APIResponse object containing status, data, and headers

        Raises:
            httpx.HTTPError: If the request fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        response = await self._client.post(path, json=data)
        response.raise_for_status()

        return APIResponse(
            status_code=response.status_code,
            data=response.json() if response.content else {},
            headers=dict(response.headers),
        )
