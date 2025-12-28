# VM Storage Lifecycle Management

This guide covers MAQET's transactional storage management features for maintaining consistency between VM entries and storage files.

## Table of Contents

- [Overview](#overview)
- [VM Deletion with Storage Control](#vm-deletion-with-storage-control)
- [Detecting Orphaned Storage](#detecting-orphaned-storage)
- [Reattaching Orphaned Storage](#reattaching-orphaned-storage)
- [Verifying Storage Integrity](#verifying-storage-integrity)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

MAQET maintains transactional consistency between VM entries and their storage files. This prevents:

- Orphaned storage (disk images without VM entries)
- Missing storage (VM entries without disk files)
- Disk space leaks from forgotten storage files
- Manual VM configuration recreation

### Key Features

- Explicit storage control during VM deletion
- Orphaned storage detection and recovery
- Storage integrity verification
- Atomic VM and storage operations
- Snapshot preservation options

## VM Deletion with Storage Control

### Default Behavior: Keep Storage

By default, deleting a VM keeps its storage files. This allows you to reattach the storage later or prevents accidental data loss.

```bash
maqet delete my-vm
```

Interactive confirmation shows what will happen:

```
VM: my-vm
Storage files (2):
  - /home/user/.local/share/maqet/disks/my-vm-disk.qcow2 (10240.0 MB)
  - /home/user/.local/share/maqet/disks/my-vm-data.qcow2 (5120.0 MB)

Storage will be KEPT (can reattach later)

Proceed? [y/N]: y
VM 'my-vm' deleted (storage kept)
```

### Deleting Storage with VM

To delete storage along with the VM, use the `--delete-storage` flag:

```bash
maqet delete my-vm --delete-storage
```

Confirmation includes a clear warning:

```
VM: my-vm
Storage files (2):
  - /home/user/.local/share/maqet/disks/my-vm-disk.qcow2 (10240.0 MB)
  - /home/user/.local/share/maqet/disks/my-vm-data.qcow2 (5120.0 MB)

WARNING: Storage will be DELETED (cannot be recovered)

Proceed? [y/N]: y
VM 'my-vm' and storage deleted
```

### Keeping Snapshots

To delete storage but preserve snapshots, combine both flags:

```bash
maqet delete my-vm --delete-storage --keep-snapshots
```

This removes the main disk images but keeps snapshot files for potential recovery.

### Force Deletion

To skip confirmation prompts (use with caution):

```bash
maqet delete my-vm --force
maqet delete my-vm --delete-storage --force
```

### Examples

#### Delete VM, Keep Storage for Later Reuse

```bash
# Delete VM but keep storage (default)
maqet delete test-vm

# Storage remains:
# /home/user/.local/share/maqet/disks/test-vm.qcow2

# Can reattach later to new VM
maqet storage attach recovered-vm \
    /home/user/.local/share/maqet/disks/test-vm.qcow2 \
    --vm-config config.yaml
```

#### Delete VM and All Storage

```bash
# Remove everything
maqet delete old-vm --delete-storage --force

# Both VM entry and storage files are gone
```

#### Delete Storage, Keep Snapshots

```bash
# Before cleanup, create final snapshot
maqet snapshot my-vm create system final-backup

# Delete VM and storage, but keep snapshots
maqet delete my-vm --delete-storage --keep-snapshots

# Snapshot files preserved:
# /home/user/.local/share/maqet/snapshots/my-vm-final-backup.qcow2
```

## Detecting Orphaned Storage

### What is Orphaned Storage?

Orphaned storage consists of disk image files that exist on the filesystem but have no corresponding VM entry in MAQET's database. This typically happens when:

- VMs are deleted with default behavior (keeping storage)
- Manual file operations create disk images outside MAQET
- Database corruption or migration issues
- External tools create QEMU disk images in MAQET directories

### Finding Orphaned Storage

Use the `storage orphaned` command:

```bash
maqet storage orphaned
```

Example output:

```
Found 2 orphaned storage files:

  /home/user/.local/share/maqet/disks/forgotten-vm.qcow2 (10240.0 MB)
  /home/user/.local/share/maqet/disks/old-test.qcow2 (5120.0 MB)

Total: 15360.0 MB

To attach storage to a VM:
  maqet storage attach <vm-name> <storage-path> --vm-config <config>

To delete orphaned storage manually:
  rm <storage-path>
```

### Understanding the Output

The command shows:

- **Path**: Full path to each orphaned storage file
- **Size**: File size in megabytes (actual disk usage)
- **Total**: Sum of all orphaned storage (disk space that can be reclaimed)

### No Orphans Found

If your storage is clean:

```bash
maqet storage orphaned
```

Output:

```
No orphaned storage found
```

### What Gets Scanned

MAQET scans these directories for orphaned storage:

- `~/.local/share/maqet/disks/`
- `~/.local/share/maqet/images/`
- `~/.local/share/maqet/snapshots/`

Files are considered orphaned if:

- They match disk image patterns (\*.qcow2, \*.img, \*.raw)
- No VM in the database references them
- They exist in MAQET's managed directories

## Reattaching Orphaned Storage

### When to Reattach

Reattach orphaned storage when you want to:

- Recover a deleted VM
- Import external disk images into MAQET
- Fix database inconsistencies
- Reuse existing storage for a new VM

### Prerequisites

Before reattaching, you need:

1. **Storage path**: Full path to the orphaned disk image
2. **VM configuration**: YAML file defining the VM settings
3. **VM name**: Unique name for the new VM entry

### Step-by-Step Process

#### 1. Find Orphaned Storage

```bash
maqet storage orphaned
```

Note the path to the storage you want to reattach.

#### 2. Create VM Configuration

Create a YAML file defining the VM that will use this storage:

```yaml
# recovered-vm.yaml
name: recovered-vm
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "4G"
  - smp: 2
  - enable-kvm: null

storage:
  - name: hdd
    type: qcow2
    file: /home/user/.local/share/maqet/disks/forgotten-vm.qcow2
    interface: virtio
```

Important: The `file` path must match the orphaned storage path exactly.

#### 3. Attach Storage

```bash
maqet storage attach recovered-vm \
    /home/user/.local/share/maqet/disks/forgotten-vm.qcow2 \
    --vm-config recovered-vm.yaml
```

Success output:

```
Storage attached to VM 'recovered-vm'
You can now start the VM: maqet start recovered-vm
```

#### 4. Verify and Start

```bash
# Verify VM is registered
maqet ls

# Verify storage is linked
maqet storage verify recovered-vm

# Start the VM
maqet start recovered-vm
```

### Example Workflow: Recovering a Deleted VM

```bash
# 1. Accidentally deleted VM (kept storage)
maqet delete production-db

# 2. Realize mistake, check for orphaned storage
maqet storage orphaned
# Found: /home/user/.local/share/maqet/disks/production-db.qcow2 (50000.0 MB)

# 3. Recreate VM config from backup or memory
cat > production-db-recovery.yaml << 'YAML'
name: production-db
binary: /usr/bin/qemu-system-x86_64

arguments:
  - m: "8G"
  - smp: 4
  - enable-kvm: null

storage:
  - name: system
    type: qcow2
    file: /home/user/.local/share/maqet/disks/production-db.qcow2
    interface: virtio

network:
  - type: user
    hostfwd: "tcp::5432-:5432"
YAML

# 4. Reattach storage
maqet storage attach production-db \
    /home/user/.local/share/maqet/disks/production-db.qcow2 \
    --vm-config production-db-recovery.yaml

# 5. Start recovered VM
maqet start production-db

# VM is back online with all data intact
```

### Troubleshooting Reattachment

#### VM Name Already Exists

```bash
maqet storage attach myvm /path/to/disk.qcow2 --vm-config vm.yaml
# ERROR: VM 'myvm' already exists
```

Solution: Choose a different VM name or delete the existing VM first.

#### Storage File Not Found

```bash
maqet storage attach myvm /wrong/path/disk.qcow2 --vm-config vm.yaml
# ERROR: Storage not found: /wrong/path/disk.qcow2
```

Solution: Verify the path is correct using `maqet storage orphaned`.

#### Configuration Mismatch

If the VM config references a different storage path than the one being attached, you will get an error.

Solution: Ensure the `file` path in the YAML matches the storage path argument.

## Verifying Storage Integrity

### What is Verified

The `storage verify` command checks that all registered storage files for a VM actually exist on disk.

### When to Use Verification

Run verification when:

- You suspect storage files have been manually deleted
- After moving or reorganizing VM storage directories
- When troubleshooting VM startup failures
- As part of regular maintenance checks
- After storage system migrations

### Running Verification

```bash
maqet storage verify my-vm
```

### Success Example

If all storage exists:

```
Checking storage for VM 'my-vm'...
  ✓ /home/user/.local/share/maqet/disks/my-vm-disk.qcow2 (exists)
  ✓ /home/user/.local/share/maqet/disks/my-vm-data.qcow2 (exists)

All storage verified
```

### Failure Example

If storage is missing:

```
Checking storage for VM 'my-vm'...
  ✓ /home/user/.local/share/maqet/disks/my-vm-disk.qcow2 (exists)
  ✗ /home/user/.local/share/maqet/disks/my-vm-data.qcow2 (MISSING)

ERROR: Some storage files are missing
```

### Fixing Missing Storage

If verification shows missing storage:

#### Option 1: Recreate Missing Storage

If the storage can be recreated (e.g., empty data disk):

```bash
# Manually create the missing disk
qemu-img create -f qcow2 \
    /home/user/.local/share/maqet/disks/my-vm-data.qcow2 \
    100G

# Verify again
maqet storage verify my-vm
```

#### Option 2: Restore from Backup

If you have backups:

```bash
# Restore from backup
cp /backups/my-vm-data.qcow2 \
   /home/user/.local/share/maqet/disks/my-vm-data.qcow2

# Verify again
maqet storage verify my-vm
```

#### Option 3: Update VM Configuration

If the storage is no longer needed, update the VM configuration to remove the reference.

### Verification in Scripts

Use verification in automation scripts:

```bash
#!/bin/bash

# Verify storage before starting VM
if maqet storage verify production-vm; then
    echo "Storage verified, starting VM..."
    maqet start production-vm
else
    echo "Storage verification failed, aborting startup"
    exit 1
fi
```

## Common Workflows

### Workflow 1: Temporary Test VM

Create a VM for testing, then clean up completely:

```bash
# 1. Create test VM
maqet add test.yaml --name test-vm
maqet start test-vm

# 2. Run tests...
# (test activities)

# 3. Stop VM
maqet stop test-vm

# 4. Delete VM and all storage
maqet delete test-vm --delete-storage --force

# Everything is cleaned up, no orphaned storage
```

### Workflow 2: VM Archival

Keep VM storage for archival purposes:

```bash
# 1. Create snapshot for reference
maqet snapshot archive-vm create system final-state

# 2. Delete VM, keep storage
maqet delete archive-vm --force

# 3. Move storage to archive location
mkdir -p /archive/vms/2024-11
mv /home/user/.local/share/maqet/disks/archive-vm.qcow2 \
   /archive/vms/2024-11/

# Storage is archived for potential future recovery
```

### Workflow 3: VM Migration

Move VM between systems:

```bash
# On source system:
# 1. Stop VM
maqet stop migrate-vm

# 2. Export configuration
maqet show migrate-vm > migrate-vm.yaml

# 3. Delete VM entry (keep storage)
maqet delete migrate-vm --force

# 4. Copy storage to destination
scp /home/user/.local/share/maqet/disks/migrate-vm.qcow2 \
    destination:/vms/

# On destination system:
# 5. Update config with new storage path
sed -i 's|/home/user/.local/share/maqet/disks|/vms|' migrate-vm.yaml

# 6. Attach storage to new VM entry
maqet storage attach migrate-vm \
    /vms/migrate-vm.qcow2 \
    --vm-config migrate-vm.yaml

# 7. Start VM on new system
maqet start migrate-vm
```

### Workflow 4: Regular Maintenance

Periodic cleanup of orphaned storage:

```bash
#!/bin/bash
# cleanup-orphans.sh - Run monthly

echo "Checking for orphaned storage..."
maqet storage orphaned > /tmp/orphans.txt

if grep -q "No orphaned storage" /tmp/orphans.txt; then
    echo "No orphans found, system is clean"
else
    echo "Orphaned storage detected:"
    cat /tmp/orphans.txt
    echo ""
    echo "Review and manually delete if safe to remove"
fi

# Verify all VMs have valid storage
for vm in $(maqet ls | awk '{print $1}'); do
    echo "Verifying $vm..."
    if ! maqet storage verify "$vm"; then
        echo "WARNING: $vm has missing storage"
    fi
done
```

### Workflow 5: Snapshot-Based Testing

Test changes with snapshots, keep snapshots on cleanup:

```bash
# 1. Create baseline snapshot
maqet snapshot test-vm create system baseline

# 2. Run destructive tests
# (make changes, break things, etc.)

# 3. Delete VM and storage, but keep snapshots
maqet delete test-vm --delete-storage --keep-snapshots

# 4. Later: recover from snapshot if needed
maqet storage attach recovered-vm \
    /home/user/.local/share/maqet/snapshots/test-vm-baseline.qcow2 \
    --vm-config test-vm.yaml
```

## Troubleshooting

### Storage Path Confusion

**Problem**: Cannot find storage files manually

**Solution**:

```bash
# List all VM storage paths
maqet ls | while read vm _; do
    echo "VM: $vm"
    maqet show "$vm" | grep "file:"
done

# Find all QEMU disk images
find ~/.local/share/maqet -name "*.qcow2" -o -name "*.img"
```

### Orphaned Storage Not Detected

**Problem**: Know storage is orphaned but not showing up

**Possible causes**:

1. Storage is outside MAQET's managed directories
2. File extension not recognized (not .qcow2, .img, .raw)
3. File permissions prevent access

**Solution**:

```bash
# Check if file is in managed directory
ls -la ~/.local/share/maqet/disks/

# Check file permissions
ls -l /path/to/suspected/orphan.qcow2

# Manually move to managed directory
mv /external/path/disk.qcow2 ~/.local/share/maqet/disks/

# Run detection again
maqet storage orphaned
```

### Cannot Delete Running VM

**Problem**:

```
ERROR: Cannot delete running VM 'myvm'. Stop it first.
```

**Solution**:

```bash
# Stop VM first
maqet stop myvm

# Then delete
maqet delete myvm --delete-storage
```

### Storage Registry Database Corruption

**Problem**: Storage commands fail with database errors

**Solution**:

```bash
# Check database integrity
sqlite3 ~/.local/share/maqet/maqet.db "PRAGMA integrity_check;"

# If corrupted, restore from backup
cp ~/.local/share/maqet/maqet.db.backup \
   ~/.local/share/maqet/maqet.db

# Re-run storage commands
maqet storage orphaned
```

### Large Amount of Orphaned Storage

**Problem**: Many orphaned files consuming disk space

**Solution**:

```bash
# 1. List all orphans
maqet storage orphaned > orphans.txt

# 2. Review the list carefully
cat orphans.txt

# 3. For each orphan, decide:
#    a) Reattach if needed
#    b) Delete if not needed

# 4. Delete confirmed orphans manually
rm /home/user/.local/share/maqet/disks/old-vm-1.qcow2
rm /home/user/.local/share/maqet/disks/old-vm-2.qcow2

# 5. Verify cleanup
maqet storage orphaned
```

## Best Practices

### 1. Default to Keeping Storage

Unless you are certain you do not need the storage, use the default behavior (keep storage):

```bash
# Safe default
maqet delete my-vm

# Only use --delete-storage when certain
maqet delete temporary-vm --delete-storage
```

### 2. Create Snapshots Before Deletion

Create a final snapshot before deleting VMs with important data:

```bash
# Create final backup snapshot
maqet snapshot important-vm create system final-backup-$(date +%Y%m%d)

# Then delete VM (storage kept)
maqet delete important-vm

# Or delete storage but keep snapshots
maqet delete important-vm --delete-storage --keep-snapshots
```

### 3. Regular Orphan Detection

Schedule monthly orphan detection:

```bash
# Add to crontab
0 0 1 * * maqet storage orphaned | mail -s "Monthly Orphan Report" admin@example.com
```

### 4. Document VM Configurations

Keep VM configurations in version control:

```bash
# Export all VM configs
mkdir -p ~/vm-configs
for vm in $(maqet ls | awk '{print $1}'); do
    maqet show "$vm" > ~/vm-configs/$vm.yaml
done

# Commit to git
cd ~/vm-configs
git add *.yaml
git commit -m "VM configuration snapshot $(date +%Y-%m-%d)"
```

This makes reattachment easier if you need to recover a VM.

### 5. Use Descriptive VM Names

Use names that indicate the VM's purpose and importance:

```bash
# Good names
maqet add --name prod-database-primary ...
maqet add --name dev-test-vm-001 ...
maqet add --name staging-webserver ...

# Less clear names
maqet add --name vm1 ...
maqet add --name test ...
```

This helps when reviewing orphaned storage or deciding what to delete.

### 6. Separate Storage Directories

Organize storage by purpose:

```yaml
storage:
  # Production: /vms/production/
  - name: system
    file: /vms/production/db-primary.qcow2

  # Development: /vms/dev/
  - name: system
    file: /vms/dev/test-vm.qcow2

  # Temporary: /tmp/
  - name: system
    file: /tmp/ephemeral-vm.qcow2
```

This makes it easier to identify what can be safely deleted.

### 7. Verify Before Important Operations

Always verify storage integrity before critical operations:

```bash
# Before backup
maqet storage verify production-vm
maqet snapshot production-vm create system backup-$(date +%Y%m%d)

# Before migration
maqet storage verify migrate-vm
# (proceed with migration)

# Before major updates
maqet storage verify app-server
maqet snapshot app-server create system pre-upgrade
```

### 8. Use Force Flag Sparingly

Avoid `--force` in interactive contexts to prevent accidents:

```bash
# Interactive use: see confirmation
maqet delete test-vm --delete-storage

# Automated scripts: use --force
maqet delete ephemeral-vm --delete-storage --force
```

### 9. Monitor Disk Space

Keep an eye on disk usage:

```bash
# Check MAQET storage usage
du -sh ~/.local/share/maqet/disks/

# Check for orphans periodically
maqet storage orphaned

# Alert if storage exceeds threshold
USAGE=$(du -s ~/.local/share/maqet/disks | awk '{print $1}')
THRESHOLD=100000000  # 100GB in KB
if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "WARNING: MAQET storage exceeds threshold"
    maqet storage orphaned
fi
```

### 10. Test Recovery Procedures

Periodically test your ability to recover VMs:

```bash
# 1. Create test VM
maqet add test-recovery.yaml --name recovery-test

# 2. Delete VM, keep storage
maqet delete recovery-test --force

# 3. Practice recovery
maqet storage orphaned
maqet storage attach recovery-test-restored \
    /path/to/orphan.qcow2 \
    --vm-config test-recovery.yaml

# 4. Verify recovery works
maqet start recovery-test-restored

# 5. Clean up
maqet delete recovery-test-restored --delete-storage --force
```

## See Also

- [Storage Management Guide](storage.md) - QEMU storage types, snapshots, and performance
- [Configuration Guide](configuration.md) - VM configuration details
- [Troubleshooting Guide](troubleshooting.md) - General troubleshooting
- [Quickstart Guide](quickstart.md) - Getting started with MAQET
