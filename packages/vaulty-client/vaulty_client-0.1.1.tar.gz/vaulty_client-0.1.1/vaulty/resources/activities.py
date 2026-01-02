"""Activity resource client."""

from datetime import datetime

from ..http import HTTPClient
from ..models import (
    ActivityResponse,
    PaginatedResponse,
)
from ..retry import RetryConfig, retry_with_backoff


class ActivityResource:
    """Client for activity management operations."""

    def __init__(self, http_client: HTTPClient, retry_config: RetryConfig | None = None):
        self.http_client = http_client
        self.retry_config = retry_config

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        method: str | None = None,
        resource_id: str | None = None,
        search: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> PaginatedResponse[ActivityResponse]:
        """List activities with filters and pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page (1-100)
            action: Filter by action (e.g., "create_secret")
            method: Filter by HTTP method (e.g., "POST")
            resource_id: Filter by resource ID
            search: Search term
            start_date: Filter activities after this date
            end_date: Filter activities before this date

        Returns:
            PaginatedResponse with activities
        """

        async def _list():
            params = {"page": page, "page_size": page_size}
            if action:
                params["action"] = action
            if method:
                params["method"] = method
            if resource_id:
                params["resource_id"] = resource_id
            if search:
                params["search"] = search
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()

            response = await self.http_client.get("/api/v1/activities", params=params)
            data = response.json()

            # Parse datetime strings back to datetime objects
            items = []
            for item in data["items"]:
                # Parse created_at
                if isinstance(item.get("created_at"), str):
                    item["created_at"] = datetime.fromisoformat(
                        item["created_at"].replace("Z", "+00:00")
                    )
                items.append(ActivityResponse(**item))

            return PaginatedResponse[ActivityResponse](
                items=items,
                total=data["total"],
                page=data["page"],
                page_size=data["page_size"],
                total_pages=data["total_pages"],
                has_next=data["has_next"],
                has_previous=data["has_previous"],
            )

        return await retry_with_backoff(_list, self.retry_config)
