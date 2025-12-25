"""
VM Manager

Manages VM lifecycle operations: add, start, stop, remove, list.
Extracted from Maqet class to follow Single Responsibility Principle.

Path Handling:
- Functions accept Union[str, Path] for path parameters
- Internally uses pathlib.Path objects for all path operations
- Converts to str only when calling external APIs or serializing to JSON
"""

from __future__ import annotations

import fcntl
import os
import signal
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import psutil

if TYPE_CHECKING:
    from ..config.parser import ConfigParser
    from ..managers.qmp_manager import QMPManager

from ..config import ConfigMerger
from ..utils.process_utils import ProcessVerifier
from ..constants import Intervals, Timeouts, MAX_PARALLEL_WORKERS
from ..decorators import handle_vm_errors, handle_snapshot_errors
from ..exceptions import (
    SnapshotError,
    VMLifecycleError,
)
from ..logger import LOG
from ..snapshot import SnapshotManager
from ..state import StateManager, VMInstance
from ..storage import StorageManager
from ..utils.process_validation import validate_pid_exists
from ..utils.error_files import read_runner_error
from ..vm_lifecycle import VMLifecycleManager


class VMManager:
    """
    Manages VM lifecycle operations.

    Responsibilities:
    - Create VMs (add)
    - Start VMs (spawn runner processes)
    - Stop VMs (via IPC or process kill)
    - Remove VMs (from database)
    - List VMs
    - Clean up dead processes
    """

    def __init__(
        self,
        state_manager: StateManager,
        config_parser: ConfigParser,
        qmp_manager: Optional[QMPManager] = None,
    ) -> None:
        """
        Initialize VM manager.

        Args:
            state_manager: State management instance
            config_parser: Configuration parser instance
            qmp_manager: QMP manager for live snapshot operations (optional)
        """
        self.state_manager = state_manager
        self.config_parser = config_parser
        self.qmp_manager = qmp_manager
        self._machines: Dict[str, Any] = {}  # Machine instances cache
        # Initialize lifecycle manager for transactional storage management
        self.lifecycle_manager = VMLifecycleManager(state_manager)
        LOG.debug("VMManager initialized")

    def get_machine_cache(self) -> Dict[str, Any]:
        """
        Get reference to machine instances cache.

        Returns:
            Dictionary mapping VM IDs to Machine instances

        Note:
            This provides read-only access for coordinators (like CleanupCoordinator).
            Cache clearing operations should be done via VMManager methods.
        """
        return self._machines

    def clear_machine_cache(self, vm_id: Optional[str] = None) -> None:
        """
        Clear machine instances from cache.

        Args:
            vm_id: Specific VM ID to remove from cache. If None, clears entire cache.

        Example:
            vm_manager.clear_machine_cache()  # Clear all
            vm_manager.clear_machine_cache("vm-123")  # Clear specific VM
        """
        if vm_id is None:
            self._machines.clear()
            LOG.debug("Cleared all machine instances from cache")
        else:
            self._machines.pop(vm_id, None)
            LOG.debug(f"Removed machine instance {vm_id} from cache")

    @handle_vm_errors("VM creation")
    def add(
        self,
        vm_config: Optional[Union[str, List[str]]] = None,
        name: Optional[str] = None,
        empty: bool = False,
        **kwargs,
    ) -> str:
        """
        Create a new VM from configuration file(s) or parameters.

        Args:
            vm_config: Path to YAML configuration file, or list of config
                files for deep-merge
            name: VM name (auto-generated if not provided)
            empty: Create empty VM without any configuration (won't be
                startable until configured)
            **kwargs: Additional VM configuration parameters

        Returns:
            VM instance ID

        Raises:
            VMLifecycleError: If VM creation fails

        Examples:
            Single config: add(vm_config="vm.yaml", name="myvm")
            Multiple configs: add(
                vm_config=["base.yaml", "custom.yaml"], name="myvm"
            )
            Config + params: add(vm_config="base.yaml", memory="8G", cpu=4)
            Empty VM: add(name="placeholder-vm", empty=True)
        """
        # Layer 2: Extract client working directory (reserved for future path resolution)
        kwargs.pop("_client_cwd", None)  # Discard for now - not yet implemented

        # Handle empty VM creation
        if empty:
            # Validate that no vm_config or kwargs are provided with --empty
            if vm_config:
                raise VMLifecycleError(
                    "Cannot specify config files with --empty flag"
                )
            if kwargs:
                raise VMLifecycleError(
                    "Cannot specify configuration parameters "
                    "with --empty flag"
                )

            # Create completely empty config
            config_data = {}
            config_file = None

            # Generate name if not provided
            if not name:
                # Generate unique name using UUID without creating temp VM
                import uuid
                unique_suffix = str(uuid.uuid4()).split('-')[-1][:8]
                name = f"empty-vm-{unique_suffix}"

            # Skip validation for empty VMs
            # Create VM in database with empty config
            vm_id = self.state_manager.create_vm(
                name, config_data, config_file
            )

            return vm_id

        # Normal VM creation path
        # Load and deep-merge configuration files
        if vm_config:
            config_data = ConfigMerger.load_and_merge_files(vm_config)
            if isinstance(vm_config, str):
                config_file = vm_config
            elif vm_config:
                config_file = vm_config[0]
            else:
                config_file = None
        else:
            config_data = {}
            config_file = None

        # Merge kwargs with config data (kwargs take precedence)
        if kwargs:
            config_data = ConfigMerger.deep_merge(config_data, kwargs)

        # Handle name priority: CLI --name > config name > auto-generated
        if not name:
            # Check if name is present in merged config
            name = config_data.get("name")

        # Always remove name from config_data as it's VM metadata, not QEMU
        # config
        if "name" in config_data:
            config_data = {
                k: v for k, v in config_data.items() if k != "name"
            }

        # Generate name if still not provided
        if not name:
            # Generate unique name using UUID without creating temp VM
            import uuid
            unique_suffix = str(uuid.uuid4()).split('-')[-1][:8]
            name = f"vm-{unique_suffix}"

        # Validate the final merged configuration
        config_data = self.config_parser.validate_config(config_data)

        # Create VM in database
        vm_id = self.state_manager.create_vm(
            name, config_data, config_file
        )

        return vm_id

    def _acquire_start_lock(self, vm_id: str):
        """
        Acquire file lock to prevent concurrent VM starts.

        Uses fcntl file locking (Unix only) to ensure only one
        process can start a VM at a time.

        Args:
            vm_id: VM identifier

        Returns:
            Open file handle (must be kept open during VM lifetime)

        Raises:
            BlockingIOError: If VM already being started
        """
        lock_file_path = self.state_manager.get_lock_path(vm_id)
        lock_file_path.parent.mkdir(parents=True, exist_ok=True)

        lock_file = open(lock_file_path, "w")
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_file
        except BlockingIOError:
            lock_file.close()
            raise BlockingIOError(
                f"VM '{vm_id}' is already being started by another process"
            )

    @handle_vm_errors("VM start")
    def start(
        self,
        vm_id: str,
        wait: bool = True,
        wait_for: str = "process-started",
        timeout: Optional[float] = None,
        **wait_kwargs
    ) -> VMInstance:
        """
        Start a virtual machine by spawning a detached VM runner process.

        Changes from previous implementation:
        - No longer manages Machine directly
        - Spawns VM runner process that manages QEMU lifecycle
        - VM runner survives CLI exit
        - Returns immediately after runner is ready (if wait=True)
        - Includes file locking to prevent concurrent starts
        - Supports extensible wait conditions

        Args:
            vm_id: VM identifier (name or ID)
            wait: Wait for condition before returning (default True)
            wait_for: Wait condition name (default "process-started")
                     Options: process-started, file-exists
            timeout: Maximum wait time in seconds (default Timeouts.VM_START)
            **wait_kwargs: Additional wait condition parameters

        Returns:
            VM instance information

        Raises:
            VMLifecycleError: If VM start fails or timeout expires
            BlockingIOError: If another process is already starting this VM

        Examples:
            Basic start with default wait:
                vm = manager.start("myvm")

            Start without waiting:
                vm = manager.start("myvm", wait=False)

            Wait for specific file:
                vm = manager.start("myvm", wait_for="file-exists", file_path="/tmp/marker")
        """
        # Acquire lock first to prevent concurrent starts
        lock_file = self._acquire_start_lock(vm_id)

        try:
            # Get VM from database
            vm = self.state_manager.get_vm(vm_id)
            if not vm:
                raise VMLifecycleError(f"VM '{vm_id}' not found")

            # Check if VM is already running
            if vm.status == "running":
                # Check if runner process is actually alive
                from ..process_spawner import is_runner_alive

                if vm.runner_pid and is_runner_alive(vm.runner_pid):
                    raise VMLifecycleError(
                        f"VM '{vm_id}' is already running "
                        f"(runner PID: {vm.runner_pid})"
                    )
                else:
                    # Stale state - clean up and continue
                    LOG.warning(
                        f"VM '{vm_id}' has stale 'running' status, cleaning up"
                    )
                    self.state_manager.update_vm_status(
                        vm_id, "stopped", runner_pid=None, socket_path=None
                    )

            # Check if VM has required configuration
            if not vm.config_data or not vm.config_data.get("binary"):
                raise VMLifecycleError(
                    f"VM '{vm_id}' cannot be started: missing required "
                    f"configuration. Use 'maqet apply {vm_id} "
                    f"--config <config.yaml>' to add configuration."
                )

            # Spawn VM runner process
            from ..process_spawner import (
                spawn_vm_runner,
                wait_for_vm_ready,
            )

            # Get database path for runner
            db_path = self.state_manager.xdg.database_path

            runner_pid = spawn_vm_runner(vm.id, db_path, timeout=Timeouts.PROCESS_SPAWN)
            LOG.info(f"Spawned VM runner process for '{vm_id}' (PID: {runner_pid})")

            # Register session for cleanup (only in test context)
            try:
                from tests.integration.conftest import register_vm_session
                register_vm_session(runner_pid)
            except ImportError:
                pass  # Not running in test context

            # Determine wait timeout with parallel execution multiplier
            if timeout is None:
                base_timeout = Timeouts.VM_START
                timeout_multiplier = int(os.environ.get('MAQET_TEST_TIMEOUT_MULTIPLIER', '1'))
                timeout = base_timeout * timeout_multiplier

                if timeout_multiplier > 1:
                    LOG.debug(
                        f"Waiting for VM start (timeout={timeout}s, "
                        f"multiplier={timeout_multiplier}x, base={base_timeout}s)"
                    )

            # Apply wait logic if requested
            if wait:
                from ..utils.wait_conditions import (
                    get_wait_condition,
                    normalize_condition_name,
                )
                from ..utils.wait_logic import wait_for_condition

                # Normalize condition name (handle aliases)
                wait_for_normalized = normalize_condition_name(wait_for)

                # Create wait condition
                try:
                    condition = get_wait_condition(
                        wait_for_normalized,
                        vm.id,
                        self.state_manager,
                        **wait_kwargs
                    )
                except ValueError as e:
                    # Invalid condition - cleanup and raise
                    from ..process_spawner import kill_runner
                    kill_runner(runner_pid, force=True)
                    raise VMLifecycleError(str(e))

                # Wait for condition
                outcome = wait_for_condition(condition, timeout=timeout)

                if not outcome.is_success():
                    # Wait failed - cleanup runner
                    from ..process_spawner import kill_runner
                    from ..utils.paths import get_log_path

                    kill_runner(runner_pid, force=True)

                    # Include error file details if available
                    error_details = read_runner_error(vm.id)
                    error_context = ""
                    if error_details:
                        error_context = f"\n\nError details:\n{error_details}"

                    # Build error message based on wait result
                    if outcome.is_timeout():
                        from ..exceptions import WaitTimeout
                        raise WaitTimeout(
                            f"Wait condition '{wait_for}' not met within {timeout}s "
                            f"after {outcome.metadata.get('attempts', 0)} attempts. "
                            f"Check logs: {get_log_path(vm.id)}{error_context}"
                        )
                    else:
                        raise VMLifecycleError(
                            f"Wait condition '{wait_for}' failed: {outcome.error_message}. "
                            f"Check logs: {get_log_path(vm.id)}{error_context}"
                        )

                LOG.info(
                    f"Wait condition '{wait_for}' met after {outcome.elapsed_time:.2f}s "
                    f"({outcome.metadata.get('attempts', 0)} attempts)"
                )
            else:
                # No wait - just ensure runner process started
                # Legacy behavior for backward compatibility
                ready = wait_for_vm_ready(
                    vm.id, self.state_manager, timeout=Timeouts.VM_START
                )

                if not ready:
                    # Runner process started but socket not available - cleanup
                    from ..process_spawner import kill_runner
                    from ..utils.paths import get_log_path

                    kill_runner(runner_pid, force=True)

                    # PHASE 2: Include error file details in exception
                    error_details = read_runner_error(vm.id)
                    if error_details:
                        raise VMLifecycleError(
                            f"VM runner did not become ready within {Timeouts.VM_START}s.\n\n"
                            f"Error details:\n{error_details}\n\n"
                            f"Full log: {get_log_path(vm.id)}"
                        )

                    # Fallback error message
                    raise VMLifecycleError(
                        f"VM runner did not become ready within {Timeouts.VM_START}s. "
                        f"Check logs at: {get_log_path(vm.id)}"
                    )

            # Verify VM is actually running (runner updated DB)
            vm_updated = self.state_manager.get_vm(vm_id)
            if vm_updated.status != "running":
                raise VMLifecycleError(
                    f"VM runner started but VM status is '{vm_updated.status}'"
                )

            # PHASE 2: Final validation - QEMU process exists
            if vm_updated.pid:
                from ..utils.paths import get_log_path

                try:
                    validate_pid_exists(
                        vm_updated.pid,
                        process_name=f"QEMU for VM '{vm_id}'",
                        raise_on_missing=True
                    )
                    LOG.info(f"QEMU process {vm_updated.pid} confirmed running for VM '{vm_id}'")
                except Exception as e:
                    # Critical: DB says running but QEMU is dead
                    LOG.error(
                        f"QEMU process {vm_updated.pid} not found despite 'running' status "
                        f"for VM '{vm_id}': {e}"
                    )

                    # Update DB to reflect reality
                    self.state_manager.update_vm_status(vm_id, status="failed")

                    # Check error file for diagnostic information
                    error_details = read_runner_error(vm.id)
                    error_context = ""
                    if error_details:
                        error_context = f"\n\nError details:\n{error_details}"

                    from ..exceptions import VMStartError
                    raise VMStartError(
                        f"VM marked as running but QEMU process {vm_updated.pid} does not exist. "
                        f"This indicates QEMU crashed immediately after startup. "
                        f"Check logs: {get_log_path(vm.id)}{error_context}"
                    )

            # Audit log successful VM start
            LOG.info(
                f"VM start: {vm_id} | runner_pid={runner_pid} | "
                f"user={os.getenv('USER', 'unknown')}"
            )

            return vm_updated

        finally:
            # Lock automatically released when file closed
            lock_file.close()

    @handle_vm_errors("VM stop")
    def stop(
        self, vm_id: str, force: bool = False, timeout: int = 30
    ) -> VMInstance:
        """
        Stop a VM by sending stop command to VM runner or killing runner process.

        This method implements a state machine with clear precedence:
        1. VM already stopped -> ensure DB consistency and return
        2. Runner process dead -> cleanup orphaned QEMU and return
        3. Force flag set -> immediately kill runner process
        4. Normal flow -> try graceful IPC stop, fallback to SIGTERM

        Args:
            vm_id: VM identifier (name or ID)
            force: If True, kill runner immediately (SIGKILL).
                   If False, graceful shutdown (SIGTERM)
            timeout: Timeout for graceful shutdown

        Returns:
            VM instance information

        Raises:
            VMLifecycleError: If VM stop fails
        """
        # Get VM and validate it exists
        vm = self._get_and_validate_vm(vm_id)

        # Early return: VM already stopped or in error state
        if vm.status != "running":
            return self._ensure_stopped_status(vm_id, vm)

        # Early return: Runner process dead (orphaned QEMU possible)
        if not self._is_runner_alive(vm):
            return self._cleanup_orphaned_vm(vm_id, vm, force)

        # Early return: Force flag set, skip graceful shutdown
        if force:
            return self._force_stop_runner(vm_id, vm, force)

        # Normal flow: Try graceful IPC stop first
        stopped_vm = self._try_graceful_stop(vm_id, vm, timeout)
        if stopped_vm:
            return stopped_vm

        # Fallback: Graceful stop failed, force stop the runner
        return self._force_stop_runner(vm_id, vm, force)

    def _get_and_validate_vm(self, vm_id: str) -> VMInstance:
        """Get VM from database and validate it exists."""
        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise VMLifecycleError(f"VM '{vm_id}' not found")
        return vm

    def _ensure_stopped_status(self, vm_id: str, vm: VMInstance) -> VMInstance:
        """Ensure VM has 'stopped' status when not running."""
        LOG.info(f"VM '{vm_id}' is not running (status: {vm.status})")

        if vm.status != "stopped":
            self.state_manager.update_vm_status(
                vm_id, "stopped", pid=None, runner_pid=None, socket_path=None
            )
            vm = self.state_manager.get_vm(vm_id)

        return vm

    def _is_runner_alive(self, vm: VMInstance) -> bool:
        """Check if runner process is alive."""
        from ..process_spawner import is_runner_alive
        return vm.runner_pid and is_runner_alive(vm.runner_pid)

    def _cleanup_orphaned_vm(
        self, vm_id: str, vm: VMInstance, force: bool
    ) -> VMInstance:
        """
        Clean up VM with dead runner but potentially live QEMU.

        Handles orphaned QEMU processes with identity verification.
        """
        LOG.warning(
            f"VM '{vm_id}' runner process not found, checking for orphaned QEMU"
        )

        if vm.pid:
            self._terminate_orphaned_qemu(vm.pid, vm_id, vm.name, force)

        self.state_manager.update_vm_status(
            vm_id, "stopped", pid=None, runner_pid=None, socket_path=None
        )

        self._audit_log_stop(vm_id, "orphaned_cleanup")
        return self.state_manager.get_vm(vm_id)

    def _verify_qemu_process(
        self, qemu_pid: int, vm_id: str, vm_name: str
    ) -> bool:
        """
        Verify PID is actually a QEMU process for this VM.

        Implements PID reuse protection by checking:
        1. Process name contains "qemu"
        2. Command line contains VM ID or name
        3. Process creation time (optional warning for recent PIDs)

        Args:
            qemu_pid: Process ID to verify
            vm_id: Expected VM ID
            vm_name: Expected VM name

        Returns:
            True if verified, False if process doesn't exist

        Raises:
            VMLifecycleError: If PID exists but is not QEMU or wrong VM
        """
        return ProcessVerifier.verify_or_raise(
            qemu_pid,
            expected_names=["qemu", "qemu-system-x86_64"],
            expected_tokens=[vm_id, vm_name],
            error_type=VMLifecycleError,
            process_description=f"QEMU for VM '{vm_id}'"
        )

    def _terminate_orphaned_qemu(
        self, qemu_pid: int, vm_id: str, vm_name: str, force: bool
    ) -> None:
        """
        Kill orphaned QEMU process with identity verification.

        Verifies process is actually QEMU before killing (PID reuse protection).
        """
        try:
            # Verify this is actually QEMU for this VM
            if not self._verify_qemu_process(qemu_pid, vm_id, vm_name):
                # Process already dead, return
                return

            # Now safe to kill - verified it's QEMU for this VM
            LOG.warning(f"Killing orphaned QEMU process (PID {qemu_pid})")
            from ..constants import ProcessManagement

            signal = (
                ProcessManagement.SIGNAL_FORCE
                if force
                else ProcessManagement.SIGNAL_GRACEFUL
            )
            os.kill(qemu_pid, signal)
            time.sleep(Intervals.PROCESS_WAIT_AFTER_KILL)

        except ProcessLookupError:
            LOG.debug(f"QEMU process {qemu_pid} already dead")
        except PermissionError:
            LOG.error(f"Permission denied when killing QEMU process {qemu_pid}")
            raise VMLifecycleError(f"Permission denied to kill process {qemu_pid}")
        except VMLifecycleError:
            # Re-raise PID verification failures
            raise
        except Exception as e:
            LOG.error(f"Failed to verify/kill QEMU process {qemu_pid}: {e}")
            raise

    def _try_graceful_stop(
        self, vm_id: str, vm: VMInstance, timeout: int
    ) -> Optional[VMInstance]:
        """
        Attempt graceful stop via IPC.

        Returns VMInstance if successful, None if IPC failed.
        """
        from ..ipc.runner_client import RunnerClient, RunnerClientError

        client = RunnerClient(vm.id, self.state_manager)

        try:
            client.send_command("stop", timeout=timeout)
            LOG.info(f"VM '{vm_id}' stopped gracefully via IPC")

            time.sleep(Intervals.CLEANUP_WAIT)
            vm_updated = self.state_manager.get_vm(vm_id)

            self._audit_log_stop(vm_id, "ipc_graceful")
            return vm_updated

        except RunnerClientError as e:
            LOG.warning(
                f"IPC stop failed for '{vm_id}': {e}, falling back to SIGTERM"
            )
            return None

    def _force_stop_runner(
        self, vm_id: str, vm: VMInstance, force: bool
    ) -> VMInstance:
        """
        Force stop runner process with signal.

        Uses SIGTERM (graceful) or SIGKILL (force).
        """
        from ..process_spawner import kill_runner

        LOG.info(
            f"Killing VM runner for '{vm_id}' (PID: {vm.runner_pid}, force={force})"
        )

        killed = kill_runner(vm.runner_pid, force=force)
        if not killed:
            raise VMLifecycleError(f"Failed to kill runner process {vm.runner_pid}")

        time.sleep(Intervals.CLEANUP_WAIT)

        vm_updated = self.state_manager.get_vm(vm_id)
        if vm_updated.status == "running":
            # Runner didn't clean up - do it manually
            self.state_manager.update_vm_status(
                vm_id, "stopped", runner_pid=None, socket_path=None
            )
            vm_updated = self.state_manager.get_vm(vm_id)

        method = "force_kill" if force else "sigterm"
        self._audit_log_stop(vm_id, method)

        return vm_updated

    def _audit_log_stop(self, vm_id: str, method: str) -> None:
        """Log VM stop event for audit trail."""
        LOG.info(
            f"VM stop: {vm_id} | method={method} | "
            f"user={os.getenv('USER', 'unknown')}"
        )

    @handle_vm_errors("VM removal")
    def remove(
        self,
        vm_id: Optional[str] = None,
        force: bool = False,
        all: bool = False,
        delete_storage: bool = False,
        keep_snapshots: bool = False,
    ) -> bool:
        """
        Remove a virtual machine completely.

        Args:
            vm_id: VM identifier (name or ID)
            force: Force removal even if VM is running (skip confirmation)
            all: Remove all virtual machines
            delete_storage: Delete storage files (default: keep storage)
            keep_snapshots: Keep snapshot files even if delete_storage=True

        Returns:
            True if removed successfully

        Raises:
            VMLifecycleError: If VM removal fails
        """
        # Validate arguments
        if all and vm_id:
            raise VMLifecycleError("Cannot specify both vm_id and --all flag")
        if not all and not vm_id:
            raise VMLifecycleError("Must specify either vm_id or --all flag")

        # Handle bulk removal
        if all:
            return self._remove_all_vms(force, delete_storage, keep_snapshots)

        # Handle single VM removal
        return self._remove_single_vm(vm_id, force, delete_storage, keep_snapshots)

    def _is_process_alive(self, pid: int, process_name: str) -> bool:
        """
        Check if process is alive (not zombie, not gone).

        Uses psutil for cross-platform zombie detection.

        Args:
            pid: Process ID to check
            process_name: Name for logging

        Returns:
            True if process is alive and running, False if zombie or gone
        """
        try:
            p = psutil.Process(pid)
            # Check status - will raise ZombieProcess if zombie
            status = p.status()
            if status == psutil.STATUS_ZOMBIE:
                LOG.debug(f"{process_name} process {pid} is zombie (dead)")
                return False
            return True
        except psutil.ZombieProcess:
            LOG.debug(f"{process_name} process {pid} is zombie (dead)")
            return False
        except psutil.NoSuchProcess:
            LOG.debug(f"{process_name} process {pid} does not exist")
            return False
        except psutil.AccessDenied:
            # Process exists but we can't access it - consider it alive
            LOG.warning(f"Access denied checking {process_name} process {pid}")
            return True

    def _kill_and_wait(self, pid: int, process_name: str) -> None:
        """
        Kill a process and wait for it to die or become a zombie.

        Zombies are considered "dead" since they've been terminated.
        Uses psutil for cross-platform zombie detection.
        """
        try:
            os.kill(pid, signal.SIGKILL)
            LOG.debug(f"Sent SIGKILL to {process_name} process {pid}")
        except OSError:
            LOG.debug(f"{process_name} process {pid} already dead, verifying...")

        # Wait for process to die or become zombie (max 10 seconds)
        for i in range(100):  # 100 * 0.1s = 10 seconds
            if not self._is_process_alive(pid, process_name):
                return
            time.sleep(0.1)

        LOG.warning(f"{process_name} process {pid} still alive after 10 seconds")

    def _force_stop_and_wait(self, vm) -> None:
        """
        Force stop VM and wait for all processes to terminate.

        Ensures both QEMU and runner processes are dead (or zombies) before returning.
        Uses process verification to prevent PID reuse attacks.
        """
        # CRITICAL: Capture PIDs and identifiers BEFORE calling stop() to avoid race condition
        # stop() may clear PIDs in database, making vm object stale
        qemu_pid = vm.pid
        runner_pid = vm.runner_pid
        vm_id = vm.id
        vm_name = vm.name

        LOG.debug(f"Force stopping VM {vm.id}: qemu_pid={qemu_pid}, runner_pid={runner_pid}")

        # First try stop via IPC (this will also kill processes)
        try:
            self.stop(vm.id, force=True)
            LOG.debug(f"Stop command succeeded for {vm.id}")
        except Exception as e:
            LOG.warning(f"Stop command failed for {vm.id}, will force kill: {e}")

        # Verify QEMU PID before killing (prevent PID reuse)
        if qemu_pid:
            try:
                ProcessVerifier.verify_or_raise(
                    qemu_pid,
                    expected_names=["qemu", "qemu-system-x86_64"],
                    expected_tokens=[vm_id, vm_name],
                    error_type=VMLifecycleError,
                    process_description=f"QEMU for VM '{vm_id}'"
                )
                self._kill_and_wait(qemu_pid, "QEMU")
            except VMLifecycleError as e:
                LOG.warning(f"QEMU PID verification failed: {e}")

        # Verify runner PID before killing
        if runner_pid:
            try:
                ProcessVerifier.verify_or_raise(
                    runner_pid,
                    expected_names=["python", "python3"],
                    expected_tokens=["maqet", "vm_runner", vm_id],
                    error_type=VMLifecycleError,
                    process_description=f"Runner for VM '{vm_id}'"
                )
                self._kill_and_wait(runner_pid, "runner")
            except VMLifecycleError as e:
                LOG.warning(f"Runner PID verification failed: {e}")

    def _remove_single_vm(
        self,
        vm_id: str,
        force: bool,
        delete_storage: bool = False,
        keep_snapshots: bool = False,
    ) -> bool:
        """
        Remove a single VM with confirmation and storage summary.

        Args:
            vm_id: VM identifier
            force: Force removal without confirmation
            delete_storage: Delete storage files
            keep_snapshots: Keep snapshot files even if delete_storage=True

        Returns:
            True if removed successfully
        """
        # Get VM from database
        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise VMLifecycleError(f"VM '{vm_id}' not found")

        # Stop VM if running
        if vm.status == "running":
            if not force:
                raise VMLifecycleError(
                    f"VM '{vm_id}' is running. Use --force to remove running VMs"
                )
            # Force stop and ensure processes are dead
            self._force_stop_and_wait(vm)

        # Get storage info for confirmation
        storage_entries = self.lifecycle_manager.storage_registry.get_vm_storage(
            vm.name
        )

        # Show confirmation prompt unless --force is used
        if not force:
            print(f"VM: {vm.name}")
            print(f"Storage files ({len(storage_entries)}):")

            total_size_bytes = 0
            for entry in storage_entries:
                size_mb = (
                    entry.size_bytes / (1024 * 1024) if entry.size_bytes else 0
                )
                total_size_bytes += entry.size_bytes or 0
                print(f"  - {entry.storage_path} ({size_mb:.1f} MB)")

            if total_size_bytes > 0:
                total_mb = total_size_bytes / (1024 * 1024)
                print(f"\nTotal storage: {total_mb:.1f} MB")

            print()
            if delete_storage:
                print("WARNING: Storage will be DELETED (cannot be recovered)")
                if keep_snapshots:
                    print("         Snapshot files will be kept")
            else:
                print("Storage will be KEPT (can reattach later)")

            try:
                confirm = input("\nProceed? [y/N]: ")
                if confirm.lower() != "y":
                    print("Cancelled")
                    return False
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled")
                return False

        # Use VMLifecycleManager for transactional deletion
        try:
            self.lifecycle_manager.delete_vm(
                vm.name, delete_storage=delete_storage, keep_snapshots=keep_snapshots
            )
        except ValueError as e:
            raise VMLifecycleError(str(e))

        # Print success message
        if delete_storage:
            if keep_snapshots:
                print(
                    f"VM '{vm.name}' and storage deleted (snapshots kept)"
                )
            else:
                print(f"VM '{vm.name}' and storage deleted")
        else:
            print(f"VM '{vm.name}' deleted (storage kept)")

        # Audit log VM removal
        LOG.info(
            f"VM remove: {vm_id} | force={force} | delete_storage={delete_storage} | "
            f"keep_snapshots={keep_snapshots} | user={os.getenv('USER', 'unknown')}"
        )

        return True

    def _remove_all_vms(
        self,
        force: bool,
        delete_storage: bool = False,
        keep_snapshots: bool = False,
    ) -> bool:
        """Remove all VMs with confirmation."""
        # Get all VMs
        all_vms = self.state_manager.list_vms()

        if not all_vms:
            print("No virtual machines found.")
            return True

        # Display VMs that will be removed
        print(f"Found {len(all_vms)} virtual machine(s) to remove:")
        print()

        # Create table header
        header = f"{'NAME':<20} {'STATUS':<10} {'PID':<8}"
        separator = "-" * 40
        print(header)
        print(separator)

        running_count = 0
        for vm in all_vms:
            pid_str = str(vm.pid) if vm.pid else "-"
            print(f"{vm.name:<20} {vm.status:<10} {pid_str:<8}")
            if vm.status == "running":
                running_count += 1

        print()

        # Show warning for running VMs
        if running_count > 0 and not force:
            print(
                f"WARNING: {running_count} VM(s) are currently running "
                f"and will be forcefully stopped."
            )
            print("Use --force to skip this warning in the future.")
            print()

        # Confirmation prompt
        try:
            response = (
                input(
                    f"Are you sure you want to remove ALL {len(all_vms)} "
                    f"virtual machines? [y/N]: "
                )
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return False

        if response not in ["y", "yes"]:
            print("Operation cancelled.")
            return False

        # Remove all VMs
        removed_count = 0
        failed_count = 0

        print()
        print("Removing virtual machines...")

        for vm in all_vms:
            try:
                # Stop VM if running
                if vm.status == "running":
                    try:
                        self.stop(vm.id, force=True)
                        print(f"  Stopped VM: {vm.name}")
                    except Exception as e:
                        print(f"  Warning: Failed to stop VM '{vm.name}': {e}")

                # Use lifecycle manager for transactional deletion
                try:
                    self.lifecycle_manager.delete_vm(
                        vm.name,
                        delete_storage=delete_storage,
                        keep_snapshots=keep_snapshots,
                    )
                    print(f"  Removed VM: {vm.name}")
                    removed_count += 1
                except (ValueError, Exception) as e:
                    print(f"  Failed to remove VM '{vm.name}': {e}")
                    failed_count += 1

            except Exception as e:
                print(f"  Error removing VM '{vm.name}': {e}")
                failed_count += 1

        print()
        print(
            f"Removal complete: {removed_count} removed, "
            f"{failed_count} failed"
        )

        # Audit log bulk removal
        LOG.info(
            f"VM remove: ALL | removed={removed_count} | failed={failed_count} | "
            f"force={force} | delete_storage={delete_storage} | "
            f"user={os.getenv('USER', 'unknown')}"
        )

        if failed_count > 0:
            raise VMLifecycleError(f"Failed to remove {failed_count} VM(s)")

        return True

    def list_vms(self, status: Optional[str] = None, validate_status: bool = True) -> List[VMInstance]:
        """
        List virtual machines with optional status validation.

        Args:
            status: Filter by status ('running', 'stopped', 'created',
                'failed')
            validate_status: Check process reality and update status (default: True)

        Returns:
            List of VM instances with accurate status
        """
        vms = self.state_manager.list_vms(status_filter=status)

        if not validate_status:
            return vms

        # Validate each VM's status against process reality
        for vm in vms:
            actual_status = self._validate_vm_status(vm)

            if actual_status != vm.status:
                # Update database if status changed
                self.state_manager.update_vm_status(
                    vm.id, actual_status,
                    pid=None if actual_status in ("corrupted", "orphaned") else vm.pid,
                    runner_pid=None if actual_status in ("corrupted", "orphaned") else vm.runner_pid,
                    socket_path=None if actual_status in ("corrupted", "orphaned") else vm.socket_path
                )
                vm.status = actual_status
                if actual_status in ("corrupted", "orphaned"):
                    vm.pid = None
                    vm.runner_pid = None
                    vm.socket_path = None

        return vms

    def _validate_vm_status(self, vm: VMInstance) -> str:
        """
        Validate VM status against process reality.

        Determines actual VM status by checking:
        1. Runner process alive (if runner_pid is set)
        2. QEMU process alive (if pid is set)
        3. Socket file exists (if socket_path is set)

        Args:
            vm: VM instance to validate

        Returns:
            Corrected status string ("orphaned", "corrupted", or current status)
        """
        if vm.status != "running":
            return vm.status  # Only validate running VMs

        # Check runner process (if we have a runner_pid)
        if vm.runner_pid is not None:
            if not self.state_manager._is_process_alive(vm.runner_pid):
                # Runner dead - check if QEMU orphaned
                if vm.pid and self.state_manager._is_process_alive(vm.pid):
                    return "orphaned"
                else:
                    return "corrupted"

        # Check QEMU process (if we have a pid)
        if vm.pid is not None:
            if not self.state_manager._is_process_alive(vm.pid):
                return "corrupted"

        # Check socket file (if we have a socket_path)
        if vm.socket_path is not None:
            if not Path(vm.socket_path).exists():
                return "corrupted"

        return "running"  # All checks passed

    def cleanup_dead_processes(self) -> List[str]:
        """
        Check for VMs with running status but dead runner processes.
        Update DB to reflect reality.

        This runs on VMManager initialization to clean up stale state from
        crashed runners or improperly terminated VMs.

        Returns:
            List of VM IDs that were cleaned up
        """
        from ..process_spawner import is_runner_alive

        cleaned = []

        # Get all VMs marked as running
        all_vms = self.state_manager.list_vms()
        running_vms = [vm for vm in all_vms if vm.status == "running"]

        for vm in running_vms:
            if not vm.runner_pid or not is_runner_alive(vm.runner_pid):
                LOG.warning(
                    f"VM '{vm.name}' marked as running but runner process "
                    f"(PID: {vm.runner_pid}) is dead"
                )

                # Check for orphaned QEMU process with verification
                if vm.pid:
                    self._terminate_orphaned_qemu(
                        vm.pid, vm.id, vm.name, force=True
                    )

                # Update DB
                self.state_manager.update_vm_status(
                    vm.name, "stopped", pid=None, runner_pid=None, socket_path=None
                )
                cleaned.append(vm.id)

        return cleaned

    def status(self, vm_id: str, detailed: bool = False) -> Dict[str, Any]:
        """
        Get basic status information for a VM.

        Args:
            vm_id: VM identifier (name or ID)
            detailed: (DEPRECATED) Use 'inspect' method instead for detailed information

        Returns:
            Dictionary with basic VM status information

        Raises:
            VMLifecycleError: If VM not found
        """
        # Note: detailed parameter kept for backward compatibility
        # but deprecated in favor of inspect() method
        if detailed:
            LOG.warning(
                "The detailed parameter for 'status' method is deprecated. "
                "Use 'inspect(%s)' for detailed VM inspection instead.",
                vm_id
            )

        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise VMLifecycleError(f"VM '{vm_id}' not found")

        # Check if process is actually running and update status
        is_actually_running = self._check_process_alive(vm_id, vm)

        # Check if VM is empty/unconfigured
        is_empty_vm = not vm.config_data or not vm.config_data.get("binary")

        # Build simplified status response (no configuration or detailed info)
        status_info = {
            "name": vm.name,
            "status": vm.status,
            "is_running": is_actually_running,
            "is_empty": is_empty_vm,
            "pid": vm.pid,
            "socket_path": vm.socket_path,
        }

        # Add QMP socket info if socket exists
        if vm.socket_path:
            status_info["qmp_socket"] = {
                "path": vm.socket_path,
                "exists": Path(vm.socket_path).exists(),
            }

        return status_info

    def info(self, vm_id: str) -> Dict[str, Any]:
        """
        Get VM configuration details.

        This method provides configuration information about a VM,
        including binary, memory, CPU, display settings, and storage devices.
        It's a focused view of the VM's configuration without runtime details.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            Dictionary with VM configuration details

        Raises:
            VMLifecycleError: If VM not found
        """
        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise VMLifecycleError(f"VM '{vm_id}' not found")

        # Build info response with configuration details
        info_data = {
            "vm_id": vm.id,
            "name": vm.name,
            "config_path": vm.config_path,
            "config_data": vm.config_data,
            "configuration": self._get_config_summary(vm.config_data),
        }

        return info_data

    def inspect(self, vm_id: str) -> Dict[str, Any]:
        """
        Get detailed inspection information for a VM.

        This method provides comprehensive information including VM status,
        configuration, process details (if running), QMP socket status,
        and snapshot information. It's the most detailed view of a VM.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            Dictionary with comprehensive VM inspection data

        Raises:
            VMLifecycleError: If VM not found
        """
        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise VMLifecycleError(f"VM '{vm_id}' not found")

        # Check if process is actually running
        is_actually_running = self._check_process_alive(vm_id, vm)

        # Build comprehensive inspection response
        inspect_data = {
            "vm_id": vm.id,
            "name": vm.name,
            "status": vm.status,
            "is_running": is_actually_running,
            "pid": vm.pid,
            "socket_path": vm.socket_path,
            "config_path": vm.config_path,
            "created_at": vm.created_at.isoformat() if vm.created_at else None,
            "updated_at": vm.updated_at.isoformat() if vm.updated_at else None,
            "configuration": self._get_config_summary(vm.config_data),
        }

        # Add process details if running
        if is_actually_running and vm.pid:
            process_info = self._get_process_info(vm.pid)
            if process_info:
                inspect_data["process"] = process_info

        # Add QMP socket status
        if vm.socket_path:
            inspect_data["qmp_socket"] = {
                "path": vm.socket_path,
                "exists": Path(vm.socket_path).exists(),
            }

        return inspect_data

    def apply(
        self,
        vm_id: str,
        vm_config: Optional[Union[str, List[str]]] = None,
        **kwargs,
    ) -> VMInstance:
        """
        Apply configuration to existing VM, or create it if it doesn't exist.

        Args:
            vm_id: VM identifier (name or ID)
            vm_config: Path to configuration file, or list of config
                files for deep-merge
            **kwargs: Configuration parameters to update

        Returns:
            VM instance (created or updated)

        Raises:
            VMLifecycleError: If configuration is invalid or operation fails
        """
        # Get VM from database
        vm = self.state_manager.get_vm(vm_id)

        if not vm:
            # VM doesn't exist, create it using add functionality
            LOG.info(f"VM '{vm_id}' not found, creating new VM")
            new_vm_id = self.add(vm_config=vm_config, name=vm_id, **kwargs)
            return self.state_manager.get_vm(new_vm_id)

        # VM exists, check if running (config cannot be applied to running VMs)
        if vm.status == "running":
            raise VMLifecycleError(
                f"Cannot apply configuration to running VM '{vm_id}'. "
                f"Stop the VM first with 'maqet stop {vm_id}'"
            )

        # VM exists and stopped, update its configuration
        # Load and merge new configuration files
        if vm_config:
            new_config = ConfigMerger.load_and_merge_files(vm_config)
        else:
            new_config = {}

        # Merge kwargs with new config (kwargs take precedence)
        if kwargs:
            new_config = ConfigMerger.deep_merge(new_config, kwargs)

        # Remove name from new_config as it's not QEMU configuration
        # (VM already exists with its name)
        if "name" in new_config:
            new_config = {k: v for k, v in new_config.items() if k != "name"}

        # Merge with existing configuration (existing config provides base)
        final_config = ConfigMerger.deep_merge(dict(vm.config_data), new_config)

        # Validate the merged configuration
        final_config = self.config_parser.validate_config(final_config)

        # Update VM configuration in database
        self.state_manager.update_vm_config(vm.id, final_config)

        return self.state_manager.get_vm(vm_id)

    def _check_process_alive(self, vm_id: str, vm: VMInstance) -> bool:
        """
        Check if VM process is actually alive and update status if needed.

        Args:
            vm_id: VM identifier
            vm: VM instance

        Returns:
            True if process is alive, False otherwise
        """
        if vm.status != "running" or not vm.pid:
            return False

        # Check if process exists
        if validate_pid_exists(vm.pid, process_name=f"QEMU for VM {vm_id}", log_permission_warning=False):
            return True
        else:
            # Process doesn't exist, update status
            self.state_manager.update_vm_status(
                vm.id, "stopped", pid=None, socket_path=None
            )
            return False

    def _get_config_summary(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract configuration summary from config data.

        Args:
            config_data: VM configuration dictionary

        Returns:
            Dictionary with configuration summary
        """
        summary = {
            "binary": config_data.get("binary"),
            "memory": config_data.get("memory"),
            "cpu": config_data.get("cpu"),
            "display": config_data.get("display"),
        }

        # Count and list storage devices
        storage_devices = config_data.get("storage", [])
        if isinstance(storage_devices, list):
            summary["storage_count"] = len(storage_devices)
            summary["storage_devices"] = [
                {
                    "name": dev.get("name", "unnamed"),
                    "type": dev.get("type", "unknown"),
                    "size": dev.get("size"),
                }
                for dev in storage_devices
            ]
        else:
            summary["storage_count"] = 0
            summary["storage_devices"] = []

        return summary

    def _get_process_info(self, pid: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed process information using psutil if available.

        Args:
            pid: Process ID

        Returns:
            Dictionary with process information or None if psutil not available
        """
        try:
            import psutil

            try:
                proc = psutil.Process(pid)
                return {
                    "cpu_percent": proc.cpu_percent(),
                    "memory_info": proc.memory_info()._asdict(),
                    "create_time": proc.create_time(),
                    "cmdline": proc.cmdline(),
                    "status": proc.status(),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        except ImportError:
            # psutil not available
            return {"note": "Install psutil for detailed process information"}

    # Snapshot operations (merged from SnapshotCoordinator)

    def _get_snapshot_manager(self, vm_id: str) -> SnapshotManager:
        """
        Internal helper to create SnapshotManager for a VM.

        Args:
            vm_id: VM identifier

        Returns:
            Configured SnapshotManager instance

        Raises:
            SnapshotError: If VM not found
        """
        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise SnapshotError(f"VM '{vm_id}' not found")

        storage_manager = StorageManager(vm.id)
        storage_configs = vm.config_data.get("storage", [])
        if storage_configs:
            storage_manager.add_storage_from_config(storage_configs)

        # Pass QMP manager for live snapshot support
        return SnapshotManager(vm.id, storage_manager, self.qmp_manager, self.state_manager)

    @handle_snapshot_errors("Snapshot creation")
    def create_snapshot(
        self, vm_id: str, drive: str, name: str, overwrite: bool = False, live: bool = False
    ) -> Dict[str, Any]:
        """
        Create VM snapshot.

        Args:
            vm_id: VM identifier
            drive: Drive identifier (e.g., 'drive0')
            name: Snapshot name
            overwrite: Overwrite existing snapshot
            live: Use live snapshot (QMP savevm) vs offline (qemu-img)

        Returns:
            Snapshot creation result

        Raises:
            SnapshotError: If creation fails
        """
        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise SnapshotError(f"VM '{vm_id}' not found")

        storage_manager = StorageManager(vm_id)
        storage_configs = vm.config_data.get("storage", [])
        if storage_configs:
            storage_manager.add_storage_from_config(storage_configs)

        # Initialize SnapshotManager with QMPManager for live snapshot support
        snapshot_mgr = SnapshotManager(
            vm_id=vm.id,
            storage_manager=storage_manager,
            qmp_manager=self.qmp_manager,
            state_manager=self.state_manager
        )

        result = snapshot_mgr.create(drive, name, overwrite=overwrite, live=live)
        LOG.info(
            f"Created snapshot '{name}' on drive '{drive}' for VM '{vm_id}'"
        )
        return result

    @handle_snapshot_errors("Snapshot restoration")
    def load_snapshot(self, vm_id: str, drive: str, name: str) -> Dict[str, Any]:
        """
        Load VM snapshot.

        Args:
            vm_id: VM identifier
            drive: Drive identifier
            name: Snapshot name

        Returns:
            Snapshot load result

        Raises:
            SnapshotError: If load fails
        """
        snapshot_mgr = self._get_snapshot_manager(vm_id)
        result = snapshot_mgr.load(drive, name)
        LOG.info(
            f"Loaded snapshot '{name}' on drive '{drive}' for VM '{vm_id}'"
        )
        return result

    @handle_snapshot_errors("Snapshot listing")
    def list_snapshots(
        self, vm_id: str, drive: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List available snapshots for VM.

        Args:
            vm_id: VM identifier
            drive: Optional drive filter

        Returns:
            Snapshot list

        Raises:
            SnapshotError: If listing fails
        """
        snapshot_mgr = self._get_snapshot_manager(vm_id)
        snapshots = snapshot_mgr.list(drive)
        LOG.debug(
            f"Listed {len(snapshots)} snapshot(s) on drive '{drive}' "
            f"for VM '{vm_id}'"
        )
        return snapshots

    @handle_snapshot_errors("Get snapshot-capable drives")
    def get_snapshot_capable_drives(self, vm_id: str) -> List[str]:
        """
        Get list of drives that support snapshots.

        Args:
            vm_id: VM identifier

        Returns:
            List of drive names that support snapshots (QCOW2 only)

        Raises:
            SnapshotError: If VM not found
        """
        snapshot_mgr = self._get_snapshot_manager(vm_id)
        drives = snapshot_mgr.list_snapshot_capable_drives()
        LOG.debug(
            f"Found {len(drives)} snapshot-capable drive(s) for VM '{vm_id}'"
        )
        return drives

    @handle_snapshot_errors("Get drive information")
    def get_drive_info(self, vm_id: str, drive: str) -> Dict[str, Any]:
        """
        Get snapshot information for specific drive.

        Args:
            vm_id: VM identifier
            drive: Drive identifier

        Returns:
            Drive information including snapshots

        Raises:
            SnapshotError: If VM or drive not found
        """
        snapshot_mgr = self._get_snapshot_manager(vm_id)
        return snapshot_mgr.get_drive_info(drive)

    # Cleanup operations (merged from CleanupCoordinator)

    def cleanup_all(self, timeout: int = None) -> Dict[str, Any]:
        """
        Stop all running VMs in parallel.

        Gracefully stops all VMs managed by this VMManager instance,
        executing stops in parallel for efficiency.

        Args:
            timeout: Timeout per VM stop operation (seconds)

        Returns:
            Dictionary with cleanup results

        Example:
            vm_manager.cleanup_all()  # Uses default timeout
            vm_manager.cleanup_all(timeout=10)  # Custom timeout
        """
        if timeout is None:
            timeout = Timeouts.CLEANUP_VM_STOP

        # Find running VMs from our cache
        running_vms = [
            vm_id for vm_id, machine in self._machines.items()
            if machine._qemu_machine and machine._qemu_machine.is_running()
        ]

        if not running_vms:
            LOG.debug("No running VMs to cleanup")
            # Clear cache even if no running VMs
            self.clear_machine_cache()
            return {"stopped": 0, "errors": []}

        LOG.info(f"Stopping {len(running_vms)} running VM(s) in parallel...")

        # Stop in parallel
        results = self._parallel_vm_shutdown(running_vms, timeout)

        # Clear cache after stopping all VMs
        self.clear_machine_cache()

        stopped_count = len([r for r in results if r["success"]])
        errors = [r for r in results if not r["success"]]

        LOG.debug(f"MAQET cleanup completed: {stopped_count} stopped, {len(errors)} errors")

        return {
            "stopped": stopped_count,
            "errors": errors,
        }

    def _parallel_vm_shutdown(
        self, vm_ids: List[str], timeout: int
    ) -> List[Dict[str, Any]]:
        """
        Execute parallel VM shutdown.

        Internal helper for cleanup_all(). Uses ThreadPoolExecutor to stop
        VMs concurrently, with per-VM timeout protection.

        Args:
            vm_ids: List of VM identifiers to stop
            timeout: Timeout in seconds for each VM stop operation

        Returns:
            List of dictionaries with stop results
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def stop_vm(vm_id: str) -> Dict[str, Any]:
            """
            Stop a single VM with force flag.

            Args:
                vm_id: VM identifier

            Returns:
                Dictionary with stop result
            """
            try:
                LOG.debug(f"Stopping VM {vm_id}")
                self.stop(vm_id, force=True)
                return {"vm_id": vm_id, "success": True}
            except Exception as e:
                LOG.warning(f"Failed to stop VM {vm_id} during cleanup: {e}")
                return {"vm_id": vm_id, "success": False, "error": str(e)}

        results = []
        # Use configurable thread pool sizing for I/O-bound operations
        max_workers = min(MAX_PARALLEL_WORKERS, len(vm_ids))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(stop_vm, vm_id): vm_id for vm_id in vm_ids}

            for future in as_completed(futures):
                vm_id = futures[future]
                try:
                    # Per-VM timeout
                    result = future.result(timeout=timeout)
                    results.append(result)
                except Exception as e:
                    LOG.warning(f"Timeout or error stopping VM {vm_id}: {e}")
                    results.append({
                        "vm_id": vm_id,
                        "success": False,
                        "error": f"Timeout or exception: {str(e)}"
                    })

        return results
