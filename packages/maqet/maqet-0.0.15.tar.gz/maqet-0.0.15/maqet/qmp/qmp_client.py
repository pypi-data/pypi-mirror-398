"""
QMP Client - Low-level QMP communication for MAQET.

Handles QMP (QEMU Machine Protocol) command execution with timeout handling
and security validation. Extracted from Machine class for better separation
of concerns and testability.

This class focuses solely on QMP communication, allowing the Machine class
to focus on VM lifecycle management.
"""

import threading
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..constants import Timeouts
from ..logger import LOG

if TYPE_CHECKING:
    try:
        from qemu.machine import QEMUMachine
    except ImportError:
        from ..vendor.qemu.machine import QEMUMachine


class QMPClientError(Exception):
    """QMP client-related errors."""


class QMPClient:
    """
    Low-level QMP client for executing commands on QEMU VMs.

    Responsibilities:
    - Execute QMP commands with timeout handling
    - Validate command safety (dangerous vs safe commands)
    - Thread-safe command execution
    - Error handling and logging

    Does NOT handle:
    - VM lifecycle (start/stop) - that's Machine's job
    - Configuration validation - that's ConfigValidator's job
    - State management - that's StateManager's job

    Extracted from Machine.qmp_command() as per CRITICAL-2 in code review.
    """

    # Dangerous QMP commands that could harm VM or data
    DANGEROUS_QMP_COMMANDS = {
        "quit",  # Terminates VM without graceful shutdown
        "system_powerdown",  # Powers down VM (safe but user should use stop())
        "system_reset",  # Force reboot without saving
        "inject-nmi",  # Crashes guest OS for debugging
        "migrate",  # Could corrupt VM if done incorrectly
        "migrate_set_speed",
        "migrate_cancel",
        "pmemsave",  # Dumps memory (security risk)
        "memsave",  # Dumps memory (security risk)
        "drive_del",  # Removes storage device
        "blockdev-del",  # Removes block device
        "device_del",  # Removes device (should use device_del method)
    }

    # Safe QMP commands that are commonly used
    SAFE_QMP_COMMANDS = {
        "query-status",  # Get VM status
        "query-version",  # Get QEMU version
        "query-commands",  # List available commands
        "query-kvm",  # Check if KVM is enabled
        "query-cpus",  # Get CPU info
        "query-block",  # Get block device info
        "query-chardev",  # Get character devices
        "screendump",  # Take screenshot
        "send-key",  # Send keyboard input
        "human-monitor-command",  # Execute monitor command
        "cont",  # Resume VM from pause
        "stop",  # Pause VM
        "input-send-event",  # Send input events
    }

    def __init__(self, vm_id: str, timeout: Optional[int] = None):
        """
        Initialize QMP client.

        Args:
            vm_id: VM identifier for logging and error messages
            timeout: Command timeout in seconds (default: from Timeouts.QMP_COMMAND)
        """
        self.vm_id = vm_id
        self.timeout = timeout or Timeouts.QMP_COMMAND
        LOG.debug(f"QMPClient initialized for VM {vm_id} (timeout={self.timeout}s)")

    def execute(
        self,
        qemu_machine: "QEMUMachine",
        command: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute QMP command with security validation and timeout.

        Args:
            qemu_machine: QEMUMachine instance to execute command on
            command: QMP command to execute (e.g., "query-status")
            **kwargs: Command parameters

        Returns:
            QMP command result dictionary

        Raises:
            QMPClientError: If VM not running, command times out, or execution fails
        """
        # Verify VM is running
        if not qemu_machine or not qemu_machine.is_running():
            raise QMPClientError(f"VM {self.vm_id} is not running")

        # Security: Validate command safety
        self._validate_command_safety(command)

        # Execute command with timeout
        try:
            result = self._execute_with_timeout(qemu_machine, command, **kwargs)
            LOG.debug(f"QMP command '{command}' completed successfully on {self.vm_id}")
            return result

        except QMPClientError:
            # Re-raise our own errors as-is
            raise
        except Exception as e:
            LOG.error(f"QMP command '{command}' failed on VM {self.vm_id}: {e}")
            raise QMPClientError(f"QMP command failed: {e}")

    def _validate_command_safety(self, command: str) -> None:
        """
        Validate command safety and log warnings for dangerous commands.

        Args:
            command: QMP command name to validate

        Note: This method logs warnings but does NOT block dangerous commands.
              Advanced users can still execute them. A future enhancement could
              add a confirmation prompt or --force flag.
        """
        if command in self.DANGEROUS_QMP_COMMANDS:
            LOG.warning(
                f"QMP command '{command}' is potentially dangerous and may harm the VM. "
                f"Consider using the appropriate maqet method instead (e.g., stop() for powerdown)."
            )
        elif command not in self.SAFE_QMP_COMMANDS:
            # Unknown command - warn but allow
            LOG.info(
                f"QMP command '{command}' is not in the known safe commands list. "
                f"Proceeding with caution."
            )

    def _execute_with_timeout(
        self,
        qemu_machine: "QEMUMachine",
        command: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute QMP command in separate thread with timeout.

        Uses threading to enforce timeout on QMP commands that might hang.
        Thread-safe result container ensures proper exception propagation.

        Args:
            qemu_machine: QEMUMachine instance
            command: QMP command name
            **kwargs: Command parameters

        Returns:
            QMP command result

        Raises:
            QMPClientError: If command times out
            Exception: Any exception raised during command execution
        """
        # Build QMP command for logging
        qmp_cmd = {"execute": command}
        if kwargs:
            qmp_cmd["arguments"] = kwargs
        LOG.debug(f"Executing QMP command on {self.vm_id}: {qmp_cmd}")

        # Create thread-safe result container
        result_container = {"result": None, "error": None}

        def execute_qmp():
            """Thread target function for QMP execution."""
            try:
                result_container["result"] = qemu_machine.qmp(command, **kwargs)
            except Exception as e:
                result_container["error"] = e

        # Execute QMP command in thread with timeout
        qmp_thread = threading.Thread(target=execute_qmp, name=f"QMP-{self.vm_id}")
        qmp_thread.daemon = True
        qmp_thread.start()
        qmp_thread.join(timeout=self.timeout)

        # Check for timeout
        if qmp_thread.is_alive():
            raise QMPClientError(
                f"QMP command '{command}' timed out after {self.timeout} seconds. "
                f"VM may be unresponsive."
            )

        # Check for execution error
        if result_container["error"]:
            raise result_container["error"]

        return result_container["result"]
