"""
MAQET Machine

Enhanced QEMUMachine integration for MAQET VM management.
Handles VM process lifecycle, QMP communication, and state tracking.
"""

import fcntl
import os  # noqa: F401 - Used by tests for mocking os.kill in force_kill tests
import signal
import time  # noqa: F401 - Used by tests for mocking time.sleep and time.time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

try:
    from qemu.machine import QEMUMachine
except ImportError:
    # Fallback to vendored version
    from maqet.vendor.qemu.machine import QEMUMachine

from .config_handlers import ConfigurableMachine
from .constants import Timeouts
from .logger import LOG
from .managers.process_lifecycle_manager import (
    ProcessLifecycleManager,
)
from .qmp import QMPClient, QMPClientError
from .storage import StorageManager
from .utils.process_validation import validate_pid_exists
from .validation import ConfigValidator

if TYPE_CHECKING:
    from .protocols.storage import StorageRegistryProtocol
    from .state import StateManager


class MaqetQEMUMachine(QEMUMachine):
    """
    MAQET's simplified QEMUMachine without display defaults.

    Removes hardcoded display/VGA arguments from _base_args, letting QEMU
    use its own defaults or user-configured values. Maintains QMP and
    console configuration from parent class.

    Users configure display explicitly if needed (e.g., -display none for headless).

    Also ensures QEMU dies when parent process dies using PR_SET_PDEATHSIG.
    """

    def _launch(self) -> None:
        """
        Launch QEMU with PR_SET_PDEATHSIG to ensure cleanup on parent death.

        PR_SET_PDEATHSIG is a Linux kernel feature that sends a signal to the
        child process when the parent dies, REGARDLESS of how the parent was killed.
        This works even for SIGKILL (kill -9) where Python cleanup cannot run.

        When VMRunner dies (crash, kill -9, SIGTERM, etc.), kernel automatically
        sends SIGKILL to QEMU process. No orphaned processes possible.
        """
        import ctypes
        import subprocess

        # Import PR_SET_PDEATHSIG constant
        # This is Linux-specific, set to 1 based on prctl.h
        PR_SET_PDEATHSIG = 1

        def set_pdeathsig():
            """
            Set parent death signal to SIGKILL for this process.

            Called in child process before exec via preexec_fn.
            When parent dies, kernel sends SIGKILL to this process.
            """
            try:
                # Load libc
                libc = ctypes.CDLL('libc.so.6')

                # Call prctl(PR_SET_PDEATHSIG, SIGKILL)
                # SIGKILL = 9
                result = libc.prctl(PR_SET_PDEATHSIG, signal.SIGKILL)

                if result != 0:
                    # prctl failed, but we can't log here (in child process)
                    # Parent will detect if QEMU fails to start
                    pass

            except Exception:
                # If prctl fails (non-Linux, missing libc), continue anyway
                # QEMU will start but won't have death signal protection
                pass

        # Call parent's pre-launch
        self._pre_launch()
        LOG.debug('VM launch command: %r', ' '.join(self._qemu_full_args))

        # Launch QEMU with preexec_fn to set parent death signal
        # pylint: disable=consider-using-with
        self._popen = subprocess.Popen(
            self._qemu_full_args,
            stdin=subprocess.DEVNULL,
            stdout=self._qemu_log_file,
            stderr=subprocess.STDOUT,
            shell=False,
            close_fds=False,
            preexec_fn=set_pdeathsig  # Set PR_SET_PDEATHSIG before exec
        )
        self._launched = True
        self._post_launch()

    @property
    def _base_args(self) -> List[str]:
        """
        Override base args to only include essential QMP/console config.

        No display or VGA defaults - users configure these explicitly if needed.
        QEMU will use its own defaults (typically GTK/SDL if available).
        """
        args = []

        # QMP configuration (from parent class)
        if self._qmp_set:
            if self._sock_pair:
                moncdev = f"socket,id=mon,fd={self._sock_pair[0].fileno()}"
            elif isinstance(self._monitor_address, tuple):
                moncdev = "socket,id=mon,host={},port={}".format(
                    *self._monitor_address
                )
            else:
                moncdev = f"socket,id=mon,path={self._monitor_address}"
            args.extend(
                ["-chardev", moncdev, "-mon", "chardev=mon,mode=control"]
            )

        # Machine type (from parent class)
        if self._machine is not None:
            args.extend(["-machine", self._machine])

        # Console configuration (from parent class)
        for _ in range(self._console_index):
            args.extend(["-serial", "null"])
        if self._console_set:
            assert self._cons_sock_pair is not None
            fd = self._cons_sock_pair[0].fileno()
            chardev = f"socket,id=console,fd={fd}"
            args.extend(["-chardev", chardev])
            if self._console_device_type is None:
                args.extend(["-serial", "chardev:console"])
            else:
                device = "%s,chardev=console" % self._console_device_type
                args.extend(["-device", device])

        return args


class MachineError(Exception):
    """Machine-related errors"""


class Machine(ConfigurableMachine):
    """
    VM process lifecycle orchestrator for MAQET.

    Orchestrates VM lifecycle by coordinating specialized components:
    - ConfigValidator: Configuration validation and health checks
    - QMPClient: QMP command execution
    - StorageManager: Storage device setup and management
    - ProcessLifecycleManager: Process cleanup and signal handling

    Responsibilities:
    - Orchestrate component interactions during VM lifecycle
    - Manage QEMU process lifecycle (start, stop, cleanup)
    - Create and configure QEMU machine instances
    - Handle context manager protocol (__enter__/__exit__)
    - Coordinate cleanup on exit/error
    - Handle startup sequencing and locking (file locks, PID files)

    Delegates to specialized components:
    - All validation to ConfigValidator
    - All QMP commands to QMPClient
    - All storage operations to StorageManager
    - All state persistence to StateManager
    - All process cleanup to ProcessLifecycleManager

    Example:
        config = {"binary": "/usr/bin/qemu-system-x86_64", "memory": "2G"}
        with Machine(config, "my-vm", state_manager) as machine:
            machine.start()
            status = machine.qmp("query-status")
        # VM automatically cleaned up on exit

    Architecture:
        Machine is a thin orchestration layer that coordinates specialized
        components. Each component has a single, well-defined responsibility.
        This design improves testability, maintainability, and extensibility.

    # REFACTORED (2025-10-27): Responsibilities extracted to focused managers
    # Machine class reduced from 790 -> 673 lines by delegating to:
    #   - ConfigValidator: validate_machine_requirements(), pre_start_validation()
    #   - QMPClient: QMP command execution with timeout and safety checks
    #   - StorageManager: Storage device setup and QEMU args generation
    #   - ProcessLifecycleManager: Process cleanup, signal handling, PID registry
    # Machine now focuses purely on orchestrating component interactions.
    #
    # REFACTORED (2025-10-30): QEMUMachineFactory eliminated (Phase 4)
    # Factory inlined into Machine._create_qemu_machine() method (-103 LOC net)
    # Simple QEMU instance creation now co-located with its usage point.
    #
    # REFACTORED (2025-10-30): StartupCoordinator eliminated (Phase 2)
    # Startup methods inlined into Machine class as they were only used here
    # Startup locking, PID file management now handled directly by Machine

    # FIXED (2025-10-26): Cross-process QMP Communication - IMPLEMENTED via IPC
    # Original Problem: QMP commands failed from CLI after VM start because QEMUMachine
    # instances could not be shared between processes (unpicklable file descriptors).
    #
    # Implemented Solution: Per-VM process architecture with IPC-based QMP forwarding
    #   - Each VM runs in dedicated VMRunner process (tracked via runner_pid in database)
    #   - VMRunner owns QMP connection to QEMU, maintains it throughout VM lifecycle
    #   - QMPManager sends IPC messages to VMRunner, which forwards to QEMU QMP socket
    #   - Communication flow: CLI -> IPC Socket -> VMRunner -> QMP Socket -> QEMU
    #   - All QMP commands (query-status, screendump, send-key, etc.) work from CLI
    #
    # See: specs/fix-cross-process-qmp-communication.md for original problem analysis
    # See: maqet/managers/qmp_manager.py for implementation details
    # See: maqet/ipc/runner_client.py for IPC infrastructure
    """

    def __init__(
        self,
        config_data: Dict[str, Any],
        vm_id: str,
        state_manager: "StateManager",
        config_validator: Optional[ConfigValidator] = None,
        storage_registry: Optional["StorageRegistryProtocol"] = None,
    ):
        """
        Initialize machine instance.

        Orchestrates VM initialization by:
        1. Validating complete configuration (via ConfigValidator)
        2. Initializing component managers (QMP, Storage, Process, etc.)
        3. Preparing VM for start (no QEMU process created yet)

        Args:
            config_data: VM configuration dictionary
            vm_id: VM instance ID
            state_manager: State manager instance
            config_validator: Configuration validator (optional, creates default if None)
            storage_registry: Storage registry for file tracking (optional, for dependency injection)

        Raises:
            MachineError: If configuration validation fails
        """
        LOG.debug(f"Initializing Machine for VM {vm_id}")

        # Initialize ConfigurableMachine (creates instance-specific config registry)
        super().__init__()

        # Initialize validator (use provided or create default)
        self.config_validator = config_validator or ConfigValidator()

        # Validate all machine requirements (schema + runtime checks)
        # This consolidates all validation needed before resource creation
        try:
            self.config_validator.validate_machine_requirements(config_data)
        except Exception as e:
            # Wrap validation errors as MachineError for consistency
            raise MachineError(f"Configuration validation failed: {e}")

        self.config_data = config_data
        self.vm_id = vm_id
        self.state_manager = state_manager
        self._storage_registry = storage_registry  # Optional injected registry
        self._qemu_machine: Optional[QEMUMachine] = None
        self._pid: Optional[int] = None

        # Initialize QMP client for command execution
        self.qmp_client = QMPClient(vm_id=vm_id)

        # Initialize storage manager
        self.storage_manager = StorageManager(vm_id)
        storage_configs = config_data.get("storage", [])
        if storage_configs:
            self.storage_manager.add_storage_from_config(storage_configs)

        # Initialize process lifecycle manager
        self.process_lifecycle_manager = ProcessLifecycleManager(
            vm_id=vm_id,
            state_manager=state_manager,
        )

        # Startup lock file handle (for file locking during VM start)
        self._lock_file: Optional[object] = None

    def __enter__(self):
        """
        Context manager entry - allows using Machine with 'with' statement.

        Example:
            with Machine(config, vm_id, state_manager) as machine:
                machine.start()
                # Do work...
            # QEMU automatically cleaned up on exit
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - ensures QEMU is stopped when exiting 'with' block.

        This is called AUTOMATICALLY when:
        - 'with' block completes normally
        - Exception is raised in 'with' block
        - Process is killed (Python cleanup)

        This is the SIMPLE, RELIABLE way to ensure QEMU cleanup.
        """
        try:
            if self._qemu_machine and self._qemu_machine.is_running():
                LOG.debug(f"Context manager exit: stopping QEMU for {self.vm_id}")
                # Use graceful stop with short timeout for faster exit
                self.stop(force=False, timeout=Timeouts.VM_GRACEFUL_SHUTDOWN_SHORT)
        except Exception as e:
            LOG.error(f"Error stopping QEMU during context exit: {e}")
            # Try force kill as last resort
            if self._pid:
                if not self.process_lifecycle_manager.force_kill(self._pid):
                    LOG.error(f"Failed to force kill VM {self.vm_id} during context exit")

        return False  # Don't suppress exceptions

    def __del__(self):
        """
        Cleanup destructor - ensures QEMU process is stopped when Machine is garbage collected.

        This prevents orphaned QEMU processes when tests or scripts exit without
        explicitly stopping VMs.
        """
        try:
            if self._qemu_machine and self._qemu_machine.is_running():
                LOG.debug(
                    f"Machine {
                        self.vm_id} being garbage collected - stopping QEMU process"
                )
                # Force kill without trying graceful shutdown to avoid hanging
                # during GC
                if self._pid:
                    if self.process_lifecycle_manager.force_kill(self._pid):
                        LOG.debug(
                            f"Killed orphan QEMU process {
                                self._pid} for VM {self.vm_id}"
                        )
                    else:
                        # Log error but don't raise - destructors must not raise
                        LOG.error(
                            f"Failed to kill orphan QEMU process {
                                self._pid} for VM {self.vm_id}"
                        )
                    # Unregister from cleanup registry
                    self.process_lifecycle_manager.unregister_pid(self._pid)
                # Update state if possible
                try:
                    self.state_manager.update_vm_status(
                        self.vm_id, "stopped", pid=None, socket_path=None, qmp_socket_path=None
                    )
                except Exception:
                    pass  # State manager might be gone during shutdown
        except Exception as e:
            # Destructors should never raise exceptions
            try:
                LOG.debug(f"Error in Machine.__del__ for {self.vm_id}: {e}")
            except Exception:
                pass  # Logger might be gone during interpreter shutdown

    def _acquire_start_lock(self) -> None:
        """
        Acquire file lock to prevent concurrent VM starts.

        Raises:
            BlockingIOError: If lock cannot be acquired (another start in progress)
        """
        lock_file_path = self.state_manager.get_lock_path(self.vm_id)
        lock_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = open(lock_file_path, "w")

        try:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise BlockingIOError(
                f"VM {self.vm_id} is already being started by another process. "
                f"Wait for that process to complete."
            )

    def _release_start_lock(self) -> None:
        """Release file lock and clean up lock file."""
        if self._lock_file:
            try:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                lock_path = Path(self._lock_file.name)
                self._lock_file.close()
                lock_path.unlink(missing_ok=True)
            except Exception as e:
                LOG.debug(f"Error releasing VM start lock: {e}")
            finally:
                self._lock_file = None

    def _write_pid_file(self, pid: int) -> None:
        """
        Write PID to file for tracking.

        Args:
            pid: Process ID to write
        """
        pid_path = self.state_manager.get_pid_path(self.vm_id)
        with open(pid_path, "w") as f:
            f.write(str(pid))

    def _get_socket_path(self, qemu_machine) -> str:
        """
        Get the actual socket path used by QEMU machine.

        Args:
            qemu_machine: QEMU machine instance

        Returns:
            Socket path as string
        """
        # Get the actual socket path used by QEMUMachine
        actual_socket_path = qemu_machine._monitor_address
        if not actual_socket_path:
            LOG.warning(
                f"QEMUMachine did not create QMP monitor socket for VM {self.vm_id}"
            )
            actual_socket_path = str(
                self.state_manager.get_socket_path(self.vm_id)
            )
        return str(actual_socket_path)

    def _update_running_status(
        self, pid: int, socket_path: str, qmp_socket_path: Optional[str] = None
    ) -> None:
        """
        Update database with running status.

        Args:
            pid: Process ID
            socket_path: IPC socket path for VMRunner communication
            qmp_socket_path: QMP socket path for QEMU communication (optional)
        """
        self.state_manager.update_vm_status(
            self.vm_id,
            "running",
            pid=pid,
            socket_path=socket_path,
            qmp_socket_path=qmp_socket_path,
        )
        LOG.debug(f"VM {self.vm_id} IPC socket: {socket_path}")
        if qmp_socket_path:
            LOG.debug(f"VM {self.vm_id} QMP socket: {qmp_socket_path}")

    def _cleanup_failed_start(self, pid: Optional[int] = None) -> None:
        """
        Clean up partial state after failed VM start.

        Removes PID file, socket file, and updates database status.
        Storage file cleanup is handled by storage.py (partial file removal).

        Args:
            pid: Process ID if available (for unregistration)
        """
        # Unregister PID from cleanup registry if set
        if self._pid:
            self.process_lifecycle_manager.unregister_pid(self._pid)

        try:
            # Remove PID file if it exists
            if pid:
                pid_path = self.state_manager.get_pid_path(self.vm_id)
                if pid_path.exists():
                    pid_path.unlink()
                    LOG.debug(f"Removed PID file for failed start: {pid_path}")

            # Remove socket file if it exists
            socket_path = self.state_manager.get_socket_path(self.vm_id)
            if socket_path.exists():
                socket_path.unlink()
                LOG.debug(f"Removed socket file for failed start: {socket_path}")

            # Update database status to failed
            self.state_manager.update_vm_status(
                self.vm_id, "failed", pid=None, socket_path=None
            )
            LOG.debug(f"Updated VM {self.vm_id} status to failed")

        except Exception as cleanup_error:
            LOG.warning(f"Error during cleanup of failed start: {cleanup_error}")

    def start(self) -> None:
        """
        Start VM and wait for it to be ready.

        Implements file locking to prevent concurrent starts and ensures
        cleanup of partial state (PID, socket) on any failure.
        Storage file cleanup is handled by storage.py.
        """
        try:
            # Acquire lock to prevent concurrent VM starts
            self._acquire_start_lock()

            # Pre-start validation
            self._pre_start_validation()

            try:
                self._create_qemu_machine()
                self._configure_machine()

                LOG.info(f"Starting VM {self.vm_id}")
                self._qemu_machine.launch()

                # Get process PID
                self._pid = self._qemu_machine._popen.pid

                # Register PID in global registry for cleanup on exit
                self.process_lifecycle_manager.register_pid(self._pid)

                # Write PID file
                self._write_pid_file(self._pid)

                # Get the actual socket path used by QEMUMachine
                actual_socket_path = self._get_socket_path(self._qemu_machine)

                # Extract QMP socket path from QEMUMachine
                # QEMUMachine stores this in self._monitor_address after launch
                qmp_socket = self._qemu_machine._monitor_address
                LOG.debug(
                    f"Extracted QMP socket path from QEMUMachine: {qmp_socket}"
                )

                # Update database with VM status, IPC socket, and QMP socket paths
                self._update_running_status(
                    self._pid, actual_socket_path, qmp_socket_path=str(qmp_socket) if qmp_socket else None
                )

                # Wait for VM to be ready (handled by QEMUMachine)
                self._wait_for_ready()

            except Exception as e:
                LOG.error(f"Failed to start VM {self.vm_id}: {e}")
                self._cleanup_failed_start()
                raise MachineError(f"Failed to start VM: {e}")

        finally:
            # Release lock
            self._release_start_lock()

    def _pre_start_validation(self) -> None:
        """
        Perform pre-start validation checks (delegates to ConfigValidator).

        Raises:
            MachineError: If validation fails
        """
        try:
            self.config_validator.pre_start_validation(self.config_data)
        except Exception as e:
            # Wrap validation errors as MachineError for backward compatibility
            raise MachineError(str(e))

    def _graceful_shutdown(self, timeout: int = 30) -> bool:
        """
        Attempt graceful shutdown of VM via QMP.
        (Delegates to ProcessLifecycleManager)

        Args:
            timeout: Maximum seconds to wait for shutdown

        Returns:
            True if shutdown succeeded, False otherwise
        """
        if not self._qemu_machine:
            return False

        return self.process_lifecycle_manager.graceful_shutdown(
            self._qemu_machine, timeout
        )

    def _force_kill(self) -> None:
        """
        Force kill the VM process using SIGTERM then SIGKILL.

        Delegates to ProcessLifecycleManager for process termination.

        Raises:
            RuntimeError: If process cannot be killed after all attempts
        """
        if not self._pid:
            return

        # Delegate to ProcessLifecycleManager
        if not self.process_lifecycle_manager.force_kill(self._pid):
            raise RuntimeError(f"Failed to kill QEMU process {self._pid} for VM {self.vm_id}")

    def _emergency_cleanup(self) -> None:
        """
        Emergency cleanup if normal cleanup didn't happen.

        Called by atexit handler to ensure QEMU process is killed even if
        normal stop() wasn't called. This is a last-resort safety mechanism.

        NEVER raises exceptions - only logs errors.
        """
        if self.is_running and self._pid:
            self.process_lifecycle_manager.emergency_cleanup(self._pid)

    def _cleanup_after_stop(self) -> None:
        """
        Cleanup after VM stops (GUARANTEED to run in finally block).

        NEVER raises exceptions - only logs errors. This method MUST be called
        in a finally block to ensure cleanup happens even if stop fails.

        Delegates to ProcessLifecycleManager for:
        - Unregisters PID from active registry
        - Updates database status
        - Removes temporary files
        """
        self.process_lifecycle_manager.cleanup_after_stop(self._pid)

    def stop(self, force: bool = False, timeout: int = 30) -> None:
        """
        Stop the VM with robust cleanup guarantees.

        Uses try/finally to ensure cleanup ALWAYS happens, even if stop fails.
        Cleanup is delegated to ProcessLifecycleManager which never raises exceptions.

        Args:
            force: Force kill immediately, skip graceful shutdown
            timeout: Timeout for graceful shutdown (only used when force=False)

        Raises:
            MachineError: If VM stop fails (cleanup still happens in finally)
        """
        try:
            if self._qemu_machine and self._qemu_machine.is_running():
                LOG.info(f"Stopping VM {self.vm_id}")

                if force:
                    # Force kill immediately - skip graceful shutdown
                    self._force_kill()
                else:
                    # Try graceful shutdown first
                    success = self._graceful_shutdown(timeout)
                    if not success:
                        # Graceful shutdown failed, force kill
                        LOG.warning(
                            f"Graceful shutdown failed for VM {self.vm_id}, force killing"
                        )
                        self._force_kill()

        except Exception as e:
            LOG.error(f"Error stopping VM {self.vm_id}: {e}")
            # Re-raise after cleanup happens in finally
            raise MachineError(f"Failed to stop VM: {e}")

        finally:
            # ALWAYS cleanup, even if stop failed or VM wasn't running
            # This method is guaranteed to never raise exceptions
            self._cleanup_after_stop()

    def qmp(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute QMP command (alias for qmp_command).

        Args:
            command: QMP command name
            **kwargs: Command arguments

        Returns:
            Command result dictionary

        Raises:
            MachineError: If VM is not running or command fails
        """
        return self.qmp_command(command, **kwargs)

    def qmp_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute QMP command on the VM (delegates to QMPClient).

        Args:
            command: QMP command to execute
            **kwargs: Command parameters

        Returns:
            QMP command result

        Raises:
            MachineError: If VM is not running, command is dangerous, or timeout occurs
        """
        try:
            # Delegate to QMP client for execution
            return self.qmp_client.execute(self._qemu_machine, command, **kwargs)
        except QMPClientError as e:
            # Convert QMPClientError to MachineError for backward compatibility
            raise MachineError(str(e))

    @property
    def pid(self) -> Optional[int]:
        """Get VM process PID."""
        if self._qemu_machine and self._qemu_machine._popen:
            return self._qemu_machine._popen.pid
        return self._pid

    @property
    def is_running(self) -> bool:
        """Check if VM is running."""
        if self._qemu_machine:
            return self._qemu_machine.is_running()
        if self._pid:
            return self._is_process_alive(self._pid)
        return False

    def _create_qemu_machine(self) -> None:
        """
        Create and configure QEMUMachine instance.

        Internal helper to create the underlying QEMUMachine object
        with proper socket paths and directories.

        Raises:
            MachineError: If creation or verification fails
        """
        # Get QEMU binary from config
        binary = self.config_data.get("binary", "/usr/bin/qemu-system-x86_64")

        # Get socket path for QMP communication
        socket_path = str(self.state_manager.get_socket_path(self.vm_id))
        socket_path_obj = Path(socket_path)

        # Ensure socket directory exists
        socket_path_obj.parent.mkdir(parents=True, exist_ok=True)

        LOG.debug(f"Creating MaqetQEMUMachine with QMP socket: {socket_path}")

        # Create QEMU machine instance
        self._qemu_machine = MaqetQEMUMachine(
            binary=binary,
            name=self.vm_id,
            log_dir=str(self.state_manager.xdg.runtime_dir),
            monitor_address=socket_path,
        )

        # Verify QMP is enabled
        LOG.debug(f"QMP enabled: {self._qemu_machine._qmp_set}")

    def _configure_machine(self) -> None:
        """Configure QEMU machine using handler-based system."""
        if not self._qemu_machine:
            return

        # Process configuration using registered handlers
        processed_keys = self.process_configuration(self.config_data)

        # Apply defaults for any unprocessed keys
        self.apply_default_configuration()

        LOG.debug(
            f"Machine configuration complete. Processed keys: {processed_keys}"
        )

    def _add_storage_devices(self) -> None:
        """Add all storage devices to QEMU machine using unified storage manager."""
        if not self._qemu_machine:
            return

        # Create storage files if needed
        self.storage_manager.create_storage_files()

        # Persist updated storage configs to database
        # This ensures file paths are saved for offline operations (e.g., snapshots)
        self._persist_storage_configs()

        # Register storage files in storage_registry (opportunistic)
        self._register_storage_files()

        # Add QEMU arguments for all storage devices
        storage_args = self.storage_manager.get_qemu_args()
        for args_list in storage_args:
            # Each args_list is like ["-drive", "file=...,if=...,format=..."]
            self._qemu_machine.add_args(*args_list)

    def _persist_storage_configs(self) -> None:
        """
        Persist updated storage configurations to database.

        After storage files are created, their actual paths are stored in the device
        configs. This method updates the VM configuration in the database so that
        subsequent operations (like offline snapshots) can find the correct file paths.
        """
        try:
            # Get current VM config from database
            vm = self.state_manager.get_vm(self.vm_id)
            if not vm or not vm.config_data:
                LOG.debug(
                    f"Cannot persist storage config for VM {self.vm_id}: VM not found"
                )
                return

            # Get updated storage configs from storage manager
            updated_storage_configs = self.storage_manager.get_storage_configs()

            # Only update if storage configs exist and changed
            if not updated_storage_configs:
                return

            # Create updated config with new storage configs
            updated_config = dict(vm.config_data)
            updated_config["storage"] = updated_storage_configs

            # Persist to database
            self.state_manager.update_vm_config(self.vm_id, updated_config)
            LOG.debug(f"Persisted updated storage config for VM {self.vm_id}")

        except Exception as e:
            # Log but don't fail - storage config persistence is opportunistic
            LOG.warning(
                f"Failed to persist storage config for VM {self.vm_id}: {e}"
            )

    def _register_storage_files(self) -> None:
        """
        Register file-based storage devices in storage_registry.

        This method opportunistically registers storage files after they are created.
        Registration failures are logged as warnings but don't fail VM creation,
        maintaining backward compatibility with older database schemas.

        Only file-based storage (QCOW2, Raw) is registered. VirtFS and other
        non-file storage types are skipped.
        """
        try:
            # Get file-based storage devices (QCOW2, Raw) before accessing database
            file_devices = self.storage_manager.get_file_based_devices()

            if not file_devices:
                LOG.debug(f"No file-based storage to register for VM {self.vm_id}")
                return

            # Get VM instance to retrieve VM name
            vm_instance = self.state_manager.get_vm(self.vm_id)
            if not vm_instance:
                LOG.debug(
                    f"Cannot register storage for VM {self.vm_id}: VM not found in database"
                )
                return

            # Use injected storage registry if available
            if not self._storage_registry:
                LOG.debug(
                    f"No storage registry injected for VM {self.vm_id}, "
                    "skipping storage registration"
                )
                return

            # Register each storage file
            registered_count = 0
            for device in file_devices:
                try:
                    # Only register if file exists (was actually created)
                    if not device.file_path.exists():
                        LOG.debug(
                            f"Skipping registration of non-existent file: "
                            f"{device.file_path}"
                        )
                        continue

                    self._storage_registry.register_storage(
                        vm_name=vm_instance.name,
                        path=device.file_path,
                    )
                    registered_count += 1
                    LOG.debug(
                        f"Registered storage for VM '{vm_instance.name}': "
                        f"{device.file_path}"
                    )
                except Exception as e:
                    # Log but don't fail - storage registration is opportunistic
                    LOG.debug(
                        f"Failed to register storage {device.file_path} "
                        f"for VM '{vm_instance.name}': {e}"
                    )

            if registered_count > 0:
                LOG.info(
                    f"Registered {registered_count} storage file(s) "
                    f"for VM '{vm_instance.name}'"
                )

        except Exception as e:
            # Storage registration is opportunistic - don't fail VM creation
            LOG.debug(
                f"Storage registration skipped for VM {self.vm_id}: {e}"
            )

    # NOTE: Storage handling has been refactored to use the extensible
    # StorageManager system
    # New storage types can be added by creating new device classes with
    # @storage_device decorator

    # NOTE: QEMUMachine handles wait-for-ready, but we verify QMP connectivity
    def _wait_for_ready(self) -> None:
        """
        Wait for VM QMP to be ready.

        QEMUMachine.launch() already establishes QMP connection,
        so we just verify it's working with a simple query.
        """
        if not self._qemu_machine:
            return

        # QEMUMachine.launch() already establishes QMP connection
        # Just verify it's working with a simple query
        try:
            if self._qemu_machine.is_running():
                # Test QMP is responsive
                self._qemu_machine.qmp("query-status")
                LOG.info(f"VM {self.vm_id} is ready")
        except Exception as e:
            LOG.warning(f"VM {self.vm_id} QMP verification failed: {e}")
            # VM process started but QMP may not be fully ready yet
            # This is usually not critical as QMP will become available shortly

    def _is_process_alive(self, pid: int) -> bool:
        """
        Check if process is still running.

        Note: This method is NOT delegated to ProcessLifecycleManager to maintain
        backward compatibility with tests that mock this method directly.
        """
        return validate_pid_exists(pid, process_name="QEMU process", log_permission_warning=False)

    def _cleanup_files(self) -> None:
        """
        Clean up temporary files.
        (Delegates to ProcessLifecycleManager)
        """
        self.process_lifecycle_manager.cleanup_files()
