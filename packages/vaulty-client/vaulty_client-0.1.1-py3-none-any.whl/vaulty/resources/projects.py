"""Project resource client."""

import urllib.parse

from ..http import HTTPClient
from ..models import (
    PaginatedResponse,
    ProjectResponse,
)
from ..retry import RetryConfig, retry_with_backoff


class ProjectResource:
    """Client for project management operations."""

    def __init__(self, http_client: HTTPClient, retry_config: RetryConfig | None = None):
        self.http_client = http_client
        self.retry_config = retry_config

    async def create(self, name: str, description: str | None = None) -> ProjectResponse:
        """Create a new project.

        Args:
            name: Project name
            description: Optional project description

        Returns:
            ProjectResponse with created project data
        """

        async def _create():
            response = await self.http_client.post(
                "/api/v1/projects", json={"name": name, "description": description}
            )
            return ProjectResponse(**response.json())

        return await retry_with_backoff(_create, self.retry_config)

    async def list(self, page: int = 1, page_size: int = 50) -> PaginatedResponse[ProjectResponse]:
        """List projects with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page (1-100)

        Returns:
            PaginatedResponse with projects
        """

        async def _list():
            response = await self.http_client.get(
                "/api/v1/projects", params={"page": page, "page_size": page_size}
            )
            data = response.json()
            return PaginatedResponse[ProjectResponse](
                items=[ProjectResponse(**item) for item in data["items"]],
                total=data["total"],
                page=data["page"],
                page_size=data["page_size"],
                total_pages=data["total_pages"],
                has_next=data["has_next"],
                has_previous=data["has_previous"],
            )

        return await retry_with_backoff(_list, self.retry_config)

    async def get(self, name: str) -> ProjectResponse:
        """Get project by name.

        Args:
            name: Project name

        Returns:
            ProjectResponse with project data
        """

        async def _get():
            # URL encode project name
            encoded_name = urllib.parse.quote(name, safe="")
            response = await self.http_client.get(f"/api/v1/projects/{encoded_name}")
            return ProjectResponse(**response.json())

        return await retry_with_backoff(_get, self.retry_config)

    async def update(self, name: str, description: str | None = None) -> ProjectResponse:
        """Update project.

        Args:
            name: Project name
            description: Optional project description

        Returns:
            ProjectResponse with updated project data
        """

        async def _update():
            encoded_name = urllib.parse.quote(name, safe="")
            response = await self.http_client.patch(
                f"/api/v1/projects/{encoded_name}",
                json={"description": description} if description else {},
            )
            return ProjectResponse(**response.json())

        return await retry_with_backoff(_update, self.retry_config)

    async def delete(self, name: str) -> None:
        """Delete project.

        Args:
            name: Project name
        """

        async def _delete():
            encoded_name = urllib.parse.quote(name, safe="")
            await self.http_client.delete(f"/api/v1/projects/{encoded_name}")

        await retry_with_backoff(_delete, self.retry_config)
