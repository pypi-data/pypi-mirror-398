"""Health check resource client."""

from typing import Any

from ..http import HTTPClient
from ..retry import RetryConfig, retry_with_backoff


class HealthResource:
    """Client for health check operations."""

    def __init__(self, http_client: HTTPClient, retry_config: RetryConfig = None):
        self.http_client = http_client
        self.retry_config = retry_config

    async def check(self) -> dict[str, Any]:
        """Health check.

        Returns:
            Health status dictionary
        """

        async def _check():
            # Health endpoints are at root, not under /api
            response = await self.http_client.get("/health")
            return response.json()

        return await retry_with_backoff(_check, self.retry_config)

    async def ready(self) -> dict[str, Any]:
        """Readiness check.

        Returns:
            Readiness status dictionary
        """

        async def _ready():
            # Health endpoints are at root, not under /api
            response = await self.http_client.get("/health/ready")
            return response.json()

        return await retry_with_backoff(_ready, self.retry_config)

    async def live(self) -> dict[str, Any]:
        """Liveness check.

        Returns:
            Liveness status dictionary
        """

        async def _live():
            # Health endpoints are at root, not under /api
            response = await self.http_client.get("/health/live")
            return response.json()

        return await retry_with_backoff(_live, self.retry_config)
