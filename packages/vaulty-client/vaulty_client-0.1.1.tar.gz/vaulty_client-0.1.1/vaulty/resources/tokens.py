"""Token resource client."""

from ..http import HTTPClient
from ..models import (
    PaginatedResponse,
    TokenResponse,
)
from ..retry import RetryConfig, retry_with_backoff


class TokenResource:
    """Client for token management operations."""

    def __init__(self, http_client: HTTPClient, retry_config: RetryConfig | None = None):
        self.http_client = http_client
        self.retry_config = retry_config

    async def create(
        self, scope: str, description: str | None = None, password: str | None = None
    ) -> TokenResponse:
        """Create API token (full scope or project-scoped).

        Args:
            scope: Token scope ("full", "read", "write", or "project:{project_id}:read/write")
            description: Optional token description
            password: Customer password (required for first token if no DEK exists)

        Returns:
            TokenResponse with token data (includes token value on creation)
        """

        async def _create():
            data = {"scope": scope}
            if description:
                data["description"] = description
            if password:
                data["password"] = password

            response = await self.http_client.post("/api/v1/tokens", json=data)
            return TokenResponse(**response.json())

        return await retry_with_backoff(_create, self.retry_config)

    async def list(self, page: int = 1, page_size: int = 50) -> PaginatedResponse[TokenResponse]:
        """List tokens with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page (1-100)

        Returns:
            PaginatedResponse with tokens
        """

        async def _list():
            response = await self.http_client.get(
                "/api/v1/tokens", params={"page": page, "page_size": page_size}
            )
            data = response.json()

            # Handle both paginated response and direct list
            if isinstance(data, list):
                # Direct list response
                items = [TokenResponse(**item) for item in data]
                total = len(items)
                total_pages = 1 if total <= page_size else (total + page_size - 1) // page_size
                return PaginatedResponse[TokenResponse](
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    has_next=page < total_pages,
                    has_previous=page > 1,
                )
            # Paginated response
            return PaginatedResponse[TokenResponse](
                items=[TokenResponse(**item) for item in data["items"]],
                total=data["total"],
                page=data["page"],
                page_size=data["page_size"],
                total_pages=data["total_pages"],
                has_next=data["has_next"],
                has_previous=data["has_previous"],
            )

        return await retry_with_backoff(_list, self.retry_config)

    async def delete(self, token_id: str) -> None:
        """Delete token.

        Args:
            token_id: Token ID
        """

        async def _delete():
            await self.http_client.delete(f"/api/v1/tokens/{token_id}")

        await retry_with_backoff(_delete, self.retry_config)
