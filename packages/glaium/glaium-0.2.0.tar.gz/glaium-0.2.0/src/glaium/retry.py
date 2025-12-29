"""Retry logic with exponential backoff for Glaium SDK."""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from glaium.exceptions import RateLimitError, ServerError, TimeoutError

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    """Maximum number of retry attempts."""
    initial_delay: float = 1.0
    """Initial delay in seconds before first retry."""
    backoff_multiplier: float = 2.0
    """Multiplier for exponential backoff."""
    max_delay: float = 60.0
    """Maximum delay between retries."""
    jitter: bool = True
    """Add random jitter to prevent thundering herd."""

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = min(
            self.initial_delay * (self.backoff_multiplier ** attempt),
            self.max_delay,
        )
        if self.jitter:
            delay = delay * (0.5 + random.random())
        return delay


def should_retry(exception: Exception) -> bool:
    """Determine if an exception should trigger a retry."""
    if isinstance(exception, RateLimitError):
        return True
    if isinstance(exception, ServerError):
        return True
    if isinstance(exception, (ConnectionError, TimeoutError)):
        return True
    return False


def retry_sync(
    func: Callable[[], T],
    config: RetryConfig | None = None,
) -> T:
    """
    Execute a function with retry logic (synchronous).

    Args:
        func: Function to execute.
        config: Retry configuration.

    Returns:
        Result from the function.

    Raises:
        The last exception if all retries are exhausted.
    """
    config = config or RetryConfig()
    last_exception: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if not should_retry(e) or attempt >= config.max_retries:
                raise

            delay = config.get_delay(attempt)

            # Check for rate limit retry-after header
            if isinstance(e, RateLimitError) and e.retry_after:
                delay = max(delay, e.retry_after)

            time.sleep(delay)

    # Should not reach here, but for type safety
    raise last_exception  # type: ignore


async def retry_async(
    func: Callable[[], T],
    config: RetryConfig | None = None,
) -> T:
    """
    Execute a function with retry logic (asynchronous).

    Args:
        func: Async function to execute.
        config: Retry configuration.

    Returns:
        Result from the function.

    Raises:
        The last exception if all retries are exhausted.
    """
    config = config or RetryConfig()
    last_exception: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            result = func()
            if asyncio.iscoroutine(result):
                return await result
            return result  # type: ignore
        except Exception as e:
            last_exception = e
            if not should_retry(e) or attempt >= config.max_retries:
                raise

            delay = config.get_delay(attempt)

            # Check for rate limit retry-after header
            if isinstance(e, RateLimitError) and e.retry_after:
                delay = max(delay, e.retry_after)

            await asyncio.sleep(delay)

    # Should not reach here, but for type safety
    raise last_exception  # type: ignore
