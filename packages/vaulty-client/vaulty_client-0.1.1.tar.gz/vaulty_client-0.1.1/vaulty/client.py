"""Main VaultyClient class."""

import os

from .auth import AuthHandler
from .http import HTTPClient
from .resources import (
    ActivityResource,
    CustomerResource,
    HealthResource,
    ProjectResource,
    SecretResource,
    TokenResource,
)
from .retry import RetryConfig


class VaultyClient:
    """Main client for Vaulty API.

    This is the primary interface for interacting with the Vaulty API. It provides
    access to all resources (customers, projects, secrets, tokens, activities, health)
    through convenient attributes.

    The client supports both API tokens (full-scope or project-scoped) and JWT tokens
    for authentication. It includes automatic retry logic with exponential backoff
    and rate limit handling.

    Example:
        >>> # Initialize with API token
        >>> client = VaultyClient(
        ...     base_url="https://api.vaulty.com",
        ...     api_token="vaulty_abc123..."
        ... )
        >>>
        >>> # Use async context manager for automatic cleanup
        >>> async with VaultyClient(api_token="vaulty_abc123...") as client:
        ...     secret = await client.secrets.get_value(
        ...         project_name="my-project",
        ...         key="API_KEY"
        ...     )
        ...     print(secret.value)
    """

    def __init__(
        self,
        base_url: str = "https://api.vaulty.com",
        api_token: str | None = None,
        jwt_token: str | None = None,
        email: str | None = None,
        password: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 2.0,
        rate_limit_retry: bool = True,
        api_version: str = "v1",
    ):
        """Initialize Vaulty client.

        Args:
            base_url: API base URL (default: https://api.vaulty.com)
            api_token: API token (full scope or project-scoped).
                       Tokens starting with 'vaulty_' are API tokens.
            jwt_token: JWT token obtained from login. Takes precedence over api_token.
            email: Customer email (for JWT login). Note: login() must be called explicitly.
            password: Customer password (for JWT login). Note: login() must be called explicitly.
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retry attempts for failed requests (default: 3)
            retry_backoff_factor: Exponential backoff multiplier (default: 2.0)
            rate_limit_retry: Enable automatic retry on rate limit errors (default: True)
            api_version: API version string (default: "v1")

        Note:
            If both api_token and jwt_token are provided, jwt_token takes precedence.
            For email/password login, call client.auth.login(email, password) explicitly.

        Raises:
            ValueError: If invalid configuration is provided
        """
        # Create HTTP client
        self.http_client = HTTPClient(
            base_url=base_url,
            api_token=api_token,
            jwt_token=jwt_token,
            timeout=timeout,
            api_version=api_version,
        )

        # Create auth handler
        self.auth = AuthHandler(self.http_client)

        # Create retry config
        self.retry_config = RetryConfig(
            max_retries=max_retries, backoff_factor=retry_backoff_factor
        )

        # Create resource clients
        self.customers = CustomerResource(self.http_client, self.retry_config)
        self.projects = ProjectResource(self.http_client, self.retry_config)
        self.secrets = SecretResource(self.http_client, self.retry_config)
        self.tokens = TokenResource(self.http_client, self.retry_config)
        self.activities = ActivityResource(self.http_client, self.retry_config)
        self.health = HealthResource(self.http_client, self.retry_config)

        # Handle email/password login
        if email and password:
            # This will be async, so we'll need to handle it differently
            # For now, users should call login() explicitly
            pass

    @classmethod
    def from_config(cls) -> "VaultyClient":
        """Load client from configuration file.

        Loads configuration from:
        1. Environment variables (highest priority)
        2. ~/.vaulty/config.yaml file
        3. Encrypted credentials file

        Returns:
            VaultyClient instance

        Raises:
            ValueError: If no authentication token is found
        """
        from pathlib import Path

        import yaml

        # Default values
        base_url = "https://api.vaulty.com"
        api_token = None
        jwt_token = None

        # Load from config file if it exists
        config_file = Path.home() / ".vaulty" / "config.yaml"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config_data = yaml.safe_load(f) or {}
                    if config_data.get("api_url"):
                        base_url = config_data["api_url"]
                    if config_data.get("api_token"):
                        api_token = config_data["api_token"]
                    if config_data.get("jwt_token"):
                        jwt_token = config_data["jwt_token"]
            except Exception:
                # If config file is invalid, continue with defaults
                pass

        # Override with environment variables (highest priority)
        if os.getenv("VAULTY_API_URL"):
            base_url = os.getenv("VAULTY_API_URL")
        if os.getenv("VAULTY_API_TOKEN"):
            api_token = os.getenv("VAULTY_API_TOKEN")
        if os.getenv("VAULTY_JWT_TOKEN"):
            jwt_token = os.getenv("VAULTY_JWT_TOKEN")

        # Try to load from encrypted credentials if no token found
        if not api_token and not jwt_token:
            from .cli.config import CLIConfig

            config = CLIConfig()
            auth_info = config.get_auth_info()
            if auth_info:
                if auth_info.get("type") == "api_token":
                    api_token = auth_info.get("token")
                elif auth_info.get("type") == "jwt":
                    jwt_token = auth_info.get("token")
                if auth_info.get("base_url"):
                    base_url = auth_info.get("base_url")

        if not api_token and not jwt_token:
            raise ValueError(
                "No authentication token found. "
                "Set VAULTY_API_TOKEN or VAULTY_JWT_TOKEN environment variable, "
                "or run 'vaulty login'"
            )

        return cls(base_url=base_url, api_token=api_token, jwt_token=jwt_token)

    @classmethod
    def from_env(cls) -> "VaultyClient":
        """Load client from environment variables.

        Returns:
            VaultyClient instance
        """
        base_url = os.getenv("VAULTY_API_URL", "https://api.vaulty.com")
        api_token = os.getenv("VAULTY_API_TOKEN")
        jwt_token = os.getenv("VAULTY_JWT_TOKEN")

        if api_token:
            return cls(base_url=base_url, api_token=api_token)
        if jwt_token:
            return cls(base_url=base_url, jwt_token=jwt_token)
        raise ValueError("VAULTY_API_TOKEN or VAULTY_JWT_TOKEN environment variable required")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close HTTP client connections.

        Closes all HTTP connections and cleans up resources. This should be called
        when the client is no longer needed, or use the async context manager.

        Example:
            >>> client = VaultyClient(api_token="vaulty_abc123...")
            >>> # ... use client ...
            >>> await client.close()
        """
        await self.http_client.close()
