"""State management package.

Re-exports from state_manager.py for backwards compatibility.
"""

from maqet.state_manager import (
    StateManager,
    VMInstance,
    XDGDirectories,
    MIGRATIONS,
)
from .migration_runner import MigrationRunner
from .vm_repository import VMRepository

# Re-export StateError from exceptions (for backward compatibility)
from ..exceptions import StateError, MigrationError

# Re-export validate_pid_exists for backward compatibility (used in tests)
from ..utils.process_validation import validate_pid_exists

__all__ = [
    "StateManager",
    "VMInstance",
    "XDGDirectories",
    "MIGRATIONS",
    "MigrationRunner",
    "VMRepository",
    "StateError",
    "MigrationError",
    "validate_pid_exists",
]
