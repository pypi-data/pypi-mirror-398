"""
Process validation and monitoring utilities.

This module provides utilities for checking process existence and
monitoring process lifecycle. Centralizes PID validation patterns
to ensure consistent error handling across the codebase.

Key utilities:
- validate_pid_exists(): Check if a process exists by PID
- wait_for_process_exit(): Wait for a process to terminate

Usage:
    from maqet.utils.process_validation import validate_pid_exists

    # Raise exception if QEMU process doesn't exist
    validate_pid_exists(qemu_pid, "QEMU process", raise_on_missing=True)
"""

import os
import time
import logging

from ..exceptions import ProcessNotFoundError

LOG = logging.getLogger(__name__)


def validate_pid_exists(
    pid: int,
    process_name: str = "process",
    raise_on_missing: bool = False,
    log_permission_warning: bool = True
) -> bool:
    """
    Check if a process exists by PID using os.kill signal 0.

    Signal 0 is a special case that doesn't actually send a signal but
    performs error checking on whether the process exists.

    Args:
        pid: Process ID to check
        process_name: Descriptive name for error messages (e.g., "QEMU process")
        raise_on_missing: If True, raise ProcessNotFoundError instead of returning False
        log_permission_warning: If True, log warning when PermissionError occurs

    Returns:
        True if process exists (or permission denied), False if process not found

    Raises:
        ProcessNotFoundError: If raise_on_missing=True and process doesn't exist
        ValueError: If PID is invalid (<= 0)

    Note:
        PermissionError is treated as "exists" because we can't verify but
        the error indicates the process is running (owned by different user).
        This should not happen in normal maqet usage since we check our own processes.

    Examples:
        >>> validate_pid_exists(12345, "QEMU", raise_on_missing=True)
        True

        >>> validate_pid_exists(99999)  # Non-existent PID
        False

        >>> validate_pid_exists(1, raise_on_missing=True)  # init process, permission denied
        True  # Exists but can't verify
    """
    if not pid or pid <= 0:
        if raise_on_missing:
            raise ValueError(f"Invalid PID: {pid} (must be > 0)")
        return False

    try:
        os.kill(pid, 0)  # Signal 0 = check existence without killing
        LOG.debug(f"{process_name} (PID {pid}) verified alive")
        return True

    except ProcessLookupError:
        # Process definitively does not exist
        LOG.debug(f"{process_name} (PID {pid}) not found")

        if raise_on_missing:
            raise ProcessNotFoundError(
                f"{process_name} (PID {pid}) does not exist"
            )
        return False

    except PermissionError:
        # Process exists but we don't have permission to signal it
        # This should NOT happen for our own QEMU processes
        if log_permission_warning:
            LOG.warning(
                f"Permission denied checking {process_name} (PID {pid}). "
                f"Process exists but owned by different user (unexpected)."
            )
        # Treat as "exists" since error confirms process is running
        return True


def wait_for_process_exit(
    pid: int,
    timeout: float,
    check_interval: float = 0.1,
    process_name: str = "process"
) -> bool:
    """
    Wait for a process to exit, checking periodically.

    Args:
        pid: Process ID to monitor
        timeout: Maximum seconds to wait
        check_interval: Seconds between existence checks
        process_name: Descriptive name for logging

    Returns:
        True if process exited, False if timeout reached

    Examples:
        >>> wait_for_process_exit(12345, timeout=5.0, process_name="QEMU")
        True  # Process exited within 5 seconds
    """
    elapsed = 0.0
    while elapsed < timeout:
        if not validate_pid_exists(pid, process_name=process_name):
            LOG.debug(f"{process_name} (PID {pid}) exited after {elapsed:.2f}s")
            return True

        time.sleep(check_interval)
        elapsed += check_interval

    LOG.warning(f"{process_name} (PID {pid}) still running after {timeout}s timeout")
    return False
