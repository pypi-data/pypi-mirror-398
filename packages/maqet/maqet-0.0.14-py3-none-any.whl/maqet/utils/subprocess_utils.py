"""
Subprocess utilities with output size protection.

Provides wrappers for subprocess operations that truncate output to prevent
memory exhaustion from malicious or excessively verbose processes.
"""

import subprocess
from typing import Optional, Tuple

from ..constants import Limits
from ..logger import LOG


def run_with_output_limit(
    *args,
    max_output: int = Limits.MAX_SUBPROCESS_OUTPUT,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Run subprocess with output size limit protection.

    Wraps subprocess.run() and truncates stdout/stderr to prevent memory
    exhaustion from processes that produce excessive output.

    Args:
        *args: Positional arguments passed to subprocess.run()
        max_output: Maximum bytes to capture per stream (default: 1MB)
        **kwargs: Keyword arguments passed to subprocess.run()

    Returns:
        CompletedProcess with potentially truncated stdout/stderr

    Example:
        result = run_with_output_limit(
            ['qemu-system-x86_64', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
    """
    result = subprocess.run(*args, **kwargs)

    # Truncate stdout if needed
    if hasattr(result, 'stdout') and result.stdout:
        if isinstance(result.stdout, str):
            original_len = len(result.stdout)
            if original_len > max_output:
                LOG.warning(
                    f"subprocess stdout truncated from {original_len} "
                    f"to {max_output} bytes"
                )
                result.stdout = result.stdout[:max_output]
        elif isinstance(result.stdout, bytes):
            original_len = len(result.stdout)
            if original_len > max_output:
                LOG.warning(
                    f"subprocess stdout truncated from {original_len} "
                    f"to {max_output} bytes"
                )
                result.stdout = result.stdout[:max_output]

    # Truncate stderr if needed
    if hasattr(result, 'stderr') and result.stderr:
        if isinstance(result.stderr, str):
            original_len = len(result.stderr)
            if original_len > max_output:
                LOG.warning(
                    f"subprocess stderr truncated from {original_len} "
                    f"to {max_output} bytes"
                )
                result.stderr = result.stderr[:max_output]
        elif isinstance(result.stderr, bytes):
            original_len = len(result.stderr)
            if original_len > max_output:
                LOG.warning(
                    f"subprocess stderr truncated from {original_len} "
                    f"to {max_output} bytes"
                )
                result.stderr = result.stderr[:max_output]

    return result


def communicate_with_limit(
    process: subprocess.Popen,
    input=None,
    timeout: Optional[float] = None,
    max_output: int = Limits.MAX_SUBPROCESS_OUTPUT,
) -> Tuple:
    """
    Communicate with subprocess with output size limit protection.

    Wraps Popen.communicate() and truncates stdout/stderr to prevent memory
    exhaustion from processes that produce excessive output.

    Handles both text mode (str) and binary mode (bytes) automatically based
    on how the Popen was created.

    Args:
        process: Popen process instance
        input: Optional input to send to process stdin (str or bytes)
        timeout: Optional timeout in seconds
        max_output: Maximum bytes/chars to capture per stream (default: 1MB)

    Returns:
        Tuple of (stdout, stderr) with potentially truncated output.
        Types match the Popen text mode (str if text=True, bytes otherwise).

    Raises:
        subprocess.TimeoutExpired: If timeout expires

    Example:
        # Binary mode
        process = subprocess.Popen(
            ['qemu-img', 'snapshot', '-l', '/path/to/disk.qcow2'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = communicate_with_limit(process, timeout=30)

        # Text mode
        process = subprocess.Popen(
            ['qemu-img', 'snapshot', '-l', '/path/to/disk.qcow2'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = communicate_with_limit(process, timeout=30)
    """
    stdout, stderr = process.communicate(input=input, timeout=timeout)

    # Truncate stdout if needed (handles both str and bytes)
    if stdout:
        original_len = len(stdout)
        if original_len > max_output:
            LOG.warning(
                f"Popen stdout truncated from {original_len} "
                f"to {max_output} {'chars' if isinstance(stdout, str) else 'bytes'}"
            )
            stdout = stdout[:max_output]

    # Truncate stderr if needed (handles both str and bytes)
    if stderr:
        original_len = len(stderr)
        if original_len > max_output:
            LOG.warning(
                f"Popen stderr truncated from {original_len} "
                f"to {max_output} {'chars' if isinstance(stderr, str) else 'bytes'}"
            )
            stderr = stderr[:max_output]

    return stdout, stderr
