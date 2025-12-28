"""
VM Runner Process

Long-running process that manages a single VM's lifecycle.
Each VM gets its own persistent Python process running an instance of VMRunner.

Responsibilities:
- Start and monitor QEMU process
- Handle QMP communication via QEMUMachine instance
- Provide IPC server for CLI commands
- Perform periodic DB consistency checks
- Handle graceful shutdown on QEMU exit or stop command

Architecture:
One VM = One VMRunner process = One QEMUMachine instance
No daemon, no shared state. DB is single source of truth.
"""

import asyncio
import os
import signal
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from .constants import Intervals, Timeouts
from .exceptions import VMRunnerError
from .logger import LOG
from .machine import Machine
from .state import StateManager
from .vm_lifecycle import VMLifecycleManager
from .utils.paths import get_runner_error_path, get_runner_status_path, get_socket_path
from .utils.security import create_auth_secret_file
from .utils.process_validation import validate_pid_exists
from .utils.error_files import cleanup_runner_error


class VMRunner:
    """
    Long-running process that manages a single VM's lifecycle.

    Each VM gets its own persistent Python process with VMRunner instance.
    The runner creates a Machine (QEMUMachine wrapper) and keeps it alive
    while the VM is running. Provides IPC server for CLI communication.
    """

    def __init__(self, vm_id: str, db_path: Optional[Path] = None):
        """
        Initialize VM runner for specific VM.

        Args:
            vm_id: VM identifier
            db_path: Optional path to database (for testing)
        """
        self.vm_id = vm_id
        self.db_path = db_path
        self.machine: Optional[Machine] = None
        self.ipc_server = None
        self.socket_path: Optional[Path] = None
        self.state_manager: Optional[StateManager] = None
        self.lifecycle_manager: Optional[VMLifecycleManager] = None
        self.auth_secret: Optional[str] = None  # Authentication secret for IPC
        self.start_time: float = time.time()  # Track runner startup time for uptime

        # Thread-safe stop event
        self._stop_event = threading.Event()

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        LOG.debug(f"VMRunner initialized for VM {vm_id}")

    def start(self) -> None:
        """
        Initialize VM runner, start VM, run event loop.

        Process:
        1. Load VM from database
        2. Start QEMU via Machine
        3. Update DB with runner PID and socket path
        4. Start IPC server
        5. Run event loop (monitor QEMU, handle IPC, check DB)
        """
        try:
            # Remove stale error file from previous run if it exists
            # Error files are only useful for current failure, not historical
            cleanup_runner_error(self.vm_id)

            # Initialize state manager
            data_dir = None
            if self.db_path:
                data_dir = str(self.db_path.parent)
            self.state_manager = StateManager(data_dir)

            # Initialize lifecycle manager for storage registry access
            self.lifecycle_manager = VMLifecycleManager(self.state_manager)

            # Load VM from database
            vm = self.state_manager.get_vm(self.vm_id)
            if not vm:
                LOG.error(f"VM {self.vm_id} not found in database")
                sys.exit(1)

            LOG.info(f"Starting VM runner for {self.vm_id}")

            # Get socket path to determine secret file location
            self.socket_path = get_socket_path(self.vm_id)

            # Create authentication secret file atomically with secure permissions
            # This prevents TOCTOU vulnerabilities by using O_CREAT | O_EXCL | O_NOFOLLOW
            self.auth_secret = create_auth_secret_file(self.socket_path)
            LOG.info(f"Created auth secret file: {self.socket_path.with_suffix('.auth')}")

            # SIMPLE SOLUTION: Use context manager!
            # When this block exits (normally or via crash/exception),
            # Machine.__exit__() is AUTOMATICALLY called and QEMU is stopped.
            # This is Python's built-in reliability mechanism - no complex cleanup needed!
            with Machine(
                vm_id=self.vm_id,
                config_data=vm.config_data,
                state_manager=self.state_manager,
                storage_registry=self.lifecycle_manager.storage_registry,
            ) as self.machine:
                # Start QEMU process
                self.machine.start()

                # Get QEMU PID
                qemu_pid = self.machine.pid
                if not qemu_pid:
                    raise VMRunnerError("Failed to get QEMU PID after start")

                LOG.info(f"QEMU started with PID {qemu_pid}")

                # Validate QEMU PID actually exists
                validate_pid_exists(
                    qemu_pid,
                    process_name="QEMU process",
                    raise_on_missing=True
                )

                # Grace period to catch immediate crashes
                grace_ms = Intervals.QEMU_CRASH_GRACE_PERIOD * 1000
                LOG.info(f"Waiting {grace_ms:.0f}ms to detect immediate QEMU crashes...")
                time.sleep(Intervals.QEMU_CRASH_GRACE_PERIOD)

                try:
                    validate_pid_exists(
                        qemu_pid,
                        process_name="QEMU process",
                        raise_on_missing=True
                    )
                except Exception:
                    raise VMRunnerError(
                        f"QEMU process {qemu_pid} crashed within {grace_ms:.0f}ms of startup. "
                        "Check QEMU logs for detailed error. Common causes: "
                        "invalid disk path, missing OVMF firmware, port conflicts."
                    )

                LOG.info(f"QEMU process {qemu_pid} validated (still alive after grace period)")

                # Extract QMP socket path from QEMUMachine for cross-process QMP
                # See: specs/fix-cross-process-qmp-communication.md
                qmp_socket = self.machine._qemu_machine._monitor_address
                LOG.debug(f"Extracted QMP socket path: {qmp_socket}")

                # NOW safe to update database
                self.state_manager.update_vm_status(
                    self.vm_id,
                    status="running",
                    pid=qemu_pid,
                    runner_pid=os.getpid(),
                    socket_path=str(self.socket_path),
                    qmp_socket_path=str(qmp_socket) if qmp_socket else None,
                )

                LOG.info("Database updated to 'running' status")

                LOG.debug(
                    f"Updated DB: runner_pid={os.getpid()}, "
                    f"qemu_pid={qemu_pid}, socket={self.socket_path}"
                )

                # Start IPC server in background thread
                from .ipc.unix_socket_server import UnixSocketIPCServer
                import threading

                self.ipc_server = UnixSocketIPCServer(
                    socket_path=self.socket_path,
                    handler=self._handle_ipc_request,
                    auth_secret=self.auth_secret
                )

                # Run IPC server in separate thread (it's blocking)
                def run_ipc_server():
                    try:
                        asyncio.run(self.ipc_server.start())
                    except Exception as e:
                        LOG.error(f"IPC server error: {e}")

                self.ipc_thread = threading.Thread(target=run_ipc_server, daemon=True)
                self.ipc_thread.start()

                # Wait for socket to be created
                timeout = Timeouts.IPC_SOCKET_WAIT
                start = time.time()
                while not self.socket_path.exists() and time.time() - start < timeout:
                    time.sleep(Intervals.VM_HEALTH_CHECK)

                if not self.socket_path.exists():
                    raise VMRunnerError("IPC server failed to start")

                LOG.info(f"IPC server started on {self.socket_path}")

                # Write startup success marker
                LOG.info("VM runner fully started and ready")
                success_marker = get_runner_status_path(self.vm_id)
                try:
                    success_marker.write_text(
                        f"READY:{os.getpid()}:{qemu_pid}:{time.time()}"
                    )
                    LOG.debug(f"Success marker written to: {success_marker}")
                except Exception as e:
                    LOG.warning(f"Failed to write success marker: {e}")

                # Run event loop
                self._run_event_loop()

            # Context manager exit: Machine.__exit__() called automatically
            # QEMU is stopped gracefully - no orphaned processes!
            LOG.info(f"VM runner for {self.vm_id} exiting cleanly")
            sys.exit(0)

        except Exception as e:
            LOG.error(f"VM runner failed to start: {e}")
            self._cleanup()
            sys.exit(1)

    def _run_event_loop(self) -> None:
        """
        Main event loop: monitor QEMU, handle IPC, check DB.

        Loop tasks:
        - Check if QEMU process still running
        - Process IPC requests (non-blocking)
        - Periodic DB consistency check (every 5 seconds)
        - Exit on QEMU exit or DB stop command
        """
        LOG.debug("Entering event loop")
        last_db_check = time.time()
        db_check_interval = 5  # Check DB every 5 seconds

        while not self._stop_event.is_set():
            try:
                # Check if QEMU process still running
                if not self._is_qemu_running():
                    LOG.warning("QEMU process exited")
                    self._handle_qemu_exit()
                    break

                # Periodic DB state check (detect drift)
                if time.time() - last_db_check >= db_check_interval:
                    if not self._check_db_consistency():
                        LOG.warning("DB consistency check failed, stopping")
                        self._handle_db_stop_command()
                        break
                    last_db_check = time.time()

                # Sleep to avoid busy loop (short for faster detection)
                time.sleep(Intervals.EVENT_LOOP_SLEEP)

            except Exception as e:
                LOG.error(f"Error in event loop: {e}")
                self._stop_event.set()

        # Event loop exited
        LOG.debug("Exiting event loop")
        # Note: QEMU cleanup is handled by context manager (Machine.__exit__)
        # We just need to clean up IPC resources
        self._cleanup()

    def _is_qemu_running(self) -> bool:
        """
        Check if QEMU process is still alive.

        Uses both Machine.is_running() and explicit PID check for reliability.

        Returns:
            True if QEMU process is running, False otherwise
        """
        if not self.machine:
            return False

        # First check Machine's is_running property
        if not self.machine.is_running:
            return False

        # Double-check PID exists (more reliable)
        qemu_pid = self.machine.pid
        if not qemu_pid:
            return False

        # Verify PID is alive
        return validate_pid_exists(qemu_pid, process_name="QEMU")

    def _check_db_consistency(self) -> bool:
        """
        Check if DB state matches reality (detect drift).

        Consistency checks:
        1. VM deleted from DB → stop runner
        2. DB status=stopped → stop runner
        3. DB has different runner_pid → stop runner (another runner started)
        4. QEMU PID mismatch → update DB

        Returns:
            True if consistent (continue running)
            False if inconsistent (should exit)
        """
        try:
            vm = self.state_manager.get_vm(self.vm_id)

            # Check 1: VM deleted from DB
            if not vm:
                LOG.warning(f"VM {self.vm_id} deleted from DB")
                return False

            # Check 2: DB says stopped
            if vm.status == "stopped":
                LOG.warning(f"DB indicates {self.vm_id} status is stopped")
                return False

            # Check 3: DB has different runner PID
            if vm.runner_pid and vm.runner_pid != os.getpid():
                LOG.warning(
                    f"DB has different runner PID ({vm.runner_pid} "
                    f"vs {os.getpid()})"
                )
                return False

            # Check 4: QEMU PID mismatch (update DB if needed)
            current_qemu_pid = self.machine.pid if self.machine else None
            if vm.pid != current_qemu_pid:
                LOG.debug(
                    f"QEMU PID mismatch, updating DB "
                    f"({vm.pid} -> {current_qemu_pid})"
                )
                self.state_manager.update_vm_status(
                    self.vm_id,
                    status=vm.status,
                    pid=current_qemu_pid,
                    runner_pid=vm.runner_pid,
                    socket_path=vm.socket_path,
                )

            return True  # All consistent

        except Exception as e:
            LOG.error(f"Error checking DB consistency: {e}")
            return False

    def _handle_qemu_exit(self) -> None:
        """
        QEMU process exited, cleanup and exit runner.

        Called when QEMU process is detected as not running.
        Updates database and stops runner process.
        """
        LOG.info(f"QEMU for {self.vm_id} exited, cleaning up")

        # Update database
        try:
            self.state_manager.update_vm_status(
                self.vm_id,
                status="stopped",
                pid=None,
                runner_pid=None,
                socket_path=None,
                qmp_socket_path=None,
            )
        except Exception as e:
            LOG.error(f"Failed to update DB after QEMU exit: {e}")

        self._stop_event.set()

    def _handle_db_stop_command(self) -> None:
        """
        DB says VM should be stopped (drift or manual stop).

        Called when DB consistency check detects stop condition.
        Stops QEMU gracefully and exits runner.
        """
        LOG.info(f"DB indicates {self.vm_id} should stop, shutting down")

        # Stop QEMU using Machine.stop() (handles graceful + force)
        if self.machine and self._is_qemu_running():
            try:
                self.machine.stop(force=False, timeout=Timeouts.VM_GRACEFUL_SHUTDOWN)
            except Exception as e:
                LOG.error(f"Failed to stop QEMU: {e}")

        self._stop_event.set()

    async def _handle_ipc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle IPC request from CLI.

        Args:
            request: {
                "method": "qmp" | "stop" | "status" | "ping",
                "args": [...],
                "kwargs": {...}
            }

        Returns:
            {"status": "success", "result": ...} or
            {"status": "error", "error": ...}
        """
        method_name = request.get("method")
        args = request.get("args", [])
        kwargs = request.get("kwargs", {})

        LOG.debug(f"IPC request: method={method_name}, args={args}")

        try:
            # Special methods handled directly
            if method_name == "qmp":
                # QMP command: args = [command], kwargs = QMP arguments
                if not args:
                    return {"status": "error", "error": "QMP command required"}

                command = args[0]
                result = self.machine.qmp(command, **kwargs)
                return {"status": "success", "result": result}

            elif method_name == "stop":
                # Signal runner to stop (event loop will handle QEMU shutdown)
                LOG.info(f"Stop command received via IPC for {self.vm_id}")

                # Don't stop QEMU here - avoid asyncio conflicts
                # Just signal event loop to exit, it will handle cleanup
                self._stop_event.set()

                return {"status": "success", "result": "VM stopping"}

            elif method_name == "status":
                # Get VM status via dedicated handler
                result = self._handle_status_command(kwargs)
                return {"status": "success", "result": result}

            elif method_name == "ping":
                # Health check
                return {"status": "success", "result": "pong"}

            else:
                return {"status": "error", "error": f"Unknown method: {method_name}"}

        except Exception as e:
            LOG.error(f"Error handling IPC request: {e}")
            return {"status": "error", "error": str(e)}

    def _handle_status_command(self, params: dict) -> dict:
        """
        Handle 'status' IPC command.

        Provides comprehensive status information about the VM runner
        including runner PID, QEMU PID, VM ID, and uptime.

        Args:
            params: Command parameters (currently unused)

        Returns:
            Status dictionary with:
                - runner_pid: VM runner process ID
                - qemu_pid: QEMU process ID (or None if not running)
                - vm_id: VM identifier
                - uptime: Seconds since runner started
                - running: Whether QEMU is currently running
                - socket_path: Unix socket path for IPC
        """
        uptime = time.time() - self.start_time
        status = {
            "runner_pid": os.getpid(),
            "qemu_pid": self.machine.pid if self.machine else None,
            "vm_id": self.vm_id,
            "uptime": uptime,
            "running": self._is_qemu_running(),
            "socket_path": str(self.socket_path) if self.socket_path else None,
        }
        return status

    def _handle_signal(self, signum: int, frame) -> None:
        """
        Handle termination signals (SIGTERM, SIGINT).

        Args:
            signum: Signal number
            frame: Current stack frame (unused)
        """
        LOG.info(f"Received signal {signum}, initiating shutdown")
        self._stop_event.set()

    def _cleanup(self) -> None:
        """
        Cleanup resources before exit.

        Cleanup tasks:
        - Stop IPC server
        - Remove socket file EXPLICITLY
        - Update database to stopped status
        """
        LOG.debug("Cleaning up VM runner resources")

        # Stop IPC server (use sync method for cross-thread safety)
        if self.ipc_server:
            try:
                LOG.debug("Stopping IPC server thread")
                self.ipc_server.stop_sync()
                # Wait for IPC thread to finish (it's a daemon, but let's be clean)
                if hasattr(self, 'ipc_thread') and self.ipc_thread.is_alive():
                    LOG.debug("Waiting for IPC thread to finish")
                    self.ipc_thread.join(timeout=1.0)
                    if self.ipc_thread.is_alive():
                        LOG.warning("IPC thread did not finish within timeout")
            except Exception as e:
                LOG.error(f"Failed to stop IPC server: {e}")

        # Remove socket file EXPLICITLY (in case IPC server didn't)
        if self.socket_path and self.socket_path.exists():
            try:
                self.socket_path.unlink()
                LOG.debug(f"Removed socket file {self.socket_path}")
            except Exception as e:
                LOG.error(f"Failed to remove socket: {e}")

        # Remove secret file
        if self.socket_path:
            secret_file = self.socket_path.with_suffix('.auth')
            if secret_file.exists():
                try:
                    secret_file.unlink()
                    LOG.debug(f"Removed auth secret file: {secret_file}")
                except Exception as e:
                    LOG.warning(f"Failed to remove secret file: {e}")

        # Update DB to stopped status
        if self.state_manager:
            try:
                self.state_manager.update_vm_status(
                    self.vm_id,
                    status="stopped",
                    pid=None,
                    runner_pid=None,
                    socket_path=None,
                    qmp_socket_path=None,
                )
                LOG.debug(f"Updated DB status to stopped for {self.vm_id}")
            except Exception as e:
                LOG.error(f"Failed to update DB on cleanup: {e}")


def main() -> None:
    """
    Entry point for VM runner process.

    Usage: python3 -m maqet.vm_runner <vm_id> [db_path]

    Args:
        vm_id: Virtual machine identifier (required)
        db_path: Optional database path (for testing)
    """
    # Initialize logging BEFORE any operations
    LOG.info("=" * 80)
    LOG.info(f"VM Runner starting (PID: {os.getpid()})")
    LOG.info("=" * 80)

    if len(sys.argv) < 2:
        print("Usage: python3 -m maqet.vm_runner <vm_id> [db_path]", file=sys.stderr)
        sys.exit(1)

    vm_id = sys.argv[1]
    db_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    LOG.info(f"VM ID: {vm_id}")
    LOG.info(f"Database: {db_path}")

    # Create and start VM runner
    runner = VMRunner(vm_id, db_path)

    try:
        runner.start()
    except KeyboardInterrupt:
        LOG.info("VM runner interrupted by user")
        sys.exit(0)
    except Exception as e:
        LOG.error(f"VM runner failed to start: {e}", exc_info=True)

        # Write error to dedicated file for parent process
        error_file = get_runner_error_path(vm_id)
        try:
            qemu_pid = runner.machine.pid if runner.machine else None
            error_content = (
                f"VM Runner Startup Failed\n"
                f"Error: {e}\n"
                f"Type: {type(e).__name__}\n"
                f"Runner PID: {os.getpid()}\n"
                f"QEMU PID: {qemu_pid if qemu_pid else 'N/A'}\n"
                f"Timestamp: {time.time()}\n"
                f"\nFull Traceback:\n{traceback.format_exc()}"
            )

            # Create file with atomic permissions using file descriptor
            import stat
            try:
                # O_WRONLY: Write-only
                # O_CREAT: Create if doesn't exist
                # O_TRUNC: Truncate if exists (for retry scenarios)
                # O_EXCL removed: Allow overwriting stale error files
                fd = os.open(
                    str(error_file),
                    os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                    mode=stat.S_IRUSR | stat.S_IWUSR  # 0600 (owner read/write only)
                )
                try:
                    os.write(fd, error_content.encode('utf-8'))
                finally:
                    os.close(fd)

                LOG.debug(f"Wrote error file with 0600 permissions: {error_file}")

            except OSError as write_err:
                # Log but don't crash - error file is best-effort diagnostics
                LOG.warning(f"Failed to write error file {error_file}: {write_err}")

        except Exception as write_error:
            LOG.error(f"Failed to write error file: {write_error}")

        sys.exit(1)


if __name__ == "__main__":
    main()
