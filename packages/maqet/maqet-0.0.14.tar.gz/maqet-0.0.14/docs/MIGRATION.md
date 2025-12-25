# MAQET Migration Guide

This guide helps you migrate between MAQET versions, highlighting breaking changes and upgrade paths.

## Table of Contents

- [Upgrading to v0.0.11](#upgrading-to-v0011)
- [Upgrading to v0.0.8](#upgrading-to-v008)
- [Upgrading from v0.0.7](#upgrading-from-v007)

---

## Upgrading to v0.0.11

### Release Date

2025-10-13

### What Changed

#### 1. License Change: MIT → GPL-2.0-only

**Why**: MAQET vendors QEMU Python bindings (GPL-2.0), making MAQET a derivative work that must also be GPL-2.0.

**Impact on Your Project**:

| Your Use Case | Impact | Action Required |
|---------------|--------|-----------------|
| Using MAQET as CLI tool | None | No changes needed |
| Using MAQET as Python library in GPL-compatible project | None | No changes needed |
| Using MAQET as Python library in proprietary/MIT project | **Significant** | Review GPL compatibility |

**GPL-2.0 Compatibility**:

- GPL-2.0, GPL-3.0: Compatible
- Apache 2.0, BSD, MIT: May require license change if using as library
- Proprietary: May require commercial license or license change

**Resources**:

- [GPL FAQ](https://www.gnu.org/licenses/gpl-faq.html)
- [License Compatibility](https://www.gnu.org/licenses/license-list.html)

**Alternatives if GPL is incompatible**:

1. Use MAQET v0.0.7 (MIT-licensed, but lacks security fixes)
2. Fork before v0.0.8 and maintain separately (not recommended)
3. Use MAQET only as CLI tool via subprocess (preserves license separation)

#### 2. Critical Security Fixes

**Automatic** - No action required, but be aware:

- **Unix Socket Permissions**: Changed from 755 to 600
  - Sockets now only accessible by owner
  - Multi-user systems: Only VM owner can control VMs (expected behavior)
  - If you need multi-user access, use sudo or group permissions (not recommended)

- **Path Traversal Protection**: System directories now blocked
  - Cannot create storage in /etc, /sys, /proc, /boot, /root, /usr, /var
  - If your config specifies system paths, you'll get `ValueError`
  - **Fix**: Update storage paths to user directories (e.g., /home/user/vms/)

```yaml
# Before (v0.0.10 and earlier - DANGEROUS)
storage:
  - name: system-disk
    file: /etc/my-disk.qcow2  # Allowed but dangerous

# After (v0.0.11 - SECURE)
storage:
  - name: system-disk
    file: /etc/my-disk.qcow2  # ValueError: Refusing to create storage in system directory
```

**Migration**:

```yaml
# Use user directories instead
storage:
  - name: system-disk
    file: ~/vms/my-disk.qcow2  # Safe
  # OR
  - name: system-disk
    file: /home/user/vms/my-disk.qcow2  # Safe
```

#### 3. Performance Improvements

**Automatic** - No action required:

- Database queries 100x faster with 100 VMs (O(n) → O(log n))
- Binary lookups cached (qemu-img path)

### Installation

```bash
# Upgrade from any previous version
pip install --upgrade maqet

# Verify version
maqet --version
# Should show: maqet 0.0.11
```

### API Compatibility

**No breaking API changes** - All existing code works:

```python
# This code works in v0.0.7, v0.0.8, v0.0.10, and v0.0.11
from maqet import Maqet

maqet = Maqet()
vm_id = maqet.add(name='myvm', vm_config='config.yaml')
maqet.start(vm_id)
maqet.stop(vm_id)
```

### Configuration Compatibility

**Breaking change**: System directory paths now rejected

```yaml
# This will fail in v0.0.11:
storage:
  - name: disk
    file: /etc/disk.qcow2  # ValueError

# Fix: Use user directory
storage:
  - name: disk
    file: ~/vms/disk.qcow2  # OK
```

### Testing Your Migration

```bash
# 1. Backup existing VMs
cp -r ~/.local/share/maqet ~/.local/share/maqet.backup

# 2. Upgrade
pip install --upgrade maqet

# 3. Test basic operations
maqet ls
maqet add test.yaml --name test-vm
maqet start test-vm
maqet stop test-vm
maqet rm test-vm

# 4. If issues occur, rollback:
pip install maqet==0.0.10
rm -rf ~/.local/share/maqet
mv ~/.local/share/maqet.backup ~/.local/share/maqet
```

---

## Upgrading to v0.0.8

### Release Date

2025-10-11

### What Changed

#### QEMU Vendoring

MAQET now vendors QEMU Python bindings internally instead of using the external `qemu.qmp` package.

**Before** (v0.0.7 and earlier):

```bash
pip install maqet[qemu]  # Installed external qemu.qmp dependency
```

**After** (v0.0.8+):

```bash
pip install maqet  # QEMU bindings included automatically
```

### Why This Change?

The official `qemu.qmp` PyPI package had reliability issues:

- Inconsistent packaging across platforms
- Installation failures on some systems
- Version conflicts with other packages

Vendoring ensures:

- Consistent installation across all platforms
- No external dependency on unreliable package
- Controlled QEMU version

### Migration Steps

1. **Uninstall old version** (if installed with `[qemu]` extra):

   ```bash
   pip uninstall maqet qemu.qmp
   ```

2. **Install new version**:

   ```bash
   pip install maqet
   ```

3. **Verify installation**:

   ```bash
   maqet --version
   python -c "from maqet import Maqet; print('OK')"
   ```

### API Compatibility

**No code changes needed** if you use MAQET's API:

```python
# This works in both v0.0.7 and v0.0.8+
from maqet import Maqet

maqet = Maqet()
vm_id = maqet.add(name='myvm', vm_config='config.yaml')
```

**Code changes needed** if you import QEMU directly:

```python
# Before (v0.0.7 - external dependency)
from qemu.machine import QEMUMachine
from qemu.qmp import QMPClient

# After (v0.0.8+ - vendored, but DO NOT import directly)
# Instead, use MAQET's API methods:
maqet.qmp(vm_id, 'query-status')  # Use this
maqet.start(vm_id)                # Use this
```

**Recommendation**: Always use MAQET's API methods instead of direct QEMU imports.

---

## Upgrading from v0.0.7

If upgrading directly from v0.0.7 to v0.0.11, you'll experience all changes from v0.0.8, v0.0.9, v0.0.10, and v0.0.11.

### Summary of All Changes

1. **License**: MIT → GPL-2.0-only (v0.0.11)
2. **QEMU**: External dependency → Vendored (v0.0.8)
3. **Security**: Socket permissions fixed, path traversal blocked (v0.0.11)
4. **Performance**: Database queries optimized (v0.0.11)
5. **Installation**: `maqet[qemu]` → `maqet` (v0.0.8)

### Migration Path

```bash
# 1. Backup
cp -r ~/.local/share/maqet ~/.local/share/maqet.backup

# 2. Uninstall old version
pip uninstall maqet qemu.qmp

# 3. Install latest
pip install maqet

# 4. Update storage paths in configs (if using system directories)
# Edit your YAML configs to use user directories

# 5. Review license compatibility (if using as library)
# See "License Change" section above

# 6. Test
maqet ls
maqet add test.yaml --name test-vm
```

---

## Common Migration Issues

### Issue: "ValueError: Refusing to create storage in system directory"

**Cause**: v0.0.11 blocks storage in system directories for security.

**Fix**: Update your config to use user directories:

```yaml
# Bad
storage:
  - file: /etc/disk.qcow2

# Good
storage:
  - file: ~/vms/disk.qcow2
  # OR
  - file: /home/yourusername/vms/disk.qcow2
```

### Issue: "ModuleNotFoundError: No module named 'qemu.qmp'"

**Cause**: Upgrading from v0.0.7 without uninstalling first.

**Fix**:

```bash
pip uninstall maqet qemu.qmp
pip install maqet
```

### Issue: "License incompatibility with my project"

**Cause**: v0.0.11 is GPL-2.0, your project is proprietary/MIT.

**Options**:

1. Use MAQET as CLI tool only (via subprocess) - preserves license separation
2. Change your project license to GPL-compatible
3. Stay on v0.0.7 (MIT) - but missing security fixes (not recommended)

**CLI-only example** (preserves your project's MIT license):

```python
# Your MIT-licensed project
import subprocess

# Use MAQET as external tool (no GPL contamination)
result = subprocess.run(['maqet', 'start', 'myvm'], capture_output=True)
```

### Issue: "Socket permission denied"

**Cause**: v0.0.11 uses 600 permissions (user-only).

**Expected**: Only the user who created the VM can control it.

**If you need multi-user access** (not recommended for security):

```bash
# Option 1: Use sudo
sudo maqet start vm-name

# Option 2: Run as specific user
su - otheruser -c "maqet start vm-name"
```

---

## Getting Help

- **Issues**: <https://gitlab.com/m4x0n_24/maqet/issues>
- **Documentation**: <https://gitlab.com/m4x0n_24/maqet/blob/main/README.md>
- **Changelog**: <https://gitlab.com/m4x0n_24/maqet/blob/main/CHANGELOG.md>

---

## Version Compatibility Matrix

| Feature | v0.0.7 | v0.0.8 | v0.0.9 | v0.0.10 | v0.0.11 |
|---------|--------|--------|--------|---------|---------|
| License | MIT | GPL-2.0 | GPL-2.0 | GPL-2.0 | GPL-2.0 |
| QEMU Dependency | External | Vendored | Vendored | Vendored | Vendored |
| Socket Security | 755 (insecure) | 755 | 755 | 755 | 600 (secure) |
| Path Traversal Protection | No | No | No | No | Yes |
| DB Performance | O(n) | O(n) | O(n) | O(n) | O(log n) |
| Installation | `maqet[qemu]` | `maqet` | `maqet` | `maqet` | `maqet` |

**Recommendation**: Always use the latest version (v0.0.11) for security and performance.
