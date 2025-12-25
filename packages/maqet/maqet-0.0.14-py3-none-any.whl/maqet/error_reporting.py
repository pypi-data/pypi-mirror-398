"""
Structured error reporting for CLI commands.

Provides consistent error output with actionable suggestions and
support for both human-readable and JSON formats.

Key Components:
- ErrorReport: Structured error report with JSON and human formats
- report_error(): Convenience function for reporting errors and exiting
- report_success(): Convenience function for reporting success

Usage:
    from maqet.error_reporting import report_error
    from maqet.constants import ExitCode

    # Report error and exit
    report_error(
        command="start",
        error="VM 'test-vm' not found",
        code=ExitCode.INVALID_ARGS,
        suggestions=["List VMs: maqet ls", "Create VM: maqet add ..."],
        format="human"
    )

    # Or create ErrorReport manually
    report = ErrorReport(
        status="error",
        code=ExitCode.FAILURE,
        command="start",
        error="QEMU failed to start",
        details="Exit code: 1",
        log_file=Path("/var/log/maqet/vm.log"),
        suggestions=["Check logs", "Verify memory"]
    )
    report.print_and_exit(format="json")
"""

import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class ErrorReport:
    """Structured error report for CLI commands.

    Attributes:
        status: Status indicator ("error", "timeout", "invalid", "success")
        code: Exit code (use ExitCode constants)
        command: Command that was executed
        error: Short error description
        details: Detailed error message (optional)
        log_file: Path to log file with more info (optional)
        suggestions: List of suggestions for fixing the error (optional)
        data: Additional structured data (optional)
    """

    status: str
    code: int
    command: str
    error: str
    details: Optional[str] = None
    log_file: Optional[Path] = None
    suggestions: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            JSON-formatted error report

        Example:
            >>> report = ErrorReport(status="error", code=1, command="start",
            ...                      error="VM not found")
            >>> print(report.to_json())
            {
              "status": "error",
              "code": 1,
              "command": "start",
              "error": "VM not found"
            }
        """
        data = asdict(self)

        # Convert Path to string for JSON serialization
        if data["log_file"]:
            data["log_file"] = str(data["log_file"])

        # Remove None values for cleaner JSON
        data = {k: v for k, v in data.items() if v is not None}

        return json.dumps(data, indent=2)

    def to_human(self) -> str:
        """Convert to human-readable format.

        Returns:
            Human-readable error report

        Example:
            >>> report = ErrorReport(status="error", code=1, command="start",
            ...                      error="VM not found",
            ...                      suggestions=["List VMs: maqet ls"])
            >>> print(report.to_human())
            Error: VM not found

            Suggestions:
              - List VMs: maqet ls
        """
        lines = []

        # Main error message
        if self.status == "success":
            lines.append(f"Success: {self.error}")
        else:
            lines.append(f"Error: {self.error}")

        # Detailed error message
        if self.details:
            lines.append(f"\nDetails: {self.details}")

        # Log file reference
        if self.log_file:
            lines.append(f"\nLog file: {self.log_file}")

        # Actionable suggestions
        if self.suggestions:
            lines.append("\nSuggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")

        return "\n".join(lines)

    def print_and_exit(self, format: str = "human") -> None:
        """Print error and exit with appropriate code.

        Args:
            format: Output format ("human" or "json")

        Note:
            This function does not return - it calls sys.exit()
        """
        if format == "json":
            print(self.to_json(), file=sys.stderr if self.code != 0 else sys.stdout)
        else:
            print(self.to_human(), file=sys.stderr if self.code != 0 else sys.stdout)

        sys.exit(self.code)


def report_error(
    command: str,
    error: str,
    code: int = 1,
    details: Optional[str] = None,
    log_file: Optional[Path] = None,
    suggestions: Optional[List[str]] = None,
    format: str = "human",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Report error and exit with appropriate code.

    Convenience function for creating ErrorReport and exiting.

    Args:
        command: Command that failed
        error: Short error description
        code: Exit code (default: 1)
        details: Detailed error message
        log_file: Path to log file with more info
        suggestions: List of suggestions for fixing
        format: Output format ("human" or "json")
        data: Additional structured data

    Example:
        >>> from maqet.constants import ExitCode
        >>> report_error(
        ...     command="start",
        ...     error="VM 'test-vm' not found",
        ...     code=ExitCode.INVALID_ARGS,
        ...     suggestions=["List VMs: maqet ls"]
        ... )
        Error: VM 'test-vm' not found

        Suggestions:
          - List VMs: maqet ls

    Note:
        This function does not return - it calls sys.exit()
    """
    # Map exit code to status
    status_map = {
        0: "success",
        1: "error",
        2: "timeout",
        3: "invalid",
        4: "permission_denied",
    }
    status = status_map.get(code, "error")

    report = ErrorReport(
        status=status,
        code=code,
        command=command,
        error=error,
        details=details,
        log_file=log_file,
        suggestions=suggestions,
        data=data,
    )
    report.print_and_exit(format)


def report_success(
    command: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    format: str = "human",
) -> None:
    """Report success and exit with code 0.

    Convenience function for consistent success reporting.

    Args:
        command: Command that succeeded
        message: Success message
        data: Additional structured data
        format: Output format ("human" or "json")

    Example:
        >>> report_success(
        ...     command="start",
        ...     message="VM started successfully",
        ...     data={"vm_name": "test-vm", "pid": 12345}
        ... )
        Success: VM started successfully

    Note:
        This function does not return - it calls sys.exit()
    """
    report = ErrorReport(
        status="success",
        code=0,
        command=command,
        error=message,  # Reuse error field for success message
        data=data,
    )
    report.print_and_exit(format)


def format_exception_for_report(exc: Exception) -> tuple[str, Optional[str]]:
    """Format exception for error reporting.

    Extracts error message and details from exception.

    Args:
        exc: Exception to format

    Returns:
        Tuple of (error_message, details)

    Example:
        >>> try:
        ...     raise ValueError("Invalid VM name")
        ... except Exception as e:
        ...     error, details = format_exception_for_report(e)
        ...     print(error)
        Invalid VM name
    """
    error = str(exc)
    details = f"{type(exc).__name__}: {exc}"

    # For known exception types, provide better formatting
    if hasattr(exc, "__cause__") and exc.__cause__:
        details += f"\nCaused by: {exc.__cause__}"

    return error, details
