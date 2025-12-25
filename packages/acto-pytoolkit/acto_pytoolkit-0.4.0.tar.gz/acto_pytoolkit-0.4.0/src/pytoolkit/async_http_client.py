"""Async HTTP client wrapper using aiohttp.

This module requires the 'async' extra: pip install pytoolkit[async]
"""

import asyncio
import logging
from typing import Any, Optional, Union

try:
    import aiohttp
    from aiohttp import ClientResponse, ClientSession, ClientTimeout
except ImportError:
    raise ImportError(
        "aiohttp is required for async_http_client. "
        "Install it with: pip install pytoolkit[async]"
    ) from None


class AsyncHttpClient:
    """Async wrapper around aiohttp with retry logic and helpers.

    Examples
    --------
    >>> async def fetch_data():
    ...     async with AsyncHttpClient(base_url="https://api.example.com") as client:
    ...         response = await client.get("/users")
    ...         return await client.json(response)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 0,
        backoff_factor: float = 0.3,
        logger: Optional[logging.Logger] = None,
        session: Optional[ClientSession] = None,
        default_headers: Optional[dict[str, str]] = None,
    ) -> None:
        """Initialize the async HTTP client.

        Parameters
        ----------
        base_url : Optional[str]
            Base URL to prepend to all requests
        timeout : float
            Default timeout in seconds for requests
        max_retries : int
            Maximum number of retries for failed requests
        backoff_factor : float
            Factor for exponential backoff between retries
        logger : Optional[logging.Logger]
            Logger instance for logging
        session : Optional[ClientSession]
            Existing aiohttp session to use
        default_headers : Optional[dict[str, str]]
            Default headers to include in all requests
        """
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._session = session
        self._default_headers = default_headers or {}
        self._owned_session = session is None

    async def __aenter__(self) -> "AsyncHttpClient":
        """Enter async context manager."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers=self._default_headers,
                timeout=self.timeout,
            )
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Exit async context manager."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and self._owned_session:
            await self._session.close()
            self._session = None

    def _get_session(self) -> ClientSession:
        """Get the current session or create a new one."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers=self._default_headers,
                timeout=self.timeout,
            )
            self._owned_session = True
        return self._session

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> ClientResponse:
        """Make an HTTP request with retry logic."""
        if self.base_url and not url.startswith("http://") and not url.startswith("https://"):
            full_url = f"{self.base_url}/{url.lstrip('/')}"
        else:
            full_url = url

        session = self._get_session()
        attempt = 0

        while True:
            try:
                response = await session.request(method, full_url, **kwargs)
                response.raise_for_status()
                return response
            except aiohttp.ClientError as exc:
                if attempt >= self.max_retries:
                    self.logger.error("HTTP %s %s failed: %s", method, full_url, exc)
                    raise

                delay = self.backoff_factor * (2**attempt)
                self.logger.warning(
                    "HTTP %s %s failed on attempt %s, retrying in %.2f seconds",
                    method,
                    full_url,
                    attempt + 1,
                    delay,
                )
                await asyncio.sleep(delay)
                attempt += 1

    async def get(
        self, url: str, params: Optional[dict[str, Any]] = None, **kwargs: Any
    ) -> ClientResponse:
        """Make a GET request."""
        return await self._request("GET", url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: Optional[Union[dict[str, Any], str]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Make a POST request."""
        return await self._request("POST", url, data=data, json=json, **kwargs)

    async def put(
        self,
        url: str,
        data: Optional[Union[dict[str, Any], str]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Make a PUT request."""
        return await self._request("PUT", url, data=data, json=json, **kwargs)

    async def patch(
        self,
        url: str,
        data: Optional[Union[dict[str, Any], str]] = None,
        json: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Make a PATCH request."""
        return await self._request("PATCH", url, data=data, json=json, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> ClientResponse:
        """Make a DELETE request."""
        return await self._request("DELETE", url, **kwargs)

    @staticmethod
    async def json(response: ClientResponse) -> Any:
        """Parse JSON response safely."""
        try:
            return await response.json()
        except (ValueError, aiohttp.ContentTypeError) as exc:
            raise ValueError(f"Failed to decode JSON: {exc}") from exc

    @staticmethod
    async def text(response: ClientResponse) -> str:
        """Get response text."""
        result: str = await response.text()
        return result
