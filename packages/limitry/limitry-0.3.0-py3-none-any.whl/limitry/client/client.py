"""Main client for Limitry SDK"""

from typing import Any, Dict, Optional

import httpx

from .config import ClientConfig
from .exceptions import APIError, AuthenticationError, LimitryError, NetworkError

# fmt: off
# BEGIN AUTO-GENERATED IMPORTS
from .resources import (
    Customers,
    Events,
    Project,
    Quotas,
    RateLimits,
    Track,
    Usage,
)
# END AUTO-GENERATED IMPORTS
# fmt: on


class Client:
    """Main client for interacting with the Limitry API"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the Limitry client.

        Args:
            api_key: Your Limitry API key
            base_url: Base URL for the API (defaults to https://api.limitry.com/v1)
            timeout: Request timeout in seconds (defaults to 30)
            headers: Additional headers to include in requests

        Example:
            ```python
            client = Client(api_key="your-api-key")
            ```
        """
        self._config = ClientConfig(api_key, base_url, timeout, headers)
        self._client: Optional[httpx.AsyncClient] = None

        # fmt: off
        # BEGIN AUTO-GENERATED INIT
        # Initialize operation classes
        self.customers = Customers(self)
        self.events = Events(self)
        self.project = Project(self)
        self.quotas = Quotas(self)
        self.rate_limits = RateLimits(self)
        self.track = Track(self)
        self.usage = Usage(self)
        # END AUTO-GENERATED INIT
        # fmt: on

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _ensure_client(self):
        """Ensure HTTP client is initialized"""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._config.api_key}",
                **self._config.headers,
            }
            self._client = httpx.AsyncClient(
                base_url=self._config.base_url,
                headers=headers,
                timeout=self._config.timeout,
            )

    async def close(self):
        """Close the HTTP client"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API endpoint path
            params: Query parameters
            json: JSON body for request
            headers: Additional headers for this request

        Returns:
            Response data (parsed JSON)

        Raises:
            AuthenticationError: When authentication fails (401/403)
            APIError: When API request fails
            NetworkError: When network error occurs
        """
        await self._ensure_client()
        assert self._client is not None  # Type narrowing for mypy

        request_headers = headers or {}

        try:
            response = await self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
                headers=request_headers,
            )

            if not response.is_success:
                await self._handle_error_response(response)

            # Handle empty responses
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return {}

        except httpx.HTTPStatusError as e:
            raise NetworkError(f"HTTP error: {e}", e) from e
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {e}", e) from e
        except Exception as e:
            if isinstance(e, (APIError, LimitryError)):
                raise
            raise NetworkError(f"Unexpected error: {e}", e) from e

    async def _handle_error_response(self, response: httpx.Response):
        """Handle error responses and raise appropriate exceptions"""
        try:
            error_data = response.json()
        except Exception:
            error_data = {"error": response.text}

        if response.status_code in (401, 403):
            raise AuthenticationError(
                "Authentication failed. Please check your API key.",
                response.status_code,
                error_data,
            )

        raise APIError(
            f"API request failed: {response.status_code} {response.reason_phrase}",
            response.status_code,
            response.reason_phrase or "Unknown",
            error_data,
        )
