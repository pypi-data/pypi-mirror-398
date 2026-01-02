"""Vaulty Python SDK."""

from importlib.metadata import PackageNotFoundError, version

from .client import VaultyClient
from .exceptions import (
    VaultyAPIError,
    VaultyAuthenticationError,
    VaultyAuthorizationError,
    VaultyError,
    VaultyNotFoundError,
    VaultyRateLimitError,
    VaultyValidationError,
)

__all__ = [
    "VaultyAPIError",
    "VaultyAuthenticationError",
    "VaultyAuthorizationError",
    "VaultyClient",
    "VaultyError",
    "VaultyNotFoundError",
    "VaultyRateLimitError",
    "VaultyValidationError",
]

try:
    __version__ = version("vaulty-client")
except PackageNotFoundError:
    # Package not installed, use version from pyproject.toml
    __version__ = "0.1.1"
