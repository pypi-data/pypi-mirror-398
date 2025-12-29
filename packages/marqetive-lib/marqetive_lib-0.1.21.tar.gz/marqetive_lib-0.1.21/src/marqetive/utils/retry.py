"""Retry utilities for handling transient failures in API calls.

This module provides decorators and utilities for implementing retry logic
with exponential backoff for async functions.
"""

import asyncio
import functools
import logging
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx

logger = logging.getLogger(__name__)

# Type variable for function return types
T = TypeVar("T")


@dataclass
class BackoffConfig:
    """Configuration for exponential backoff retry logic.

    Attributes:
        max_attempts: Maximum number of retry attempts (including first try).
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delay times.

    Example:
        >>> config = BackoffConfig(max_attempts=5, base_delay=2, max_delay=30)
        >>> print(config.calculate_delay(attempt=2))
        4.0
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0
    exponential_base: float = 2.0
    jitter: bool = True

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        Args:
            attempt: The attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        delay = min(
            self.base_delay * (self.exponential_base**attempt),
            self.max_delay,
        )

        if self.jitter:
            # Add random jitter (0-25% of delay)
            jitter_amount = delay * random.uniform(0, 0.25)
            delay += jitter_amount

        return delay


# Standard backoff configuration used across the library
STANDARD_BACKOFF = BackoffConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True,
)


def is_retryable_error(error: Exception) -> bool:
    """Determine if an error is retryable.

    Args:
        error: The exception to check.

    Returns:
        True if error is retryable, False otherwise.
    """
    # HTTP errors that are retryable
    if isinstance(error, httpx.HTTPStatusError):
        # Retry on 5xx server errors and 429 rate limit
        return bool(
            error.response.status_code >= 500 or error.response.status_code == 429
        )

    # Network/connection errors are retryable
    if isinstance(
        error, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
    ):
        return True

    # Any other httpx error (or not retryable)
    return isinstance(error, httpx.HTTPError)


def retry_async(
    config: BackoffConfig | None = None,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
    error_classifier: Callable[[Exception], bool] | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for retrying async functions with exponential backoff.

    Args:
        config: Backoff configuration (uses STANDARD_BACKOFF if None).
        retryable_exceptions: Tuple of exception types to retry.
                             If None, uses is_retryable_error().
        error_classifier: Custom function to determine if error is retryable.
                         Overrides retryable_exceptions if provided.

    Returns:
        Decorator function.

    Example:
        >>> @retry_async(config=BackoffConfig(max_attempts=5))
        ... async def fetch_data(url: str) -> dict:
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get(url)
        ...         response.raise_for_status()
        ...         return response.json()
    """
    if config is None:
        config = STANDARD_BACKOFF

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Determine if error is retryable
                    should_retry = False
                    if error_classifier is not None:
                        should_retry = error_classifier(e)
                    elif retryable_exceptions is not None:
                        should_retry = isinstance(e, retryable_exceptions)
                    else:
                        should_retry = is_retryable_error(e)

                    if not should_retry:
                        raise

                    # Check if we should retry
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed "
                            f"for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed "
                            f"for {func.__name__}: {str(e)}"
                        )
                        raise

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator


async def retry_async_func[T](
    func: Callable[..., Awaitable[T]],
    *args: Any,
    config: BackoffConfig | None = None,
    **kwargs: Any,
) -> T:
    """Retry an async function with exponential backoff.

    Alternative to the decorator for cases where you can't use decorators.

    Args:
        func: Async function to retry.
        *args: Positional arguments to pass to function.
        config: Backoff configuration (uses STANDARD_BACKOFF if None).
        **kwargs: Keyword arguments to pass to function.

    Returns:
        Function return value.

    Example:
        >>> async def fetch_data(url: str) -> dict:
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get(url)
        ...         response.raise_for_status()
        ...         return response.json()
        >>>
        >>> data = await retry_async_func(fetch_data, "https://api.example.com")
    """
    if config is None:
        config = STANDARD_BACKOFF

    last_exception: Exception | None = None

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            last_exception = e

            if not is_retryable_error(e):
                raise

            if attempt < config.max_attempts - 1:
                delay = config.calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_attempts} failed: {str(e)}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {config.max_attempts} attempts failed: {str(e)}")
                raise

    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")
