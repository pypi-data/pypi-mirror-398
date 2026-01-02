"""Custom exceptions for Vaulty SDK."""


class VaultyError(Exception):
    """Base exception for all Vaulty errors."""


class VaultyAPIError(VaultyError):
    """API returned an error response."""

    def __init__(self, message: str, status_code: int, detail: str | None = None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class VaultyAuthenticationError(VaultyAPIError):
    """Authentication failed."""


class VaultyAuthorizationError(VaultyAPIError):
    """Insufficient permissions."""


class VaultyNotFoundError(VaultyAPIError):
    """Resource not found."""


class VaultyValidationError(VaultyAPIError):
    """Request validation failed."""


class VaultyRateLimitError(VaultyAPIError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        status_code: int,
        detail: str | None = None,
        retry_after: int | None = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code, detail)
