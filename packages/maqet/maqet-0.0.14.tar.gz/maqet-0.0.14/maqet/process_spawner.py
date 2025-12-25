"""
Process Spawner

Utilities for spawning and managing detached VM runner processes.
Used by CLI to create independent VM runner processes that survive parent exit.

Architecture:
- Each VM gets its own persistent Python process (VM runner)
- Spawned processes are detached (new session, own process group)
- Processes redirect stdout/stderr to log files
- Socket-based readiness checking with timeout
- Health checks using psutil or fallback methods

Key Functions:
- spawn_vm_runner(): Create detached VM runner process
- wait_for_vm_ready(): Wait for authenticated VM runner readiness (production)
- wait_for_socket_exists(): Wait for socket file creation only (testing)
- get_socket_path(): Get Unix socket path for VM
- get_log_path(): Get log file path for VM runner
- is_runner_alive(): Check if runner process is alive
- kill_runner(): Terminate VM runner process
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .state import StateManager

from .constants import Intervals, Timeouts
from .exceptions import RunnerSpawnError
from .logger import LOG
from .security.validation import InputValidator, ValidationError
from .utils.paths import get_log_path, get_socket_path
from .utils.process_utils import ProcessVerifier, ProcFS
from .utils.process_validation import validate_pid_exists
from .utils.error_files import read_runner_error

# Optional dependency - imported inline with fallback
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def spawn_vm_runner(
    vm_id: str,
    db_path: Optional[Path] = None,
    timeout: int = Timeouts.PROCESS_SPAWN
) -> int:
    """
    Spawn a detached VM runner process.

    The spawned process:
    - Runs in background (detached from CLI)
    - Has its own process group (start_new_session=True)
    - Redirects stdout/stderr to log files
    - Survives parent CLI process exit
    - Returns immediately (non-blocking)

    Args:
        vm_id: VM identifier (validated for security)
        db_path: Optional path to database (validated if provided)
        timeout: Maximum time to wait for process to start (seconds)

    Returns:
        runner_pid: PID of spawned runner process

    Raises:
        RunnerSpawnError: If spawn fails, validation fails, or process dies immediately

    Example:
        runner_pid = spawn_vm_runner("vm1")
        # Returns: PID of spawned runner process
    """
    # SECURITY: Validate vm_id before use in subprocess
    # Prevents command injection, path traversal, argument injection
    try:
        vm_id = InputValidator.validate_vm_id(vm_id)
    except ValidationError as e:
        raise RunnerSpawnError(f"Invalid VM ID: {e}")

    # SECURITY: Validate db_path if provided
    if db_path is not None:
        try:
            db_path = InputValidator.validate_path(
                db_path,
                must_be_absolute=True,
                description="Database path"
            )
        except ValidationError as e:
            raise RunnerSpawnError(f"Invalid database path: {e}")

    # Get Python interpreter path (same interpreter as CLI)
    python_exe = sys.executable

    # Build command: python3 -m maqet.vm_runner <vm_id> [db_path]
    cmd = [python_exe, "-m", "maqet.vm_runner", vm_id]
    if db_path:
        cmd.append(str(db_path))

    # Get log file path for stdout/stderr
    log_path = get_log_path(vm_id)

    LOG.debug(f"Spawning VM runner for {vm_id}: {' '.join(cmd)}")
    LOG.debug(f"Log output: {log_path}")

    try:
        # Open log file for output
        log_file = open(log_path, "w")

        # Spawn detached process
        process = subprocess.Popen(
            cmd,
            start_new_session=True,  # Detach from parent process group
            stdin=subprocess.DEVNULL,  # No stdin (non-interactive)
            stdout=log_file,  # Redirect stdout to log
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout (combined log)
            close_fds=True,  # Close all file descriptors
        )

        runner_pid = process.pid
        LOG.info(f"VM runner spawned: PID {runner_pid}")

        # Wait briefly to ensure process started successfully
        time.sleep(Intervals.PROCESS_STARTUP_WAIT)

        # Check if process still alive (didn't crash immediately)
        if process.poll() is not None:
            # Process exited immediately - get error details
            exit_code = process.poll()
            log_file.close()

            # Check error file first (more detailed than log)
            error_details = read_runner_error(vm_id)
            if error_details:
                raise RunnerSpawnError(
                    f"VM runner '{vm_id}' failed during startup (exit code {exit_code}).\n\n"
                    f"{error_details}\n\n"
                    f"Full log: {log_path}"
                )

            # Fallback: Read log file
            try:
                with open(log_path, "r") as f:
                    error_output = f.read().strip()
            except Exception:
                error_output = "(could not read log)"

            raise RunnerSpawnError(
                f"VM runner '{vm_id}' failed to start (exit code {exit_code}). "
                f"Error: {error_output}. Check log at: {log_path}"
            )

        # Close log file handle (process has its own handle now)
        log_file.close()

        return runner_pid

    except RunnerSpawnError:
        # Re-raise RunnerSpawnError as-is (don't wrap it again)
        raise
    except FileNotFoundError:
        raise RunnerSpawnError(
            f"Python interpreter not found: {python_exe}. "
            f"This should never happen - check sys.executable."
        )
    except PermissionError as e:
        raise RunnerSpawnError(
            f"Permission denied when spawning VM runner '{vm_id}': {e}. "
            f"Check file permissions for log directory."
        )
    except Exception as e:
        raise RunnerSpawnError(
            f"Failed to spawn VM runner '{vm_id}': {e}"
        )


def wait_for_socket_exists(
    vm_id: str,
    socket_path: Optional[Path] = None,
    timeout: int = Timeouts.VM_START
) -> bool:
    """
    Wait for VM runner socket file to exist (testing/legacy use only).

    WARNING: This does NOT verify the runner is actually ready or connectable!
    Use wait_for_vm_ready() in production code for authenticated readiness checks.

    This function is intended for:
    - Unit tests that mock socket creation
    - Legacy code migration path
    - Debugging socket file creation issues

    Args:
        vm_id: VM identifier
        socket_path: Optional socket path (auto-detected if not provided)
        timeout: Maximum wait time in seconds

    Returns:
        True if socket file exists within timeout, False otherwise

    Example:
        # Unit testing - check socket file created
        socket_path = get_socket_path("test-vm")
        exists = wait_for_socket_exists("test-vm", socket_path, timeout=5)
    """
    if socket_path is None:
        socket_path = get_socket_path(vm_id)

    start_time = time.time()
    poll_interval = 0.1  # Start with 100ms
    max_poll_interval = 0.5  # Cap at 500ms

    LOG.debug(f"Waiting for socket file to exist: {socket_path}")

    while time.time() - start_time < timeout:
        if socket_path.exists():
            LOG.debug(f"Socket file exists: {socket_path}")
            return True

        # Sleep with exponential backoff
        time.sleep(poll_interval)
        poll_interval = min(poll_interval * 1.2, max_poll_interval)

        # Log progress every 5 seconds
        elapsed = time.time() - start_time
        if int(elapsed) % 5 == 0 and elapsed > 0:
            LOG.debug(f"Still waiting for socket file... ({int(elapsed)}s elapsed)")

    # Timeout
    LOG.debug(f"Timeout waiting for socket file after {timeout}s")
    return False


def wait_for_vm_ready(
    vm_id: str,
    state_manager: "StateManager",  # Required for authentication
    timeout: int = Timeouts.VM_START
) -> bool:
    """
    Wait for VM runner to be ready with authenticated ping (production use).

    Performs authenticated ping via RunnerClient to verify the runner is:
    1. Socket created and connectable
    2. IPC server responding
    3. Authentication succeeds
    4. Ping command returns pong

    This is the recommended function for production code as it performs
    comprehensive readiness verification with security.

    Purpose: Ensure VM runner process is fully initialized before returning.
    Can fail: Yes, if runner doesn't start within timeout.

    Edge case: Under high system load (e.g., parallel tests), process spawning
               can take longer than usual. Increased timeout handles this.

    Args:
        vm_id: VM identifier
        state_manager: StateManager instance (required for auth secret)
        timeout: Maximum wait time in seconds

    Returns:
        True if runner responds to authenticated ping within timeout, False otherwise

    Raises:
        ValueError: If state_manager is None

    Example:
        # Production code - authenticated readiness check
        ready = wait_for_vm_ready("vm1", state_manager, timeout=30)
        if ready:
            # Safe to send QMP commands
            client.send_command("qmp", "query-status")
    """
    if state_manager is None:
        raise ValueError(
            "state_manager is required for authenticated VM readiness check. "
            "For testing socket file creation only, use wait_for_socket_exists()."
        )

    # Detect if running in test environment
    is_testing = "PYTEST_CURRENT_TEST" in os.environ
    if is_testing:
        # Increase timeout for parallel test execution
        timeout = max(timeout, 60.0)

    socket_path = get_socket_path(vm_id)
    start_time = time.time()
    backoff = 0.05  # Start with 50ms
    max_backoff = 0.5  # Cap at 500ms

    LOG.debug(f"Waiting for VM runner to be ready (authenticated): {socket_path}")
    if is_testing:
        LOG.debug("Test environment detected, using minimum timeout of 60s")

    while time.time() - start_time < timeout:
        # Check if socket exists first (fast check before attempting connection)
        if socket_path.exists():
            try:
                # Import here to avoid circular dependency (process_spawner -> runner_client -> state)
                from .ipc.runner_client import RunnerClient

                # Try authenticated ping via RunnerClient
                client = RunnerClient(vm_id, state_manager)
                if client.ping():
                    LOG.debug("VM runner ready (authenticated ping successful)")

                    # PHASE 2: Validate QEMU process via IPC
                    try:
                        status = client.status()
                        qemu_pid = status.get("qemu_pid")

                        if not qemu_pid:
                            LOG.warning(
                                f"IPC responded but no QEMU PID available for VM {vm_id}"
                            )
                            # Continue waiting - QEMU might not be started yet
                            time.sleep(backoff)
                            backoff = min(backoff * 1.5, max_backoff)
                            continue

                        # PHASE 2: Verify QEMU PID exists on host
                        if validate_pid_exists(qemu_pid, process_name=f"QEMU for VM {vm_id}"):
                            LOG.debug(f"QEMU process {qemu_pid} verified alive for VM {vm_id}")
                            return True  # All checks passed
                        else:
                            LOG.error(
                                f"QEMU PID {qemu_pid} reported by runner but process not found. "
                                f"Runner may be out of sync with reality for VM {vm_id}"
                            )
                            # Don't return False immediately - might be transient, retry

                    except Exception as status_error:
                        LOG.debug(f"Status check error for VM {vm_id}: {status_error}")
                        # Fall through to retry

                else:
                    LOG.debug("Socket exists but ping failed, retrying...")
            except Exception as e:
                LOG.debug(f"Ping check error: {type(e).__name__}: {e}")

        # Exponential backoff (up to 500ms)
        time.sleep(backoff)
        backoff = min(backoff * 1.5, max_backoff)

        # Log progress every 5 seconds
        elapsed = time.time() - start_time
        if int(elapsed) % 5 == 0 and elapsed > 0:
            LOG.debug(f"Still waiting for VM runner... ({int(elapsed)}s elapsed)")

    # Timeout reached
    LOG.warning(f"Timeout waiting for VM runner after {timeout}s")

    # PHASE 2: Check error file on timeout and log details
    error_details = read_runner_error(vm_id)
    if error_details:
        LOG.error(f"VM runner error details for {vm_id}:\n{error_details}")

    return False


def is_runner_alive(runner_pid: int) -> bool:
    """
    Check if runner process is alive.

    Uses psutil if available for accurate check, otherwise falls back
    to ProcFS for zombie detection.

    Args:
        runner_pid: PID of runner process

    Returns:
        True if process exists and is not a zombie, False otherwise

    Example:
        alive = is_runner_alive(12345)
        # Returns: True if process exists and not zombie, False otherwise
    """
    if runner_pid is None or runner_pid <= 0:
        return False

    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process(runner_pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    else:
        # Fallback using ProcFS
        if not validate_pid_exists(runner_pid, "runner", log_permission_warning=False):
            return False
        return not ProcFS.is_zombie(runner_pid)


def kill_runner(runner_pid: int, force: bool = False) -> bool:
    """
    Kill VM runner process with PID reuse protection.

    Verifies the PID belongs to a maqet runner process before killing.
    This prevents accidentally killing the wrong process if PID is reused.

    Args:
        runner_pid: PID of runner process
        force: If True, use SIGKILL. If False, use SIGTERM (graceful)

    Returns:
        True if process was killed, False if process not found

    Raises:
        RunnerSpawnError: If PID exists but is not a runner process

    Example:
        # Graceful shutdown
        kill_runner(12345, force=False)

        # Force kill
        kill_runner(12345, force=True)
    """
    if not is_runner_alive(runner_pid):
        return False

    # PID reuse protection: Verify this is actually a runner process
    verified = ProcessVerifier.verify_or_raise(
        runner_pid,
        expected_names=["python", "python3"],
        expected_tokens=["maqet", "vm_runner"],
        error_type=RunnerSpawnError,
        process_description=f"VM runner (PID {runner_pid})"
    )

    if not verified:
        # Process doesn't exist
        return False

    # Now safe to kill - verified it's a runner process
    try:
        if force:
            LOG.debug(f"Force killing runner process {runner_pid} (SIGKILL)")
            os.kill(runner_pid, 9)  # SIGKILL
        else:
            LOG.debug(f"Gracefully stopping runner process {runner_pid} (SIGTERM)")
            os.kill(runner_pid, 15)  # SIGTERM
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        LOG.error(f"Permission denied when killing process {runner_pid}")
        return False
    except Exception as e:
        LOG.error(f"Failed to kill process {runner_pid}: {e}")
        return False
