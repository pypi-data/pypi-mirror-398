"""Retry logic with exponential backoff."""

import asyncio
import random
from collections.abc import Callable
from typing import TypeVar

from .exceptions import VaultyAPIError, VaultyRateLimitError
from .logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter


async def retry_with_backoff(
    func: Callable[..., T], config: RetryConfig = None, *args, **kwargs
) -> T:
    """Retry a function with exponential backoff.

    Args:
        func: Async function to retry
        config: Retry configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func

    Raises:
        VaultyAPIError: If all retries fail
    """
    if config is None:
        config = RetryConfig()

    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except VaultyRateLimitError as e:
            # Handle rate limit errors specially
            last_exception = e
            if attempt < config.max_retries:
                # Use retry_after if provided, otherwise calculate delay
                delay = (
                    e.retry_after
                    if e.retry_after
                    else config.initial_delay * (config.backoff_factor**attempt)
                )
                delay = min(delay, config.max_delay)
                if config.jitter:
                    delay += random.uniform(0, delay * 0.1)
                logger.info(
                    f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1}/{config.max_retries + 1})",
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": config.max_retries,
                        "delay": delay,
                    },
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"Rate limit retry exhausted after {config.max_retries + 1} attempts")
                raise
        except VaultyAPIError as e:
            # Retry on 5xx errors, don't retry on 4xx (except rate limit)
            if e.status_code >= 500 and attempt < config.max_retries:
                last_exception = e
                delay = config.initial_delay * (config.backoff_factor**attempt)
                delay = min(delay, config.max_delay)
                if config.jitter:
                    delay += random.uniform(0, delay * 0.1)
                logger.warning(
                    f"Server error {e.status_code}, retrying in {delay:.2f}s (attempt {attempt + 1}/{config.max_retries + 1})",
                    extra={"attempt": attempt + 1, "status_code": e.status_code, "delay": delay},
                )
                await asyncio.sleep(delay)
            else:
                raise
        except Exception as e:
            # Retry on network errors, etc.
            last_exception = e
            if attempt < config.max_retries:
                delay = config.initial_delay * (config.backoff_factor**attempt)
                delay = min(delay, config.max_delay)
                if config.jitter:
                    delay += random.uniform(0, delay * 0.1)
                logger.warning(
                    f"Request failed: {type(e).__name__}, retrying in {delay:.2f}s (attempt {attempt + 1}/{config.max_retries + 1})",
                    exc_info=True,
                    extra={"attempt": attempt + 1, "error_type": type(e).__name__, "delay": delay},
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"Retry exhausted after {config.max_retries + 1} attempts", exc_info=True
                )
                raise

    if last_exception:
        raise last_exception
