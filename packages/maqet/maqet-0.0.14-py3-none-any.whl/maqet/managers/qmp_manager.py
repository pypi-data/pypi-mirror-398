"""
QMP Manager

Manages QMP (QEMU Machine Protocol) operations for VMs.
Supports both IPC and direct socket communication modes.

Responsibilities:
- Execute arbitrary QMP commands
- Send keyboard input (keys, typing)
- Take screenshots
- Pause/resume VM execution
- Hot-plug/unplug devices
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List

from ..decorators import handle_qmp_errors
from ..exceptions import (
    QMPError,
)
from ..ipc.runner_client import RunnerClient
from ..logger import LOG
from ..qmp import KeyboardEmulator
from ..qmp.qmp_socket_client import QMPSocketClient
from ..state import StateManager, VMInstance

# QMP Command Classification for Security
# Dangerous commands that can compromise guest security/stability
DANGEROUS_QMP_COMMANDS = {
    "human-monitor-command",  # Allows arbitrary monitor commands
    "inject-nmi",             # Can crash guest OS
}

# Privileged commands that affect VM availability (logged with warning)
PRIVILEGED_QMP_COMMANDS = {
    "system_powerdown",
    "system_reset",
    "quit",
    "device_del",
    "blockdev-del",
}

# Memory dump commands (allowed for testing, logged)
MEMORY_DUMP_COMMANDS = {
    "pmemsave",  # Physical memory dump
    "memsave",   # Virtual memory dump
}

# QMP Command Name Validation Regex
# Valid QMP commands: lowercase, hyphens, underscores only
# Examples: query-status, send-key, device_add, system_powerdown
# Prevents injection attacks like "quit; rm -rf /"
QMP_COMMAND_PATTERN = re.compile(r'^[a-z][a-z0-9_-]*$')


class QMPManager:
    """
    Manages QMP (QEMU Machine Protocol) operations across process boundaries.

    Architecture - Dual Communication Modes:
        This manager supports two communication modes for cross-process QMP:

        1. IPC Mode (Default, Recommended):
           CLI/Python API -> QMPManager -> IPC Socket -> VMRunner -> QMP Socket -> QEMU

           Benefits:
           - Single Point of Control: VMRunner owns the QMP connection to QEMU
           - Consistent Error Handling: All QMP errors handled in one place
           - Secure Authentication: IPC provides challenge-response auth
           - No Permission Issues: No need for shared socket access
           - Consistent with maqet's per-VM process architecture

        2. Direct Socket Mode (Alternative, Fallback):
           CLI/Python API -> QMPManager -> QMPSocketClient -> QMP Socket -> QEMU

           Benefits:
           - Simple and direct: No intermediate process required
           - Lower latency: Direct socket communication
           - Useful for debugging and testing
           - Works even if IPC layer has issues

    Mode Selection:
        - Default: IPC mode (use_direct_socket=False)
        - Override: Set use_direct_socket=True to use direct socket mode
        - Requires: VM must have qmp_socket_path in database

    Database Integration:
        - runner_pid: Tracks VMRunner process for each VM (IPC mode)
        - socket_path: IPC Unix socket path for communication (IPC mode)
        - qmp_socket_path: QMP Unix socket path (Direct socket mode)
        - VMRunner process maintains QEMU QMP connection internally

    Security Features:
        - Command name validation (prevents injection attacks)
        - Dangerous command blocking (requires explicit permission)
        - Privileged command warnings
        - Comprehensive audit logging

    This solves the critical cross-process QMP limitation where QMP commands
    failed from CLI with "No such file or directory" after the CLI process
    that started the VM had exited.

    See Also:
        - specs/fix-cross-process-qmp-communication.md (original problem analysis)
        - ipc/runner_client.py (IPC implementation)
        - qmp/qmp_socket_client.py (Direct socket implementation)
        - vm_runner.py (VMRunner that handles QMP forwarding)
    """

    def __init__(self, state_manager: StateManager, use_direct_socket: bool = False):
        """
        Initialize QMP manager.

        Args:
            state_manager: State management instance for VM database access
            use_direct_socket: Use direct QMP socket communication instead of IPC
                             (default: False, uses IPC mode)
        """
        self.state_manager = state_manager
        self.use_direct_socket = use_direct_socket

        mode = "direct socket" if use_direct_socket else "IPC"
        LOG.debug(f"QMPManager initialized (mode={mode})")

    @handle_qmp_errors("QMP command execution")
    def execute_qmp(
        self,
        vm_id: str,
        command: str,
        allow_dangerous: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute QMP command on VM with security validation.

        Communication Mode:
            - IPC mode (default): Routes through VMRunner process via IPC socket
            - Direct socket mode: Connects directly to QMP socket

        Args:
            vm_id: VM identifier (name or ID)
            command: QMP command to execute (e.g., "query-status", "system_powerdown")
            allow_dangerous: Allow dangerous commands (default: False)
            **kwargs: Command parameters

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, command validation fails,
                     or command is dangerous without permission

        Example:
            result = qmp_manager.execute_qmp("myvm", "query-status")
            result = qmp_manager.execute_qmp("myvm", "screendump", filename="screen.ppm")

            # Dangerous command (requires explicit permission)
            result = qmp_manager.execute_qmp(
                "myvm", "human-monitor-command",
                allow_dangerous=True,
                command_line="info status"
            )
        """
        # Security: Validate QMP command name to prevent injection
        if not QMP_COMMAND_PATTERN.match(command):
            raise QMPError(
                f"Invalid QMP command name '{command}'. "
                f"Command names must match pattern: {QMP_COMMAND_PATTERN.pattern}. "
                f"This prevents injection attacks."
            )

        # Security: Validate command is not dangerous
        if command in DANGEROUS_QMP_COMMANDS and not allow_dangerous:
            raise QMPError(
                f"Dangerous QMP command '{command}' blocked. "
                f"This command can compromise guest security or stability. "
                f"If you really need this, use allow_dangerous=True and "
                f"understand the risks. See: docs/security/qmp-security.md"
            )

        # Log privileged commands with warning
        if command in PRIVILEGED_QMP_COMMANDS:
            LOG.warning(
                f"QMP privileged: {vm_id} | {command} | "
                f"user={os.getenv('USER', 'unknown')}"
            )

        # Log memory dump commands (allowed for testing)
        if command in MEMORY_DUMP_COMMANDS:
            LOG.info(
                f"QMP memory dump: {vm_id} | {command} | "
                f"user={os.getenv('USER', 'unknown')} | purpose=testing"
            )

        # Audit log all QMP commands
        mode = "direct_socket" if self.use_direct_socket else "ipc"
        LOG.info(
            f"QMP: {vm_id} | {command} | "
            f"params={list(kwargs.keys())} | "
            f"mode={mode} | "
            f"user={os.getenv('USER', 'unknown')} | "
            f"timestamp={datetime.now().isoformat()}"
        )

        # Get VM from database
        vm = self.state_manager.get_vm(vm_id)
        if not vm:
            raise QMPError(f"VM '{vm_id}' not found")

        # Check VM is running
        if vm.status != "running":
            raise QMPError(
                f"VM '{vm_id}' is not running (status: {vm.status})"
            )

        # Execute via direct socket or IPC based on mode
        if self.use_direct_socket:
            result = self._execute_via_direct_socket(vm, command, **kwargs)
        else:
            result = self._execute_via_ipc(vm, command, **kwargs)

        LOG.debug(f"QMP command '{command}' executed successfully on {vm_id}")
        return result

    def _execute_via_ipc(
        self, vm: VMInstance, command: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute QMP command via IPC to VMRunner process.

        Args:
            vm: VM instance from database
            command: QMP command name
            **kwargs: Command arguments

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If runner process not available or IPC fails
        """
        # Verify runner process is alive
        if not vm.runner_pid:
            raise QMPError(
                f"VM '{vm.id}' has no runner process (state corrupted)"
            )

        # Create IPC client and send QMP command
        client = RunnerClient(vm.id, self.state_manager)
        result = client.send_command("qmp", command, **kwargs)

        return result

    def _execute_via_direct_socket(
        self, vm: VMInstance, command: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute QMP command via direct socket connection.

        Connects directly to QMP Unix socket without using VMRunner IPC.
        Implements the approach from Component 4 of the specification.

        Args:
            vm: VM instance from database
            command: QMP command name
            **kwargs: Command arguments

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If QMP socket not found or connection fails
        """
        # Verify QMP socket path is available
        if not vm.qmp_socket_path:
            raise QMPError(
                f"VM '{vm.id}' has no QMP socket path. "
                f"Direct socket mode requires qmp_socket_path in database. "
                f"VM may have been started before this feature was added. "
                f"Try restarting the VM or use IPC mode (default)."
            )

        # Connect directly to QMP socket
        client = QMPSocketClient(vm.qmp_socket_path)
        try:
            client.connect()
            result = client.execute(command, **kwargs)
            return result
        finally:
            client.disconnect()

    @handle_qmp_errors("Send keys")
    def send_keys(
        self, vm_id: str, *keys: str, hold_time: int = 100
    ) -> Dict[str, Any]:
        """
        Send key combination to VM via QMP.

        Uses KeyboardEmulator to translate key names into QMP send-key command.

        Args:
            vm_id: VM identifier (name or ID)
            *keys: Key names to press (e.g., 'ctrl', 'alt', 'f2')
            hold_time: How long to hold keys in milliseconds (default: 100)

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails

        Example:
            qmp_manager.send_keys("myvm", "ctrl", "alt", "f2")
            qmp_manager.send_keys("myvm", "ret", hold_time=200)
        """
        # Generate QMP command from key names
        qmp_cmd = KeyboardEmulator.press_keys(*keys, hold_time=hold_time)

        # Execute QMP command via IPC
        result = self.execute_qmp(
            vm_id, qmp_cmd["command"], **qmp_cmd["arguments"]
        )

        LOG.debug(f"Sent keys {keys} to VM {vm_id}")
        return result

    @handle_qmp_errors("Type text")
    def type_text(
        self, vm_id: str, text: str, hold_time: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Type text string to VM via QMP.

        Sends each character as a separate QMP send-key command.

        Args:
            vm_id: VM identifier (name or ID)
            text: Text to type
            hold_time: How long to hold each key in milliseconds (default: 100)

        Returns:
            List of QMP command results (one per character)

        Raises:
            QMPError: If VM not found, not running, or command fails

        Example:
            qmp_manager.type_text("myvm", "hello world")
            qmp_manager.type_text("myvm", "slow typing", hold_time=50)
        """
        # Generate QMP commands for each character
        qmp_commands = KeyboardEmulator.type_string(text, hold_time=hold_time)

        # Execute each command via IPC
        results = []
        for cmd in qmp_commands:
            result = self.execute_qmp(
                vm_id, cmd["command"], **cmd["arguments"]
            )
            results.append(result)

        LOG.debug(f"Typed {len(text)} characters to VM {vm_id}")
        return results

    @handle_qmp_errors("Take screenshot")
    def take_screenshot(self, vm_id: str, filename: str) -> Dict[str, Any]:
        """
        Take screenshot of VM screen.

        Saves screenshot to specified file in PPM format (QEMU default).

        Args:
            vm_id: VM identifier (name or ID)
            filename: Output filename for screenshot (e.g., "screenshot.ppm")

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails

        Example:
            qmp_manager.take_screenshot("myvm", "/tmp/screenshot.ppm")
        """
        result = self.execute_qmp(vm_id, "screendump", filename=filename)
        LOG.info(f"Screenshot saved to {filename} for VM {vm_id}")
        return result

    @handle_qmp_errors("Pause VM")
    def pause(self, vm_id: str) -> Dict[str, Any]:
        """
        Pause VM execution via QMP.

        Suspends VM execution (freezes guest). VM can be resumed later.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails

        Example:
            qmp_manager.pause("myvm")
        """
        result = self.execute_qmp(vm_id, "stop")
        LOG.info(f"VM {vm_id} paused")
        return result

    @handle_qmp_errors("Resume VM")
    def resume(self, vm_id: str) -> Dict[str, Any]:
        """
        Resume VM execution via QMP.

        Resumes a previously paused VM.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails

        Example:
            qmp_manager.resume("myvm")
        """
        result = self.execute_qmp(vm_id, "cont")
        LOG.info(f"VM {vm_id} resumed")
        return result

    @handle_qmp_errors("Device hot-plug")
    def device_add(
        self, vm_id: str, driver: str, device_id: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Hot-plug device to VM via QMP.

        Adds a device to running VM without restart.

        Args:
            vm_id: VM identifier (name or ID)
            driver: Device driver name (e.g., 'usb-storage', 'e1000', 'virtio-net-pci')
            device_id: Unique device identifier
            **kwargs: Additional device properties (e.g., drive="usb-drive", netdev="user1")

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails

        Example:
            qmp_manager.device_add("myvm", "usb-storage", "usb1", drive="usb-drive")
            qmp_manager.device_add("myvm", "e1000", "net1", netdev="user1")
        """
        result = self.execute_qmp(
            vm_id, "device_add", driver=driver, id=device_id, **kwargs
        )
        LOG.info(f"Device {device_id} (driver={driver}) added to VM {vm_id}")
        return result

    @handle_qmp_errors("Device hot-unplug")
    def device_del(self, vm_id: str, device_id: str) -> Dict[str, Any]:
        """
        Hot-unplug device from VM via QMP.

        Removes a device from running VM without restart.

        Args:
            vm_id: VM identifier (name or ID)
            device_id: Device identifier to remove

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails

        Example:
            qmp_manager.device_del("myvm", "usb1")
        """
        result = self.execute_qmp(vm_id, "device_del", id=device_id)
        LOG.info(f"Device {device_id} removed from VM {vm_id}")
        return result
