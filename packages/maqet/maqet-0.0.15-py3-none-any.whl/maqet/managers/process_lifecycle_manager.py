"""
Process Lifecycle Manager

Handles QEMU process lifecycle operations including:
- Graceful shutdown via QMP
- Force kill with SIGTERM/SIGKILL escalation
- Process state tracking
- Cleanup coordination after VM stop
- Instance-scoped PID registry management

Extracted from Machine class to follow Single Responsibility Principle.

CRITICAL ARCHITECTURE: Each ProcessLifecycleManager instance maintains its own
PID registry to prevent cross-contamination between Maqet instances in concurrent
test environments. This ensures one instance's cleanup never affects another's.
"""

import atexit
import os
import signal
import threading
import time
from typing import TYPE_CHECKING, Dict, Optional, Set

from ..constants import Intervals, Timeouts
from ..logger import LOG
from ..utils.process_validation import validate_pid_exists

if TYPE_CHECKING:
    from qemu.machine import QEMUMachine
    from ..state import StateManager


class ProcessLifecycleManager:
    """
    Manages QEMU process lifecycle operations.

    Responsibilities:
    - Graceful shutdown via QMP
    - Force kill with signal escalation
    - Process state checking
    - Cleanup coordination (PID registry, files, database state)

    CRITICAL: Each instance maintains its own process registry to prevent
    cross-contamination between Maqet instances in concurrent tests.
    """

    def __init__(
        self,
        vm_id: str,
        state_manager: "StateManager",
    ):
        """
        Initialize ProcessLifecycleManager.

        Args:
            vm_id: VM identifier
            state_manager: State manager instance for file paths and status updates
        """
        self.vm_id = vm_id
        self.state_manager = state_manager

        # Instance-level registry of active QEMU PIDs for cleanup on exit
        # Maps PID to VM ID for better tracking and debugging
        self._qemu_process_registry: Dict[int, str] = {}
        self._registry_lock = threading.Lock()

        # Register instance cleanup on exit
        atexit.register(self.cleanup_all_qemu_processes)

    def graceful_shutdown(
        self,
        qemu_machine: "QEMUMachine",
        timeout: int = Timeouts.VM_GRACEFUL_SHUTDOWN,
    ) -> bool:
        """
        Attempt graceful shutdown of VM via QMP.

        Args:
            qemu_machine: QEMU machine instance
            timeout: Maximum seconds to wait for shutdown

        Returns:
            True if shutdown succeeded, False otherwise
        """
        if not qemu_machine:
            return False

        try:
            LOG.debug(f"Attempting graceful shutdown of VM {self.vm_id}")
            qemu_machine.shutdown()

            # Wait for process to exit
            start_time = time.time()
            while (
                qemu_machine.is_running()
                and (time.time() - start_time) < timeout
            ):
                time.sleep(Intervals.SHUTDOWN_POLL)

            # Check if shutdown succeeded
            if not qemu_machine.is_running():
                LOG.info(f"VM {self.vm_id} shutdown gracefully")
                return True
            else:
                LOG.warning(
                    f"VM {self.vm_id} didn't shutdown gracefully in {timeout}s"
                )
                return False

        except Exception as e:
            LOG.warning(f"Graceful shutdown failed for VM {self.vm_id}: {e}")
            return False

    def force_kill(self, pid: int) -> bool:
        """
        Force kill the VM process using SIGTERM then SIGKILL.

        Sends SIGTERM first, waits briefly, then sends SIGKILL if needed.
        Verifies the process is actually dead after kill attempts.

        This method NEVER raises exceptions - it only logs errors and returns
        a status boolean. This ensures cleanup paths (like __del__) are never
        disrupted.

        Args:
            pid: Process ID to kill

        Returns:
            True if kill succeeded (or process already dead), False if kill failed
        """
        if not pid:
            return True

        LOG.info(f"Force killing VM {self.vm_id} (PID {pid})")
        try:
            # Send SIGTERM first
            os.kill(pid, signal.SIGTERM)
            time.sleep(Intervals.SIGTERM_WAIT)

            # Check if still alive, send SIGKILL if needed
            if self.is_process_alive(pid):
                LOG.debug(f"Process {pid} still alive, sending SIGKILL")
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.2)  # Brief wait for SIGKILL to take effect
        except ProcessLookupError:
            # Process already dead - success
            return True

        # Final verification that process is actually dead
        if self.is_process_alive(pid):
            LOG.critical(f"Failed to kill QEMU process {pid} for VM {self.vm_id} after SIGTERM and SIGKILL")
            return False

        return True

    def is_process_alive(self, pid: int) -> bool:
        """
        Check if process is still running.

        Args:
            pid: Process ID to check

        Returns:
            True if process is alive, False otherwise
        """
        return validate_pid_exists(pid, process_name="process", log_permission_warning=False)

    def cleanup_after_stop(self, pid: Optional[int]) -> None:
        """
        Cleanup after VM stops.

        GUARANTEED to run in finally block. NEVER raises exceptions - only logs errors.

        - Unregisters PID from active registry
        - Updates database status
        - Removes temporary files

        Args:
            pid: Process ID that was stopped (None if already cleaned up)
        """
        try:
            # Unregister PID from cleanup registry
            if pid:
                with self._registry_lock:
                    self._qemu_process_registry.pop(pid, None)
        except Exception as e:
            LOG.warning(f"Failed to unregister PID {pid}: {e}")

        try:
            # Update database status to stopped
            self.state_manager.update_vm_status(
                self.vm_id, "stopped", pid=None, socket_path=None, qmp_socket_path=None
            )
        except Exception as e:
            LOG.warning(f"Failed to update VM status for {self.vm_id}: {e}")

        try:
            # Clean up files
            self.cleanup_files()
        except Exception as e:
            LOG.warning(f"Failed to cleanup files for {self.vm_id}: {e}")

    def cleanup_files(self) -> None:
        """Clean up temporary files (PID file, socket handled by QEMUMachine)."""
        # Remove PID file
        pid_path = self.state_manager.get_pid_path(self.vm_id)
        if pid_path.exists():
            pid_path.unlink()

        # Socket cleanup is handled by QEMUMachine

    def register_pid(self, pid: int) -> None:
        """
        Register PID in instance cleanup registry (thread-safe).

        Args:
            pid: Process ID to register
        """
        with self._registry_lock:
            self._qemu_process_registry[pid] = self.vm_id

    def unregister_pid(self, pid: int) -> None:
        """
        Unregister PID from instance cleanup registry (thread-safe).

        Args:
            pid: Process ID to unregister
        """
        with self._registry_lock:
            self._qemu_process_registry.pop(pid, None)

    def emergency_cleanup(self, pid: int) -> None:
        """
        Emergency cleanup if normal cleanup didn't happen.

        This is called by atexit handler to ensure process is killed even if
        normal stop() wasn't called.

        Args:
            pid: Process ID to cleanup
        """
        if not pid:
            return

        if self.is_process_alive(pid):
            try:
                LOG.warning(f"Emergency cleanup: killing orphan QEMU process {pid} for VM {self.vm_id}")
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            finally:
                with self._registry_lock:
                    self._qemu_process_registry.pop(pid, None)

    def get_active_pids(self) -> Set[int]:
        """
        Get set of all active QEMU PIDs for this instance.

        Returns:
            Set of active process IDs
        """
        with self._registry_lock:
            return set(self._qemu_process_registry.keys())

    def get_process_registry(self) -> Dict[int, str]:
        """
        Get copy of process registry for this instance (thread-safe).

        Returns:
            Dict mapping PID to VM ID
        """
        with self._registry_lock:
            return self._qemu_process_registry.copy()

    def cleanup_orphan_processes(self) -> None:
        """
        Kill any QEMU processes that are still running for this instance.

        This is typically called during Python exit to prevent orphaned processes.
        Thread-safe implementation using the instance registry lock.
        """
        with self._registry_lock:
            pids = list(self._qemu_process_registry.keys())

        if pids:
            LOG.debug(
                f"Cleaning up {len(pids)} orphan QEMU processes for instance"
            )
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                    LOG.debug(f"Killed orphan QEMU process {pid}")
                except (ProcessLookupError, OSError):
                    pass  # Process already dead

            with self._registry_lock:
                self._qemu_process_registry.clear()

    def cleanup_all_qemu_processes(self) -> None:
        """
        Cleanup all tracked QEMU processes for this instance.

        Instance method registered with atexit to ensure all QEMU processes
        managed by this instance are cleaned up on Python exit.
        Thread-safe implementation using the instance registry lock.

        This method can be called from tests to ensure all QEMU processes
        for a specific Maqet instance are cleaned up between test runs.
        """
        with self._registry_lock:
            pids = list(self._qemu_process_registry.keys())

        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
                LOG.debug(f"Killed QEMU process {pid}")
            except (ProcessLookupError, OSError):
                pass  # Process already dead

        with self._registry_lock:
            self._qemu_process_registry.clear()
