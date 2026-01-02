"""Customer resource client."""

from ..http import HTTPClient
from ..models import (
    CustomerResponse,
    CustomerSettingsResponse,
)
from ..retry import RetryConfig, retry_with_backoff


class CustomerResource:
    """Client for customer management operations."""

    def __init__(self, http_client: HTTPClient, retry_config: RetryConfig | None = None):
        self.http_client = http_client
        self.retry_config = retry_config

    async def register(self, email: str, password: str) -> CustomerResponse:
        """Register a new customer.

        Args:
            email: Customer email
            password: Customer password (min 8 characters)

        Returns:
            CustomerResponse with customer data
        """

        async def _register():
            response = await self.http_client.post(
                "/api/v1/customers/register", json={"email": email, "password": password}
            )
            return CustomerResponse(**response.json())

        return await retry_with_backoff(_register, self.retry_config)

    async def login(self, email: str, password: str) -> dict:
        """Login and get JWT token.

        Args:
            email: Customer email
            password: Customer password

        Returns:
            Token response with access_token
        """

        async def _login():
            response = await self.http_client.post(
                "/api/v1/customers/login", json={"email": email, "password": password}
            )
            return response.json()

        return await retry_with_backoff(_login, self.retry_config)

    async def get_current(self) -> CustomerResponse:
        """Get current customer info.

        Returns:
            CustomerResponse with current customer data
        """

        async def _get_current():
            response = await self.http_client.get("/api/v1/customers/me")
            return CustomerResponse(**response.json())

        return await retry_with_backoff(_get_current, self.retry_config)

    async def update_settings(
        self,
        rate_limit_enabled: bool | None = None,
        rate_limit_requests_per_minute: int | None = None,
        rate_limit_auth_attempts_per_minute: int | None = None,
        cache_ttl_customer: int | None = None,
        cache_ttl_project: int | None = None,
        cache_ttl_token: int | None = None,
        cache_ttl_dek: int | None = None,
    ) -> CustomerSettingsResponse:
        """Update customer settings.

        Args:
            rate_limit_enabled: Enable/disable rate limiting
            rate_limit_requests_per_minute: Rate limit for API requests
            rate_limit_auth_attempts_per_minute: Rate limit for auth endpoints
            cache_ttl_customer: Cache TTL for customer data
            cache_ttl_project: Cache TTL for project data
            cache_ttl_token: Cache TTL for token data
            cache_ttl_dek: Cache TTL for DEK data

        Returns:
            CustomerSettingsResponse with updated settings
        """
        data = {}
        if rate_limit_enabled is not None:
            data["rate_limit_enabled"] = rate_limit_enabled
        if rate_limit_requests_per_minute is not None:
            data["rate_limit_requests_per_minute"] = rate_limit_requests_per_minute
        if rate_limit_auth_attempts_per_minute is not None:
            data["rate_limit_auth_attempts_per_minute"] = rate_limit_auth_attempts_per_minute
        if cache_ttl_customer is not None:
            data["cache_ttl_customer"] = cache_ttl_customer
        if cache_ttl_project is not None:
            data["cache_ttl_project"] = cache_ttl_project
        if cache_ttl_token is not None:
            data["cache_ttl_token"] = cache_ttl_token
        if cache_ttl_dek is not None:
            data["cache_ttl_dek"] = cache_ttl_dek

        async def _update_settings():
            response = await self.http_client.patch("/api/v1/customers/settings", json=data)
            return CustomerSettingsResponse(**response.json())

        return await retry_with_backoff(_update_settings, self.retry_config)

    async def get_settings(self) -> CustomerSettingsResponse:
        """Get customer settings.

        Returns:
            CustomerSettingsResponse with current settings
        """

        async def _get_settings():
            response = await self.http_client.get("/api/v1/customers/settings")
            return CustomerSettingsResponse(**response.json())

        return await retry_with_backoff(_get_settings, self.retry_config)
