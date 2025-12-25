"""
Error Handling Decorators

Provides reusable decorators for common error handling patterns across the codebase.
Reduces repetitive try/catch blocks while maintaining specific, actionable error messages.

Usage:
    @handle_vm_errors("VM creation")
    def add(self, vm_config, name, empty, **kwargs):
        # Business logic only - no error handling needed
        config_data = ConfigMerger.load_and_merge_files(vm_config)
        return self.state_manager.create_vm(name, config_data)

    @handle_qmp_errors("QMP command execution")
    def execute_qmp(self, vm_id, command, **kwargs):
        # Business logic only
        return client.send_command("qmp", command, **kwargs)

Benefits:
- Reduces code duplication (~200 lines across codebase)
- Consistent error messages and handling
- Easy to add new error types centrally
- Separates error handling from business logic
"""

import functools
from typing import Callable, Type

from .exceptions import (
    ConfigurationError,
    IPCError,
    QMPError,
    SnapshotError,
    StateError,
    VMLifecycleError,
    VMNotFoundError,
    VMNotRunningError,
)
from .logger import LOG


def handle_vm_errors(operation: str) -> Callable:
    """
    Decorator for common VM lifecycle error handling.

    Wraps FileNotFoundError, PermissionError, ConfigurationError, and StateError
    into VMLifecycleError with actionable context.

    Catches and wraps:
    - FileNotFoundError, PermissionError (file access errors)
    - ConfigurationError (and all subclasses including ConfigError)
    - StateError (and all subclasses including DatabaseError, DatabaseLockError)
    - VMLifecycleError (re-raised as-is with original context)
    - All other exceptions (wrapped as unexpected errors with full context)

    Does NOT catch (let them propagate):
    - KeyboardInterrupt, SystemExit (process control signals)
    - These are intentionally not caught to allow graceful shutdown

    Args:
        operation: Human-readable operation description (e.g., "VM creation", "VM start")

    Returns:
        Decorator function

    Example:
        @handle_vm_errors("VM creation")
        def add(self, vm_config, name, **kwargs):
            config_data = ConfigMerger.load_and_merge_files(vm_config)
            return self.state_manager.create_vm(name, config_data)

        # Error: VMLifecycleError("VM creation: File not found - /path/to/config.yaml")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except FileNotFoundError as e:
                error_msg = (
                    f"{operation}: File not found - {e.filename}. "
                    f"Check that the file path is correct."
                )
                LOG.error(error_msg)
                raise VMLifecycleError(error_msg) from e

            except PermissionError as e:
                error_msg = (
                    f"{operation}: Permission denied - {e.filename}. "
                    f"Check file permissions and ownership."
                )
                LOG.error(error_msg)
                raise VMLifecycleError(error_msg) from e

            except ConfigurationError as e:
                error_msg = f"{operation}: Configuration error - {e}"
                LOG.error(error_msg)
                raise VMLifecycleError(error_msg) from e

            except StateError as e:
                error_msg = f"{operation}: Database error - {e}"
                LOG.error(error_msg)
                raise VMLifecycleError(error_msg) from e

            except VMLifecycleError:
                # Re-raise VMLifecycleError as-is (already has context)
                raise

            except Exception as e:
                # Last resort - log unexpected errors with context
                error_msg = f"{operation}: Unexpected error - {type(e).__name__}: {e}"
                LOG.error(error_msg, exc_info=True)
                raise VMLifecycleError(error_msg) from e

        return wrapper

    return decorator


def handle_qmp_errors(operation: str) -> Callable:
    """
    Decorator for common QMP error handling.

    Wraps IPCError and generic exceptions into QMPError with actionable context.

    Catches and wraps:
    - IPCError (and all subclasses including RunnerClientError, UnixSocketError)
    - QMPError (re-raised as-is with original context)
    - All other exceptions (wrapped as unexpected errors with full context)

    Does NOT catch (let them propagate):
    - KeyboardInterrupt, SystemExit (process control signals)

    Args:
        operation: Human-readable operation description (e.g., "QMP command execution")

    Returns:
        Decorator function

    Example:
        @handle_qmp_errors("QMP command execution")
        def execute_qmp(self, vm_id, command, **kwargs):
            client = RunnerClient(vm.id, self.state_manager)
            return client.send_command("qmp", command, **kwargs)

        # Error: QMPError("QMP command execution: Failed to communicate with VM runner - timeout")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except IPCError as e:
                error_msg = (
                    f"{operation}: Failed to communicate with VM runner - {e}"
                )
                LOG.error(error_msg)
                raise QMPError(error_msg) from e

            except QMPError:
                # Re-raise QMPError as-is (already has context)
                raise

            except Exception as e:
                # Last resort - log unexpected errors with context
                error_msg = f"{operation}: Unexpected error - {type(e).__name__}: {e}"
                LOG.error(error_msg, exc_info=True)
                raise QMPError(error_msg) from e

        return wrapper

    return decorator


def handle_snapshot_errors(operation: str) -> Callable:
    """
    Decorator for common snapshot error handling.

    Wraps FileNotFoundError, PermissionError, and generic exceptions into
    SnapshotError with actionable context.

    Catches and wraps:
    - FileNotFoundError, PermissionError (file access errors)
    - SnapshotError (re-raised as-is with original context)
    - All other exceptions (wrapped as unexpected errors with full context)

    Does NOT catch (let them propagate):
    - KeyboardInterrupt, SystemExit (process control signals)
    - VMNotRunningError, VMNotFoundError (precondition failures - user-actionable)

    Args:
        operation: Human-readable operation description (e.g., "Snapshot creation")

    Returns:
        Decorator function

    Example:
        @handle_snapshot_errors("Snapshot creation")
        def create(self, drive_name, snapshot_name, overwrite=False):
            device = self._get_snapshot_capable_device(drive_name)
            self._run_qemu_img(["snapshot", str(drive_path), "-c", snapshot_name])
            return {"status": "success"}

        # Error: SnapshotError("Snapshot creation: File not found - /path/to/drive.qcow2")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except FileNotFoundError as e:
                error_msg = (
                    f"{operation}: File not found - {e.filename}. "
                    f"Check that the storage file exists."
                )
                LOG.error(error_msg)
                raise SnapshotError(error_msg) from e

            except PermissionError as e:
                error_msg = (
                    f"{operation}: Permission denied - {e.filename}. "
                    f"Check file permissions and ownership."
                )
                LOG.error(error_msg)
                raise SnapshotError(error_msg) from e

            except SnapshotError:
                # Re-raise SnapshotError as-is (already has context)
                raise

            except (VMNotRunningError, VMNotFoundError):
                # Propagate precondition failures directly - user-actionable errors
                # VMNotRunningError: User needs to start VM or use offline mode
                # VMNotFoundError: User needs to specify correct VM ID
                raise

            except Exception as e:
                # Last resort - log unexpected errors with context
                error_msg = f"{operation}: Unexpected error - {type(e).__name__}: {e}"
                LOG.error(error_msg, exc_info=True)
                raise SnapshotError(error_msg) from e

        return wrapper

    return decorator


def handle_errors(
    operation: str, exception_type: Type[Exception] = Exception
) -> Callable:
    """
    Generic error handling decorator.

    Wraps all exceptions into specified exception type with operation context.
    Use specific decorators (handle_vm_errors, handle_qmp_errors, etc.) when possible.

    Args:
        operation: Human-readable operation description
        exception_type: Exception type to raise (default: Exception)

    Returns:
        Decorator function

    Example:
        @handle_errors("Custom operation", CustomError)
        def custom_operation(self):
            # Business logic
            return result
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except exception_type:
                # Re-raise if already the target exception type
                raise

            except Exception as e:
                error_msg = f"{operation}: {type(e).__name__}: {e}"
                LOG.error(error_msg, exc_info=True)
                raise exception_type(error_msg) from e

        return wrapper

    return decorator
