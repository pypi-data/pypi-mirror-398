# CLI Configuration and Flag Precedence

This guide explains how maqet determines configuration values when the same setting can come from multiple sources (CLI flags, environment variables, configuration files, and defaults).

## Table of Contents

- [Precedence Order](#precedence-order)
- [Configuration Sources](#configuration-sources)
- [Common Flags Reference](#common-flags-reference)
- [Practical Examples](#practical-examples)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Precedence Order

When the same configuration value is specified in multiple places, maqet uses this precedence order (highest to lowest):

1. **Command-line flags** (highest priority)
2. **Configuration file** (`maqet.conf`)
3. **Environment variables** (XDG spec)
4. **Built-in defaults** (lowest priority)

This means:

- CLI flags ALWAYS win, even if a config file exists
- Config file values override environment variables
- Environment variables override built-in defaults
- Built-in defaults are used only when nothing else is specified

---

## Configuration Sources

### 1. Command-Line Flags (Highest Priority)

CLI flags are specified on the command line and always take precedence.

**Examples**:

```bash
# Directory overrides
maqet ls --maqet-data-dir /custom/data
maqet start myvm --maqet-runtime-dir /tmp/test-runtime
maqet add config.yaml --maqet-config-dir ~/my-configs

# Logging overrides
maqet start myvm -vv                    # Verbosity level 2 (info)
maqet start myvm --log-file /tmp/debug.log  # File logging
```

**Available directory flags**:

- `--maqet-data-dir DIR` - Override data directory path
- `--maqet-config-dir DIR` - Override config directory path
- `--maqet-runtime-dir DIR` - Override runtime directory path

**Available logging flags**:

- `-v, --verbose` - Increase verbosity (-v=warnings, -vv=info, -vvv=debug)
- `--log-file PATH` - Enable file logging to specified path

### 2. Configuration File (maqet.conf)

Configuration files provide persistent settings without needing CLI flags.

**Search order** (first found wins):

1. `MAQET_CONFIG` environment variable path
2. `./maqet.conf` or `./.maqet.conf` (current directory)
3. `~/.config/maqet/maqet.conf` (user config)
4. `/etc/maqet/maqet.conf` (system-wide)

**Example maqet.conf**:

```yaml
directories:
  data_dir: ~/custom/maqet/data
  config_dir: ~/custom/maqet/config
  runtime_dir: /tmp/maqet-runtime

logging:
  verbosity: 2  # 0=errors, 1=warnings, 2=info, 3=debug
  log_file: ~/logs/maqet.log
```

See [Runtime Configuration Guide](../runtime-configuration.md) for complete config file documentation.

### 3. Environment Variables

Environment variables follow the XDG Base Directory Specification.

**XDG variables**:

- `XDG_DATA_HOME` - Base for data directory (default: `~/.local/share`)
- `XDG_CONFIG_HOME` - Base for config directory (default: `~/.config`)
- `XDG_RUNTIME_DIR` - Base for runtime directory (default: `/run/user/$(id -u)`)

**MAQET-specific variable**:

- `MAQET_CONFIG` - Path to configuration file

**Example**:

```bash
# Override data directory via environment
export XDG_DATA_HOME=/custom/data
maqet ls  # Uses /custom/data/maqet for database

# Specify config file location
export MAQET_CONFIG=/opt/maqet/maqet.conf
maqet start myvm  # Loads config from /opt/maqet/maqet.conf
```

### 4. Built-in Defaults (Lowest Priority)

When nothing else is specified, maqet uses XDG-compliant defaults:

- **Data directory**: `~/.local/share/maqet` (or `$XDG_DATA_HOME/maqet`)
- **Config directory**: `~/.config/maqet` (or `$XDG_CONFIG_HOME/maqet`)
- **Runtime directory**: `/run/user/$(id -u)/maqet` (or `$XDG_RUNTIME_DIR/maqet`)
- **Verbosity**: 0 (errors only)
- **Log file**: None (console only)

---

## Common Flags Reference

### Global Flags (Available on All Commands)

| Flag | Environment Variable | Config Key | Default | Description |
|------|---------------------|------------|---------|-------------|
| `--maqet-data-dir` | `$XDG_DATA_HOME/maqet` | `directories.data_dir` | `~/.local/share/maqet` | VM database and state |
| `--maqet-config-dir` | `$XDG_CONFIG_HOME/maqet` | `directories.config_dir` | `~/.config/maqet` | Configuration files |
| `--maqet-runtime-dir` | `$XDG_RUNTIME_DIR/maqet` | `directories.runtime_dir` | `/run/user/$(id -u)/maqet` | Runtime sockets and PIDs |
| `-v, --verbose` | N/A | `logging.verbosity` | 0 (errors only) | Logging verbosity |
| `--log-file` | N/A | `logging.log_file` | None | File logging path |

### Verbosity Levels

| Flag | Level | What You See |
|------|-------|--------------|
| (none) | 0 | Errors only |
| `-v` | 1 | Errors + warnings |
| `-vv` | 2 | Errors + warnings + info |
| `-vvv` | 3 | Errors + warnings + info + debug |

### Command-Specific Flags

See individual command help for command-specific flags:

```bash
maqet COMMAND --help
```

Examples:

- `maqet start --help`
- `maqet add --help`
- `maqet snapshot --help`

---

## Practical Examples

### Example 1: CLI Flag Overrides Config File

**Scenario**: Config file sets data directory, but you want to use a different one for testing.

**Config file** (`~/.config/maqet/maqet.conf`):

```yaml
directories:
  data_dir: ~/production/maqet
```

**CLI usage**:

```bash
# Production (uses config file)
maqet ls
# Uses: ~/production/maqet

# Testing (CLI flag overrides config)
maqet ls --maqet-data-dir /tmp/test-maqet
# Uses: /tmp/test-maqet (config file ignored)
```

**Precedence**: CLI flag (highest) > config file

### Example 2: Config File Overrides Environment

**Scenario**: XDG environment variable exists, but config file overrides it.

**Environment**:

```bash
export XDG_DATA_HOME=/custom/data
```

**Config file** (`./maqet.conf`):

```yaml
directories:
  data_dir: ~/project-vms
```

**Result**:

```bash
maqet ls
# Uses: ~/project-vms (from config file)
# NOT: /custom/data/maqet (environment ignored)
```

**Precedence**: Config file > environment variable

### Example 3: Environment Overrides Defaults

**Scenario**: No config file, but environment variable set.

**Environment**:

```bash
export XDG_RUNTIME_DIR=/tmp/custom-runtime
```

**Result**:

```bash
maqet start myvm
# Runtime sockets in: /tmp/custom-runtime/maqet
# NOT: /run/user/$(id -u)/maqet (default)
```

**Precedence**: Environment variable > built-in default

### Example 4: Complete Precedence Chain

**Scenario**: Same setting from all four sources.

**Setup**:

```bash
# Environment variable
export XDG_DATA_HOME=/env/data

# Config file (~/. config/maqet/maqet.conf)
# directories:
#   data_dir: ~/config/data

# CLI flag
maqet ls --maqet-data-dir /cli/data
```

**Result**: Uses `/cli/data` (CLI flag wins)

**If you remove CLI flag**:

```bash
maqet ls
```

**Result**: Uses `~/config/data` (config file wins)

**If you also remove config file**:

```bash
rm ~/.config/maqet/maqet.conf
maqet ls
```

**Result**: Uses `/env/data/maqet` (environment wins)

**If you also unset environment**:

```bash
unset XDG_DATA_HOME
maqet ls
```

**Result**: Uses `~/.local/share/maqet` (default)

### Example 5: Per-Project Configuration

**Scenario**: Different settings for different projects.

**Project structure**:

```bash
~/projects/
├── dev-project/
│   └── maqet.conf          # Development settings
├── test-project/
│   └── maqet.conf          # Testing settings
└── prod-project/
    └── maqet.conf          # Production settings
```

**dev-project/maqet.conf**:

```yaml
directories:
  runtime_dir: /tmp/dev-vms
logging:
  verbosity: 3  # Debug logging
```

**test-project/maqet.conf**:

```yaml
directories:
  runtime_dir: /tmp/test-vms
logging:
  verbosity: 2  # Info logging
```

**Usage**:

```bash
cd ~/projects/dev-project
maqet start myvm
# Uses: /tmp/dev-vms and debug logging

cd ~/projects/test-project
maqet start myvm
# Uses: /tmp/test-vms and info logging
```

### Example 6: Temporary Override for Debugging

**Scenario**: Enable debug logging for one command without changing config.

**Config file**:

```yaml
logging:
  verbosity: 0  # Errors only
```

**Debugging**:

```bash
# Normal operation (quiet)
maqet start myvm

# Debug one command (verbose)
maqet start another-vm -vvv --log-file /tmp/debug.log
# Verbosity: 3 (debug) - overrides config
# Also saves to file for later analysis

# Back to normal
maqet ls
# Verbosity: 0 (from config)
```

---

## Verification

### Check Effective Configuration

You can verify which configuration values are being used:

#### Check Directories

```bash
# List VMs (shows database location in verbose mode)
maqet ls -v

# Check where data is stored
ls -la ~/.local/share/maqet/instances.db  # Default
# OR
ls -la $(custom-data-dir)/instances.db    # If overridden
```

#### Check Runtime Directory

```bash
# Check socket locations
ls -la /run/user/$(id -u)/maqet/sockets/  # Default
# OR
ls -la $(custom-runtime-dir)/sockets/     # If overridden
```

#### Check Loaded Config File

```bash
# Enable debug logging to see which config file was loaded
maqet ls -vvv 2>&1 | grep "config file"
# Output: "Found config file: /path/to/maqet.conf"
# OR: "No maqet.conf file found, using defaults"
```

### Verify Precedence

Test precedence with a simple experiment:

```bash
# 1. Create test config file
cat > /tmp/test-maqet.conf << 'YAML'
directories:
  data_dir: /tmp/from-config
YAML

# 2. Test config file wins over default
MAQET_CONFIG=/tmp/test-maqet.conf maqet ls -vv 2>&1 | grep data
# Should show: /tmp/from-config

# 3. Test CLI flag wins over config
MAQET_CONFIG=/tmp/test-maqet.conf maqet ls --maqet-data-dir /tmp/from-cli -vv 2>&1 | grep data
# Should show: /tmp/from-cli

# 4. Cleanup
rm /tmp/test-maqet.conf
```

---

## Troubleshooting

### Issue: CLI Flag Not Working

**Symptom**: CLI flag seems ignored, config file value used instead.

**Cause**: Flag specified AFTER the command instead of before subcommand arguments.

**Wrong**:

```bash
maqet start myvm --maqet-data-dir /tmp/test  # Flag ignored!
```

**Correct**:

```bash
maqet --maqet-data-dir /tmp/test start myvm  # Flag recognized
# OR
maqet start --maqet-data-dir /tmp/test myvm  # Also works
```

**Why**: Global flags can appear before the subcommand OR before subcommand arguments.

### Issue: Config File Not Loading

**Symptom**: Config file exists but settings not applied.

**Diagnosis**:

```bash
# Check which file maqet finds
maqet ls -vvv 2>&1 | grep -i config

# Should see one of:
# "Found config file: /path/to/maqet.conf"
# "No maqet.conf file found, using defaults"
```

**Common causes**:

1. **Wrong location**: File not in search path
2. **Wrong filename**: Must be exactly `maqet.conf` or `.maqet.conf`
3. **YAML syntax error**: File not parsed

**Solutions**:

```bash
# 1. Verify file location
ls -la maqet.conf
ls -la ~/.config/maqet/maqet.conf

# 2. Validate YAML syntax
python3 -c "import yaml; print(yaml.safe_load(open('maqet.conf')))"

# 3. Force specific config file
MAQET_CONFIG=/path/to/maqet.conf maqet ls -vv
```

### Issue: Environment Variable Unexpected Value

**Symptom**: Settings don't match what you expect.

**Diagnosis**:

```bash
# Check current environment
echo "XDG_DATA_HOME: $XDG_DATA_HOME"
echo "XDG_CONFIG_HOME: $XDG_CONFIG_HOME"
echo "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
echo "MAQET_CONFIG: $MAQET_CONFIG"
```

**Solution**: Unset or export correct values:

```bash
# Unset to use defaults
unset XDG_DATA_HOME

# OR set correct value
export XDG_DATA_HOME=~/custom/data
```

### Issue: Can't Find VMs After Changing Data Directory

**Symptom**: `maqet ls` shows no VMs, but you created them before.

**Cause**: Data directory changed, now looking at wrong database.

**Solution**:

```bash
# Find your old database
find ~ -name "instances.db" -type f

# Use correct data directory
maqet ls --maqet-data-dir /path/to/old/data

# OR copy database to new location
cp /old/path/.local/share/maqet/instances.db /new/path/.local/share/maqet/
```

---

## Summary

**Key Takeaways**:

1. CLI flags always win (highest priority)
2. Config files override environment variables
3. Environment variables override defaults
4. Use config files for persistent settings
5. Use CLI flags for temporary overrides
6. Use `-vvv` to debug which values are used

**Quick Reference**:

```
Priority (highest to lowest):
1. --maqet-data-dir FLAG
2. maqet.conf: directories.data_dir
3. $XDG_DATA_HOME/maqet
4. ~/.local/share/maqet (default)
```

**Related Documentation**:

- [Runtime Configuration Guide](../runtime-configuration.md) - Complete maqet.conf reference
- [Configuration Guide](configuration.md) - VM configuration (YAML files)
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

---

**Last Updated**: 2025-10-29
**MAQET Version**: 0.0.14
