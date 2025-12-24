"""
Retry logic utilities with exponential backoff and jitter

This module provides decorators and functions for retrying operations that may fail transiently.
"""
import time
import random
import logging
from typing import TypeVar, Callable, Optional, Tuple, Type
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds

    Example:
        >>> exponential_backoff_with_jitter(0)  # ~1 second
        >>> exponential_backoff_with_jitter(1)  # ~2 seconds
        >>> exponential_backoff_with_jitter(2)  # ~4 seconds
        >>> exponential_backoff_with_jitter(10)  # ~60 seconds (capped at max_delay)
    """
    # Calculate exponential delay: base * 2^attempt
    delay = min(base_delay * (2 ** attempt), max_delay)

    # Add jitter: random value between 50% and 100% of delay
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function with exponential backoff on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called before each retry

    Returns:
        Decorated function

    Example:
        >>> @retry_with_backoff(max_attempts=3, base_delay=1.0)
        ... def fetch_data():
        ...     response = requests.get('https://api.example.com/data')
        ...     response.raise_for_status()
        ...     return response.json()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Retry succeeded on attempt {attempt + 1}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt + 1,
                                'max_attempts': max_attempts
                            }
                        )
                    return result

                except exceptions as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"All {max_attempts} attempts failed",
                            exc_info=True,
                            extra={
                                'function': func.__name__,
                                'error': str(e)
                            }
                        )
                        raise

                    # Calculate delay and wait
                    delay = exponential_backoff_with_jitter(
                        attempt,
                        base_delay=base_delay,
                        max_delay=max_delay
                    )

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed, retrying in {delay:.2f}s",
                        extra={
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'max_attempts': max_attempts,
                            'delay': delay,
                            'error': str(e)
                        }
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1, delay)

                    time.sleep(delay)

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic error: no exception raised")

        return wrapper
    return decorator


def retry_async_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator to retry an async function with exponential backoff on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated async function

    Example:
        >>> @retry_async_with_backoff(max_attempts=3)
        ... async def fetch_data():
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get('https://api.example.com/data') as response:
        ...             return await response.json()
    """
    import asyncio

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Async retry succeeded on attempt {attempt + 1}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt + 1
                            }
                        )
                    return result

                except exceptions as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"All {max_attempts} async attempts failed",
                            exc_info=True,
                            extra={
                                'function': func.__name__,
                                'error': str(e)
                            }
                        )
                        raise

                    # Calculate delay and wait
                    delay = exponential_backoff_with_jitter(
                        attempt,
                        base_delay=base_delay,
                        max_delay=max_delay
                    )

                    logger.warning(
                        f"Async attempt {attempt + 1}/{max_attempts} failed, retrying in {delay:.2f}s",
                        extra={
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'delay': delay,
                            'error': str(e)
                        }
                    )

                    await asyncio.sleep(delay)

            if last_exception:
                raise last_exception
            raise RuntimeError("Async retry logic error: no exception raised")

        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    import requests

    @retry_with_backoff(
        max_attempts=3,
        base_delay=1.0,
        exceptions=(requests.RequestException,)
    )
    def fetch_url(url: str) -> str:
        """Fetch URL content with retry logic."""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    # This will retry up to 3 times with exponential backoff
    try:
        content = fetch_url('https://httpstat.us/500')
        print(f"Success: {content[:100]}")
    except requests.RequestException as e:
        print(f"Failed after retries: {e}")
