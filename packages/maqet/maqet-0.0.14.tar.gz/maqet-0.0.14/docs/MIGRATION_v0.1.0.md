# Migration Guide: v0.0.x to v0.1.0

## Overview

Maqet v0.1.0 removes SSH readiness checking and boot complete checking to focus exclusively on VM infrastructure management. This is a breaking change that affects CLI commands and Python API.

## Breaking Changes Summary

### Removed Features

- **SSH readiness checking** (`--wait-for ssh-ready`)
- **Boot complete checking** (`--wait-for boot-complete`)
- **CLI arguments**: `--ssh-port`, `--ssh-host`
- **Python API parameters**: `ssh_port`, `ssh_host` from `start()` method

### Why This Changed

Maqet v0.0.x included `--wait-for ssh-ready` which only checked if TCP port 2222 was open. This was:

1. **Misleading**: Port open does not mean SSH is operational
   - maqet reported "SSH ready" when port was open
   - Actual SSH authentication could still fail
   - Users wasted time debugging maqet instead of their SSH config

2. **Out of scope**: SSH is a guest OS service, not VM infrastructure
   - Maqet manages QEMU processes, storage, and QMP communication
   - SSH server is a Linux service running inside the guest OS
   - These are different layers with different concerns

3. **Feature creep**: If SSH, why not HTTP, PostgreSQL, Redis, etc.?
   - Adding every service check bloats maqet
   - Standard tools already exist for these checks
   - Better to compose with existing tools

Maqet v0.1.0 focuses exclusively on VM infrastructure management (QEMU process lifecycle, storage, QMP) and delegates guest OS concerns to standard tools.

## Available Wait Conditions

After v0.1.0, maqet supports these wait conditions:

| Condition | Description | Use Case |
|-----------|-------------|----------|
| `process-started` | VM runner IPC socket ready (default) | Default - always reliable |
| `file-exists` | Wait for specific file | Custom synchronization |

## Migration Scenarios

### Scenario 1: Basic SSH Waiting

**Before (v0.0.x)**:

```bash
maqet start myvm --wait-for ssh-ready --ssh-port 2222 --timeout 120
```

**After v0.1.0 - Option A (Simple sleep)**:

```bash
maqet start myvm && sleep 10 && ssh user@localhost -p 2222
```

**After v0.1.0 - Option B (Proper SSH checking)**:

```bash
maqet start myvm

# Wait for SSH to actually be ready (not just port open)
until ssh-keyscan -p 2222 localhost 2>/dev/null | grep -q ssh; do
    echo "Waiting for SSH..."
    sleep 2
done

# Now SSH is actually operational
ssh user@localhost -p 2222
```

**After v0.1.0 - Option C (Retry with timeout)**:

```bash
maqet start myvm

# Robust SSH waiting with timeout
timeout=120
elapsed=0
while ! ssh -o ConnectTimeout=1 -o StrictHostKeyChecking=no \
           -p 2222 user@localhost "exit" 2>/dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "SSH timeout after ${timeout}s"
        exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

echo "SSH ready!"
```

### Scenario 2: Automation Scripts

**Before (v0.0.x pipeline.sh)**:

```bash
# This will fail in v0.1.0:
maqet start demo-validate --wait-for ssh-ready --ssh-port 2222 --timeout 120
```

**After v0.1.0 (recommended approach)**:

```bash
#!/bin/bash

# Start VM (just infrastructure)
maqet start demo-validate --timeout 30

# Wait for SSH separately (application-level concern)
wait_for_ssh() {
    local host="${1:-localhost}"
    local port="${2:-22}"
    local user="${3:-root}"
    local timeout="${4:-120}"

    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if ssh -o ConnectTimeout=2 \
               -o StrictHostKeyChecking=no \
               -o UserKnownHostsFile=/dev/null \
               -p "$port" "$user@$host" "exit" 2>/dev/null; then
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    return 1
}

if wait_for_ssh localhost 2222 demo 120; then
    echo "SSH ready!"
else
    echo "SSH timeout"
    exit 1
fi
```

### Scenario 3: Python Automation

**Before (v0.0.x)**:

```python
from maqet import Maqet
m = Maqet()
m.start("myvm", wait_for="ssh-ready", ssh_port=2222, timeout=120)
```

**After v0.1.0**:

```python
import socket
import subprocess
import time
from maqet import Maqet

def wait_for_ssh(host: str = "localhost", port: int = 22,
                  timeout: int = 120) -> bool:
    """Wait for SSH to be ready (proper check, not just port open)."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            # Use ssh-keyscan to verify SSH is actually operational
            result = subprocess.run(
                ["ssh-keyscan", "-p", str(port), host],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0 and b"ssh" in result.stdout:
                return True
        except subprocess.TimeoutExpired:
            pass
        time.sleep(2)
    return False

# Usage
m = Maqet()
m.start("myvm", wait_for="process-started", timeout=30)

if wait_for_ssh("localhost", 2222, timeout=120):
    print("SSH ready!")
else:
    print("SSH timeout")
```

## User Benefits

Migrating to v0.1.0 provides these benefits:

1. **Clearer expectations**: Maqet no longer pretends to check SSH functionality
2. **Better error messages**: SSH failures are clearly user's SSH config, not maqet bugs
3. **Proper SSH checking**: Users write real SSH checks instead of misleading port checks
4. **Composability**: Maqet does one thing well, users combine with standard SSH tools
5. **Less maintenance**: Maqet doesn't need to keep up with SSH protocols/versions
6. **Faster startup**: No SSH port checking overhead (~100-500ms per check)

## Error Messages

### CLI Error for Removed Arguments

```bash
$ maqet start myvm --ssh-port 2222
maqet: error: unrecognized arguments: --ssh-port

SSH readiness checking was removed in maqet v0.1.0.
See migration guide: https://gitlab.com/m4x0n_24/maqet/docs/MIGRATION_v0.1.0.md
```

### Python API Error for Removed Condition

```python
>>> from maqet import Maqet
>>> m = Maqet()
>>> m.start("myvm", wait_for="ssh-ready")
ValueError: Invalid wait condition 'ssh-ready'

Available conditions:
  - process-started (default): VM runner process is ready
  - file-exists: Wait for specific file to exist
```

## Frequently Asked Questions

### Q: Why remove SSH checking instead of fixing it?

A: SSH is fundamentally a guest OS concern, not VM infrastructure. Proper SSH checking requires:

- Key exchange verification
- Authentication testing
- SSH daemon readiness (not just port open)

This belongs in SSH tools (ssh-keyscan, ssh with retries), not VM management tools.

### Q: Will SSH checking be added back in the future?

A: No. This is a permanent scope clarification. Maqet focuses on VM infrastructure (QEMU, storage, QMP). Guest OS concerns should be handled by standard tools.

### Q: What about boot-complete?

A: `boot-complete` was never implemented (always returned False). It's removed for the same reasons as SSH checking - boot detection is a guest OS concern.

### Q: Can I still use process-started?

A: Yes! `process-started` is the default and recommended wait condition. It verifies the VM runner process is ready and the IPC socket is operational - this IS maqet's responsibility.

### Q: What tools should I use for SSH checking?

A: Use standard SSH tools:

- `ssh-keyscan`: Verify SSH server is responding
- `ssh` with retry loop: Test actual authentication
- `nc` (netcat): Basic port checking
- `timeout` command: Add timeouts to scripts

## Related Documentation

- [CHANGELOG.md](../CHANGELOG.md) - Complete list of changes in v0.1.0
- [README.md](../README.md) - Updated documentation without SSH examples
- [Unix Philosophy](https://en.wikipedia.org/wiki/Unix_philosophy) - Do one thing well
