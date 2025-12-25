# Maqet Layered Architecture

## Overview

Maqet implements a **5-layer clean architecture** designed to eliminate circular dependencies, enforce clear separation of concerns, and enable independent testing of components.

The architecture follows the **Dependency Inversion Principle**: upper layers depend on lower layers through protocol interfaces, never the reverse.

---

## Layer Diagram

```
+--------------------------------------------------+
|              PRESENTATION LAYER                  |
|     CLI Commands    |    Python API              |
|    (entry points)   |    (@api_method)           |
+--------------------------------------------------+
                          |
              (depends on facade)
                          |
+--------------------------------------------------+
|                 FACADE LAYER                     |
|              Maqet Class                         |
|   - Composition root (all DI wiring)             |
|   - API registry for CLI/Python generation       |
+--------------------------------------------------+
                          |
          (depends on managers)
                          |
+--------------------------------------------------+
|            BUSINESS LOGIC LAYER                  |
|   VMManager | QMPManager | ConfigManager        |
|                                                  |
|   Coordinates operations between domain         |
|   services and state management                 |
+--------------------------------------------------+
                          |
          (depends on services)
                          |
+--------------------------------------------------+
|             DOMAIN SERVICES LAYER                |
|   StorageManager | SnapshotManager              |
|   WaitConditions | ProcessSpawner               |
|   VMLifecycleManager | ProcessVerifier          |
|                                                  |
|   Business logic for specific domains           |
|   without knowledge of state persistence        |
+--------------------------------------------------+
                          |
         (depends on infrastructure)
                          |
+--------------------------------------------------+
|          INFRASTRUCTURE LAYER                    |
|   StateManager | ProcessLifecycleManager        |
|   ConfigMerger | XDGPathResolver                |
|                                                  |
|   Database, file I/O, OS interactions           |
|   No dependencies on upper layers               |
+--------------------------------------------------+
```

---

## Dependency Rules

These rules are **enforced** by architectural tests and code review:

1. **Unidirectional Dependencies**: Upper layers depend on lower layers only
   - Business Logic depends on Domain Services
   - Domain Services depend on Infrastructure
   - Infrastructure depends on nothing (only stdlib/3rd-party)

2. **Protocol-Based Integration**: Cross-layer dependencies use Protocol interfaces
   - Never import concrete classes from lower layers in upper layers
   - Always use protocols defined in `maqet/protocols/`
   - Concrete implementation wiring happens in Maqet composition root only

3. **No Inline Imports**: Circular dependencies are forbidden
   - All imports must be module-level (top of file)
   - No imports inside functions/methods
   - Architectural tests verify this

4. **Single Composition Root**: All dependency wiring in `Maqet.__init__`
   - No global state or singletons
   - No implicit dependencies
   - Dependencies flow top-down from composition root

---

## Layers Explained

### 1. Infrastructure Layer
**Location**: `maqet/state/`, `maqet/managers/config_manager.py`, `maqet/utils/`

**Responsibility**: Database, file I/O, OS operations

**Key Components**:
- `StateManager`: SQLite VM database, repository pattern
- `ProcessLifecycleManager`: Process monitoring and cleanup
- `ConfigMerger`: YAML configuration merging
- `XDGPathResolver`: XDG Base Directory Specification

**Dependency Constraints**:
- No imports from upper layers
- Uses only stdlib and third-party libraries
- Provides concrete implementations

**When to Add**: When you need database queries, file operations, or OS interactions

### 2. Domain Services Layer
**Location**: `maqet/` (most modules at this level)

**Responsibility**: Business logic for specific domains, independent of storage

**Key Components**:
- `StorageManager`: VM disk image management
- `SnapshotManager`: Snapshot creation and lifecycle
- `VMLifecycleManager`: VM state transitions
- `ProcessSpawner`: VM runner process spawning
- `ProcessVerifier`: Process status verification
- `WaitConditions`: QMP-based wait conditions

**Dependency Constraints**:
- Depends on infrastructure through protocols
- Does NOT directly instantiate infrastructure classes
- Receives dependencies via constructor injection
- Can depend on other domain services

**When to Add**: When you need specific business logic that doesn't fit managers

**Example**:
```python
# Domain service - receives dependencies, doesn't create them
class StorageManager:
    def __init__(self, state: StateProtocol):
        self._state = state  # Protocol interface, not concrete
```

### 3. Business Logic Layer
**Location**: `maqet/managers/`

**Responsibility**: Coordinate between multiple domain services and state management

**Key Components**:
- `VMManager`: VM lifecycle operations (add, start, stop, rm, ls)
- `QMPManager`: QMP command execution and live snapshots
- `ConfigManager`: Configuration directory resolution (deprecated, use infrastructure directly)

**Dependency Constraints**:
- Depends on domain services and infrastructure
- Coordinates multiple operations
- Delegates to specialized managers
- Receives all dependencies via constructor

**When to Add**: When you need to coordinate multiple domain services

**Example**:
```python
# Manager - coordinates multiple services
class VMManager:
    def __init__(
        self,
        state_manager: StateManager,
        storage_manager: StorageManager,
        process_spawner: ProcessSpawner,
    ):
        self.state = state_manager
        self.storage = storage_manager
        self.spawner = process_spawner
```

### 4. Facade Layer
**Location**: `maqet/maqet.py`

**Responsibility**: Unified API, dependency wiring (composition root)

**Key Component**:
- `Maqet`: Main class implementing unified VM management

**Responsibilities**:
1. Define public API methods (decorated with `@api_method`)
2. Delegate to appropriate managers
3. **Composition Root**: Create and wire all dependencies in `__init__`

**Key Principle**: This is the ONLY place that knows about concrete implementations.
All other classes work with protocols.

**Example**:
```python
class Maqet(AutoRegisterAPI):
    def __init__(self, **kwargs):
        # === COMPOSITION ROOT ===
        # Infrastructure layer (no dependencies)
        state = StateManager(...)
        process_verifier = ProcessVerifier()
        
        # Domain services (depend on infrastructure)
        storage_mgr = StorageManager(state_manager=state)
        spawner = ProcessSpawner(process_verifier=process_verifier)
        
        # Business logic (depends on services)
        self._vm_manager = VMManager(
            state_manager=state,
            storage_manager=storage_mgr,
            process_spawner=spawner,
        )
```

### 5. Presentation Layer
**Location**: `maqet/cli.py`, `maqet/generators.py`

**Responsibility**: CLI commands and Python API generation

**Key Components**:
- `CLIGenerator`: Generates CLI from `@api_method` decorators
- `PythonAPIGenerator`: Generates Python API reference docs
- CLI entry point: calls Maqet methods via Python API

**Dependency Constraints**:
- Depends only on Maqet facade
- No direct manager access
- Delegates all operations to Maqet

---

## Protocol Interfaces

Protocols enable dependency inversion without external DI frameworks.

### Available Protocols

Located in `maqet/protocols/`:

#### StateProtocol
**File**: `maqet/protocols/state.py`

Combines VM repository and path resolver operations.

```python
from maqet.protocols import StateProtocol

class MyService:
    def __init__(self, state: StateProtocol):
        vm = state.get_vm("vm-name")
        path = state.get_vm_socket_path("vm-name")
```

**Methods**:
- `get_vm(name) -> Optional[VMInstance]`
- `list_vms(status=None) -> List[VMInstance]`
- `update_vm(name, **fields) -> VMInstance`
- `exists(name) -> bool`
- `get_vm_socket_path(vm_name) -> Path`
- `get_vm_storage_dir(vm_name) -> Path`
- `get_runtime_dir() -> Path`

#### ProcessProtocol
**File**: `maqet/protocols/process.py`

Process lifecycle operations.

```python
from maqet.protocols import ProcessProtocol

class MyService:
    def __init__(self, process: ProcessProtocol):
        if process.is_alive(pid):
            process.verify_or_raise(pid, "runner")
            process.wait_for_exit(pid, timeout=30)
```

**Methods**:
- `is_alive(pid: int) -> bool`
- `verify_or_raise(pid: int, process_type: str) -> None`
- `wait_for_exit(pid: int, timeout: float) -> bool`

#### ProcessSpawnerProtocol
**File**: `maqet/protocols/process.py`

Spawning VM runner processes.

```python
from maqet.protocols import ProcessSpawnerProtocol

class MyService:
    def __init__(self, spawner: ProcessSpawnerProtocol):
        pid = spawner.spawn_vm_runner("vm-name", "/path/config", Path("/socket"))
```

**Methods**:
- `spawn_vm_runner(vm_name, config_path, socket_path) -> int`

#### IPCClientProtocol
**File**: `maqet/protocols/ipc.py`

IPC communication with runner processes.

```python
from maqet.protocols import IPCClientProtocol

class MyService:
    def __init__(self, client_factory: Callable[[str], IPCClientProtocol]):
        client = client_factory("vm-name")
        result = client.send_command("query-status")
```

**Methods**:
- `connect() -> None`
- `disconnect() -> None`
- `send_command(command, **kwargs) -> Dict[str, Any]`
- `get_status() -> Dict[str, Any]`

#### StorageRegistryProtocol
**File**: `maqet/protocols/storage.py`

VM storage file management.

```python
from maqet.protocols import StorageRegistryProtocol

class MyService:
    def __init__(self, storage: StorageRegistryProtocol):
        storage.register_storage("vm-name", Path("/path/to/disk"))
        files = storage.get_storage_files("vm-name")
```

**Methods**:
- `register_storage(vm_name, path) -> None`
- `get_storage_files(vm_name) -> List[Path]`
- `cleanup_storage(vm_name) -> None`

---

## Composition Root Pattern

The Maqet class serves as the **composition root** - the single place where all dependencies are wired together.

### Why Composition Root?

1. **Single Responsibility**: One place to understand all dependencies
2. **Easy Testing**: Mock dependencies in tests by creating Maqet with test doubles
3. **No Global State**: All instances created explicitly
4. **Pythonic**: No external DI container framework needed

### Structure

```python
class Maqet(AutoRegisterAPI):
    def __init__(self, data_dir=None, config_dir=None, ...):
        # === COMPOSITION ROOT ===
        # Build dependency graph bottom-up
        
        # Layer 1: Infrastructure (no dependencies)
        config_mgr = ConfigManager(...)
        process_verifier = ProcessVerifier()
        
        # Layer 2: State (depends on infrastructure)
        state_mgr = StateManager(
            data_dir=data_dir,
            config_manager=config_mgr
        )
        
        # Layer 3: Domain Services (depend on infrastructure)
        storage_mgr = StorageManager(
            state_repository=state_mgr  # Via protocol
        )
        
        process_spawner = ProcessSpawner(
            process_verifier=process_verifier,
            client_factory=lambda name: RunnerClient(name),
        )
        
        # Layer 4: Business Logic (depend on domain services)
        self._vm_manager = VMManager(
            state_manager=state_mgr,
            storage_manager=storage_mgr,
            process_spawner=process_spawner,
        )
        
        self._qmp_manager = QMPManager(
            state_manager=state_mgr,
            process_verifier=process_verifier,
        )
        
        # === END COMPOSITION ROOT ===
        # All instances are now ready to use
```

### Key Points

1. **Bottom-Up Construction**: Build layers from infrastructure up
2. **Explicit Dependencies**: Every dependency visible in code
3. **No Singletons**: Each instance is created once and passed around
4. **Testability**: Easy to swap with mocks in tests

---

## Import Guidelines

### Correct Imports (By Layer)

**Infrastructure Layer** - imports stdlib and third-party only:
```python
# maqet/state/state_manager.py
import sqlite3
from pathlib import Path
from typing import Optional

# No imports from upper layers
```

**Domain Services Layer** - imports infrastructure via protocols:
```python
# maqet/storage.py
from maqet.protocols import StateProtocol  # Protocol interface

class StorageManager:
    def __init__(self, state: StateProtocol):
        # Depends on protocol, not concrete StateManager
        self._state = state
```

**Business Logic Layer** - imports domain services directly:
```python
# maqet/managers/vm_manager.py
from maqet.storage import StorageManager
from maqet.process_spawner import ProcessSpawner

class VMManager:
    def __init__(self, storage_manager: StorageManager, ...):
        self.storage = storage_manager
```

**Facade Layer** - imports managers directly (composition root):
```python
# maqet/maqet.py
from maqet.managers import VMManager, QMPManager
from maqet.state import StateManager

class Maqet(AutoRegisterAPI):
    def __init__(self):
        # Only place that imports concrete implementations
        self._state = StateManager(...)
        self._vm_mgr = VMManager(...)
```

### Incorrect Imports (What to Avoid)

**Never**: Upper layer imports lower layer concrete classes directly
```python
# WRONG - circular dependency risk
class StorageManager:
    def __init__(self):
        from maqet.state import StateManager  # Inline import!
        self._state = StateManager()  # Direct instantiation!
```

**Never**: Lower layer imports upper layer
```python
# WRONG - dependency inversion violation
class StateManager:
    def __init__(self):
        from maqet.managers import VMManager  # Lower layer importing upper!
```

**Never**: Domain service creates its own dependencies
```python
# WRONG - no dependency injection
class ProcessSpawner:
    def spawn(self):
        from maqet.ipc import RunnerClient  # Should be injected!
        client = RunnerClient()
```

---

## Testing Patterns

### Unit Testing (Mock Dependencies)

```python
from unittest.mock import Mock
from maqet.managers import VMManager

def test_vm_manager_lists_vms():
    # Create mock for protocol interface
    mock_state = Mock()
    mock_state.list_vms.return_value = [...]
    
    # Inject mock into manager
    manager = VMManager(
        state_manager=mock_state,
        storage_manager=Mock(),
        process_spawner=Mock(),
    )
    
    # Test uses mocked dependencies
    vms = manager.list()
    mock_state.list_vms.assert_called_once()
```

### Integration Testing (Real Dependencies)

```python
from maqet.state import StateManager
from maqet.managers import VMManager

def test_vm_manager_with_real_state(tmp_path):
    # Real infrastructure
    state = StateManager(data_dir=tmp_path)
    
    # Manager with real state
    manager = VMManager(
        state_manager=state,
        storage_manager=Mock(),
        process_spawner=Mock(),
    )
    
    # Test with real state operations
    manager.add("vm1", config={...})
    assert state.get_vm("vm1") is not None
```

---

## Enforcing Architecture

### Architectural Tests

Located in `tests/architecture/test_import_rules.py`

Verifies:
- No inline imports within functions
- Proper layer boundaries respected
- No forbidden cross-layer imports

Run before committing:
```bash
pytest tests/architecture/ -v
```

### Code Review Checklist

When reviewing changes:

1. **Import Check**: Are all imports at module level (not inside functions)?
2. **Protocol Check**: Do cross-layer dependencies use protocols?
3. **Layer Check**: Is the file in the correct layer for its responsibility?
4. **Dependency Check**: Does it depend only on same layer or lower?
5. **Composition Check**: Is dependency wiring in Maqet.__init__, not elsewhere?

---

## Migration from Non-Layered Code

If you're refactoring existing code:

### Step 1: Identify Layer
```
Ask: What is this class's primary responsibility?
- Database/file I/O? -> Infrastructure
- OS/process operations? -> Infrastructure
- Domain logic? -> Domain Services
- Orchestrating multiple services? -> Business Logic
- Public API? -> Facade
```

### Step 2: Check Dependencies
```
Ask: What does it depend on?
- Only stdlib/third-party? -> Infrastructure ok
- Infrastructure layers? -> Domain Services ok
- Domain services? -> Business Logic ok
- Managers? -> Facade only
```

### Step 3: Extract to Protocol
```python
# Before: Direct import
class MyService:
    def __init__(self):
        from maqet.state import StateManager
        self._state = StateManager()

# After: Dependency injection via protocol
class MyService:
    def __init__(self, state: StateProtocol):
        self._state = state  # Protocol interface
```

### Step 4: Wire in Composition Root
```python
# In Maqet.__init__:
my_service = MyService(state_manager=state)  # Pass real instance
```

---

## Summary

- **5 layers**: Infrastructure → Domain Services → Business Logic → Facade → Presentation
- **One direction**: Upper layers depend on lower, never reverse
- **Protocols**: Cross-layer dependencies use protocol interfaces
- **One composition root**: All DI wiring in Maqet.__init__
- **No inline imports**: All dependencies injected via constructor
- **Testable**: Easy to mock and test components in isolation

This architecture keeps maqet maintainable, testable, and ready for growth.
