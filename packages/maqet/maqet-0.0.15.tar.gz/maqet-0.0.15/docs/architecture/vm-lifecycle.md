# VM Lifecycle State Machine

**Document Version**: 1.0
**Last Updated**: 2025-10-15
**Status**: Production
**Related Specifications**: specs/fix-code-review-critical-issues-phase2.md (Issue #7, Task 3.2)

---

## Overview

Maqet manages virtual machines through a well-defined state machine with four distinct states: `created`, `running`, `stopped`, and `failed`. Each VM transitions through these states based on user operations and system events. This document describes the complete lifecycle, valid state transitions, recovery mechanisms for stale states, and implementation details.

The VM lifecycle is implemented across three core components:

- **StateManager** (`maqet/state.py`): Database persistence of VM state
- **VMManager** (`maqet/managers/vm_manager.py`): Lifecycle operation orchestration
- **VM Runner Process** (`maqet/vm_runner.py`): Per-VM QEMU management daemon

Understanding this state machine is critical for:

- Developers extending lifecycle operations
- Operators troubleshooting VM issues
- Testers validating state transitions

---

## States

### 1. created

**Definition**: VM is defined in the database with configuration but has never been started.

**Database Fields**:

```
status = "created"
pid = None
runner_pid = None
socket_path = None
auth_secret = <256-bit hex string>
```

**Valid Operations**:

- `start()` - Spawn VM runner process to start QEMU (transitions to `running`)
- `remove()` - Delete VM from database
- `apply()` - Update VM configuration

**Invalid Operations**:

- `stop()` - No-op, logs info message (VM not running)

**How to Enter This State**:

```bash
maqet add vm.yaml --name myvm
# or
maqet add --name empty-vm --empty  # VM without config
```

**Typical Use Cases**:

- Pre-configured VM templates ready to start
- Placeholder VMs waiting for configuration
- VMs that were stopped and can be restarted

---

### 2. running

**Definition**: VM is active with a VM runner process managing the QEMU instance. The runner process survives CLI exit and manages the QEMU lifecycle.

**Database Fields**:

```
status = "running"
pid = <QEMU process ID>
runner_pid = <VM runner process ID>
socket_path = "/run/user/<uid>/maqet/sockets/<vm_id>.sock"
auth_secret = <256-bit hex string>
```

**Valid Operations**:

- `stop()` - Gracefully shut down VM via IPC or kill runner (transitions to `stopped`)
- `remove(force=True)` - Force remove running VM (stops then deletes)
- IPC commands via socket (status, QMP commands, etc.)

**Invalid Operations**:

- `start()` - Raises `VMAlreadyRunningError` (VM already running)
- `remove()` without `force=True` - Raises error (must stop first or use `--force`)

**How to Enter This State**:

```bash
maqet start myvm
```

**Architecture Details**:

- **Runner Process**: Detached daemon spawned by `spawn_vm_runner()` in `process_spawner.py`
- **IPC Socket**: Unix domain socket for command/control (authenticated with per-VM secret)
- **QEMU Process**: Child process of runner, managed via QMP (QEMU Machine Protocol)
- **Process Relationship**: CLI -> Runner -> QEMU (CLI can exit, Runner persists)

**Implementation Reference**:

- Start workflow: `maqet/managers/vm_manager.py:206-298`
- Runner spawn: `maqet/process_spawner.py:spawn_vm_runner()`
- Socket creation: `maqet/process_spawner.py:get_socket_path()`

---

### 3. stopped

**Definition**: VM was previously running but is now stopped. Configuration remains in database, ready to restart.

**Database Fields**:

```
status = "stopped"
pid = None
runner_pid = None
socket_path = None
auth_secret = <preserved from creation>
```

**Valid Operations**:

- `start()` - Restart VM (transitions to `running`)
- `remove()` - Delete VM from database
- `apply()` - Update VM configuration

**Invalid Operations**:

- `stop()` - No-op, logs info message (already stopped)

**How to Enter This State**:

```bash
maqet stop myvm
# or automatic: runner crash, OOM kill, system shutdown
```

**Cleanup Behavior**:
When transitioning to `stopped`, the system automatically:

1. Clears `pid`, `runner_pid`, `socket_path` in database
2. Removes stale socket file (if exists)
3. Removes stale PID file (if exists)
4. Preserves `auth_secret` for future starts

**Implementation Reference**:

- Stop workflow: `maqet/managers/vm_manager.py:303-454`
- Cleanup: `maqet/state.py:718-776` (`cleanup_dead_processes()`)

---

### 4. failed

**Definition**: VM start operation failed or the VM crashed unexpectedly. Requires investigation before retry.

**Database Fields**:

```
status = "failed"
pid = None
runner_pid = None
socket_path = None
auth_secret = <preserved from creation>
```

**Valid Operations**:

- `start()` - Retry VM start (may succeed if transient issue)
- `remove()` - Delete failed VM from database
- `apply()` - Update configuration to fix issue

**Invalid Operations**:

- `stop()` - No-op, logs info message (VM not running)

**How to Enter This State**:

- QEMU binary not found
- Invalid configuration (missing required fields)
- Insufficient system resources (memory, disk space)
- QEMU startup failure (incompatible options)
- VM runner crash during startup

**Common Failure Causes**:

1. **Configuration Errors**: Missing `binary`, invalid storage paths
2. **Resource Exhaustion**: Out of memory, disk full
3. **Permission Denied**: Cannot access storage files, QEMU binary
4. **QEMU Errors**: Invalid arguments, unsupported features

**Recovery Actions**:

1. Check VM logs: `journalctl -u maqet` or runner process output
2. Validate configuration: `maqet show <vm_id>`
3. Fix configuration: `maqet apply <vm_id> fixed.yaml`
4. Retry start: `maqet start <vm_id>`
5. If unrecoverable: `maqet rm <vm_id>`

**Implementation Reference**:

- Failure detection: `maqet/managers/vm_manager.py:start()` exception handlers
- Status update: `maqet/state.py:615-685` (`update_vm_status()`)

---

## State Transition Diagram

```
                    +----------+
                    | created  |
                    +----------+
                         |
                         | start()
                         v
                    +----------+
              +---> | running  | <---+
              |     +----------+     |
              |          |           |
              |     stop()|          | start()
              |          v           | (retry)
              |     +----------+     |
              |     | stopped  |-----+
              |     +----------+
              |          |
              |     start() fails
              |          v
              |     +----------+
              +-----| failed   |
                    +----------+
                         |
                      remove()
                         v
                    [ DELETED ]
```

**Key Transition Rules**:

1. **created -> running**: Via `start()` - spawns runner process
2. **running -> stopped**: Via `stop()` or automatic (crash, OOM kill)
3. **running -> failed**: Via crash during operation (rare, usually goes to stopped)
4. **stopped -> running**: Via `start()` - restart VM
5. **failed -> running**: Via `start()` - retry after fixing issue
6. **Any state -> DELETED**: Via `remove()` or `remove(force=True)`

---

## Allowed Operations by State

| Operation         | created | running | stopped | failed |
|-------------------|---------|---------|---------|--------|
| `start()`         | OK      | ERROR   | OK      | OK     |
| `stop()`          | NO-OP   | OK      | NO-OP   | NO-OP  |
| `remove()`        | OK      | FORCE   | OK      | OK     |
| `apply()`         | OK      | ERROR   | OK      | OK     |
| `show()`          | OK      | OK      | OK      | OK     |
| IPC commands      | ERROR   | OK      | ERROR   | ERROR  |

**Legend**:

- **OK**: Operation allowed and will succeed
- **ERROR**: Operation rejected with exception
- **NO-OP**: Operation accepted but does nothing (logs info message)
- **FORCE**: Operation requires `--force` flag to proceed

**Error Types**:

- `VMAlreadyRunningError`: Attempting to start running VM
- `VMNotRunningError`: Attempting IPC command on non-running VM
- `VMManagerError`: Generic lifecycle operation failure

**Implementation Reference**:

- Operation validation: `maqet/managers/vm_manager.py` (each method's status checks)
- Exception types: `maqet/exceptions.py`

---

## Stale State Recovery

### Problem Statement

**Scenario**: VM runner process crashes (OOM kill, segfault, system reboot) leaving VM in `running` state in database, but no actual process exists.

**Impact**:

- User cannot start VM (thinks it's already running)
- Resources (sockets, PID files) left behind
- Process liveness checks return false positives

**Detection Windows**:

1. **Startup**: `VMManager.__init__()` calls `cleanup_dead_processes()`
2. **List Operation**: `list_vms()` verifies process liveness
3. **Start Operation**: `start()` checks runner alive before rejecting

### Detection Mechanisms

#### 1. Automatic Cleanup on Startup

**When**: VMManager instance creation (every CLI command, VM runner spawn)

**Implementation**: `maqet/state.py:718-776` (`cleanup_dead_processes()`)

**Algorithm**:

```python
def cleanup_dead_processes(self) -> List[str]:
    """
    1. Query all VMs with status='running'
    2. For each VM:
       a. Check if runner_pid process exists (os.kill(pid, 0))
       b. If dead:
          - Kill orphaned QEMU process (if PID exists and verified)
          - Update status to 'stopped'
          - Clear pid, runner_pid, socket_path
          - Remove stale socket file
          - Remove stale PID file
    3. Return list of cleaned VM IDs
    """
```

**Example Output**:

```
WARNING: VM 'ubuntu-vm' marked as running but runner process (PID: 12345) is dead
WARNING: Found orphaned QEMU process (PID 12346) for VM 'ubuntu-vm', terminating it
INFO: Cleaned up 1 dead VM(s): ubuntu-vm
```

#### 2. Liveness Check in list_vms()

**When**: User runs `maqet list`

**Implementation**: `maqet/managers/vm_manager.py:647-671`

**Algorithm**:

```python
def list_vms(self, status: Optional[str] = None) -> List[VMInstance]:
    """
    1. Get VMs from database
    2. For each VM with status='running':
       - Check if PID exists
       - If dead: Update status to 'stopped', clear PID
    3. Return updated VM list
    """
```

**User Experience**: Running VMs with dead processes automatically show as `stopped`

#### 3. Stale State Check in start()

**When**: User attempts to start VM that shows as `running`

**Implementation**: `maqet/managers/vm_manager.py:232-248`

**Algorithm**:

```python
if vm.status == "running":
    if vm.runner_pid and is_runner_alive(vm.runner_pid):
        raise VMAlreadyRunningError(...)
    else:
        # Stale state - clean up and continue
        LOG.warning("VM has stale 'running' status, cleaning up")
        update_vm_status(vm_id, "stopped", runner_pid=None, socket_path=None)
        # Continue with start operation
```

**User Experience**: Start succeeds even if database showed `running` (automatic recovery)

### Recovery Actions

#### Automatic Recovery (Recommended)

**Just restart the VMManager** (any CLI command triggers cleanup):

```bash
maqet list  # Triggers cleanup_dead_processes()
maqet start myvm  # Now works
```

#### Manual Recovery

**Force stop the VM** (even if already dead):

```bash
maqet stop myvm --force
```

This will:

1. Check if runner alive (no)
2. Check for orphaned QEMU process (kill if found with PID verification)
3. Update status to `stopped`
4. Clean up stale files

#### Nuclear Option (Database Reset)

**If automatic recovery fails** (rare):

```bash
# Backup first
cp ~/.local/share/maqet/instances.db instances.db.backup

# Manually update database
sqlite3 ~/.local/share/maqet/instances.db
UPDATE vm_instances SET status='stopped', pid=NULL, runner_pid=NULL, socket_path=NULL WHERE id='<vm_id>';
.quit
```

### Preventing Stale States

**Best Practices**:

1. Always use `maqet stop` (not `kill -9` on runner)
2. Let runner handle QEMU lifecycle (don't kill QEMU directly)
3. Ensure proper shutdown on system reboot (systemd unit for cleanup)
4. Monitor for OOM kills (`journalctl -k | grep -i oom`)

**Implementation Reference**:

- Process liveness check: `maqet/state.py:778-784` (`_is_process_alive()`)
- Runner liveness check: `maqet/process_spawner.py:is_runner_alive()`
- Cleanup on init: `maqet/state.py:242-260` (StateManager.**init**)

---

## Implementation Details

### start() Workflow

**File**: `maqet/managers/vm_manager.py:206-298`

**Step-by-Step Execution**:

1. **Get VM from Database** (line 227)

   ```python
   vm = self.state_manager.get_vm(vm_id)
   if not vm:
       raise VMManagerError(f"VM '{vm_id}' not found")
   ```

2. **Check Not Already Running** (lines 232-248)

   ```python
   if vm.status == "running":
       if vm.runner_pid and is_runner_alive(vm.runner_pid):
           raise VMManagerError("VM is already running")
       else:
           # Stale state - clean up and continue
           update_vm_status(vm_id, "stopped", runner_pid=None)
   ```

3. **Verify VM Has Configuration** (lines 251-256)

   ```python
   if not vm.config_data or not vm.config_data.get("binary"):
       raise VMManagerError("VM cannot be started: missing required configuration")
   ```

4. **Spawn VM Runner Process** (lines 269-272)

   ```python
   db_path = self.state_manager.xdg.database_path
   runner_pid = spawn_vm_runner(vm.id, db_path, timeout=Timeouts.PROCESS_SPAWN)
   LOG.info(f"Spawned VM runner process for '{vm_id}' (PID: {runner_pid})")
   ```

5. **Wait for Socket Ready** (lines 275-283)

   ```python
   socket_path = get_socket_path(vm.id)
   ready = wait_for_vm_ready(vm.id, socket_path, timeout=Timeouts.VM_START)
   if not ready:
       kill_runner(runner_pid, force=True)
       raise VMManagerError("VM runner did not become ready within timeout")
   ```

6. **Verify Status Updated to Running** (lines 286-290)

   ```python
   vm_updated = self.state_manager.get_vm(vm_id)
   if vm_updated.status != "running":
       raise VMManagerError(f"VM runner started but VM status is '{vm_updated.status}'")
   ```

7. **Audit Log & Return** (lines 293-298)

   ```python
   LOG.info(f"VM start: {vm_id} | runner_pid={runner_pid} | user={os.getenv('USER')}")
   return vm_updated
   ```

**Success Criteria**:

- Runner process spawned successfully
- Socket created and listening within timeout
- Database status updated to `running`
- VM runner PID and socket path recorded

**Failure Scenarios**:

- Runner spawn fails -> `VMManagerError`
- Socket not ready within timeout -> Kill runner, raise error
- Status not updated to `running` -> Raise error (runner failed internally)

---

### stop() Workflow

**File**: `maqet/managers/vm_manager.py:303-454`

**Step-by-Step Execution**:

1. **Get VM from Database** (line 328)

   ```python
   vm = self.state_manager.get_vm(vm_id)
   if not vm:
       raise VMManagerError(f"VM '{vm_id}' not found")
   ```

2. **Check if Running** (lines 333-341)

   ```python
   if vm.status != "running":
       LOG.info(f"VM '{vm_id}' is not running (status: {vm.status})")
       if vm.status != "stopped":
           update_vm_status(vm_id, "stopped", pid=None, runner_pid=None, socket_path=None)
       return vm
   ```

3. **Verify Runner Process Alive** (lines 347-393)

   ```python
   if not vm.runner_pid or not is_runner_alive(vm.runner_pid):
       # Runner missing/dead - check for orphaned QEMU
       if vm.pid:
           try:
               os.kill(vm.pid, 0)  # Check if QEMU alive
               # Kill orphaned QEMU (with PID verification in production)
               os.kill(vm.pid, 9 if force else 15)
           except ProcessLookupError:
               pass  # QEMU already dead
       # Clean up DB
       update_vm_status(vm_id, "stopped", pid=None, runner_pid=None, socket_path=None)
       return get_vm(vm_id)
   ```

4. **Try Graceful IPC Stop** (lines 396-415, if not force)

   ```python
   if not force:
       client = RunnerClient(vm.id, self.state_manager)
       try:
           result = client.send_command("stop", timeout=timeout)
           LOG.info(f"VM '{vm_id}' stopped gracefully via IPC")
           time.sleep(Intervals.CLEANUP_WAIT)
           return get_vm(vm_id)
       except RunnerClientError as e:
           LOG.warning(f"IPC stop failed: {e}, falling back to SIGTERM")
   ```

5. **Fallback: Kill Runner Process** (lines 423-451)

   ```python
   LOG.info(f"Killing VM runner for '{vm_id}' (PID: {vm.runner_pid}, force={force})")
   killed = kill_runner(vm.runner_pid, force=force)
   if killed:
       time.sleep(Intervals.CLEANUP_WAIT)
       vm_updated = get_vm(vm_id)
       if vm_updated.status == "running":
           # Runner didn't clean up - do it manually
           update_vm_status(vm_id, "stopped", runner_pid=None, socket_path=None)
       return get_vm(vm_id)
   else:
       raise VMManagerError(f"Failed to kill runner process {vm.runner_pid}")
   ```

**Success Criteria**:

- Runner process terminated (gracefully or forcefully)
- Database status updated to `stopped`
- PIDs and socket path cleared
- Orphaned QEMU process killed (if found)

**Stop Methods** (in order of preference):

1. **IPC Graceful**: Send stop command via socket (cleanest)
2. **SIGTERM**: Graceful signal to runner (allows cleanup)
3. **SIGKILL**: Force kill runner (immediate termination)

---

### cleanup_dead_processes() Workflow

**File**: `maqet/state.py:718-776` (StateManager class)

**Step-by-Step Execution**:

1. **List All Running VMs** (lines 732-733)

   ```python
   all_vms = self.list_vms()
   running_vms = [vm for vm in all_vms if vm.status == "running"]
   ```

2. **Check Each Running VM** (line 735)

   ```python
   for vm in running_vms:
       if not vm.runner_pid or not is_runner_alive(vm.runner_pid):
           # Runner is dead...
   ```

3. **Kill Orphaned QEMU Process** (lines 700-722)

   ```python
   if vm.pid:
       try:
           os.kill(vm.pid, 0)  # Check if QEMU alive
           LOG.warning(f"Found orphaned QEMU process (PID {vm.pid}), terminating it")
           os.kill(vm.pid, 9)  # SIGKILL
           time.sleep(0.5)
       except ProcessLookupError:
           pass  # QEMU already dead
   ```

4. **Update Database** (lines 724-727)

   ```python
   update_vm_status(vm.name, "stopped", pid=None, runner_pid=None, socket_path=None)
   cleaned.append(vm.id)
   ```

5. **Return Cleaned VM IDs** (line 730)

   ```python
   return cleaned
   ```

**When Executed**:

- Automatically on `StateManager.__init__()` (every CLI command)
- Can be called manually for testing/debugging

**Side Effects**:

- Updates database status to `stopped`
- Kills orphaned QEMU processes (with PID verification in production)
- No exception raised (cleanup is best-effort)

---

## Edge Cases

### 1. Concurrent Starts

**Scenario**: Two users run `maqet start vm1` simultaneously on the same host.

**Timeline**:

```
T0: User A: maqet start vm1 -> Check status (stopped) -> Continue
T1: User B: maqet start vm1 -> Check status (stopped) -> Continue
T2: User A: Spawn runner (PID 1001) -> Update DB (running)
T3: User B: Spawn runner (PID 1002) -> Check status -> ERROR (already running)
```

**Handling**:

- Second start detects `running` status in step 2 (line 232)
- Checks if runner process alive (yes, spawned by first user)
- Raises `VMAlreadyRunningError` with runner PID

**Code**: `maqet/managers/vm_manager.py:232-240`

**Outcome**: First start succeeds, second start fails cleanly with error message

**Race Window**: Small (milliseconds between spawn and DB update), but handled correctly

---

### 2. Crashed Runners

**Scenario**: VM runner process crashes (segfault, OOM kill, unhandled exception) while VM is running.

**Symptoms**:

- VM status shows `running` in database
- No runner process exists (PID invalid)
- QEMU process may be orphaned (still running without manager)
- Socket file may be stale

**Detection**:

1. **On Next CLI Command**: `cleanup_dead_processes()` finds dead runner
2. **On `maqet list`**: Process liveness check updates status
3. **On `maqet start`**: Stale state detection allows restart

**Recovery Actions** (automatic):

1. Detect runner PID is dead (`is_runner_alive()` returns False)
2. Check for orphaned QEMU process (verify PID with name/cmdline)
3. Kill QEMU if alive (SIGKILL for cleanup)
4. Update status to `stopped`
5. Clear PIDs and socket path
6. Remove stale socket/PID files

**Code**:

- Detection: `maqet/state.py:718-776` (cleanup_dead_processes)
- Recovery: `maqet/managers/vm_manager.py:347-393` (stop method, orphaned QEMU handling)

**User Experience**: Transparent recovery, VM can be restarted immediately

---

### 3. Orphaned QEMU Processes

**Scenario**: VM runner dies (killed, crash) but QEMU survives as orphaned process.

**Why This Happens**:

- Runner killed with SIGKILL before it can terminate QEMU
- Runner crash before cleanup handler executes
- System resource exhaustion (OOM killer targets runner, not QEMU)

**Detection**:

```python
if not is_runner_alive(vm.runner_pid) and vm.pid:
    try:
        os.kill(vm.pid, 0)  # Signal 0 checks existence
        # QEMU is alive but runner is dead -> orphaned
    except ProcessLookupError:
        # QEMU also dead
```

**Recovery** (automatic):

1. Verify PID is actually QEMU process (not reused PID):
   - Check process name contains "qemu" (psutil or /proc/PID/cmdline)
   - Check command line contains VM ID or name
   - Optional: Check process start time (not recently started)
2. Kill QEMU process: `os.kill(vm.pid, 9)` (SIGKILL)
3. Update status to `stopped`
4. Clear PIDs and socket path

**Security**: PID verification prevents killing wrong process if PID reused

**Code**:

- Detection: `maqet/managers/vm_manager.py:347-393` (stop method)
- PID verification: See specs/fix-code-review-critical-issues-phase2.md Issue #4

**User Impact**: VM shows as `stopped`, can be restarted, no manual cleanup needed

---

### 4. OOM-Killed Processes

**Scenario**: Linux OOM (Out-Of-Memory) killer terminates VM runner or QEMU due to memory pressure.

**Symptoms**:

- Process suddenly disappears (PID invalid)
- Kernel logs show OOM kill: `dmesg | grep -i oom` or `journalctl -k | grep -i oom`
- Example: `Out of memory: Killed process 12345 (vm_runner) total-vm:4GB`

**Detection**: Same as crashed runners (process liveness check returns False)

**Recovery**: Automatic via `cleanup_dead_processes()` (same as crashed runners)

**Prevention**:

1. Monitor system memory: `free -h`, `vmstat 1`
2. Configure VM memory limits appropriately (don't overcommit)
3. Set QEMU memory limits: `-m 2G` (enforced by config validation)
4. Use systemd memory limits for runner: `MemoryMax=4G` in unit file

**Investigation**:

```bash
# Check OOM kills in last hour
journalctl -k --since "1 hour ago" | grep -i oom

# Check which process was killed
dmesg | grep -i "killed process"

# Check current memory pressure
cat /proc/pressure/memory
```

**Code**: Same as crashed runners (no special OOM handling needed)

---

### 5. Stale Socket Files

**Scenario**: Socket file exists but runner process is dead.

**Why This Happens**:

- Runner killed before cleanup
- System crash/reboot
- Socket file left behind after cleanup failure

**Detection**: Runner liveness check, not socket existence

**Behavior**:

- `cleanup_dead_processes()` removes stale sockets (lines 746-755 in state.py)
- Next runner start overwrites socket file (socket.bind() replaces file)

**No User Impact**: Socket cleanup is automatic, doesn't block operations

**Code**:

```python
# In cleanup_dead_processes()
socket_path = self.get_socket_path(vm.id)
if socket_path.exists():
    try:
        socket_path.unlink()
        LOG.debug(f"Removed stale socket: {socket_path}")
    except OSError as e:
        LOG.warning(f"Failed to remove stale socket: {e}")
```

**Manual Cleanup** (if needed):

```bash
rm -f /run/user/$(id -u)/maqet/sockets/*.sock
```

---

### 6. PID Reuse Vulnerability (MITIGATED)

**Scenario**: Process PID recorded in database gets reused by another process after QEMU dies.

**Attack Timeline**:

1. VM QEMU runs as PID 12345
2. QEMU crashes/exits
3. Kernel reuses PID 12345 for unrelated process (e.g., user's Firefox)
4. User runs `maqet stop vm1 --force`
5. Without verification: Firefox killed (wrong process!)

**Mitigation** (Issue #4 in Phase 2 spec):

```python
# Verify PID is actually QEMU before killing
if PSUTIL_AVAILABLE:
    process = psutil.Process(vm.pid)

    # Check 1: Process name contains "qemu"
    if "qemu" not in process.name().lower():
        raise VMManagerError("PID is not a QEMU process. Possible PID reuse.")

    # Check 2: Command line contains VM ID
    cmdline = " ".join(process.cmdline())
    if vm_id not in cmdline and vm.name not in cmdline:
        raise VMManagerError("PID does not match VM identifier.")

    # Check 3: Process start time (optional)
    if time.time() - process.create_time() < 1.0:
        LOG.warning("PID was created very recently. Possible reuse, but name/cmdline match.")
```

**Fallback** (without psutil):

```python
# Read /proc/PID/cmdline
with open(f"/proc/{vm.pid}/cmdline", "rb") as f:
    cmdline = f.read().decode("utf-8")
    if "qemu" not in cmdline.lower():
        raise VMManagerError("PID is not QEMU. NOT killing.")
    if vm_id not in cmdline:
        raise VMManagerError("PID does not match VM. NOT killing.")
```

**Status**: Implemented in Phase 2 (see specs/fix-code-review-critical-issues-phase2.md)

**Code**: `maqet/managers/vm_manager.py:stop()` and `cleanup_dead_processes()`

---

## Thread Safety

### WARNING: VMManager is NOT Thread-Safe

**Current Architecture**:

- SQLite database has timeout-based locking (5 seconds)
- No application-level locking around VM operations
- Multiple VMManager instances can access database concurrently

**Safe Usage Patterns**:

```python
# SAFE: One VMManager per thread, short-lived operations
def worker_thread():
    manager = VMManager(state_manager, config_parser)
    manager.start("vm1")

# UNSAFE: Shared VMManager across threads
manager = VMManager(...)
Thread(target=lambda: manager.start("vm1")).start()
Thread(target=lambda: manager.stop("vm1")).start()  # Race condition!
```

**Known Race Conditions**:

1. **Concurrent start()**: Second start may race with first's DB update
   - **Mitigation**: status check in start() catches this (raises error)
2. **Concurrent stop()**: Multiple stops may attempt to kill same process
   - **Mitigation**: kill_runner() handles ProcessLookupError gracefully
3. **Database lock contention**: SQLite may return "database is locked"
   - **Mitigation**: Retry logic with exponential backoff (5 attempts, 5s total)

**Recommendation**:

- Use separate VMManager instances per thread
- Do not share VMManager across threads
- For concurrent operations, use process-level isolation (separate maqet CLI invocations)

**Future Work**:

- Add thread-safe database wrapper with connection pooling
- Implement per-VM operation locks (fcntl-based or SQLite application_id)
- Consider switching to PostgreSQL for production (better concurrency)

**Reference**: specs/fix-code-review-critical-issues-phase2.md discusses thread-safety fixes

---

## Testing State Transitions

### Unit Test Examples

#### Test 1: created -> running

```python
def test_vm_lifecycle_created_to_running():
    """Test VM starts successfully from created state."""
    # Create VM
    vm_id = manager.add(vm_config="vm.yaml", name="test-vm")
    vm = state_manager.get_vm(vm_id)

    # Verify initial state
    assert vm.status == "created"
    assert vm.pid is None
    assert vm.runner_pid is None
    assert vm.socket_path is None

    # Start VM
    vm_updated = manager.start(vm_id)

    # Verify running state
    assert vm_updated.status == "running"
    assert vm_updated.pid is not None
    assert vm_updated.runner_pid is not None
    assert vm_updated.socket_path is not None

    # Verify processes are alive
    assert is_runner_alive(vm_updated.runner_pid)
    assert os.path.exists(vm_updated.socket_path)
```

#### Test 2: running -> stopped

```python
def test_vm_lifecycle_running_to_stopped():
    """Test VM stops successfully from running state."""
    # Setup: Start VM
    vm_id = manager.add(vm_config="vm.yaml", name="test-vm")
    manager.start(vm_id)

    # Stop VM
    vm_stopped = manager.stop(vm_id)

    # Verify stopped state
    assert vm_stopped.status == "stopped"
    assert vm_stopped.pid is None
    assert vm_stopped.runner_pid is None
    assert vm_stopped.socket_path is None

    # Verify cleanup
    assert not os.path.exists(state_manager.get_socket_path(vm_id))
    assert not os.path.exists(state_manager.get_pid_path(vm_id))
```

#### Test 3: Stale state recovery

```python
def test_stale_state_recovery():
    """Test automatic recovery from stale running state."""
    # Setup: Start VM
    vm_id = manager.add(vm_config="vm.yaml", name="test-vm")
    vm = manager.start(vm_id)

    # Simulate crash: Kill runner without cleanup
    os.kill(vm.runner_pid, 9)  # SIGKILL (no cleanup)
    time.sleep(0.5)

    # VM still shows as running in DB (stale state)
    vm_stale = state_manager.get_vm(vm_id)
    assert vm_stale.status == "running"

    # Create new VMManager (triggers cleanup)
    new_manager = VMManager(state_manager, config_parser)

    # Stale state should be cleaned automatically
    vm_cleaned = state_manager.get_vm(vm_id)
    assert vm_cleaned.status == "stopped"
    assert vm_cleaned.runner_pid is None
```

#### Test 4: Concurrent start rejection

```python
def test_concurrent_start_rejection():
    """Test that concurrent starts are rejected."""
    vm_id = manager.add(vm_config="vm.yaml", name="test-vm")

    # Start VM
    manager.start(vm_id)

    # Attempt second start
    with pytest.raises(VMManagerError) as exc_info:
        manager.start(vm_id)

    assert "already running" in str(exc_info.value).lower()
```

#### Test 5: Orphaned QEMU cleanup

```python
def test_orphaned_qemu_cleanup():
    """Test cleanup of orphaned QEMU process."""
    # Setup: Start VM
    vm_id = manager.add(vm_config="vm.yaml", name="test-vm")
    vm = manager.start(vm_id)

    # Kill runner but leave QEMU alive (simulate orphaned QEMU)
    os.kill(vm.runner_pid, 9)
    time.sleep(0.5)

    # Verify QEMU still alive
    try:
        os.kill(vm.pid, 0)
        qemu_alive = True
    except ProcessLookupError:
        qemu_alive = False

    assert qemu_alive, "QEMU should still be alive after runner killed"

    # Run cleanup
    cleaned = state_manager.cleanup_dead_processes()

    # Verify QEMU killed
    try:
        os.kill(vm.pid, 0)
        qemu_alive = True
    except ProcessLookupError:
        qemu_alive = False

    assert not qemu_alive, "Orphaned QEMU should be killed"
    assert vm_id in cleaned
```

### Integration Test Scenarios

```python
def test_full_lifecycle_integration():
    """Test complete VM lifecycle: create -> start -> stop -> restart -> remove."""
    # Create
    vm_id = manager.add(vm_config="vm.yaml", name="integration-test")
    assert state_manager.get_vm(vm_id).status == "created"

    # Start
    manager.start(vm_id)
    assert state_manager.get_vm(vm_id).status == "running"

    # Stop
    manager.stop(vm_id)
    assert state_manager.get_vm(vm_id).status == "stopped"

    # Restart
    manager.start(vm_id)
    assert state_manager.get_vm(vm_id).status == "running"

    # Remove (force)
    manager.remove(vm_id, force=True)
    assert state_manager.get_vm(vm_id) is None
```

### Test Fixtures

```python
@pytest.fixture
def vm_manager(tmp_path):
    """Create VMManager with isolated test database."""
    state_manager = StateManager(custom_data_dir=str(tmp_path / "data"))
    config_parser = ConfigParser()
    return VMManager(state_manager, config_parser)

@pytest.fixture
def running_vm(vm_manager):
    """Create and start a test VM."""
    vm_id = vm_manager.add(vm_config="tests/fixtures/minimal-vm.yaml")
    vm_manager.start(vm_id)
    yield vm_id
    # Cleanup
    try:
        vm_manager.stop(vm_id, force=True)
        vm_manager.remove(vm_id)
    except:
        pass
```

**Test File Location**: `tests/unit/managers/test_vm_lifecycle.py`

**Coverage Target**: 90%+ for lifecycle-related code

---

## Troubleshooting Guide

### VM Stuck in "running" State

**Symptoms**: `maqet list` shows VM as running but it's not responding

**Diagnosis**:

```bash
# Check if runner process exists
ps aux | grep -i "vm_runner.*<vm_id>"

# Check if socket exists
ls -la /run/user/$(id -u)/maqet/sockets/<vm_id>.sock

# Try connecting to socket
nc -U /run/user/$(id -u)/maqet/sockets/<vm_id>.sock
```

**Solutions**:

1. **Automatic recovery**: Just run any command (triggers cleanup)

   ```bash
   maqet list  # Triggers cleanup_dead_processes()
   ```

2. **Force stop**:

   ```bash
   maqet stop <vm_id> --force
   ```

3. **Manual database update** (last resort):

   ```bash
   sqlite3 ~/.local/share/maqet/instances.db
   UPDATE vm_instances SET status='stopped', pid=NULL, runner_pid=NULL, socket_path=NULL WHERE id='<vm_id>';
   ```

### VM Won't Start (Already Running Error)

**Symptoms**: `maqet start vm1` fails with "already running" but `ps` shows no process

**Cause**: Stale database state

**Solution**: Automatic stale state detection handles this (start should succeed on retry)

**Manual Workaround**:

```bash
maqet stop vm1  # Updates status even if not actually running
maqet start vm1  # Now works
```

### Orphaned QEMU Process

**Symptoms**: `ps aux | grep qemu` shows QEMU process but `maqet list` shows VM as stopped

**Diagnosis**:

```bash
# Find orphaned QEMU
ps aux | grep qemu

# Check if it matches a VM
cat /proc/<qemu_pid>/cmdline | grep -o "vm-[a-f0-9-]*"
```

**Solution**: Automatic cleanup on next VMManager init, or manual:

```bash
# Verify it's safe to kill (check PID and cmdline)
cat /proc/<pid>/cmdline

# Kill if confirmed it's orphaned QEMU
kill -9 <pid>
```

### Database Locked Errors

**Symptoms**: `StateError: Database locked after 5 attempts`

**Causes**:

- Multiple concurrent maqet commands
- Long-running SQLite transaction
- NFS/network filesystem issues (SQLite doesn't work well on NFS)

**Solutions**:

1. **Wait and retry**: Usually resolves in seconds
2. **Check for hung processes**:

   ```bash
   lsof ~/.local/share/maqet/instances.db
   ```

3. **Kill hung processes** (if found)
4. **Move database to local filesystem** (if on NFS):

   ```bash
   export XDG_DATA_HOME=/tmp/maqet-data
   maqet list  # Uses /tmp database
   ```

---

## Changelog

### Version 1.0 (2025-10-15)

- Initial documentation release
- Covers 4-state lifecycle (created, running, stopped, failed)
- Documents stale state recovery mechanisms
- Includes implementation details and code references
- Adds troubleshooting guide and test examples

---

## References

### Internal Documentation

- **Phase 2 Specification**: `/mnt/internal/git/m4x0n/the-linux-project/maqet/specs/fix-code-review-critical-issues-phase2.md`
- **Code Review Report**: `docs/reports/CODE_REVIEW_ISSUES_2025-10-15.md`

### Source Code Files

- **VMManager**: `maqet/managers/vm_manager.py` (lifecycle operations)
- **StateManager**: `maqet/state.py` (database persistence)
- **VMInstance**: `maqet/state.py:97-112` (dataclass definition)
- **Process Spawner**: `maqet/process_spawner.py` (runner process management)
- **IPC Client**: `maqet/ipc/runner_client.py` (socket communication)
- **VM Runner**: `maqet/vm_runner.py` (per-VM daemon)

### Related Topics

- **Thread Safety**: See "Thread Safety" section above
- **PID Reuse Security**: specs/fix-code-review-critical-issues-phase2.md Issue #4
- **Socket Authentication**: specs/fix-code-review-critical-issues-phase2.md Issue #3
- **Database Migration**: `maqet/state.py:91-94` (MIGRATIONS registry)

---

**Document Maintainer**: Development Team
**Review Cycle**: Update on major lifecycle changes
**Feedback**: Report issues via project issue tracker
