# Database Migration Guide

This guide explains how maqet handles database schema migrations when upgrading between versions, and how to troubleshoot migration issues.

## Table of Contents

- [Overview](#overview)
- [Automatic Migration](#automatic-migration)
- [Migration History](#migration-history)
- [Understanding Migration Process](#understanding-migration-process)
- [Backup and Restore](#backup-and-restore)
- [Troubleshooting](#troubleshooting)
- [Manual Migration](#manual-migration)

---

## Overview

### What Are Database Migrations?

Maqet stores VM state in a SQLite database (`instances.db`). When new features are added, the database schema must be updated to support them. Database migrations are the automated process of updating your existing database to the new schema.

### When Do Migrations Happen?

Migrations run automatically when:

1. You upgrade to a new maqet version with schema changes
2. You run any maqet command for the first time after upgrading
3. The database schema version is older than what maqet expects

### Migration Architecture Changes

**v0.0.13 Architectural Change**: Per-VM Process Architecture

Starting with v0.0.13 (current development), maqet moved from a single-process architecture to a per-VM process architecture where each VM runs in its own dedicated process (`vm_runner.py`). This change required database schema updates to track per-VM processes.

**Key architectural changes**:

- **Old (v0.0.12 and earlier)**: Single maqet process managed all VMs
- **New (v0.0.13+)**: Each VM runs in separate VMRunner process
- **Database impact**: Added `runner_pid` and `qmp_socket_path` columns to track per-VM processes

---

## Automatic Migration

### How It Works

Migrations happen automatically and transparently:

1. **Detection**: Maqet checks database schema version on startup
2. **Backup**: Automatic backup created before migration (for safety)
3. **Migration**: Schema changes applied sequentially
4. **Verification**: Schema version updated after successful migration

**Example first run after upgrade**:

```bash
$ maqet ls
# Migration happens silently on first use
VM Name    Status    PID     Created
--------   -------   -----   -------------------
myvm       stopped   -       2025-10-15 10:23:45
```

### What Gets Migrated

Migrations can include:

- **Adding columns**: New fields for new features
- **Removing columns**: Deprecated fields cleaned up
- **Creating indexes**: Performance optimizations
- **Data transformations**: Updating existing data format

### Safety Features

1. **Automatic backups**: Database backed up before migration
2. **Atomic transactions**: Migrations succeed completely or rollback
3. **Version checking**: Migrations only run when needed
4. **Idempotent**: Safe to run multiple times

### Backup Location

Automatic backups are created in the same directory as the database:

```bash
# Default location
~/.local/share/maqet/instances.db.backup-YYYYMMDD-HHMMSS

# Example
~/.local/share/maqet/instances.db.backup-20251029-143022
```

---

## Migration History

### Schema Version Timeline

| Schema Version | Maqet Version | Changes | Migration Function |
|----------------|---------------|---------|-------------------|
| 1 | v0.0.1 - v0.0.12 | Initial schema | N/A |
| 2 | v0.0.13 | Added `runner_pid` column for per-VM processes | `migrate_v1_to_v2` |
| 3 | v0.0.13 | Added `auth_secret` column for socket authentication | `migrate_v2_to_v3` |
| 4 | v0.0.13 | Removed `auth_secret` column (moved to ephemeral files) | `migrate_v3_to_v4` |
| 5 | v0.0.13+ | Added `qmp_socket_path` column for cross-process QMP | `migrate_v4_to_v5` |

### v0.0.12 to v0.0.13 Migration Details

**Major architectural change**: Single-process to per-VM process architecture.

**Schema changes**:

1. **Added `runner_pid` column** (v1 → v2):
   - Stores PID of VMRunner process for each VM
   - Enables per-VM process tracking
   - Indexed for fast lookups

2. **Added `auth_secret` column** (v2 → v3):
   - Initially stored authentication secrets in database
   - Used for IPC socket authentication

3. **Removed `auth_secret` column** (v3 → v4):
   - Security improvement: Secrets moved to ephemeral files
   - Database no longer stores sensitive auth data
   - Files deleted when VM stops

4. **Added `qmp_socket_path` column** (v4 → v5):
   - Stores QMP socket path for cross-process communication
   - Enables CLI to send QMP commands to running VMs
   - Solves cross-process QMP communication issue

**Impact on users**:

- **Automatic**: Migrations run on first use after upgrade
- **Transparent**: Existing VMs continue working
- **Safe**: Automatic backups created
- **No data loss**: All VM configurations preserved

---

## Understanding Migration Process

### Migration Workflow

```
┌─────────────────┐
│ Maqet Starts    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Check Schema Version    │
│ Current: 1              │
│ Required: 5             │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Create Backup           │
│ instances.db.backup-... │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Run Migrations          │
│ v1→v2→v3→v4→v5          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Update Schema Version   │
│ Set version = 5         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Continue Normal         │
│ Operation               │
└─────────────────────────┘
```

### Migration Code Location

Migrations are defined in `maqet/state.py`:

```python
# Migration registry
MIGRATIONS: Dict[int, callable] = {
    2: migrate_v1_to_v2,   # Add runner_pid
    3: migrate_v2_to_v3,   # Add auth_secret
    4: migrate_v3_to_v4,   # Remove auth_secret
    5: migrate_v4_to_v5,   # Add qmp_socket_path
}
```

Each migration is implemented as a separate function using the Template Method Pattern via `ColumnMigration` base class.

---

## Backup and Restore

### Manual Backup Before Upgrade

While maqet creates automatic backups, you can create manual backups for extra safety:

```bash
# Backup database
cp ~/.local/share/maqet/instances.db \
   ~/.local/share/maqet/instances.db.manual-backup

# Backup entire data directory (includes storage)
cp -r ~/.local/share/maqet \
      ~/.local/share/maqet.backup-$(date +%Y%m%d)

# Verify backup
ls -lh ~/.local/share/maqet.backup-*
```

### Restore from Backup

If migration fails or causes issues:

```bash
# Stop all VMs first
maqet ls
maqet stop --all  # If this command exists
# OR manually:
for vm in $(maqet ls --format=plain | awk '{print $1}'); do
    maqet stop "$vm" --force
done

# Restore database
cp ~/.local/share/maqet/instances.db.backup-YYYYMMDD-HHMMSS \
   ~/.local/share/maqet/instances.db

# OR restore full backup
rm -rf ~/.local/share/maqet
cp -r ~/.local/share/maqet.backup-YYYYMMDD \
      ~/.local/share/maqet

# Verify VMs
maqet ls
```

### Backup Best Practices

1. **Before major upgrades**: Manual backup before upgrading maqet
2. **Regular backups**: Backup database weekly if running production VMs
3. **Test restores**: Verify backups can be restored successfully
4. **Multiple backups**: Keep several backup generations

---

## Troubleshooting

### Issue: "Database is locked" During Migration

**Symptom**: Migration fails with "database is locked" error.

**Cause**: Another maqet process is accessing the database.

**Solution**:

```bash
# 1. Check for running maqet processes
ps aux | grep maqet

# 2. Stop all maqet processes
pkill -f maqet

# 3. Check for running VMs
ps aux | grep qemu

# 4. Stop running VMs if safe
# (or wait for them to finish)

# 5. Retry operation
maqet ls
```

### Issue: Migration Fails Midway

**Symptom**: Error during migration, database in unknown state.

**Cause**: Unexpected error during migration (disk full, permissions, etc.).

**Solution**:

```bash
# 1. Check available disk space
df -h ~/.local/share/maqet

# 2. Check permissions
ls -la ~/.local/share/maqet/instances.db

# 3. Check database integrity
sqlite3 ~/.local/share/maqet/instances.db "PRAGMA integrity_check;"
# Expected: ok

# 4. If corrupted, restore from backup
cp ~/.local/share/maqet/instances.db.backup-YYYYMMDD-HHMMSS \
   ~/.local/share/maqet/instances.db

# 5. Free up space if needed
df -h
# Clean up old VMs
maqet rm old-vm --force

# 6. Retry
maqet ls
```

### Issue: Missing VMs After Migration

**Symptom**: VMs not listed after migration.

**Diagnosis**:

```bash
# 1. Check database exists
ls -la ~/.local/share/maqet/instances.db

# 2. Check database content
sqlite3 ~/.local/share/maqet/instances.db \
    "SELECT name, status FROM vm_instances;"

# 3. Check schema version
sqlite3 ~/.local/share/maqet/instances.db \
    "SELECT value FROM schema_version;"
```

**Common causes**:

1. **Wrong data directory**: Migration ran on different database
2. **Restore used old backup**: Backup from before VMs created
3. **Data corruption**: Database corrupted during migration

**Solutions**:

```bash
# Check for multiple databases
find ~ -name "instances.db" -type f

# Use correct data directory
maqet ls --maqet-data-dir /correct/path

# If database corrupted, restore latest backup
cp ~/.local/share/maqet/instances.db.backup-* \
   ~/.local/share/maqet/instances.db
```

### Issue: "Column already exists" Error

**Symptom**: Migration fails with "duplicate column name" error.

**Cause**: Migration was partially applied or run multiple times.

**Diagnosis**:

```bash
# Check current schema
sqlite3 ~/.local/share/maqet/instances.db ".schema vm_instances"
```

**Solution**:

This shouldn't happen with maqet's migration system (migrations check if columns exist), but if it does:

```bash
# 1. Restore from backup before migration
cp ~/.local/share/maqet/instances.db.backup-YYYYMMDD-HHMMSS \
   ~/.local/share/maqet/instances.db

# 2. Retry
maqet ls

# 3. If still failing, report bug
# Include output of:
sqlite3 ~/.local/share/maqet/instances.db ".schema"
maqet --version
```

### Issue: Downgrade After Migration

**Symptom**: Want to downgrade to older maqet version after migration.

**Problem**: Older versions don't understand new schema.

**Solution**:

```bash
# 1. Restore database backup from before migration
cp ~/.local/share/maqet/instances.db.backup-YYYYMMDD-HHMMSS \
   ~/.local/share/maqet/instances.db

# 2. Downgrade maqet
pip install maqet==0.0.12  # Or desired version

# 3. Verify
maqet --version
maqet ls
```

**Warning**: Any VMs created/modified after migration will be lost when restoring backup.

---

## Manual Migration

### When to Manually Migrate

You should NOT need to manually migrate. Migrations are automatic.

Manual migration is only needed if:

- Developing maqet and testing migrations
- Recovering from migration failure
- Debugging migration issues

### Manual Migration Process

**WARNING**: Only for advanced users and developers.

```bash
# 1. Backup database
cp ~/.local/share/maqet/instances.db \
   ~/.local/share/maqet/instances.db.manual-backup

# 2. Connect to database
sqlite3 ~/.local/share/maqet/instances.db

# 3. Check current schema version
SELECT value FROM schema_version;

# 4. Apply migrations manually (example: v1 → v2)
-- Add runner_pid column
ALTER TABLE vm_instances ADD COLUMN runner_pid INTEGER;
CREATE INDEX IF NOT EXISTS idx_vm_runner_pid ON vm_instances(runner_pid);

-- Update schema version
UPDATE schema_version SET value = 2;

# 5. Verify
.schema vm_instances
SELECT value FROM schema_version;

# 6. Exit
.quit

# 7. Test maqet
maqet ls
```

### Verifying Migration Success

```bash
# Check schema version
sqlite3 ~/.local/share/maqet/instances.db \
    "SELECT value FROM schema_version;"
# Should show: 5 (or latest version)

# Check new columns exist
sqlite3 ~/.local/share/maqet/instances.db ".schema vm_instances"
# Should include: runner_pid, qmp_socket_path

# Test VM operations
maqet ls
maqet status myvm
maqet start myvm
```

---

## Migration FAQ

### Q: Will migration delete my VMs?

**A**: No. Migrations only change the database schema, not VM data. All VM configurations, disk images, and settings are preserved.

### Q: How long does migration take?

**A**: Usually instant (< 1 second) for most databases. Large databases (100+ VMs) may take a few seconds.

### Q: Can I skip migrations?

**A**: No. Migrations are required for maqet to work correctly with the new version. You can downgrade to an older version if needed (see troubleshooting).

### Q: What if migration fails?

**A**: Maqet creates automatic backups. Restore from backup (see [Restore from Backup](#restore-from-backup)) and report the issue.

### Q: Can I run old and new maqet versions simultaneously?

**A**: No. Once database is migrated to new schema, old versions won't understand it. Use separate data directories if you need multiple versions:

```bash
# Old version
maqet --maqet-data-dir ~/maqet-old ls

# New version
maqet --maqet-data-dir ~/maqet-new ls
```

### Q: Where are migration backups stored?

**A**: Same directory as database: `~/.local/share/maqet/instances.db.backup-YYYYMMDD-HHMMSS`

### Q: How do I check my schema version?

**A**:

```bash
sqlite3 ~/.local/share/maqet/instances.db \
    "SELECT value FROM schema_version;"
```

---

## Best Practices

1. **Backup before upgrading**: Manual backup before major version upgrades
2. **Test in dev environment**: Test upgrades in development environment first
3. **Read release notes**: Check CHANGELOG.md for breaking changes
4. **Keep backups**: Maintain several backup generations
5. **Monitor first run**: Watch output when running first command after upgrade
6. **Verify VMs**: Check `maqet ls` works after migration

---

## Related Documentation

- [CHANGELOG.md](../../CHANGELOG.md) - Version history and breaking changes
- [Migration Guide](../../docs/MIGRATION.md) - Version-specific migration guides
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Architecture Documentation](../architecture/vm-lifecycle.md) - VM lifecycle and state management

---

**Last Updated**: 2025-10-29
**MAQET Version**: 0.0.14
**Current Schema Version**: 5

**Remember**: Migrations are automatic, safe, and designed to preserve your data. If you encounter issues, restore from backup and report the problem.
