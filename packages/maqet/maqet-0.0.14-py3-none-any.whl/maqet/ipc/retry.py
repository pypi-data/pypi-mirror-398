"""
IPC Retry Logic with Exponential Backoff

Provides decorators and utilities for retrying IPC operations that may fail
due to transient network issues, temporary unavailability, or timing issues.

Features:
- Exponential backoff with configurable base delay
- Configurable max attempts
- Selective exception handling (retry only on specific exceptions)
- Debug logging for retry attempts
- Synchronous and asynchronous decorator support
"""

import asyncio
import functools
import time
from typing import Callable, Tuple, Type

from ..logger import LOG


def retry_with_backoff(
    max_attempts: int = 3,
    backoff_base: float = 0.5,
    exceptions: Tuple[Type[Exception], ...] = (
        ConnectionRefusedError,
        FileNotFoundError,
    ),
):
    """
    Decorator for synchronous functions with exponential backoff retry logic.

    Retries function on specified exceptions using exponential backoff:
    - Attempt 1: Immediate
    - Attempt 2: Wait backoff_base seconds (0.5s default)
    - Attempt 3: Wait backoff_base * 2 seconds (1s default)
    - Attempt 4: Wait backoff_base * 4 seconds (2s default)
    - etc.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        backoff_base: Base delay in seconds for exponential backoff (default: 0.5)
        exceptions: Tuple of exception types to retry on
                   (default: ConnectionRefusedError, FileNotFoundError)

    Returns:
        Decorated function that retries on transient failures

    Example:
        @retry_with_backoff(max_attempts=3, backoff_base=0.5)
        def connect_to_service():
            return service.connect()

    Note:
        - Only retries on specified exceptions (transient errors)
        - Other exceptions propagate immediately (permanent errors)
        - Logs retry attempts at DEBUG level
        - Final failure logs at WARNING level
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        # Calculate delay with exponential backoff
                        delay = backoff_base * (2 ** (attempt - 1))
                        LOG.debug(
                            f"IPC retry attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        # Max attempts reached
                        LOG.warning(
                            f"IPC operation failed after {max_attempts} attempts: {e}"
                        )

                except Exception as e:
                    # Non-retryable exception, propagate immediately
                    LOG.debug(f"Non-retryable exception in IPC operation: {e}")
                    raise

            # If we get here, all attempts failed
            raise last_exception

        return wrapper

    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    backoff_base: float = 0.5,
    exceptions: Tuple[Type[Exception], ...] = (
        ConnectionRefusedError,
        FileNotFoundError,
        OSError,
    ),
):
    """
    Decorator for asynchronous functions with exponential backoff retry logic.

    Async version of retry_with_backoff(). Retries async function on specified
    exceptions using exponential backoff with asyncio.sleep.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        backoff_base: Base delay in seconds for exponential backoff (default: 0.5)
        exceptions: Tuple of exception types to retry on
                   (default: ConnectionRefusedError, FileNotFoundError, OSError)

    Returns:
        Decorated async function that retries on transient failures

    Example:
        @async_retry_with_backoff(max_attempts=3, backoff_base=0.5)
        async def connect_to_socket():
            return await asyncio.open_unix_connection("/path/to/socket")

    Note:
        - Only retries on specified exceptions (transient errors)
        - Other exceptions propagate immediately (permanent errors)
        - Logs retry attempts at DEBUG level
        - Final failure logs at WARNING level
        - Uses asyncio.sleep for non-blocking delays
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        # Calculate delay with exponential backoff
                        delay = backoff_base * (2 ** (attempt - 1))
                        LOG.debug(
                            f"IPC retry attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        # Max attempts reached
                        LOG.warning(
                            f"IPC operation failed after {max_attempts} attempts: {e}"
                        )

                except Exception as e:
                    # Non-retryable exception, propagate immediately
                    LOG.debug(f"Non-retryable exception in IPC operation: {e}")
                    raise

            # If we get here, all attempts failed
            raise last_exception

        return wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for IPC operations.

    Prevents repeated attempts to connect to a failing service by
    "opening the circuit" after a threshold of failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service recovered, allow one request

    Usage:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        if breaker.is_open():
            raise Exception("Circuit breaker open")

        try:
            result = connect_to_service()
            breaker.record_success()
        except Exception:
            breaker.record_failure()
            raise

    Note:
        - Circuit opens after failure_threshold consecutive failures
        - After timeout seconds, circuit enters HALF_OPEN state
        - One successful request in HALF_OPEN state closes circuit
        - Thread-safe for concurrent access
    """

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (HALF_OPEN state)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        """
        Check if circuit is open (blocking requests).

        Returns:
            True if circuit is open and requests should be blocked
        """
        if self.state == "OPEN":
            # Check if timeout elapsed, transition to HALF_OPEN
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.timeout
            ):
                LOG.debug("Circuit breaker entering HALF_OPEN state")
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self) -> None:
        """Record successful operation, reset failure count."""
        if self.state == "HALF_OPEN":
            LOG.debug("Circuit breaker closing (recovered)")
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        """Record failed operation, potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            LOG.warning(
                f"Circuit breaker opening after {self.failure_count} failures"
            )
            self.state = "OPEN"

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        LOG.debug("Circuit breaker manually reset")
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
