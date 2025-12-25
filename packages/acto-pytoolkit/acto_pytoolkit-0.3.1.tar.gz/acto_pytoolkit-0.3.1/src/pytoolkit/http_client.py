from typing import Any, Dict, Optional, Union

import logging
import time

import requests
from requests import Response, Session


class HttpClient:
    """Thin wrapper around the `requests` library.

    Adds basic timeout handling, optional retry logic and JSON parsing helper.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 0,
        backoff_factor: float = 0.3,
        logger: Optional[logging.Logger] = None,
        session: Optional[Session] = None,
        default_headers: Optional[Dict[str, str]] = None,
        auth: Optional[tuple] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.session: Session = session or requests.Session()
        
        if default_headers:
            self.session.headers.update(default_headers)
        if auth:
            self.session.auth = auth

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> "HttpClient":
        """Support context manager usage."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Response:
        if self.base_url and not url.startswith("http://") and not url.startswith("https://"):
            full_url = f"{self.base_url}/{url.lstrip('/')}"
        else:
            full_url = url

        attempt = 0
        while True:
            try:
                response = self.session.request(method, full_url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    self.logger.error("HTTP %s %s failed: %s", method, full_url, exc)
                    raise
                delay = self.backoff_factor * (2 ** attempt)
                self.logger.warning(
                    "HTTP %s %s failed on attempt %s, retrying in %.2f seconds",
                    method,
                    full_url,
                    attempt + 1,
                    delay,
                )
                time.sleep(delay)
                attempt += 1

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Response:
        return self._request("GET", url, params=params, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        return self._request("POST", url, data=data, json=json, **kwargs)

    def put(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        return self._request("PUT", url, data=data, json=json, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self._request("DELETE", url, **kwargs)

    def patch(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        return self._request("PATCH", url, data=data, json=json, **kwargs)

    @staticmethod
    def json(response: Response) -> Any:
        """Safely parse JSON response."""
        try:
            return response.json()
        except ValueError as exc:
            raise ValueError(f"Failed to decode JSON: {exc}") from exc
