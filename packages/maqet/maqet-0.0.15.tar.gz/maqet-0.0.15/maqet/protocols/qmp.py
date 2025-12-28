"""QMP Manager Protocol definitions.

Provides Protocol-based interface for QMP (QEMU Machine Protocol) operations.
Enables dependency inversion and eliminates circular dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class QMPManagerProtocol(Protocol):
    """Protocol for QMP (QEMU Machine Protocol) manager.

    Defines the interface for QMP operations used by other components.
    Supports both IPC and direct socket communication modes.

    This protocol is used for type hints to enable loose coupling between
    components without creating circular import dependencies.
    """

    def execute_qmp(
        self,
        vm_id: str,
        command: str,
        allow_dangerous: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute QMP command on VM.

        Args:
            vm_id: VM identifier (name or ID)
            command: QMP command name (e.g., "query-status", "system_powerdown")
            allow_dangerous: Allow dangerous commands (default: False)
            **kwargs: Command parameters

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails
        """
        ...

    def send_keys(
        self,
        vm_id: str,
        *keys: str,
        hold_time: int = 100,
    ) -> Dict[str, Any]:
        """Send key combination to VM via QMP.

        Args:
            vm_id: VM identifier (name or ID)
            *keys: Key names to press (e.g., 'ctrl', 'alt', 'f2')
            hold_time: How long to hold keys in milliseconds (default: 100)

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails
        """
        ...

    def type_text(
        self,
        vm_id: str,
        text: str,
        hold_time: int = 100,
    ) -> List[Dict[str, Any]]:
        """Type text string to VM via QMP.

        Args:
            vm_id: VM identifier (name or ID)
            text: Text to type
            hold_time: How long to hold each key in milliseconds (default: 100)

        Returns:
            List of QMP command results (one per character)

        Raises:
            QMPError: If VM not found, not running, or command fails
        """
        ...

    def take_screenshot(
        self,
        vm_id: str,
        filename: str,
    ) -> Dict[str, Any]:
        """Take screenshot of VM screen.

        Args:
            vm_id: VM identifier (name or ID)
            filename: Output filename for screenshot (e.g., "screenshot.ppm")

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails
        """
        ...

    def pause(self, vm_id: str) -> Dict[str, Any]:
        """Pause VM execution via QMP.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails
        """
        ...

    def resume(self, vm_id: str) -> Dict[str, Any]:
        """Resume VM execution via QMP.

        Args:
            vm_id: VM identifier (name or ID)

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails
        """
        ...

    def device_add(
        self,
        vm_id: str,
        driver: str,
        device_id: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Hot-plug device to VM via QMP.

        Args:
            vm_id: VM identifier (name or ID)
            driver: Device driver name (e.g., 'usb-storage', 'e1000', 'virtio-net-pci')
            device_id: Unique device identifier
            **kwargs: Additional device properties

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails
        """
        ...

    def device_del(
        self,
        vm_id: str,
        device_id: str,
    ) -> Dict[str, Any]:
        """Hot-unplug device from VM via QMP.

        Args:
            vm_id: VM identifier (name or ID)
            device_id: Device identifier to remove

        Returns:
            QMP command result dictionary

        Raises:
            QMPError: If VM not found, not running, or command fails
        """
        ...
