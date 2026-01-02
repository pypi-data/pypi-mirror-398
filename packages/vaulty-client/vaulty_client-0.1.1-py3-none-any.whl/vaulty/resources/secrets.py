"""Secret resource client."""

import urllib.parse

from ..http import HTTPClient
from ..models import (
    PaginatedResponse,
    SecretResponse,
    SecretValueResponse,
)
from ..retry import RetryConfig, retry_with_backoff


class SecretResource:
    """Client for secret management operations."""

    def __init__(self, http_client: HTTPClient, retry_config: RetryConfig | None = None):
        self.http_client = http_client
        self.retry_config = retry_config

    async def create(self, project_name: str, key: str, value: str) -> SecretResponse:
        """Create a new secret.

        Creates a new secret in the specified project. The secret value will be
        encrypted by the server before storage.

        Args:
            project_name: Project name where the secret will be created
            key: Secret key (must be unique within the project)
            value: Secret value (will be encrypted by the server)

        Returns:
            SecretResponse: Created secret metadata (without value)

        Raises:
            VaultyValidationError: If key is invalid or already exists
            VaultyNotFoundError: If project doesn't exist
            VaultyAuthenticationError: If authentication fails
            VaultyAuthorizationError: If user lacks permission
            VaultyAPIError: For other API errors

        Example:
            >>> secret = await client.secrets.create(
            ...     project_name="my-project",
            ...     key="API_KEY",
            ...     value="secret123"
            ... )
            >>> print(secret.key)
            API_KEY
        """

        async def _create():
            encoded_name = urllib.parse.quote(project_name, safe="")
            response = await self.http_client.post(
                f"/api/v1/projects/{encoded_name}/secrets", json={"key": key, "value": value}
            )
            return SecretResponse(**response.json())

        return await retry_with_backoff(_create, self.retry_config)

    async def list(
        self, project_name: str | None = None, page: int = 1, page_size: int = 50
    ) -> PaginatedResponse[SecretResponse]:
        """List secrets in project with pagination.

        Args:
            project_name: Project name (required for full scope tokens, optional for project-scoped)
            page: Page number (1-indexed)
            page_size: Number of items per page (1-100)

        Returns:
            PaginatedResponse with secrets
        """

        async def _list():
            if project_name:
                encoded_name = urllib.parse.quote(project_name, safe="")
                url = f"/api/v1/projects/{encoded_name}/secrets"
            else:
                # For project-scoped tokens, get project name from projects list
                # Project-scoped tokens can list their own project
                try:
                    # Get projects list - for project-scoped tokens, this returns only their project
                    projects_response = await self.http_client.get(
                        "/api/v1/projects", params={"page": 1, "page_size": 1}
                    )
                    projects_data = projects_response.json()

                    # Handle both list and paginated response
                    projects_list = (
                        projects_data
                        if isinstance(projects_data, list)
                        else projects_data.get("items", [])
                    )

                    if projects_list and len(projects_list) > 0:
                        # Get project name from the first (and likely only) project
                        project_name_from_list = projects_list[0].get("name")
                        if project_name_from_list:
                            encoded_name = urllib.parse.quote(project_name_from_list, safe="")
                            url = f"/api/v1/projects/{encoded_name}/secrets"
                        else:
                            # Fallback: try using project ID
                            project_id = projects_list[0].get("id")
                            if project_id:
                                encoded_id = urllib.parse.quote(project_id, safe="")
                                url = f"/api/v1/projects/{encoded_id}/secrets"
                            else:
                                raise ValueError("Could not determine project name or ID")
                    else:
                        # No projects found, try fallback endpoint
                        url = "/api/v1/secrets"
                except Exception:
                    # Fallback to /api/v1/secrets if project lookup fails
                    url = "/api/v1/secrets"

            response = await self.http_client.get(
                url, params={"page": page, "page_size": page_size}
            )
            data = response.json()
            return PaginatedResponse[SecretResponse](
                items=[SecretResponse(**item) for item in data["items"]],
                total=data["total"],
                page=data["page"],
                page_size=data["page_size"],
                total_pages=data["total_pages"],
                has_next=data["has_next"],
                has_previous=data["has_previous"],
            )

        return await retry_with_backoff(_list, self.retry_config)

    async def get(self, project_name: str, key: str) -> SecretResponse:
        """Get secret metadata (without value).

        Args:
            project_name: Project name
            key: Secret key

        Returns:
            SecretResponse with secret metadata
        """

        async def _get():
            encoded_name = urllib.parse.quote(project_name, safe="")
            encoded_key = urllib.parse.quote(key, safe="")
            response = await self.http_client.get(
                f"/api/v1/projects/{encoded_name}/secrets/{encoded_key}"
            )
            return SecretResponse(**response.json())

        return await retry_with_backoff(_get, self.retry_config)

    async def get_value(self, project_name: str, key: str) -> SecretValueResponse:
        """Get secret value (decrypted).

        Retrieves the decrypted value of a secret. This is the only method that
        returns the actual secret value. Use `get()` for metadata only.

        Args:
            project_name: Project name containing the secret
            key: Secret key to retrieve

        Returns:
            SecretValueResponse: Secret with decrypted value

        Raises:
            VaultyNotFoundError: If secret or project doesn't exist
            VaultyAuthenticationError: If authentication fails
            VaultyAuthorizationError: If user lacks permission to read secret
            VaultyAPIError: For other API errors

        Example:
            >>> secret = await client.secrets.get_value(
            ...     project_name="my-project",
            ...     key="API_KEY"
            ... )
            >>> print(secret.value)
            secret123
        """

        async def _get_value():
            encoded_name = urllib.parse.quote(project_name, safe="")
            encoded_key = urllib.parse.quote(key, safe="")
            response = await self.http_client.get(
                f"/api/v1/projects/{encoded_name}/secrets/{encoded_key}"
            )
            return SecretValueResponse(**response.json())

        return await retry_with_backoff(_get_value, self.retry_config)

    async def update(self, project_name: str, key: str, value: str) -> SecretResponse:
        """Update secret value.

        Args:
            project_name: Project name
            key: Secret key
            value: New secret value

        Returns:
            SecretResponse with updated secret data
        """

        async def _update():
            encoded_name = urllib.parse.quote(project_name, safe="")
            encoded_key = urllib.parse.quote(key, safe="")
            response = await self.http_client.patch(
                f"/api/v1/projects/{encoded_name}/secrets/{encoded_key}", json={"value": value}
            )
            return SecretResponse(**response.json())

        return await retry_with_backoff(_update, self.retry_config)

    async def delete(self, project_name: str, key: str) -> None:
        """Delete secret.

        Args:
            project_name: Project name
            key: Secret key
        """

        async def _delete():
            encoded_name = urllib.parse.quote(project_name, safe="")
            encoded_key = urllib.parse.quote(key, safe="")
            await self.http_client.delete(f"/api/v1/projects/{encoded_name}/secrets/{encoded_key}")

        await retry_with_backoff(_delete, self.retry_config)
