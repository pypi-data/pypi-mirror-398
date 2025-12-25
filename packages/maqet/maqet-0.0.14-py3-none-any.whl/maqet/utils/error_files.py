"""
Error file management utilities.

Utilities for reading and managing VM runner error files with
size limits and consistent cleanup behavior.

Key utilities:
- read_runner_error(): Read error file with 10KB size limit
- cleanup_runner_error(): Remove stale error files

Usage:
    from maqet.utils.error_files import read_runner_error

    error = read_runner_error(vm_id)
    if error:
        raise VMStartError(f"Runner failed: {error}")
"""

import logging
from typing import Optional

from .paths import get_runner_error_path

LOG = logging.getLogger(__name__)

# Maximum error file size to prevent memory exhaustion
# 10KB should be plenty for error message + traceback + context
MAX_ERROR_FILE_SIZE = 10 * 1024  # 10KB


def read_runner_error(vm_id: str) -> Optional[str]:
    """
    Read error file for a VM runner if it exists.

    Implements size limits to prevent memory exhaustion from
    malicious or buggy runners writing excessive data.

    Args:
        vm_id: VM identifier

    Returns:
        Error file contents (truncated if >10KB), or None if file doesn't exist

    Examples:
        >>> error = read_runner_error("vm-123")
        >>> if error:
        ...     raise VMStartError(f"Runner failed: {error}")
    """
    error_file = get_runner_error_path(vm_id)

    if not error_file.exists():
        LOG.debug(f"Error file does not exist: {error_file}")
        return None

    try:
        file_size = error_file.stat().st_size

        if file_size == 0:
            LOG.debug(f"Error file is empty: {error_file}")
            return None

        if file_size > MAX_ERROR_FILE_SIZE:
            LOG.warning(
                f"Error file {error_file} is {file_size} bytes (max {MAX_ERROR_FILE_SIZE}), "
                f"truncating to prevent memory exhaustion"
            )
            # Read first 10KB only
            with open(error_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(MAX_ERROR_FILE_SIZE)
            return content.strip() + f"\n\n... (truncated, file was {file_size} bytes)"

        # File size is reasonable, read entire content
        content = error_file.read_text(encoding='utf-8', errors='replace').strip()
        LOG.debug(f"Read {len(content)} bytes from error file: {error_file}")
        return content

    except Exception as read_err:
        # Log but don't crash - error file is best-effort diagnostics
        LOG.warning(f"Failed to read error file {error_file}: {read_err}")
        return f"(Could not read error file: {read_err})"


def cleanup_runner_error(vm_id: str) -> None:
    """
    Remove error file for a VM runner if it exists.

    Should be called on successful VM start to prevent stale error files
    from accumulating over time.

    Args:
        vm_id: VM identifier

    Examples:
        >>> cleanup_runner_error("vm-123")  # Remove old error file
    """
    error_file = get_runner_error_path(vm_id)

    if error_file.exists():
        try:
            error_file.unlink()
            LOG.debug(f"Removed stale error file: {error_file}")
        except Exception as e:
            # Non-critical - just log and continue
            LOG.debug(f"Failed to remove error file {error_file}: {e}")
