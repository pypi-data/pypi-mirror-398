"""
Actionable error messages with diagnostic guidance.

Provides standard error messages with context-aware suggestions
to help users diagnose and fix common problems.

Key Features:
- Consistent error message formatting
- Actionable suggestions for each error type
- Context-aware guidance based on operation
- Integration with error_reporting module

Usage:
    from maqet.error_messages import ErrorMessages
    from maqet.error_reporting import report_error
    from maqet.constants import ExitCode

    # Get error and suggestions
    error, suggestions = ErrorMessages.vm_not_found("test-vm")

    # Report error with suggestions
    report_error(
        command="start",
        error=error,
        code=ExitCode.INVALID_ARGS,
        suggestions=suggestions
    )
"""

from pathlib import Path
from typing import Tuple, List, Optional


class ErrorMessages:
    """Standard error messages with actionable suggestions.

    Each method returns a tuple of (error_message, suggestions_list)
    to provide consistent error reporting across all commands.
    """

    @staticmethod
    def vm_not_found(vm_name: str) -> Tuple[str, List[str]]:
        """Error when VM doesn't exist.

        Args:
            vm_name: Name of the VM that wasn't found

        Returns:
            Tuple of (error_message, suggestions)

        Example:
            >>> error, suggestions = ErrorMessages.vm_not_found("test-vm")
            >>> print(error)
            VM 'test-vm' does not exist
        """
        return (
            f"VM '{vm_name}' does not exist",
            [
                "List available VMs: maqet ls",
                f"Create VM: maqet add --name {vm_name} <vm-config.yaml>",
                "Check for typos in VM name",
            ],
        )

    @staticmethod
    def vm_already_exists(vm_name: str) -> Tuple[str, List[str]]:
        """Error when VM already exists.

        Args:
            vm_name: Name of the VM that already exists

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"VM '{vm_name}' already exists",
            [
                "Choose a different name",
                f"Remove existing VM: maqet delete {vm_name}",
                f"View VM details: maqet status {vm_name}",
            ],
        )

    @staticmethod
    def vm_already_running(vm_name: str) -> Tuple[str, List[str]]:
        """Error when VM is already running.

        Args:
            vm_name: Name of the running VM

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"VM '{vm_name}' is already running",
            [
                f"View VM status: maqet status {vm_name}",
                f"Stop VM first: maqet stop {vm_name}",
                "Use --force flag to restart VM",
            ],
        )

    @staticmethod
    def vm_not_running(vm_name: str) -> Tuple[str, List[str]]:
        """Error when VM is not running.

        Args:
            vm_name: Name of the VM that is not running

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"VM '{vm_name}' is not running",
            [
                f"Start VM: maqet start {vm_name}",
                f"View VM status: maqet status {vm_name}",
                "Check if VM was stopped unexpectedly",
            ],
        )

    @staticmethod
    def qemu_spawn_failed(
        vm_name: str, log_file: Path, exit_code: Optional[int] = None
    ) -> Tuple[str, List[str]]:
        """Error when QEMU fails to spawn.

        Args:
            vm_name: Name of the VM
            log_file: Path to log file with error details
            exit_code: QEMU exit code (if available)

        Returns:
            Tuple of (error_message, suggestions)
        """
        if exit_code is not None:
            error = f"QEMU failed to start for VM '{vm_name}' (exit code {exit_code})"
        else:
            error = f"QEMU failed to start for VM '{vm_name}'"

        return (
            error,
            [
                f"Check logs: cat {log_file}",
                "Verify system has enough memory",
                "Check disk image files exist and are readable",
                "Verify QEMU binary is installed: qemu-system-x86_64 --version",
                "Check VM configuration is valid",
            ],
        )

    @staticmethod
    def qemu_crashed(vm_name: str, log_file: Path) -> Tuple[str, List[str]]:
        """Error when QEMU crashes immediately after start.

        Args:
            vm_name: Name of the VM
            log_file: Path to log file with crash details

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"QEMU crashed immediately after start for VM '{vm_name}'",
            [
                f"Check logs for crash details: cat {log_file}",
                "Verify disk image is not corrupted",
                "Check VM configuration for invalid options",
                "Try starting with minimal configuration",
            ],
        )

    @staticmethod
    def start_timeout(
        vm_name: str, timeout: int, condition: str = "process start"
    ) -> Tuple[str, List[str]]:
        """Error when VM start times out.

        Args:
            vm_name: Name of the VM
            timeout: Timeout value in seconds
            condition: What condition was being waited for

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"VM '{vm_name}' did not complete {condition} within {timeout}s",
            [
                f"VM may still be starting (check: maqet status {vm_name})",
                f"Increase timeout: --timeout={timeout * 2}",
                "Check VM is booting correctly",
                "Verify hardware resources are sufficient",
            ],
        )

    @staticmethod
    def ssh_timeout(vm_name: str, timeout: int) -> Tuple[str, List[str]]:
        """Error when SSH readiness times out.

        Args:
            vm_name: Name of the VM
            timeout: Timeout value in seconds

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"VM '{vm_name}' did not become SSH-ready within {timeout}s",
            [
                f"VM may still be booting (check: maqet status {vm_name})",
                "Verify SSH server is installed and enabled in the VM",
                "Check network configuration is correct",
                f"Increase timeout: --timeout={timeout * 2}",
                "Check firewall rules are not blocking SSH (port 22)",
                "Verify SSH keys are properly configured",
            ],
        )

    @staticmethod
    def stop_timeout(vm_name: str, timeout: int) -> Tuple[str, List[str]]:
        """Error when VM stop times out.

        Args:
            vm_name: Name of the VM
            timeout: Timeout value in seconds

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"VM '{vm_name}' did not stop gracefully within {timeout}s",
            [
                "VM was force-killed after timeout",
                f"Use longer timeout: --timeout={timeout * 2}",
                "Use --force flag to skip graceful shutdown",
                "Check VM's shutdown scripts are not hanging",
            ],
        )

    @staticmethod
    def permission_denied(path: Path, operation: str) -> Tuple[str, List[str]]:
        """Error when permission denied.

        Args:
            path: Path that had permission error
            operation: Operation that was attempted

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"Permission denied: cannot {operation} {path}",
            [
                f"Check file permissions: ls -la {path.parent}",
                f"Verify you own the directory: stat {path.parent}",
                "Check maqet data directory permissions",
                "Try with appropriate permissions (avoid sudo if possible)",
            ],
        )

    @staticmethod
    def database_locked() -> Tuple[str, List[str]]:
        """Error when database is locked.

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            "State database is locked (another maqet process may be running)",
            [
                "Wait for other maqet operations to complete",
                "Check for running maqet processes: ps aux | grep maqet",
                "If no processes running, database may be corrupted",
                "Try restarting maqet or system",
            ],
        )

    @staticmethod
    def snapshot_not_found(vm_name: str, snapshot_name: str) -> Tuple[str, List[str]]:
        """Error when snapshot doesn't exist.

        Args:
            vm_name: Name of the VM
            snapshot_name: Name of the snapshot

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"Snapshot '{snapshot_name}' not found for VM '{vm_name}'",
            [
                f"List available snapshots: maqet snapshot list {vm_name}",
                "Check for typos in snapshot name",
                f"Create snapshot: maqet snapshot create {vm_name} {snapshot_name}",
            ],
        )

    @staticmethod
    def snapshot_operation_failed(
        operation: str, vm_name: str, snapshot_name: str, details: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """Error when snapshot operation fails.

        Args:
            operation: Operation that failed (create, restore, delete)
            vm_name: Name of the VM
            snapshot_name: Name of the snapshot
            details: Additional error details

        Returns:
            Tuple of (error_message, suggestions)
        """
        error = f"Failed to {operation} snapshot '{snapshot_name}' for VM '{vm_name}'"
        if details:
            error += f": {details}"

        suggestions = [
            f"Check VM status: maqet status {vm_name}",
            "Verify disk has enough space",
            "Check VM disk images are not corrupted",
        ]

        if operation == "create":
            suggestions.append("Ensure VM is in stable state before snapshot")
        elif operation == "restore":
            suggestions.append(f"Verify snapshot exists: maqet snapshot list {vm_name}")
        elif operation == "delete":
            suggestions.append("Check snapshot is not in use")

        return (error, suggestions)

    @staticmethod
    def config_file_not_found(config_path: Path) -> Tuple[str, List[str]]:
        """Error when configuration file not found.

        Args:
            config_path: Path to config file

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"Configuration file not found: {config_path}",
            [
                f"Check file exists: ls -la {config_path}",
                "Verify path is correct",
                "Use absolute path or check working directory",
                "Example config: maqet example-config > vm-config.yaml",
            ],
        )

    @staticmethod
    def config_validation_failed(
        config_path: Path, details: str
    ) -> Tuple[str, List[str]]:
        """Error when configuration validation fails.

        Args:
            config_path: Path to config file
            details: Validation error details

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"Configuration validation failed: {details}",
            [
                f"Check configuration file: {config_path}",
                "Verify YAML syntax is valid",
                "Review configuration documentation",
                "Use maqet validate-config to check configuration",
            ],
        )

    @staticmethod
    def invalid_argument(argument: str, reason: str) -> Tuple[str, List[str]]:
        """Error when argument is invalid.

        Args:
            argument: Name of invalid argument
            reason: Why it's invalid

        Returns:
            Tuple of (error_message, suggestions)
        """
        return (
            f"Invalid argument '{argument}': {reason}",
            [
                "Check command syntax: maqet <command> --help",
                "Verify argument values are correct",
                "Review command documentation",
            ],
        )

    @staticmethod
    def unexpected_error(
        command: str, exception: Exception, log_file: Optional[Path] = None
    ) -> Tuple[str, List[str]]:
        """Error for unexpected exceptions.

        Args:
            command: Command that failed
            exception: Exception that was raised
            log_file: Path to log file (optional)

        Returns:
            Tuple of (error_message, suggestions)
        """
        error = f"Unexpected error in {command}: {type(exception).__name__}"

        suggestions = [
            "This may be a bug - please report if it persists",
            "Run with --debug flag for full traceback",
        ]

        if log_file:
            suggestions.insert(0, f"Check logs: cat {log_file}")

        return (error, suggestions)
