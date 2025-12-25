# QMP Command Security

## Overview

MAQET implements QMP (QEMU Machine Protocol) command validation to prevent accidental or malicious VM compromise through dangerous commands. This document describes the security model, command classification, and usage guidelines.

## Table of Contents

- [Command Classification](#command-classification)
- [Security Model](#security-model)
- [Usage Examples](#usage-examples)
- [Audit Logging](#audit-logging)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Command Classification

MAQET classifies QMP commands into three categories based on their security impact:

### Dangerous Commands (Blocked by Default)

These commands can compromise guest security or stability and are blocked unless explicitly allowed:

| Command | Risk | Impact |
|---------|------|--------|
| `human-monitor-command` | **Critical** | Allows arbitrary QEMU monitor commands, bypassing all protections |
| `inject-nmi` | **High** | Can crash guest operating system via Non-Maskable Interrupt |

**Default Behavior**: Raises `QMPManagerError` with security message

**Override**: Use `allow_dangerous=True` parameter (Python API only)

### Memory Dump Commands (Allowed with Logging)

These commands are allowed for testing and debugging but generate audit log entries:

| Command | Use Case | Privacy Risk |
|---------|----------|--------------|
| `pmemsave` | Physical memory dump | Exposes guest memory contents |
| `memsave` | Virtual memory dump | Exposes guest memory contents |

**Default Behavior**: Executes but logs at INFO level with "purpose=testing"

**Use Case**: Debugging, forensics, testing

### Privileged Commands (Logged with Warning)

These commands affect VM availability and are logged with WARNING level:

| Command | Impact |
|---------|--------|
| `system_powerdown` | Graceful VM shutdown |
| `system_reset` | Hard VM reset |
| `quit` | Immediate VM termination |
| `device_del` | Hot-unplug device |
| `blockdev-del` | Remove block device |

**Default Behavior**: Executes with warning log entry

---

## Security Model

### Defense Layers

MAQET implements multiple security layers for QMP commands:

1. **Command Classification**: Categorize commands by risk level
2. **Input Validation**: Block dangerous commands by default
3. **Explicit Permission**: Require `allow_dangerous=True` for risky commands
4. **Audit Logging**: Log all QMP commands with context
5. **Unix Socket Permissions**: 0600 permissions limit access to VM owner

### Threat Model

**Protected Against**:

- Accidental execution of dangerous commands
- Unauthorized QMP access (via socket permissions)
- Malicious scripts exploiting QMP interface
- Command injection via untrusted input

**Not Protected Against**:

- VM owner intentionally using `allow_dangerous=True`
- Physical access to host system
- Kernel-level exploits in QEMU itself
- Side-channel attacks on guest

---

## Usage Examples

### Safe Commands (No Restrictions)

```python
from maqet import Maqet

maqet = Maqet()
vm_id = maqet.add(name="test-vm", vm_config="config.yaml")
maqet.start(vm_id)

# Query status - always allowed
result = maqet.qmp(vm_id, "query-status")
print(result)  # {'status': 'running', 'singlestep': False, 'running': True}

# Graceful shutdown - allowed with logging
result = maqet.qmp(vm_id, "system_powerdown")
# WARNING: Executing privileged QMP command 'system_powerdown' on VM test-vm
```

### Blocked Dangerous Commands

```python
from maqet import Maqet
from maqet.managers.qmp_manager import QMPManagerError

maqet = Maqet()
vm_id = maqet.add(name="test-vm", vm_config="config.yaml")
maqet.start(vm_id)

# This will raise QMPManagerError
try:
    maqet.qmp(vm_id, "human-monitor-command", command_line="quit")
except QMPManagerError as e:
    print(e)
    # QMPManagerError: Dangerous QMP command 'human-monitor-command' blocked.
    # This command can compromise guest security or stability.
    # If you really need this, use allow_dangerous=True and
    # understand the risks. See: docs/security/qmp-security.md
```

### Explicit Permission for Dangerous Commands

**WARNING**: Only use in controlled testing environments. Never in production.

```python
from maqet import Maqet

maqet = Maqet()
vm_id = maqet.add(name="test-vm", vm_config="config.yaml")
maqet.start(vm_id)

# Explicitly allow dangerous command (Python API only)
result = maqet.qmp_manager.execute_qmp(
    vm_id,
    "human-monitor-command",
    allow_dangerous=True,  # Explicit permission required
    command_line="info status"
)
print(result)
```

**Note**: CLI does not support `allow_dangerous` parameter. Use Python API for dangerous commands.

### Memory Dump Commands (Testing)

```python
from maqet import Maqet

maqet = Maqet()
vm_id = maqet.add(name="test-vm", vm_config="config.yaml")
maqet.start(vm_id)

# Memory dumps allowed but logged
result = maqet.qmp(
    vm_id,
    "pmemsave",
    val=0,          # Start address
    size=1024,      # Bytes to dump
    filename="/tmp/memory.dump"
)
# INFO: QMP memory dump: test-vm | pmemsave | user=m4x0n | purpose=testing
```

---

## Audit Logging

### Log Format

All QMP commands are logged with comprehensive context:

```
2025-10-14 12:34:56 INFO QMP: vm-abc123 | query-status | params=[] | user=m4x0n | timestamp=2025-10-14T12:34:56
2025-10-14 12:35:10 WARNING QMP privileged: vm-abc123 | system_powerdown | user=m4x0n
2025-10-14 12:36:22 INFO QMP memory dump: vm-abc123 | pmemsave | user=m4x0n | purpose=testing
```

### Log Levels

| Level | Command Type | Example |
|-------|--------------|---------|
| INFO | Safe commands | `query-status`, `query-cpus` |
| INFO | Memory dumps | `pmemsave`, `memsave` |
| WARNING | Privileged commands | `system_powerdown`, `device_del` |
| ERROR | Blocked dangerous | `human-monitor-command`, `inject-nmi` |

### Log Location

```bash
# MAQET logs to stdout/stderr by default
# Redirect to file:
maqet start myvm 2>&1 | tee -a /var/log/maqet.log

# Or configure Python logging:
import logging
logging.basicConfig(
    filename='/var/log/maqet.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
```

### Analyzing Logs

```bash
# Find all QMP commands for a VM
grep "QMP: vm-abc123" /var/log/maqet.log

# Find privileged commands
grep "QMP privileged" /var/log/maqet.log

# Find memory dumps
grep "QMP memory dump" /var/log/maqet.log

# Find blocked commands (attempted dangerous commands)
grep "QMPManagerError" /var/log/maqet.log

# Count commands by user
grep "QMP:" /var/log/maqet.log | grep -oP 'user=\K\w+' | sort | uniq -c
```

---

## Security Best Practices

### For Developers

1. **Never use `allow_dangerous=True` in production code**

   ```python
   # BAD - Production code
   def shutdown_vm(vm_id):
       maqet.qmp_manager.execute_qmp(
           vm_id, "human-monitor-command",
           allow_dangerous=True,  # NEVER DO THIS IN PRODUCTION
           command_line="quit"
       )

   # GOOD - Use safe API
   def shutdown_vm(vm_id):
       maqet.stop(vm_id)  # Safe, validated method
   ```

2. **Always use MAQET's API methods instead of direct QMP**

   ```python
   # BAD - Direct QMP
   maqet.qmp(vm_id, "system_powerdown")

   # GOOD - Use API method
   maqet.stop(vm_id)  # Handles errors, validates state
   ```

3. **Validate user input before passing to QMP**

   ```python
   # BAD - Unsanitized user input
   def run_qmp_command(vm_id, command):
       return maqet.qmp(vm_id, command)

   # GOOD - Whitelist allowed commands
   SAFE_COMMANDS = {"query-status", "query-cpus", "query-block"}

   def run_qmp_command(vm_id, command):
       if command not in SAFE_COMMANDS:
           raise ValueError(f"Command not allowed: {command}")
       return maqet.qmp(vm_id, command)
   ```

4. **Monitor audit logs regularly**

   ```bash
   # Daily security check
   grep "QMP privileged" /var/log/maqet.log | grep -v "expected_user" | mail -s "Suspicious QMP activity" admin@example.com
   ```

### For System Administrators

1. **Restrict socket access** (already enforced by MAQET):

   ```bash
   # Verify socket permissions
   ls -la /run/user/$(id -u)/maqet/sockets/
   # Should show: srw------- (0600 permissions)
   ```

2. **Use filesystem permissions** for additional protection:

   ```bash
   # Restrict MAQET binary access
   sudo chmod 750 /usr/local/bin/maqet
   sudo chgrp vm-operators /usr/local/bin/maqet
   ```

3. **Monitor for suspicious patterns**:

   ```bash
   # Alert on multiple privileged commands in short time
   grep "QMP privileged" /var/log/maqet.log | \
       awk '{print $1,$2}' | \
       uniq -c | \
       awk '$1 > 10 {print "Alert: " $1 " privileged commands at " $2 " " $3}'
   ```

4. **Separate testing and production environments**:
   - Use different user accounts for testing (where `allow_dangerous=True` might be used)
   - Never mix test and production VMs on same host

### For Security Auditors

1. **Check for dangerous command usage**:

   ```bash
   # Find any use of allow_dangerous
   grep -r "allow_dangerous=True" /path/to/code/
   # Should be ZERO results in production code
   ```

2. **Verify audit logging is enabled**:

   ```python
   import logging
   assert logging.getLogger('maqet').level <= logging.INFO
   ```

3. **Review QMP command patterns**:

   ```bash
   # Analyze command distribution
   grep "QMP:" /var/log/maqet.log | \
       awk -F'|' '{print $2}' | \
       sort | uniq -c | sort -rn
   ```

---

## Troubleshooting

### Error: "Dangerous QMP command blocked"

**Symptom**:

```
QMPManagerError: Dangerous QMP command 'human-monitor-command' blocked.
```

**Cause**: Command is classified as dangerous and blocked by default.

**Solutions**:

1. **Use safe alternative** (recommended):

   ```python
   # Instead of: maqet.qmp(vm_id, "human-monitor-command", command_line="quit")
   # Use: maqet.stop(vm_id)
   ```

2. **Explicit permission** (testing only):

   ```python
   maqet.qmp_manager.execute_qmp(
       vm_id, "human-monitor-command",
       allow_dangerous=True,
       command_line="info status"
   )
   ```

### Warning: "Executing privileged QMP command"

**Symptom**:

```
WARNING: Executing privileged QMP command 'system_powerdown' on VM test-vm
```

**Cause**: Command affects VM availability (expected behavior).

**Action**: No action needed - this is informational logging.

**To suppress** (not recommended):

```python
import logging
logging.getLogger('maqet.managers.qmp_manager').setLevel(logging.ERROR)
```

### Info: "QMP memory dump"

**Symptom**:

```
INFO: QMP memory dump: test-vm | pmemsave | user=m4x0n | purpose=testing
```

**Cause**: Memory dump command executed (expected for testing).

**Action**: Verify this is intentional testing activity.

**Security concern**: Memory dumps may contain sensitive data (passwords, keys). Handle dump files securely.

---

## Command Reference

### Full Command Classification

**Dangerous** (blocked by default):

```python
DANGEROUS_QMP_COMMANDS = {
    "human-monitor-command",
    "inject-nmi",
}
```

**Memory Dumps** (allowed with logging):

```python
MEMORY_DUMP_COMMANDS = {
    "pmemsave",
    "memsave",
}
```

**Privileged** (allowed with warning):

```python
PRIVILEGED_QMP_COMMANDS = {
    "system_powerdown",
    "system_reset",
    "quit",
    "device_del",
    "blockdev-del",
}
```

**Safe** (all others):

- `query-status`
- `query-cpus`
- `query-block`
- `query-blockstats`
- `query-chardev`
- `query-migrate`
- ... (see QEMU QMP documentation)

---

## Further Reading

- [QEMU QMP Protocol Specification](https://www.qemu.org/docs/master/interop/qmp-spec.html)
- [QEMU Security](https://www.qemu.org/docs/master/system/security.html)
- [MAQET Architecture](../development/ARCHITECTURE.md)
- [MAQET Security](../SECURITY.md)

---

## Reporting Security Issues

If you discover a security vulnerability in MAQET's QMP handling:

1. **DO NOT** open a public issue
2. Email: [project maintainer email]
3. Include: Description, reproduction steps, impact assessment
4. We aim to respond within 48 hours

---

Last Updated: 2025-10-14
MAQET Version: 0.0.11+
