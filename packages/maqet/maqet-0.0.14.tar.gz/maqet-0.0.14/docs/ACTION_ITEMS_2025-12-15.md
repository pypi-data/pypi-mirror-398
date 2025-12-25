# Action Items - Code Review 2025-12-15

**Source**: Consolidated Code Review Report
**Version**: v0.0.13 (pre-v0.1.0)
**Status**: Code is commit-ready, items tracked for future work

---

## HIGH Priority (7 items)

### H1. State Module Namespace Shadowing
**File**: `maqet/state/__init__.py:14-30`
**Issue**: Uses importlib hack to work around state.py vs state/ collision
**Impact**: Breaks IDE tooling, debugging stack traces, type checkers
**Solution**: Rename `state.py` to `state_manager.py`
**Effort**: 2-3 hours (~30 import changes)
**Sprint**: Next

### H2. get_storage_info() God Method
**File**: `maqet/managers/vm_manager.py:1479-1562` (84 lines)
**Issue**: Single method handles too many responsibilities
**Solution**: Extract `_process_file_devices()` and `_process_virtfs_devices()`
**Effort**: 1-2 hours
**Sprint**: Next

### H3. _verify_started() Complexity
**File**: `maqet/managers/vm_manager.py:472-533` (62 lines)
**Issue**: Complex nested error handling
**Solution**: Extract `_verify_qemu_running()` and `_handle_qemu_verification_failure()`
**Effort**: 1-2 hours
**Sprint**: Next

### H4. Auth Secret Memory Cache
**File**: `maqet/ipc/runner_client.py:57-60`
**Issue**: Secrets stored in class-level cache without secure deletion
**Risk**: Memory disclosure via process dumps
**Solution**: Remove caching (accept file I/O cost) OR implement secure zeroing with bytearray
**Effort**: 1 hour
**Sprint**: Next

### H5. Config DoS Limits Not Enforced
**File**: `maqet/config/merger.py:326-340`
**Issue**: validate_config_size() defined but never called
**Risk**: DoS via large YAML files loaded into memory
**Solution**: Call `validate_config_size()` before `yaml.safe_load()` in merge_configs()
**Effort**: 30 minutes
**Sprint**: Next

### H6. Excessive Mock Layering in Tests
**File**: `tests/integration/test_wait_parameters.py`
**Issue**: 3-4 nested patches make tests brittle
**Solution**: Test wait logic independently or use real subprocesses
**Effort**: 3-4 hours
**Sprint**: Next

### H7. Missing Negative Test Cases
**File**: `tests/integration/test_path_resolution.py`
**Issue**: No tests for circular symlinks, non-existent paths
**Solution**: Add test_circular_symlink_detection(), test_nonexistent_path_policy()
**Effort**: 1 hour
**Sprint**: Next

---

## MEDIUM Priority (9 items)

### M1. Circular Import in Architecture Tests
**File**: `tests/architecture/test_import_rules.py`
**Issue**: test_no_direct_circular_imports failing
**Solution**: Investigate and resolve remaining circular import
**Effort**: 2-3 hours

### M2. VMManager Constructor Type Hints
**File**: `maqet/managers/vm_manager.py:53`
**Issue**: config_parser and qmp_manager parameters untyped
**Solution**: Add type hints: `config_parser: ConfigParser, qmp_manager: Optional[QMPManager]`
**Effort**: 30 minutes

### M3. ProcessSpawner Class Adds Minimal Value
**File**: `maqet/process_spawner.py:485-617`
**Issue**: Class wraps module functions without full DI adoption
**Solution**: Remove class OR make client_factory mandatory with protocol checking
**Effort**: 2 hours

### M4. Inconsistent Process Verification
**Files**: `vm_manager.py`, `state.py`, `process_spawner.py`
**Issue**: 3 different _is_process_alive implementations
**Solution**: Unify using ProcessVerifier consistently
**Effort**: 3-4 hours

### M5. Remaining Deep Nesting
**File**: `maqet/managers/vm_manager.py:1216-1220, 1256`
**Issue**: 11 instances of 3+ level indentation
**Solution**: Use guard clauses and early returns
**Effort**: 2 hours

### M6. Long Methods in process_spawner.py
**File**: `maqet/process_spawner.py`
**Issue**: kill_runner (63 lines), is_runner_alive (55 lines)
**Solution**: Extract /proc logic to helper functions
**Effort**: 2 hours

### M7. Thread Pool Sizing
**File**: `maqet/managers/vm_manager.py:70-73`
**Issue**: cpu_count*4 may be too aggressive
**Solution**: Change to min(16, max(4, cpu_count*2)) with documentation
**Effort**: 30 minutes

### M8. Wait Loop Backoff
**File**: `maqet/utils/wait_logic.py:92-114`
**Issue**: 2s max backoff may be too conservative for fast operations
**Solution**: Implement adaptive backoff based on timeout duration
**Effort**: 1 hour

### M9. Machine Cache Invalidation
**File**: `maqet/managers/vm_manager.py:65`
**Issue**: Cache not cleared on config apply
**Solution**: Clear machine cache in apply() when VM is running
**Effort**: 30 minutes

---

## LOW Priority (13 items)

### L1. Architecture Documentation Mismatch
**File**: `docs/architecture.md:93-109`
**Issue**: Says infrastructure layer has no upper layer imports, but VMRepository imports VMInstance
**Solution**: Update documentation to reflect current structure

### L2. Missing QMPManagerProtocol
**File**: `maqet/protocols/`
**Issue**: Other managers have protocols, QMPManager does not
**Solution**: Add QMPManagerProtocol for consistency

### L3. Wait Condition Handler Extraction
**File**: `maqet/managers/vm_manager.py`
**Issue**: _handle_wait_condition could be separate class
**Solution**: Extract WaitConditionHandler for better SRP

### L4. Database Connection Pool Metrics
**File**: `maqet/state.py:463-495`
**Issue**: No visibility into pool statistics
**Solution**: Add get_pool_stats() method

### L5. Query Performance Tracing
**File**: `maqet/state/vm_repository.py`
**Issue**: No slow query logging
**Solution**: Add trace_query decorator for 100ms+ queries

### L6. Wait Condition Success Rate Metrics
**File**: `maqet/utils/wait_logic.py`
**Issue**: No tracking of wait condition performance
**Solution**: Add WAIT_STATS tracking for monitoring

### L7. Batch Update Performance Monitoring
**File**: `maqet/state/vm_repository.py:342-396`
**Issue**: No timing or size warnings
**Solution**: Add elapsed time logging and large batch warnings

### L8. Test File Size
**File**: `tests/integration/test_path_resolution.py` (1,085 lines)
**Issue**: Exceeds 400 line limit from tests/README.md
**Solution**: Split into 5 focused modules

### L9. E2E Test Serialization
**File**: `tests/e2e/conftest.py`
**Issue**: Custom scheduler serializes ALL e2e tests
**Solution**: Use vm_start_lock() selectively instead

### L10. Test Class Organization
**File**: `tests/integration/test_wait_parameters.py`
**Issue**: Mix of class-based and function-based tests
**Solution**: Choose one pattern (prefer function-based)

### L11. Test Helper for Path Verification
**File**: `tests/integration/test_path_resolution.py`
**Issue**: Repeated path verification pattern
**Solution**: Extract verify_path_resolution() helper

### L12. Assertion Messages
**File**: Various test files
**Issue**: Complex assertions lack failure messages
**Solution**: Add helpful messages to path verification assertions

### L13. Performance Test for Large Configs
**File**: `tests/performance/`
**Issue**: No test for path resolution with 100+ storage devices
**Solution**: Add test_path_resolution_performance_100_storage_devices()

---

## Completed (From Previous Review)

- [x] StateManager God Object - Decomposed into VMRepository, MigrationRunner, DatabaseBackup
- [x] O(n) Linear Scan - Resolved with indexed queries
- [x] N+1 Query Pattern - Resolved with batch updates
- [x] VMManager.start() 252 lines - Refactored to 60 lines + helpers
- [x] Magic Numbers - Constants everywhere (Timeouts, Intervals, ProcessManagement)
- [x] Unix Socket Permissions - Fixed
- [x] Path Traversal - Fixed with InputValidator
- [x] Unbounded Memory - ConfigLimits added

---

## Sprint Planning

### Next Sprint (Recommended)
- H1, H4, H5 (Security/Architecture fixes) - 4 hours
- H2, H3 (Code quality) - 3 hours
- H6, H7 (Test improvements) - 5 hours
- M2, M7, M9 (Quick wins) - 1.5 hours
**Total**: ~13.5 hours

### Following Sprint
- M1, M3, M4, M5, M6, M8 - ~13 hours

### Backlog
- All LOW priority items

---

**Last Updated**: 2025-12-15
**Review Confidence**: HIGH
