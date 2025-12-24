"""Retry utilities for UniFi API calls."""

import asyncio
import random
from builtins import BaseException
from collections.abc import Callable
from functools import wraps
from typing import Any


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
) -> Callable[[Callable], Callable]:
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor by which delay increases after each retry
        jitter: Whether to add random jitter to delay to prevent thundering herd
        exceptions: Tuple of exceptions that trigger a retry
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: BaseException | None = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:  # Last attempt
                        if last_exception:
                            raise last_exception

                    # Calculate delay with exponential backoff
                    delay = _calculate_delay(
                        base_delay, backoff_factor, attempt, max_delay, jitter
                    )

                    await asyncio.sleep(delay)

            # This should never be reached, but included for type safety
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def _calculate_delay(
    base_delay: float,
    backoff_factor: float,
    attempt: int,
    max_delay: float,
    jitter: bool,
) -> float:
    """Calculate the delay with exponential backoff and optional jitter."""
    # Calculate delay with exponential backoff
    delay = min(base_delay * (backoff_factor**attempt), max_delay)

    # Add jitter to prevent thundering herd
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


async def retry_with_backoff(
    func: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: The async function to call
        *args: Arguments to pass to the function
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor by which delay increases after each retry
        jitter: Whether to add random jitter to delay
        exceptions: Tuple of exceptions that trigger a retry
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call

    Raises:
        The last exception if all attempts fail
    """
    last_exception: BaseException | None = None

    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e

            if attempt == max_attempts - 1:  # Last attempt
                if last_exception:
                    raise last_exception

            # Calculate delay with exponential backoff
            delay = _calculate_delay(
                base_delay, backoff_factor, attempt, max_delay, jitter
            )

            await asyncio.sleep(delay)

    # This should never be reached, but included for type safety
    if last_exception:
        raise last_exception
