"""Logging configuration for Vaulty SDK."""

import logging
import os
import sys


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(_get_log_level())

        # Create console handler
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(_get_log_level())

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

    return logger


def _get_log_level() -> int:
    """Get log level from environment variable.

    Returns:
        Log level (default: WARNING)
    """
    level_str = os.getenv("VAULTY_LOG_LEVEL", "WARNING").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str, logging.WARNING)


def sanitize_sensitive_data(data: dict) -> dict:
    """Sanitize sensitive data from logs.

    Args:
        data: Dictionary that may contain sensitive data

    Returns:
        Dictionary with sensitive fields redacted
    """
    sensitive_keys = {
        "password",
        "token",
        "api_token",
        "jwt_token",
        "access_token",
        "secret",
        "value",
        "authorization",
        "auth_header",
    }

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_data(value)
        else:
            sanitized[key] = value

    return sanitized
