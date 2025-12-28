"""
Wait Logic Infrastructure

Provides extensible wait/poll framework for VM operations with exponential backoff.
Supports custom wait conditions and timeout handling.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

from maqet.logger import LOG


class WaitResult(Enum):
    """Result of a wait operation."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class WaitOutcome:
    """Detailed outcome of a wait operation."""
    result: WaitResult
    elapsed_time: float
    condition_name: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def is_success(self) -> bool:
        """Check if wait operation succeeded."""
        return self.result == WaitResult.SUCCESS

    def is_timeout(self) -> bool:
        """Check if wait operation timed out."""
        return self.result == WaitResult.TIMEOUT

    def is_error(self) -> bool:
        """Check if wait operation encountered an error."""
        return self.result == WaitResult.ERROR


class WaitCondition(ABC):
    """
    Abstract base class for wait conditions.

    Subclasses implement specific readiness checks (process-started, ssh-ready, etc).
    """

    def __init__(self, name: str):
        """
        Initialize wait condition.

        Args:
            name: Human-readable condition name
        """
        self.name = name

    @abstractmethod
    def check(self) -> bool:
        """
        Check if condition is satisfied.

        Returns:
            True if condition met, False otherwise

        Raises:
            Exception: If check encounters an error (will be caught by Waiter)
        """
        pass

    def cleanup(self) -> None:
        """
        Optional cleanup after wait completes.

        Override this to release resources (close connections, etc).
        """
        pass


class Waiter:
    """
    Core wait/poll engine with exponential backoff.

    Polls a condition until it succeeds or timeout expires.
    Uses exponential backoff to reduce CPU usage while maintaining responsiveness.
    """

    def __init__(
        self,
        condition: WaitCondition,
        timeout: float,
        initial_backoff: float = 0.1,
        max_backoff: float = 2.0,
        backoff_factor: float = 1.5
    ):
        """
        Initialize waiter.

        Args:
            condition: Wait condition to poll
            timeout: Maximum wait time in seconds
            initial_backoff: Initial poll interval in seconds (default 0.1)
            max_backoff: Maximum poll interval in seconds (default 2.0)
            backoff_factor: Backoff multiplier per iteration (default 1.5)
        """
        self.condition = condition
        self.timeout = timeout
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_factor = backoff_factor

    def wait(self) -> WaitOutcome:
        """
        Execute wait operation with exponential backoff.

        Returns:
            WaitOutcome with result details

        Example:
            condition = ProcessStartedCondition(vm_id)
            waiter = Waiter(condition, timeout=30)
            outcome = waiter.wait()

            if outcome.is_success():
                print("VM started successfully")
            elif outcome.is_timeout():
                print(f"Timeout after {outcome.elapsed_time}s")
        """
        start_time = time.time()
        backoff = self.initial_backoff
        attempt = 0

        LOG.debug(
            f"Starting wait for '{self.condition.name}' "
            f"(timeout={self.timeout}s, backoff={self.initial_backoff}-{self.max_backoff}s)"
        )

        try:
            while True:
                elapsed = time.time() - start_time

                # Check timeout
                if elapsed >= self.timeout:
                    LOG.warning(
                        f"Wait timeout for '{self.condition.name}' "
                        f"after {elapsed:.2f}s ({attempt} attempts)"
                    )
                    return WaitOutcome(
                        result=WaitResult.TIMEOUT,
                        elapsed_time=elapsed,
                        condition_name=self.condition.name,
                        error_message=f"Condition not met within {self.timeout}s",
                        metadata={"attempts": attempt}
                    )

                # Check condition
                attempt += 1
                try:
                    if self.condition.check():
                        LOG.info(
                            f"Wait succeeded for '{self.condition.name}' "
                            f"after {elapsed:.2f}s ({attempt} attempts)"
                        )
                        return WaitOutcome(
                            result=WaitResult.SUCCESS,
                            elapsed_time=elapsed,
                            condition_name=self.condition.name,
                            metadata={"attempts": attempt}
                        )
                except Exception as e:
                    # Log but continue polling (transient errors may resolve)
                    LOG.debug(
                        f"Condition check failed (attempt {attempt}): {e}"
                    )

                # Sleep with exponential backoff
                time.sleep(min(backoff, self.max_backoff))
                backoff *= self.backoff_factor

        except Exception as e:
            # Unexpected error during wait
            elapsed = time.time() - start_time
            LOG.error(f"Wait error for '{self.condition.name}': {e}")
            return WaitOutcome(
                result=WaitResult.ERROR,
                elapsed_time=elapsed,
                condition_name=self.condition.name,
                error_message=str(e),
                metadata={"attempts": attempt}
            )
        finally:
            # Always cleanup
            try:
                self.condition.cleanup()
            except Exception as e:
                LOG.warning(f"Condition cleanup failed: {e}")


class FunctionCondition(WaitCondition):
    """
    Simple wait condition wrapper for functions.

    Allows using plain functions as wait conditions without subclassing.
    """

    def __init__(
        self,
        name: str,
        check_fn: Callable[[], bool],
        cleanup_fn: Optional[Callable[[], None]] = None
    ):
        """
        Initialize function-based condition.

        Args:
            name: Condition name
            check_fn: Function that returns True when condition met
            cleanup_fn: Optional cleanup function
        """
        super().__init__(name)
        self.check_fn = check_fn
        self.cleanup_fn = cleanup_fn

    def check(self) -> bool:
        """Execute check function."""
        return self.check_fn()

    def cleanup(self) -> None:
        """Execute cleanup function if provided."""
        if self.cleanup_fn:
            self.cleanup_fn()


def wait_for_condition(
    condition: WaitCondition,
    timeout: float,
    initial_backoff: float = 0.1,
    max_backoff: float = 2.0
) -> WaitOutcome:
    """
    Convenience function for waiting on a condition.

    Args:
        condition: Wait condition to check
        timeout: Maximum wait time in seconds
        initial_backoff: Initial poll interval (default 0.1s)
        max_backoff: Maximum poll interval (default 2.0s)

    Returns:
        WaitOutcome with result details

    Example:
        outcome = wait_for_condition(
            ProcessStartedCondition(vm_id),
            timeout=30
        )
    """
    waiter = Waiter(
        condition=condition,
        timeout=timeout,
        initial_backoff=initial_backoff,
        max_backoff=max_backoff
    )
    return waiter.wait()


def wait_for_function(
    name: str,
    check_fn: Callable[[], bool],
    timeout: float,
    cleanup_fn: Optional[Callable[[], None]] = None
) -> WaitOutcome:
    """
    Convenience function for waiting on a simple boolean function.

    Args:
        name: Human-readable condition name
        check_fn: Function that returns True when ready
        timeout: Maximum wait time in seconds
        cleanup_fn: Optional cleanup function

    Returns:
        WaitOutcome with result details

    Example:
        def is_vm_running():
            return vm.status == "running"

        outcome = wait_for_function(
            "VM running",
            is_vm_running,
            timeout=30
        )
    """
    condition = FunctionCondition(name, check_fn, cleanup_fn)
    return wait_for_condition(condition, timeout)
