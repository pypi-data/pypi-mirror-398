"""HTTP client wrapper for Vaulty API."""

from typing import Any

import httpx

from .exceptions import (
    VaultyAPIError,
    VaultyAuthenticationError,
    VaultyAuthorizationError,
    VaultyNotFoundError,
    VaultyRateLimitError,
    VaultyValidationError,
)
from .logging import get_logger, sanitize_sensitive_data

logger = get_logger(__name__)


class HTTPClient:
    """HTTP client wrapper for Vaulty API."""

    def __init__(
        self,
        base_url: str,
        api_token: str | None = None,
        jwt_token: str | None = None,
        timeout: float = 30.0,
        api_version: str = "v1",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.jwt_token = jwt_token
        self.timeout = timeout
        self.api_version = api_version

        # Determine auth header
        if api_token:
            self.auth_header = f"Bearer {api_token}"
        elif jwt_token:
            self.auth_header = f"Bearer {jwt_token}"
        else:
            self.auth_header = None

        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "API-Version": self.api_version,
            }
            if self.auth_header:
                headers["Authorization"] = self.auth_header

            self._client = httpx.AsyncClient(
                base_url=self.base_url, headers=headers, timeout=self.timeout
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _raise_for_status(self, response: httpx.Response):
        """Raise appropriate exception for error status codes."""
        if response.is_success:
            return

        status_code = response.status_code
        detail = None

        try:
            error_data = response.json()
            detail = error_data.get("detail", str(error_data))
        except Exception:
            detail = response.text or f"HTTP {status_code}"

        # Log error before raising
        logger.warning(
            f"HTTP {status_code} error: {detail}",
            extra={"status_code": status_code, "detail": detail},
        )

        if status_code == 401:
            raise VaultyAuthenticationError(f"Authentication failed: {detail}", status_code, detail)
        if status_code == 403:
            raise VaultyAuthorizationError(
                f"Insufficient permissions: {detail}", status_code, detail
            )
        if status_code == 404:
            raise VaultyNotFoundError(f"Resource not found: {detail}", status_code, detail)
        if status_code == 400:
            raise VaultyValidationError(f"Validation error: {detail}", status_code, detail)
        if status_code == 429:
            retry_after = None
            if "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except ValueError:
                    pass
            raise VaultyRateLimitError(
                f"Rate limit exceeded: {detail}", status_code, detail, retry_after
            )
        raise VaultyAPIError(f"API error: {detail}", status_code, detail)

    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request."""
        client = await self._get_client()

        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        # Log request (sanitize sensitive data)
        logger.debug(
            f"Making {method} request to {path}",
            extra={
                "method": method,
                "path": path,
                "params": params,
                "json": sanitize_sensitive_data(json) if json else None,
            },
        )

        try:
            response = await client.request(
                method=method, url=path, params=params, json=json, **kwargs
            )

            logger.debug(
                f"Response {response.status_code} for {method} {path}",
                extra={"status_code": response.status_code, "path": path},
            )

            self._raise_for_status(response)
            return response
        except Exception as e:
            logger.error(
                f"Request failed: {method} {path}",
                exc_info=True,
                extra={"method": method, "path": path, "error": str(e)},
            )
            raise

    async def get(
        self, path: str, params: dict[str, Any] | None = None, **kwargs
    ) -> httpx.Response:
        """GET request."""
        return await self.request("GET", path, params=params, **kwargs)

    async def post(self, path: str, json: dict[str, Any] | None = None, **kwargs) -> httpx.Response:
        """POST request."""
        return await self.request("POST", path, json=json, **kwargs)

    async def put(self, path: str, json: dict[str, Any] | None = None, **kwargs) -> httpx.Response:
        """PUT request."""
        return await self.request("PUT", path, json=json, **kwargs)

    async def patch(
        self, path: str, json: dict[str, Any] | None = None, **kwargs
    ) -> httpx.Response:
        """PATCH request."""
        return await self.request("PATCH", path, json=json, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """DELETE request."""
        return await self.request("DELETE", path, **kwargs)
