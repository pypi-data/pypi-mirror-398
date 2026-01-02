"""Authentication handling for Vaulty SDK."""

from .http import HTTPClient
from .logging import get_logger

logger = get_logger(__name__)


class AuthHandler:
    """Handles authentication for Vaulty API."""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client
        self._jwt_token: str | None = None

    async def login(self, email: str, password: str) -> dict:
        """Login with email/password and get JWT token.

        Args:
            email: Customer email
            password: Customer password

        Returns:
            Token response with access_token
        """
        logger.info(f"Attempting login for user: {email}")
        try:
            response = await self.http_client.post(
                "/api/customers/login", json={"email": email, "password": password}
            )
            data = response.json()
            self._jwt_token = data.get("access_token")

            # Update HTTP client with new JWT token
            if self._jwt_token:
                logger.info("Login successful, JWT token obtained")
                self.http_client.jwt_token = self._jwt_token
                self.http_client.auth_header = f"Bearer {self._jwt_token}"
                # Recreate client to update headers
                await self.http_client.close()
            else:
                logger.warning("Login response missing access_token")

            return data
        except Exception:
            logger.error(f"Login failed for user: {email}", exc_info=True)
            raise

    @property
    def jwt_token(self) -> str | None:
        """Get current JWT token."""
        return self._jwt_token

    @jwt_token.setter
    def jwt_token(self, token: str):
        """Set JWT token."""
        self._jwt_token = token
        self.http_client.jwt_token = token
        self.http_client.auth_header = f"Bearer {token}"
