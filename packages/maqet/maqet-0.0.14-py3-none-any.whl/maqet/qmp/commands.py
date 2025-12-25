"""
QMP Command Wrappers

Pre-built QMP command implementations that can be reused across the codebase.
These provide a clean abstraction layer over raw QMP commands.
"""

from typing import Any, Dict


class QMPCommands:
    """Collection of pre-built QMP command wrappers."""

    @staticmethod
    def screendump(machine, filename: str) -> Dict[str, Any]:
        """
        Take a screenshot of the VM display.

        Args:
            machine: Machine instance with qmp_command method
            filename: Path to save screenshot (PPM format)

        Returns:
            QMP command result
        """
        return machine.qmp_command("screendump", filename=filename)

    @staticmethod
    def pause(machine) -> Dict[str, Any]:
        """
        Pause VM execution.

        Args:
            machine: Machine instance with qmp_command method

        Returns:
            QMP command result
        """
        return machine.qmp_command("stop")

    @staticmethod
    def resume(machine) -> Dict[str, Any]:
        """
        Resume VM execution.

        Args:
            machine: Machine instance with qmp_command method

        Returns:
            QMP command result
        """
        return machine.qmp_command("cont")

    @staticmethod
    def device_del(machine, device_id: str) -> Dict[str, Any]:
        """
        Remove a hotplugged device.

        Args:
            machine: Machine instance with qmp_command method
            device_id: Device identifier to remove

        Returns:
            QMP command result
        """
        return machine.qmp_command("device_del", id=device_id)

    @staticmethod
    def system_powerdown(machine) -> Dict[str, Any]:
        """
        Send ACPI shutdown signal to VM.

        Args:
            machine: Machine instance with qmp_command method

        Returns:
            QMP command result
        """
        return machine.qmp_command("system_powerdown")

    @staticmethod
    def system_reset(machine) -> Dict[str, Any]:
        """
        Reset the VM.

        Args:
            machine: Machine instance with qmp_command method

        Returns:
            QMP command result
        """
        return machine.qmp_command("system_reset")
