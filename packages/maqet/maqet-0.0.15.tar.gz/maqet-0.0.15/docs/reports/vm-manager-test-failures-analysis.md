# VM Manager Test Failures Analysis

**Date**: 2025-12-08
**Analyst**: Claude Code
**Test Suite**: VM Manager Unit Tests
**Scope**: tests/unit/managers/test_vm_manager.py, tests/unit/managers/test_vm_manager_concurrency.py

## Executive Summary

- **Total failures**: 5 tests (updated from initial 4 count)
- **Files affected**: 1 (test_vm_manager.py only)
- **Common patterns identified**: 1 root cause with 2 manifestations
- **Root cause**: File lock mechanism not properly mocked in test environment

**Key Finding**: The concurrency test suite (test_vm_manager_concurrency.py) passed all 8 tests. All failures are concentrated in the basic VM manager tests, specifically around file lock acquisition that was added for the per-VM architecture.

## Test Results Summary

### test_vm_manager.py
- **Total tests**: 30
- **Passed**: 25
- **Failed**: 5

### test_vm_manager_concurrency.py
- **Total tests**: 8
- **Passed**: 8
- **Failed**: 0

## Failure Categories

### Category 1: File Lock Mock Missing (5 tests)

**Count**: 5 tests
**Root Cause**: Tests don't mock the `_acquire_start_lock()` method which creates real file locks. When tests run sequentially in the same class, the lock file from previous test remains locked, causing subsequent tests to fail with BlockingIOError.

**Affected Tests**:
1. `test_start_rejects_nonexistent_vm`
2. `test_start_spawns_runner_with_correct_parameters`
3. `test_error_file_included_in_exception`
4. `test_post_startup_validation_dead_qemu`
5. `test_post_startup_validation_success`

**Error Pattern**:
```
BlockingIOError: [Errno 11] Resource temporarily unavailable
    at maqet/managers/vm_manager.py:233: fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

Wrapped as:
BlockingIOError: VM 'vm-123' is already being started by another process
    at maqet/managers/vm_manager.py:237
```

**Technical Details**:
- The `_acquire_start_lock()` method was added for per-VM architecture to prevent concurrent starts
- It uses `fcntl.flock()` with `LOCK_EX | LOCK_NB` (exclusive, non-blocking lock)
- Lock file path: `/tmp/test.lock` (returned by `mock_state_manager.get_lock_path()`)
- Problem: Real file lock is acquired but not released between tests
- fcntl locks should auto-release when file is closed, but test setup doesn't close the lock file

**Example Failure** (test_start_spawns_runner_with_correct_parameters):
```python
# Test setup
self.mock_state_manager.get_lock_path.return_value = Path("/tmp/test.lock")

# First test acquires lock successfully
# Lock file handle is stored in vm_manager but never explicitly released
# Second test tries to acquire same lock -> BlockingIOError
```

**Fix Pattern**:
```python
@patch("maqet.managers.vm_manager.VMManager._acquire_start_lock")
def test_start_spawns_runner_with_correct_parameters(self, mock_lock):
    """Verify runner process spawned with correct VM ID and DB path."""
    # Mock lock acquisition to return a fake file handle
    mock_lock_file = Mock()
    mock_lock.return_value = mock_lock_file

    # Rest of test remains unchanged
    self.mock_state_manager.get_vm.return_value = self.mock_vm
    # ... existing test code
```

**Alternative Fix Pattern** (if we want to test lock behavior):
```python
def setUp(self):
    """Set up test fixtures."""
    # ... existing setup

def tearDown(self):
    """Clean up test fixtures."""
    # Remove lock file if it exists
    lock_file = Path("/tmp/test.lock")
    if lock_file.exists():
        lock_file.unlink()
```

### Category 2: Note on test_start_cleans_up_if_socket_not_ready

**Status**: PASSED in latest test run
**Previous Behavior**: This test was previously failing with cleanup verification issues
**Current Behavior**: Now passes successfully (appears in PASSED tests list)

This test validates that the runner process is killed if the socket doesn't become ready within the timeout period.


## Additional Findings

### Non-Existent VM Test Error Message Change

**Test**: `test_start_rejects_nonexistent_vm`

**Expected behavior**: Error message should contain "not found"
**Actual behavior**: Error message is "VM start: Unexpected error - BlockingIOError: VM 'nonexistent-vm' is already being started by another process"

**Analysis**: This is also caused by the lock file issue. The test expects the code to reach the "VM not found" check, but it fails at lock acquisition first. Once lock mocking is fixed, this test should pass.

**Current assertion**:
```python
self.assertIn("not found", str(context.exception))
```

This assertion is correct - it will pass once the lock is properly mocked.

### Concurrency Tests Already Pass

**Important Note**: All 8 concurrency tests in `test_vm_manager_concurrency.py` pass successfully. This suggests that:
1. Concurrency test fixtures properly mock or avoid the file lock mechanism
2. The concurrent start test (`test_concurrent_start_same_vm`) validates lock behavior at a higher level
3. Integration between runner and QEMU processes is correctly tested

**Passing Concurrency Tests**:
- test_concurrent_config_updates
- test_concurrent_delete_and_start
- test_concurrent_qmp_commands
- test_concurrent_snapshot_and_stop
- test_concurrent_start_same_vm
- test_rapid_start_stop_cycles
- test_state_db_lock_timeout
- test_vm_start_during_cleanup

## Root Cause Analysis

The fundamental issue is **insufficient test isolation** around the new file locking mechanism:

1. **Per-VM Architecture Addition**: File locking was added to `VMManager.start()` to prevent concurrent starts of the same VM
2. **Lock Implementation**: Uses `fcntl.flock()` on a lock file path returned by `state_manager.get_lock_path(vm_id)`
3. **Mock Setup Issue**: Tests mock `state_manager.get_lock_path()` to return `/tmp/test.lock`, but don't mock the actual lock acquisition
4. **Real File System Impact**: Tests create real lock files in `/tmp/` which persist between test runs
5. **Sequential Failures**: First test in a class may pass, subsequent tests fail with lock contention

## Recommended Fix Approach

### Strategy 1: Mock Lock Acquisition (Recommended)

**Pros**:
- Minimal changes to existing tests
- Tests remain focused on their original purpose
- No file system side effects
- Fast execution

**Cons**:
- Doesn't test actual lock behavior
- Requires adding mock to every start() test

**Implementation**:
```python
# Add to all tests that call vm_manager.start()
@patch("maqet.managers.vm_manager.VMManager._acquire_start_lock")
def test_name(self, mock_lock):
    mock_lock_file = Mock()
    mock_lock.return_value = mock_lock_file
    # ... rest of test
```

### Strategy 2: Add tearDown Cleanup

**Pros**:
- Tests real lock file behavior
- Better integration testing
- Simple to implement

**Cons**:
- File system side effects
- May have timing issues on CI
- Doesn't isolate lock testing

**Implementation**:
```python
class TestVMManagerStart(unittest.TestCase):
    def setUp(self):
        # ... existing setup

    def tearDown(self):
        """Clean up lock files after each test."""
        lock_file = Path("/tmp/test.lock")
        if lock_file.exists():
            try:
                lock_file.unlink()
            except (PermissionError, FileNotFoundError):
                pass  # Best effort cleanup
```

### Strategy 3: Mock get_lock_path to Use Unique Paths

**Pros**:
- Tests real lock behavior
- No cleanup needed (uses temp files)
- Tests remain isolated

**Cons**:
- More complex mock setup
- Still has file system side effects

**Implementation**:
```python
import tempfile
import uuid

def setUp(self):
    # ... existing setup

    # Create unique lock file path for each test
    unique_lock = Path(tempfile.gettempdir()) / f"test-{uuid.uuid4()}.lock"
    self.mock_state_manager.get_lock_path.return_value = unique_lock
```

## Recommended Implementation Order

1. **Apply Strategy 1 (Mock Lock Acquisition)** to all 4 failing tests
   - Fastest path to green tests
   - Keeps tests focused on their original purpose
   - No file system side effects

2. **Validate all tests pass** with proper mocking

3. **Consider extracting mock helper** to avoid repetition:
   ```python
   def mock_vm_start_dependencies(mock_state_manager, mock_lock):
       """Helper to set up common mocks for VM start tests."""
       mock_lock_file = Mock()
       mock_lock.return_value = mock_lock_file
       mock_state_manager.get_lock_path.return_value = Path("/tmp/test.lock")
       return mock_lock_file
   ```

4. **Add dedicated lock behavior tests** in concurrency suite
   - The concurrency tests already validate lock behavior
   - No additional tests needed unless specific edge cases identified

## Files Requiring Changes

### tests/unit/managers/test_vm_manager.py

**Changes Required**: 5 test methods

1. **test_start_rejects_nonexistent_vm** (line 121)
   - Add `@patch("maqet.managers.vm_manager.VMManager._acquire_start_lock")`
   - Add `mock_lock` parameter
   - Mock return value

2. **test_start_spawns_runner_with_correct_parameters** (line 60)
   - Add `@patch("maqet.managers.vm_manager.VMManager._acquire_start_lock")`
   - Add `mock_lock` parameter
   - Mock return value

3. **test_error_file_included_in_exception** (PostStartupValidation class)
   - Add `@patch("maqet.managers.vm_manager.VMManager._acquire_start_lock")`
   - Add `mock_lock` parameter
   - Mock return value

4. **test_post_startup_validation_dead_qemu** (PostStartupValidation class)
   - Add `@patch("maqet.managers.vm_manager.VMManager._acquire_start_lock")`
   - Add `mock_lock` parameter
   - Mock return value

5. **test_post_startup_validation_success** (PostStartupValidation class)
   - Add `@patch("maqet.managers.vm_manager.VMManager._acquire_start_lock")`
   - Add `mock_lock` parameter
   - Mock return value

## Validation Plan

### Per-Test Validation
```bash
# Run individual failing tests
pytest tests/unit/managers/test_vm_manager.py::TestVMManagerStart::test_start_rejects_nonexistent_vm -v
pytest tests/unit/managers/test_vm_manager.py::TestVMManagerStart::test_start_spawns_runner_with_correct_parameters -v
pytest tests/unit/managers/test_vm_manager.py::TestVMManagerPostStartupValidation::test_error_file_included_in_exception -v
pytest tests/unit/managers/test_vm_manager.py::TestVMManagerPostStartupValidation::test_post_startup_validation_dead_qemu -v
pytest tests/unit/managers/test_vm_manager.py::TestVMManagerPostStartupValidation::test_post_startup_validation_success -v
```

### Full Suite Validation
```bash
# Run all VM manager tests
pytest tests/unit/managers/test_vm_manager.py -v

# Run all VM manager concurrency tests (should remain passing)
pytest tests/unit/managers/test_vm_manager_concurrency.py -v

# Run both together
pytest tests/unit/managers/test_vm_manager*.py -v
```

### Regression Check
```bash
# Ensure no other tests broken by changes
pytest tests/unit/ -v --tb=short
```

## Success Criteria

- [ ] All 5 failing tests pass consistently
- [ ] All 25 previously passing tests remain passing
- [ ] All 8 concurrency tests remain passing
- [ ] No file system artifacts left in /tmp after test run
- [ ] Test execution time not significantly increased
- [ ] Test output clearly shows what is being tested

## Conclusion

The VM manager test failures are caused by incomplete mocking of the new file lock mechanism introduced for per-VM architecture. The fix is straightforward: add `@patch` decorator to mock `_acquire_start_lock()` in the 5 affected tests.

**Key Insight**: All failures share the same root cause - file lock contention due to unmocked `_acquire_start_lock()`. The concurrency test suite already passes (8/8), indicating that the dual-process (runner + QEMU) architecture is properly handled at the integration level.

**Estimated Fix Time**: 20-30 minutes
**Risk Level**: Low (test-only changes)
**Dependencies**: None (can proceed immediately)

## Per-VM Architecture Summary

The new per-VM architecture introduces:

1. **Two-Process Model**: VM Manager spawns detached runner processes that independently manage QEMU
2. **File-Based Locking**: Uses fcntl.flock() to prevent concurrent starts of same VM
3. **Lock Lifecycle**: Lock acquired before VM operations, released in finally block
4. **Process Tracking**: Database tracks both runner_pid and QEMU pid
5. **Validation Flow**: Multi-stage validation (existence check, lock acquisition, runner spawn, socket ready, QEMU alive)

The test failures reveal that tests need to be updated to account for this new locking infrastructure.
