"""
Process management utilities.

Provides PID verification, process token management, and safe process operations.

Process Verification Guide:
    1. Simple existence check: validate_pid_exists() from process_validation.py
    2. Token-based verification: ProcessVerifier.verify_or_raise() from this module
    3. /proc inspection: ProcFS class from this module

Use validate_pid_exists() for basic "is process alive" checks.
Use ProcessVerifier for safety-critical operations requiring PID reuse protection.
Use ProcFS for low-level /proc filesystem access.
"""

from typing import Dict, Optional, List, Type
from dataclasses import dataclass

try:
    import psutil  # noqa: F401
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from maqet.logger import LOG


class ProcFS:
    """Linux /proc filesystem utilities.

    Provides low-level access to process information via /proc filesystem.
    Linux-only. All methods return None on error (process not found, permission denied).

    Example:
        # Get process command line
        cmdline = ProcFS.get_cmdline(1234)

        # Check if process is zombie
        if ProcFS.is_zombie(1234):
            print("Process is zombie")

        # Get process state
        state = ProcFS.get_state(1234)  # "R", "S", "D", "Z", etc.
    """

    @staticmethod
    def get_cmdline(pid: int) -> Optional[List[str]]:
        """Get process command line from /proc/{pid}/cmdline.

        Args:
            pid: Process ID

        Returns:
            List of command line arguments, or None if process not found/permission denied
        """
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                data = f.read()
                if not data:
                    return None
                return data.decode().rstrip('\0').split('\0')
        except (OSError, IOError):
            return None

    @staticmethod
    def get_status(pid: int) -> Optional[Dict[str, str]]:
        """Get process status from /proc/{pid}/status.

        Args:
            pid: Process ID

        Returns:
            Dict of status fields (Name, State, PPid, etc.), or None if not found
        """
        try:
            with open(f"/proc/{pid}/status") as f:
                result = {}
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        result[key.strip()] = value.strip()
                return result
        except (OSError, IOError):
            return None

    @staticmethod
    def get_state(pid: int) -> Optional[str]:
        """Get process state character from /proc/{pid}/stat.

        Process states:
        - R: Running
        - S: Sleeping (interruptible)
        - D: Disk sleep (uninterruptible)
        - Z: Zombie
        - T: Stopped
        - t: Tracing stop
        - X: Dead
        - I: Idle

        Args:
            pid: Process ID

        Returns:
            Single character state, or None if process not found
        """
        try:
            with open(f"/proc/{pid}/stat", "r") as f:
                stat = f.read()
                # State is after closing paren: "pid (comm) S ..."
                state_start = stat.rfind(")") + 2
                return stat[state_start] if state_start < len(stat) else None
        except (FileNotFoundError, IOError):
            return None

    @staticmethod
    def is_zombie(pid: int) -> bool:
        """Check if process is a zombie (state Z).

        Args:
            pid: Process ID

        Returns:
            True if process is zombie, False otherwise (including not found)
        """
        return ProcFS.get_state(pid) == "Z"

    @staticmethod
    def get_ppid(pid: int) -> Optional[int]:
        """Get parent process ID.

        Args:
            pid: Process ID

        Returns:
            Parent PID, or None if process not found
        """
        status = ProcFS.get_status(pid)
        if not status:
            return None
        try:
            return int(status.get("PPid", ""))
        except ValueError:
            return None


@dataclass
class ProcessVerification:
    """Result of process verification."""
    pid: int
    is_verified: bool
    process_name: str
    cmdline: str
    error: Optional[str] = None


class ProcessVerifier:
    """
    Centralized process verification with error handling.

    Wraps verify_process() calls with consistent error handling patterns.
    Converts low-level ValueError exceptions into domain-specific exceptions.
    """

    @staticmethod
    def verify_or_raise(
        pid: int,
        expected_names: List[str],
        expected_tokens: List[str],
        error_type: Type[Exception],
        process_description: str = "process"
    ) -> bool:
        """
        Verify process identity and raise domain-specific exception on failure.

        Provides centralized error handling for process verification:
        1. Calls verify_process() with provided parameters
        2. Handles "does not exist" case (returns False)
        3. Converts verification failures to domain-specific exceptions

        Args:
            pid: Process ID to verify
            expected_names: List of acceptable process names (e.g., ["python", "python3"])
            expected_tokens: Tokens that must appear in cmdline (e.g., ["maqet", "vm_runner"])
            error_type: Exception class to raise on verification failure
            process_description: Human-readable process description for error messages

        Returns:
            True if process exists and verified, False if process doesn't exist

        Raises:
            error_type: If process exists but verification fails (wrong process)

        Example:
            # QEMU verification
            ProcessVerifier.verify_or_raise(
                qemu_pid,
                expected_names=["qemu", "qemu-system-x86_64"],
                expected_tokens=[vm_id, vm_name],
                error_type=VMLifecycleError,
                process_description=f"QEMU for VM '{vm_id}'"
            )

            # Runner verification
            ProcessVerifier.verify_or_raise(
                runner_pid,
                expected_names=["python", "python3"],
                expected_tokens=["maqet", "vm_runner"],
                error_type=RunnerSpawnError,
                process_description=f"VM runner (PID {runner_pid})"
            )
        """
        try:
            verify_process(pid, expected_names, expected_tokens)
            LOG.debug(f"Verified PID {pid} is {process_description}. Safe to operate on.")
            return True

        except ValueError as e:
            error_msg = str(e)

            # Process doesn't exist - return False (not an error)
            if "does not exist" in error_msg:
                LOG.debug(f"{process_description} (PID {pid}) does not exist")
                return False

            # Process exists but wrong type - raise domain exception
            LOG.error(f"PID verification failed for {process_description}: {error_msg}")
            raise error_type(
                f"Stale PID {pid} does not match expected {process_description}. "
                f"Manual cleanup required. Details: {error_msg}"
            )


def verify_process(
    pid: int,
    expected_names: List[str],
    expected_cmdline_tokens: List[str],
    warn_recent: float = 1.0
) -> ProcessVerification:
    """
    Verify process identity with PID reuse protection.

    Performs multi-layer verification:
    1. Process name matches expected names
    2. Command line contains expected tokens
    3. (Optional) Warns if process very recently created

    Args:
        pid: Process ID to verify
        expected_names: List of acceptable process names (e.g., ["python", "python3"])
        expected_cmdline_tokens: Tokens that must appear in cmdline (e.g., ["maqet", "vm_runner"])
        warn_recent: Warn if process created within this many seconds (default 1.0)

    Returns:
        ProcessVerification with verification result

    Raises:
        ValueError: If process exists but doesn't match verification criteria

    Example:
        # Verify QEMU process
        result = verify_process(
            qemu_pid,
            expected_names=["qemu-system-x86_64", "qemu"],
            expected_cmdline_tokens=[vm_id, vm_name]
        )

        # Verify runner process
        result = verify_process(
            runner_pid,
            expected_names=["python", "python3"],
            expected_cmdline_tokens=["maqet", "vm_runner"]
        )
    """
    if PSUTIL_AVAILABLE:
        try:
            import psutil
            process = psutil.Process(pid)

            # Check 1: Process name matches
            process_name = process.name().lower()
            name_match = any(name.lower() in process_name for name in expected_names)

            if not name_match:
                error = (
                    f"PID {pid} process name '{process.name()}' does not match "
                    f"expected names {expected_names}. Possible PID reuse."
                )
                LOG.error(error)
                raise ValueError(error)

            # Check 2: Command line contains expected tokens
            cmdline = process.cmdline()
            cmdline_str = " ".join(cmdline)

            tokens_found = [
                token for token in expected_cmdline_tokens
                if token.lower() in cmdline_str.lower()
            ]

            if not tokens_found:
                error = (
                    f"PID {pid} cmdline does not contain expected tokens {expected_cmdline_tokens}. "
                    f"Command: {' '.join(cmdline[:3])}... Possible PID reuse."
                )
                LOG.error(error)
                raise ValueError(error)

            # Check 3: Recent creation warning
            if warn_recent > 0:
                import time
                create_time = process.create_time()
                if time.time() - create_time < warn_recent:
                    LOG.warning(
                        f"PID {pid} created very recently ({time.time() - create_time:.2f}s ago). "
                        f"Possible PID reuse - verify this is correct process."
                    )

            LOG.debug(f"Verified PID {pid} matches expected process")

            return ProcessVerification(
                pid=pid,
                is_verified=True,
                process_name=process.name(),
                cmdline=cmdline_str
            )

        except psutil.NoSuchProcess:
            raise ValueError(f"PID {pid} does not exist")

        except psutil.AccessDenied:
            raise ValueError(f"Access denied when checking PID {pid}")

    else:
        # Fallback: Check /proc/{pid}/cmdline
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                cmdline_bytes = f.read()
                cmdline = cmdline_bytes.decode("utf-8", errors="ignore")

            # Check name (approximate - cmdline has first arg)
            name_match = any(name.lower() in cmdline.lower() for name in expected_names)
            if not name_match:
                error = f"PID {pid} cmdline does not match expected names {expected_names}"
                LOG.error(error)
                raise ValueError(error)

            # Check tokens
            tokens_found = [
                token for token in expected_cmdline_tokens
                if token.lower() in cmdline.lower()
            ]

            if not tokens_found:
                error = f"PID {pid} cmdline does not contain expected tokens {expected_cmdline_tokens}"
                LOG.error(error)
                raise ValueError(error)

            LOG.debug(f"Verified PID {pid} matches expected process (via /proc)")

            return ProcessVerification(
                pid=pid,
                is_verified=True,
                process_name=cmdline.split('\0')[0] if '\0' in cmdline else cmdline[:50],
                cmdline=cmdline
            )

        except FileNotFoundError:
            raise ValueError(f"PID {pid} does not exist")
