# Manager Architecture Patterns

## Overview

The maqet project follows a manager-based architecture pattern where functionality is organized into focused, single-responsibility managers that collaborate through dependency injection. This document establishes the conventions and patterns used across all managers in the codebase.

**Context**: The manager architecture emerged from refactoring a god object (Maqet class) that originally handled all operations. The refactoring (completed 2025-10-27) reduced the Maqet facade from ~2300 lines to 447 lines (80.6% reduction) by extracting specialized managers.

**Key Principles**:

- **Single Responsibility**: Each manager owns one domain (VM lifecycle, QMP operations, snapshots, etc.)
- **Dependency Injection**: Managers receive dependencies via constructor (no service locators)
- **Consistent Error Handling**: Decorators provide uniform error translation and logging
- **Clear Ownership**: Each resource has exactly one owner (no shared mutable state)
- **Testability**: Managers can be tested in isolation with mock dependencies

## Manager vs Coordinator Naming

### Naming Convention

The distinction between "Manager" and "Coordinator" reflects the semantic role of the component:

**Manager**: Owns and manages a specific resource or domain

- Controls lifecycle of the resource
- Maintains state for that resource
- Provides CRUD-like operations
- Examples: VMManager, QMPManager, ProcessLifecycleManager

**Coordinator**: Orchestrates operations across multiple managers or resources

- Does not own resources directly
- Delegates to managers for actual work
- Coordinates sequencing and error handling
- Examples: CleanupCoordinator, SnapshotCoordinator, StartupCoordinator

### When to Use Each

**Use "Manager" when**:

```python
# The component OWNS the resource it manages
class VMManager:
    def __init__(self, state_manager, config_parser):
        self._machines: Dict[str, Machine] = {}  # Owns this cache

    def start(self, vm_id: str) -> VMInstance:
        # Directly manipulates owned resources
        machine = self._machines.get(vm_id)
        # ...
```

**Use "Coordinator" when**:

```python
# The component ORCHESTRATES multiple managers
class CleanupCoordinator:
    def __init__(self, vm_manager: VMManager):
        self.vm_manager = vm_manager  # Uses, doesn't own

    def cleanup_all(self):
        # Coordinates operations across multiple VMs
        for vm_id in running_vms:
            self.vm_manager.stop(vm_id)  # Delegates to manager
```

### Real-World Examples

| Component | Type | Reason |
|-----------|------|--------|
| VMManager | Manager | Owns VM lifecycle and machine cache |
| QMPManager | Manager | Owns QMP communication logic |
| SnapshotCoordinator | Coordinator | Orchestrates StorageManager + SnapshotManager |
| CleanupCoordinator | Coordinator | Orchestrates parallel VM shutdown |
| StartupCoordinator | Coordinator | Orchestrates startup sequence steps |
| ProcessLifecycleManager | Manager | Owns process state and PID registry |

## Dependency Injection Patterns

### Constructor Injection (Preferred)

All managers receive dependencies through their constructor. This makes dependencies explicit and enables easy testing.

**Pattern**:

```python
class VMManager:
    """Manager with injected dependencies."""

    def __init__(self, state_manager: StateManager, config_parser):
        """
        Initialize VM manager.

        Args:
            state_manager: State management instance
            config_parser: Configuration parser instance
        """
        self.state_manager = state_manager
        self.config_parser = config_parser
        self._machines: Dict[str, Any] = {}  # Owned resources initialized here
        LOG.debug("VMManager initialized")
```

**Benefits**:

- Dependencies are explicit in the signature
- Easy to mock for testing
- No hidden dependencies or service locators
- Clear initialization order

### Real Example: QMPManager

```python
class QMPManager:
    """Manages QMP operations across process boundaries."""

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
```

### Real Example: CleanupCoordinator

```python
class CleanupCoordinator:
    """Coordinates resource cleanup with parallel VM shutdown."""

    def __init__(self, vm_manager: VMManager):
        """
        Initialize CleanupCoordinator.

        Args:
            vm_manager: VMManager instance for VM operations and cache access
        """
        self.vm_manager = vm_manager
        LOG.debug("CleanupCoordinator initialized")
```

**Note**: CleanupCoordinator receives VMManager, not the parent facade. This prevents circular dependencies.

### Initialization in Facade

The Maqet facade instantiates all managers and handles dependency wiring:

```python
class Maqet:
    """Main facade for VM management."""

    def __init__(self, xdg_config_path: Optional[str] = None):
        # Initialize dependencies first
        self.xdg = XDGDirectoryManager(xdg_config_path)
        self.state_manager = StateManager(self.xdg)
        self.config_parser = ConfigParser()

        # Initialize managers with dependencies
        self.vm_manager = VMManager(self.state_manager, self.config_parser)
        self.qmp_manager = QMPManager(self.state_manager)
        self.snapshot_coordinator = SnapshotCoordinator(self.state_manager)

        # Initialize coordinators (pass managers, not self)
        self.cleanup_coordinator = CleanupCoordinator(self.vm_manager)
```

## Error Handling Patterns

### Error Decorator System

Managers use decorators for consistent error handling across the codebase. Decorators translate low-level exceptions into domain-specific exceptions with actionable context.

**Available Decorators**:

- `@handle_vm_errors(operation)` - VM lifecycle operations
- `@handle_qmp_errors(operation)` - QMP command execution
- `@handle_snapshot_errors(operation)` - Snapshot operations

### Pattern: Decorator Usage

```python
from ..decorators import handle_vm_errors

class VMManager:
    @handle_vm_errors("VM creation")
    def add(self, vm_config: Optional[Union[str, List[str]]] = None, **kwargs) -> str:
        """
        Create a new VM from configuration.

        Business logic only - no try/except needed.
        Decorator handles all error translation.
        """
        # Load and merge configuration
        if vm_config:
            config_data = ConfigMerger.load_and_merge_files(vm_config)
        else:
            config_data = {}

        # Validate and create
        config_data = self.config_parser.validate_config(config_data)
        vm_id = self.state_manager.create_vm(name, config_data)
        return vm_id
```

### What Decorators Do

**Error Translation**:

```python
# Without decorator (old pattern):
def add(self, vm_config, **kwargs):
    try:
        config_data = ConfigMerger.load_and_merge_files(vm_config)
        # ...
    except FileNotFoundError as e:
        raise VMLifecycleError(f"VM creation: File not found - {e.filename}")
    except ConfigurationError as e:
        raise VMLifecycleError(f"VM creation: Configuration error - {e}")
    except Exception as e:
        raise VMLifecycleError(f"VM creation: Unexpected error - {e}")

# With decorator (current pattern):
@handle_vm_errors("VM creation")
def add(self, vm_config, **kwargs):
    config_data = ConfigMerger.load_and_merge_files(vm_config)
    # Error handling is automatic!
```

**Benefits**:

- Reduces code duplication (~200 lines across codebase)
- Consistent error messages
- Centralized error handling logic
- Business logic remains clean and focused

### Real Example: QMPManager

```python
class QMPManager:
    @handle_qmp_errors("QMP command execution")
    def execute_qmp(
        self,
        vm_id: str,
        command: str,
        allow_dangerous: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute QMP command with security validation.

        Decorator handles IPCError translation to QMPError.
        Method focuses on business logic only.
        """
        # Validate command name (security)
        if not QMP_COMMAND_PATTERN.match(command):
            raise QMPError(f"Invalid QMP command name '{command}'")

        # Execute via IPC (IPCError automatically wrapped by decorator)
        client = RunnerClient(vm.id, self.state_manager)
        result = client.send_command("qmp", command, **kwargs)
        return result
```

### Exception Hierarchy

Managers raise domain-specific exceptions that inherit from MaqetError:

```
MaqetError (base)
├── ConfigurationError
│   ├── ConfigFileNotFoundError
│   ├── ConfigValidationError
│   └── InvalidConfigurationError
├── VMLifecycleError
│   ├── VMNotFoundError
│   ├── VMAlreadyRunningError
│   └── VMStartError
├── QMPError
│   ├── QMPConnectionError
│   ├── QMPCommandError
│   └── QMPTimeoutError
├── SnapshotError
│   ├── SnapshotNotFoundError
│   └── SnapshotCreationError
└── StateError
    ├── DatabaseError
    └── DatabaseLockError
```

**Usage Pattern**:

```python
# Managers raise specific exceptions
@handle_vm_errors("VM start")
def start(self, vm_id: str) -> VMInstance:
    vm = self.state_manager.get_vm(vm_id)
    if not vm:
        raise VMLifecycleError(f"VM '{vm_id}' not found")  # Specific context

    if vm.status == "running":
        raise VMLifecycleError(f"VM '{vm_id}' is already running")  # Actionable
```

## Manager Responsibilities

### Single Responsibility Principle

Each manager owns exactly one domain of functionality. Clear boundaries prevent scope creep and maintain testability.

**Examples**:

| Manager | Owns | Does NOT Own |
|---------|------|--------------|
| VMManager | VM lifecycle (add, start, stop, remove, list) | QMP operations, snapshots |
| QMPManager | QMP command execution, keyboard input | VM lifecycle, storage |
| SnapshotCoordinator | Snapshot operations (create, load, list) | Storage creation, VM state |
| CleanupCoordinator | Parallel VM shutdown coordination | VM lifecycle, machine cache |
| ProcessLifecycleManager | Process state, PID registry, signals | VM configuration, QMP |

### Responsibility Examples

**VMManager - VM Lifecycle**:

```python
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

    def add(self, vm_config, name, **kwargs) -> str:
        """Create VM - VMManager's job."""

    def start(self, vm_id: str) -> VMInstance:
        """Start VM - VMManager's job."""

    def execute_qmp(self, vm_id, command):
        """QMP operation - NOT VMManager's job, delegate to QMPManager."""
        raise NotImplementedError("Use QMPManager.execute_qmp()")
```

**QMPManager - QMP Operations**:

```python
class QMPManager:
    """
    Manages QMP operations across process boundaries.

    Responsibilities:
    - Execute arbitrary QMP commands
    - Send keyboard input (keys, typing)
    - Take screenshots
    - Pause/resume VM execution
    - Hot-plug/unplug devices
    """

    def execute_qmp(self, vm_id, command, **kwargs) -> Dict[str, Any]:
        """Execute QMP command - QMPManager's job."""

    def send_keys(self, vm_id: str, *keys: str) -> Dict[str, Any]:
        """Send keyboard input - QMPManager's job."""

    def start_vm(self, vm_id: str):
        """VM lifecycle - NOT QMPManager's job, delegate to VMManager."""
        raise NotImplementedError("Use VMManager.start()")
```

### What Belongs in Facade vs Manager

**Facade (Maqet class)**:

- Public API surface (delegates to managers)
- Manager initialization and wiring
- Backward compatibility shims
- High-level workflows that span multiple managers

**Manager**:

- Domain-specific implementation
- Resource ownership and lifecycle
- Error handling for that domain
- Internal state management

**Example - Facade Delegation**:

```python
class Maqet:
    """Facade - delegates to managers."""

    def add(self, vm_config=None, name=None, **kwargs) -> str:
        """Public API - delegates to VMManager."""
        return self.vm_manager.add(vm_config, name, **kwargs)

    def start(self, vm_id: str) -> VMInstance:
        """Public API - delegates to VMManager."""
        return self.vm_manager.start(vm_id)

    def execute_qmp(self, vm_id, command, **kwargs) -> Dict[str, Any]:
        """Public API - delegates to QMPManager."""
        return self.qmp_manager.execute_qmp(vm_id, command, **kwargs)
```

## Cache Ownership Pattern

### Problem: Shared Mutable State

Early manager implementations shared cache dictionaries between classes, leading to unclear ownership and potential bugs.

**Anti-Pattern**:

```python
# BAD: Shared cache ownership
class Maqet:
    def __init__(self):
        self._machines = {}  # Maqet owns cache
        self.cleanup_coordinator = CleanupCoordinator(self, self._machines)  # Shares cache

class CleanupCoordinator:
    def __init__(self, parent, machines_cache):
        self.machines_cache = machines_cache  # Modifies shared cache

    def cleanup(self):
        self.machines_cache.clear()  # Both classes modify same dict!
```

**Problems**:

- Unclear who owns the cache
- Two classes modifying same dictionary
- Hard to track cache mutations
- Difficult to test in isolation

### Solution: Single Owner with Accessors

**Current Pattern**:

```python
class VMManager:
    """Manager owns the cache."""

    def __init__(self, state_manager, config_parser):
        self._machines: Dict[str, Any] = {}  # VMManager owns this

    def get_machine_cache(self) -> Dict[str, Any]:
        """
        Get reference to machine instances cache.

        Returns:
            Dictionary mapping VM IDs to Machine instances

        Note:
            This provides read-only access for coordinators.
            Cache clearing operations should be done via VMManager methods.
        """
        return self._machines

    def clear_machine_cache(self, vm_id: Optional[str] = None) -> None:
        """
        Clear machine instances from cache.

        Args:
            vm_id: Specific VM ID to remove. If None, clears entire cache.
        """
        if vm_id is None:
            self._machines.clear()
            LOG.debug("Cleared all machine instances from cache")
        else:
            self._machines.pop(vm_id, None)
            LOG.debug(f"Removed machine instance {vm_id} from cache")


class CleanupCoordinator:
    """Coordinator uses accessor, doesn't own cache."""

    def __init__(self, vm_manager: VMManager):
        self.vm_manager = vm_manager  # No direct cache reference

    def cleanup_all(self):
        # Read-only access via accessor
        machines_cache = self.vm_manager.get_machine_cache()
        running_vms = [
            vm_id for vm_id, machine in machines_cache.items()
            if machine._qemu_machine and machine._qemu_machine.is_running()
        ]

        # Coordinate shutdown
        self._parallel_vm_shutdown(running_vms, timeout)

        # Clear cache via owner's method
        self.vm_manager.clear_machine_cache()
```

**Benefits**:

- Single owner (VMManager) for cache
- Clear responsibility boundaries
- Coordinators get read-only access
- Mutations go through owner's methods
- Easy to track who modifies cache

## Examples from Codebase

### Complete Manager Example: VMManager

```python
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

    def __init__(self, state_manager: StateManager, config_parser):
        """
        Initialize VM manager.

        Args:
            state_manager: State management instance
            config_parser: Configuration parser instance
        """
        self.state_manager = state_manager
        self.config_parser = config_parser
        self._machines: Dict[str, Any] = {}  # Owned cache
        LOG.debug("VMManager initialized")

    @handle_vm_errors("VM creation")
    def add(
        self,
        vm_config: Optional[Union[str, List[str]]] = None,
        name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Create a new VM from configuration.

        Args:
            vm_config: Path to YAML configuration file
            name: VM name (auto-generated if not provided)
            **kwargs: Additional VM configuration parameters

        Returns:
            VM instance ID

        Raises:
            VMLifecycleError: If VM creation fails
        """
        # Load and merge configuration
        if vm_config:
            config_data = ConfigMerger.load_and_merge_files(vm_config)
        else:
            config_data = {}

        # Validate configuration
        config_data = self.config_parser.validate_config(config_data)

        # Create VM in database
        vm_id = self.state_manager.create_vm(name, config_data)
        return vm_id
```

### Complete Coordinator Example: CleanupCoordinator

```python
class CleanupCoordinator:
    """
    Coordinates resource cleanup with parallel VM shutdown.

    Responsibilities:
    - Orchestrate parallel VM shutdown during cleanup
    - Manage timeout for cleanup operations
    - Handle errors during cleanup gracefully
    - Coordinate cache clearing via VMManager
    """

    def __init__(self, vm_manager: VMManager):
        """
        Initialize CleanupCoordinator.

        Args:
            vm_manager: VMManager instance for VM operations and cache access
        """
        self.vm_manager = vm_manager
        LOG.debug("CleanupCoordinator initialized")

    def cleanup_all(self, timeout: int = Timeouts.CLEANUP_VM_STOP) -> None:
        """
        Clean up all resources (stop running VMs, close connections).

        Uses ThreadPoolExecutor for parallel VM shutdown to reduce total
        cleanup time. Each VM gets individual timeout to prevent one
        stuck VM from blocking cleanup indefinitely.

        Args:
            timeout: Timeout in seconds for each VM stop operation
        """
        LOG.debug("Cleaning up MAQET resources...")

        # Get machine cache from VMManager (read-only access)
        machines_cache = self.vm_manager.get_machine_cache()

        # Identify running VMs
        running_vms = [
            vm_id for vm_id, machine in machines_cache.items()
            if machine._qemu_machine and machine._qemu_machine.is_running()
        ]

        if running_vms:
            LOG.info(f"Stopping {len(running_vms)} running VM(s) in parallel...")
            self._parallel_vm_shutdown(running_vms, timeout)

        # Clear machine cache via VMManager (ownership respected)
        self.vm_manager.clear_machine_cache()
        LOG.debug("MAQET cleanup completed")
```

## Best Practices

### DO: Inject Dependencies

```python
# GOOD: Dependencies are explicit
class QMPManager:
    def __init__(self, state_manager: StateManager, use_direct_socket: bool = False):
        self.state_manager = state_manager
        self.use_direct_socket = use_direct_socket
```

### DO: Use Error Decorators

```python
# GOOD: Decorator handles error translation
@handle_vm_errors("VM start")
def start(self, vm_id: str) -> VMInstance:
    # Business logic only, no try/except needed
    vm = self.state_manager.get_vm(vm_id)
    if not vm:
        raise VMLifecycleError(f"VM '{vm_id}' not found")
    return spawn_vm_runner(vm.id)
```

### DO: Single Responsibility

```python
# GOOD: VMManager focuses on VM lifecycle only
class VMManager:
    def add(self, vm_config, **kwargs) -> str:
        """VM creation - VMManager's job."""

    def start(self, vm_id: str) -> VMInstance:
        """VM start - VMManager's job."""

    # Does NOT include QMP operations - that's QMPManager's job
```

### DO: Clear Resource Ownership

```python
# GOOD: VMManager owns the cache, provides accessors
class VMManager:
    def __init__(self, state_manager, config_parser):
        self._machines: Dict[str, Any] = {}  # Clear owner

    def get_machine_cache(self) -> Dict[str, Any]:
        """Read-only access for coordinators."""
        return self._machines

    def clear_machine_cache(self, vm_id: Optional[str] = None):
        """Mutations go through owner."""
        if vm_id is None:
            self._machines.clear()
        else:
            self._machines.pop(vm_id, None)
```

### DO: Document Responsibilities

```python
# GOOD: Clear docstring listing responsibilities
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
```

## Common Anti-Patterns

### AVOID: Thin Wrappers

```python
# BAD: Manager that only delegates without adding value
class ConfigManager:
    def __init__(self, config_parser):
        self.config_parser = config_parser

    def validate(self, config_data):
        # Just delegates, adds no value
        return self.config_parser.validate_config(config_data)

    def load_and_merge(self, files):
        # Just delegates, adds no value
        return ConfigMerger.load_and_merge_files(files)
```

**Fix**: Remove the wrapper and use ConfigParser/ConfigMerger directly.

### AVOID: Circular Dependencies

```python
# BAD: Coordinator calls parent facade instead of manager
class CleanupCoordinator:
    def __init__(self, parent):
        self.parent = parent  # Reference to Maqet facade

    def cleanup(self):
        # Circular: Coordinator → Facade → VMManager
        self.parent.stop(vm_id)
```

**Fix**: Inject the manager directly:

```python
# GOOD: Direct dependency on manager
class CleanupCoordinator:
    def __init__(self, vm_manager: VMManager):
        self.vm_manager = vm_manager

    def cleanup(self):
        # Direct call, no circular dependency
        self.vm_manager.stop(vm_id)
```

### AVOID: Shared Mutable State

```python
# BAD: Multiple classes modifying same dictionary
class Maqet:
    def __init__(self):
        self._machines = {}
        self.cleanup_coordinator = CleanupCoordinator(self._machines)

    def remove(self, vm_id):
        self._machines.pop(vm_id)  # Maqet modifies

class CleanupCoordinator:
    def __init__(self, machines_cache):
        self.machines_cache = machines_cache

    def cleanup(self):
        self.machines_cache.clear()  # Coordinator modifies
```

**Fix**: Single owner with accessor methods (see Cache Ownership Pattern above).

### AVOID: Service Locator Pattern

```python
# BAD: Manager gets dependencies from global registry
class VMManager:
    def __init__(self):
        # Hidden dependencies - hard to test
        self.state_manager = ServiceRegistry.get('state_manager')
        self.config_parser = ServiceRegistry.get('config_parser')
```

**Fix**: Use constructor injection:

```python
# GOOD: Dependencies are explicit
class VMManager:
    def __init__(self, state_manager: StateManager, config_parser):
        self.state_manager = state_manager
        self.config_parser = config_parser
```

### AVOID: God Managers

```python
# BAD: Manager doing too much
class VMManager:
    def add(self, vm_config, **kwargs): ...
    def start(self, vm_id): ...
    def execute_qmp(self, vm_id, command): ...  # Should be QMPManager
    def create_snapshot(self, vm_id, name): ...  # Should be SnapshotCoordinator
    def cleanup_all(self): ...  # Should be CleanupCoordinator
```

**Fix**: Extract specialized managers for each domain.

## Testing Patterns

### Manager Unit Test Example

```python
import pytest
from unittest.mock import Mock
from maqet.managers.vm_manager import VMManager
from maqet.state import StateManager

def test_vm_manager_add():
    """Test VM creation with mocked dependencies."""
    # Arrange: Create mock dependencies
    mock_state = Mock(spec=StateManager)
    mock_config_parser = Mock()
    mock_config_parser.validate_config.return_value = {"binary": "qemu-system-x86_64"}

    vm_manager = VMManager(mock_state, mock_config_parser)

    # Act: Call manager method
    vm_id = vm_manager.add(vm_config="test.yaml", name="test-vm")

    # Assert: Verify behavior
    mock_config_parser.validate_config.assert_called_once()
    mock_state.create_vm.assert_called_once()
```

### Coordinator Unit Test Example

```python
def test_cleanup_coordinator_parallel_shutdown():
    """Test parallel VM shutdown coordination."""
    # Arrange: Create mock manager
    mock_vm_manager = Mock(spec=VMManager)
    mock_vm_manager.get_machine_cache.return_value = {
        "vm1": Mock(is_running=lambda: True),
        "vm2": Mock(is_running=lambda: True),
    }

    coordinator = CleanupCoordinator(mock_vm_manager)

    # Act: Call coordinator method
    coordinator.cleanup_all()

    # Assert: Verify coordination
    assert mock_vm_manager.stop.call_count == 2
    mock_vm_manager.clear_machine_cache.assert_called_once()
```

## Migration from God Object

If you're refactoring a god object into managers, follow this pattern:

### Step 1: Identify Domains

Group methods by domain (VM lifecycle, QMP, snapshots, etc.)

### Step 2: Extract Manager

```python
# Before: God object
class Maqet:
    def add(self, vm_config, **kwargs):
        config_data = ConfigMerger.load_and_merge_files(vm_config)
        return self.state_manager.create_vm(name, config_data)

    def start(self, vm_id):
        vm = self.state_manager.get_vm(vm_id)
        return spawn_vm_runner(vm.id)

# After: Extract VMManager
class VMManager:
    def __init__(self, state_manager, config_parser):
        self.state_manager = state_manager
        self.config_parser = config_parser

    def add(self, vm_config, **kwargs):
        config_data = ConfigMerger.load_and_merge_files(vm_config)
        return self.state_manager.create_vm(name, config_data)

    def start(self, vm_id):
        vm = self.state_manager.get_vm(vm_id)
        return spawn_vm_runner(vm.id)

# After: Facade delegates
class Maqet:
    def __init__(self):
        self.vm_manager = VMManager(self.state_manager, self.config_parser)

    def add(self, vm_config, **kwargs):
        return self.vm_manager.add(vm_config, **kwargs)

    def start(self, vm_id):
        return self.vm_manager.start(vm_id)
```

### Step 3: Update Tests

```python
# Before: Test god object
def test_add():
    maqet = Maqet()
    vm_id = maqet.add(vm_config="test.yaml")

# After: Test manager directly
def test_vm_manager_add():
    mock_state = Mock(spec=StateManager)
    mock_config = Mock()
    vm_manager = VMManager(mock_state, mock_config)
    vm_id = vm_manager.add(vm_config="test.yaml")
```

## References

- **Specification**: `specs/refactor-manager-architecture-issues.md` - Manager architecture decisions
- **Original Refactoring**: `specs/refactor-maqet-god-object.md` - God object extraction
- **Existing Managers**: `maqet/managers/` - Real implementations
- **Error Decorators**: `maqet/decorators.py` - Error handling system
- **Exception Hierarchy**: `maqet/exceptions.py` - Domain exceptions

---

**Version**: 1.0
**Date**: 2025-10-28
**Status**: Active Documentation
**Maintainer**: maqet core team
