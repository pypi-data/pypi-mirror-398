"""Retry decorator with exponential backoff."""

import asyncio
import functools
import logging
import random
from typing import Any, Awaitable, Callable, TypeVar

from .exceptions import (
    MattermostConnectionError,
    MattermostRateLimitError,
    MattermostServerError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

RETRYABLE_STATUS_CODES = {500, 502, 503, 504, 429}


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for retrying async operations with exponential backoff.

    Only retries on:
    - MattermostServerError with retryable status codes (500, 502, 503, 504)
    - MattermostRateLimitError (429)
    - MattermostConnectionError
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except MattermostServerError as e:
                    if e.status_code not in RETRYABLE_STATUS_CODES:
                        raise
                    last_exception = e
                except MattermostRateLimitError as e:
                    last_exception = e
                    # Use Retry-After header if available
                    if e.retry_after is not None and attempt < max_attempts:
                        sleep_time = min(e.retry_after, max_delay)
                        logger.warning(
                            "Rate limited. Retry %d/%d for %s after %.2fs (from Retry-After header)",
                            attempt,
                            max_attempts,
                            func.__name__,
                            sleep_time,
                        )
                        await asyncio.sleep(sleep_time)
                        continue
                except MattermostConnectionError as e:
                    last_exception = e

                if attempt < max_attempts:
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay,
                    )
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = delay + jitter

                    logger.warning(
                        "Retry %d/%d for %s after %.2fs. Error: %s",
                        attempt,
                        max_attempts,
                        func.__name__,
                        sleep_time,
                        last_exception,
                    )
                    await asyncio.sleep(sleep_time)

            if last_exception:
                raise last_exception
            raise MattermostConnectionError("Max retries exceeded")

        return wrapper

    return decorator
