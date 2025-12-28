"""
msgmodel.retry
~~~~~~~~~~~~~~

Retry logic with exponential backoff for transient failures.

Provides decorators and utilities for automatically retrying operations
that may fail due to temporary issues like rate limits or network errors.
"""

import logging
import random
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type, TypeVar, Union

from .exceptions import (
    RateLimitError,
    ServiceUnavailableError,
    APIError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default exceptions that should trigger a retry
DEFAULT_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    RateLimitError,
    ServiceUnavailableError,
)


def is_retryable_status_code(status_code: Optional[int]) -> bool:
    """
    Check if an HTTP status code indicates a retryable error.
    
    Args:
        status_code: HTTP status code to check
        
    Returns:
        True if the status code indicates a retryable error
    """
    if status_code is None:
        return False
    return status_code in (429, 500, 502, 503, 504)


def calculate_backoff(
    attempt: int,
    backoff_factor: float = 1.0,
    max_backoff: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate exponential backoff delay with optional jitter.
    
    Args:
        attempt: The current attempt number (0-indexed)
        backoff_factor: Base backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        jitter: Whether to add random jitter to prevent thundering herd
        
    Returns:
        Delay in seconds before the next retry
    """
    delay = min(backoff_factor * (2 ** attempt), max_backoff)
    if jitter:
        delay = delay * (0.5 + random.random())  # 50-150% of calculated delay
    return delay


def retry_on_transient_error(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    max_backoff: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = DEFAULT_RETRYABLE_EXCEPTIONS,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry on transient errors with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Initial backoff time in seconds (default: 1.0)
        max_backoff: Maximum backoff time in seconds (default: 60.0)
        retryable_exceptions: Tuple of exception types to retry on
        on_retry: Optional callback(exception, attempt, delay) called before each retry
        
    Returns:
        Decorated function that automatically retries on transient errors
        
    Example:
        >>> @retry_on_transient_error(max_retries=3, backoff_factor=1.0)
        ... def make_api_call():
        ...     return requests.get("https://api.example.com/data")
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt >= max_retries:
                        # PRIVACY: Do not log error details - may contain prompt/response content
                        logger.warning(
                            "Max retries (%d) exceeded for %s: %s",
                            max_retries,
                            func.__name__,
                            type(e).__name__,  # Only log exception type, not message
                            extra={
                                "function": func.__name__,
                                "attempts": attempt + 1,
                                "error_type": type(e).__name__,  # Redacted for privacy
                            }
                        )
                        raise
                    
                    # Check for retry_after hint from RateLimitError
                    delay = calculate_backoff(attempt, backoff_factor, max_backoff)
                    if isinstance(e, RateLimitError) and e.retry_after:
                        delay = max(delay, e.retry_after)
                    
                    # PRIVACY: Do not log error details - may contain prompt/response content
                    logger.info(
                        "Retrying %s after %.2fs (attempt %d/%d): %s",
                        func.__name__,
                        delay,
                        attempt + 1,
                        max_retries,
                        type(e).__name__,  # Only log exception type, not message
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "delay": delay,
                            "error_type": type(e).__name__,  # Redacted for privacy
                        }
                    )
                    
                    if on_retry:
                        on_retry(e, attempt, delay)
                    
                    time.sleep(delay)
                    
                except APIError as e:
                    # Check if this APIError has a retryable status code
                    if is_retryable_status_code(e.status_code):
                        last_exception = e
                        
                        if attempt >= max_retries:
                            logger.warning(
                                "Max retries (%d) exceeded for %s",
                                max_retries,
                                func.__name__,
                            )
                            raise
                        
                        delay = calculate_backoff(attempt, backoff_factor, max_backoff)
                        logger.info(
                            "Retrying %s after %.2fs (attempt %d/%d): HTTP %d",
                            func.__name__,
                            delay,
                            attempt + 1,
                            max_retries,
                            e.status_code,
                        )
                        
                        if on_retry:
                            on_retry(e, attempt, delay)
                        
                        time.sleep(delay)
                    else:
                        # Non-retryable API error
                        raise
            
            # Should not reach here, but satisfy type checker
            if last_exception:  # pragma: no cover
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")  # pragma: no cover
        
        return wrapper
    return decorator


class RetryConfig:
    """
    Configuration class for retry behavior.
    
    Provides a reusable configuration object for retry settings.
    
    Attributes:
        max_retries: Maximum number of retry attempts
        backoff_factor: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        retryable_exceptions: Tuple of exception types to retry on
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        max_backoff: float = 60.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = DEFAULT_RETRYABLE_EXCEPTIONS,
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        self.retryable_exceptions = retryable_exceptions
    
    def decorator(self) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Return a retry decorator with this configuration."""
        return retry_on_transient_error(
            max_retries=self.max_retries,
            backoff_factor=self.backoff_factor,
            max_backoff=self.max_backoff,
            retryable_exceptions=self.retryable_exceptions,
        )


# Pre-configured retry configurations for common use cases
RETRY_AGGRESSIVE = RetryConfig(max_retries=5, backoff_factor=0.5, max_backoff=30.0)
RETRY_CONSERVATIVE = RetryConfig(max_retries=3, backoff_factor=2.0, max_backoff=120.0)
RETRY_DEFAULT = RetryConfig()
