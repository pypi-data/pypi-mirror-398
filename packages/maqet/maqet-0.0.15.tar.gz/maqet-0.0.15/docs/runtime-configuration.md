# Runtime Configuration (maqet.conf)

Starting with version 0.1, maqet supports runtime configuration files similar
to Ansible's `ansible.cfg`. This allows you to set default values for
directories, logging, and other runtime settings without having to specify
flags on every command.

## Quick Start

Create a `maqet.conf` file in your project directory:

```yaml
# maqet.conf
directories:
  runtime_dir: /tmp/my-project-vms

logging:
  verbosity: 2  # Show info-level logs
```

Now when you run maqet commands in that directory, these settings will be used automatically:

```bash
# These settings come from maqet.conf:
maqet ls  # Uses /tmp/my-project-vms and verbosity=2
```

## Configuration File Hierarchy

maqet searches for configuration files in this order and uses the **first file found**:

1. **Environment variable**: `MAQET_CONFIG=/path/to/config.conf`
2. **Current directory**: `./maqet.conf` or `./.maqet.conf`
3. **User config**: `~/.config/maqet/maqet.conf`
4. **System-wide**: `/etc/maqet/maqet.conf`

This hierarchy follows Ansible's proven approach, allowing you to have:

- Project-specific settings in your project directory
- Personal defaults in your home directory
- System-wide defaults for all users

### Example: Project-Specific Configuration

```bash
# Project structure
my-vm-project/
├── maqet.conf          # Project-specific settings
├── vm-config.yaml      # VM definitions
└── scripts/

# maqet.conf sets runtime_dir for this project
cd my-vm-project
maqet start myvm  # Uses project's runtime_dir
```

## Configuration Precedence

Settings are applied in this order (highest to lowest priority):

1. **CLI flags** (highest priority) - `--maqet-data-dir`, `--maqet-config-dir`, `--maqet-runtime-dir`
2. **Environment variables** (`MAQET_CONFIG` for config file location)
3. **Configuration file** (from hierarchy above)
4. **Built-in defaults** (lowest priority)

### Current Limitations

**Directory CLI flags implemented**: The `--maqet-data-dir`, `--maqet-config-dir`, and
`--maqet-runtime-dir` CLI flags now properly override maqet.conf settings with the
highest priority in the configuration hierarchy

### Example: Override Precedence

```yaml
# maqet.conf
logging:
  verbosity: 1
```

```bash
# Config file sets verbosity=1, but CLI flag overrides it:
maqet ls -vv  # Uses verbosity=2 from CLI flag

# No CLI flag, uses config file:
maqet ls      # Uses verbosity=1 from maqet.conf
```

## Configuration File Format

maqet uses **YAML format** for consistency with VM configuration files.

### Complete Example

```yaml
# maqet.conf

# Directory Configuration
directories:
  # Data directory for VM state database
  # Default: ~/.local/share/maqet (or $XDG_DATA_HOME/maqet)
  data_dir: /custom/data/path

  # Config directory for user configuration files
  # Default: ~/.config/maqet (or $XDG_CONFIG_HOME/maqet)
  config_dir: /custom/config/path

  # Runtime directory for sockets and PID files
  # Default: /tmp/maqet or $XDG_RUNTIME_DIR/maqet
  runtime_dir: /custom/runtime/path

# Logging Configuration
logging:
  # Verbosity level (0=errors, 1=warnings, 2=info, 3=debug)
  verbosity: 2

  # Log file path (null = no file logging)
  log_file: /var/log/maqet/maqet.log
```

### Partial Configuration

You don't need to specify all settings. Unspecified values use defaults:

```yaml
# maqet.conf - minimal example
logging:
  verbosity: 2  # Only set verbosity

# directories.* will use defaults
```

## Configuration Options

### Directories

#### `directories.data_dir`

- **Purpose**: VM state database and persistent data
- **Default**: `~/.local/share/maqet` (or `$XDG_DATA_HOME/maqet`)
- **CLI Override**: `--maqet-data-dir /path`

#### `directories.config_dir`

- **Purpose**: User configuration files
- **Default**: `~/.config/maqet` (or `$XDG_CONFIG_HOME/maqet`)
- **CLI Override**: `--maqet-config-dir /path`

#### `directories.runtime_dir`

- **Purpose**: Temporary files, QMP sockets, PID files
- **Default**: `/tmp/maqet` or `$XDG_RUNTIME_DIR/maqet`
- **CLI Override**: `--maqet-runtime-dir /path`

### Logging

#### `logging.verbosity`

- **Purpose**: Default logging verbosity level
- **Values**:
  - `0`: Errors only (default)
  - `1`: Warnings
  - `2`: Info
  - `3`: Debug
- **CLI Override**: `-v` (warnings), `-vv` (info), `-vvv` (debug)

#### `logging.log_file`

- **Purpose**: Path to log file for persistent logging
- **Default**: `null` (no file logging)
- **CLI Override**: `--log-file /path/to/file.log`

## Use Cases

### Development Environment

```yaml
# ~/projects/my-vm-project/maqet.conf
directories:
  data_dir: ~/projects/my-vm-project/data
  runtime_dir: /tmp/my-vm-project

logging:
  verbosity: 3  # Debug logging for development
  log_file: ~/projects/my-vm-project/maqet.log
```

### Production Environment

```yaml
# /etc/maqet/maqet.conf (system-wide)
directories:
  data_dir: /var/lib/maqet
  runtime_dir: /run/maqet

logging:
  verbosity: 1  # Warnings only
  log_file: /var/log/maqet.log
```

### CI/CD Environment

```yaml
# .maqet.conf (in CI workspace)
directories:
  data_dir: /tmp/ci-maqet-data
  runtime_dir: /tmp/ci-maqet-runtime

logging:
  verbosity: 2
  log_file: /tmp/ci-maqet.log
```

### Personal Defaults

```yaml
# ~/.config/maqet/maqet.conf
logging:
  verbosity: 2  # I always want info-level logs

# No directory overrides - use XDG defaults
```

## Viewing Active Configuration

When you run maqet with `-h` or `--help`, it shows which config file is being used:

```bash
maqet ls -h
# Help text includes:
# -v, --verbose  Increase verbosity (default: 2 from /home/user/project/maqet.conf)
```

## Troubleshooting

### Config File Not Being Used

**Check the search hierarchy:**

```bash
# 1. Check if MAQET_CONFIG is set
echo $MAQET_CONFIG

# 2. Check current directory
ls -la maqet.conf .maqet.conf

# 3. Check user config
ls -la ~/.config/maqet/maqet.conf

# 4. Check system-wide
ls -la /etc/maqet/maqet.conf
```

**Remember**: Only the first file found is used!

### Invalid YAML

If your config file has invalid YAML, maqet will:

1. Log a warning
2. Fall back to defaults

Check your YAML syntax:

```bash
# Test YAML syntax
python -c "import yaml; yaml.safe_load(open('maqet.conf'))"
```

### Debugging Configuration Loading

Enable debug logging to see which config file is loaded:

```bash
# Temporarily enable debug logging
maqet -vvv ls 2>&1 | grep -i config

# Output shows:
# DEBUG: Found config file: /home/user/project/maqet.conf
# DEBUG: Loaded configuration from /home/user/project/maqet.conf
```

## Comparison with Ansible

maqet's configuration system is inspired by Ansible's `ansible.cfg`:

| Feature | Ansible | maqet |
|---------|---------|-------|
| Format | INI | YAML |
| Hierarchy | ENV > CWD > Home > System | ENV > CWD > Home > System |
| First-match | Yes | Yes |
| CLI Override | Yes | Yes |
| Sections | `[defaults]`, `[privilege_escalation]`, etc. | `directories`, `logging`, etc. |

**Why YAML instead of INI?**

- Consistency with maqet's VM configuration files
- Better support for nested structures
- More familiar to maqet users

## VM Configuration vs Runtime Configuration

**Important distinction:**

| Type | File | Purpose | Example |
|------|------|---------|---------|
| **Runtime Config** | `maqet.conf` | CLI behavior, directories, logging | `directories.runtime_dir: /tmp/vms` |
| **VM Config** | `vm-config.yaml` | VM definitions (memory, CPU, storage) | `memory: 4G` |

These are separate systems:

- **Runtime config** affects how maqet runs
- **VM config** defines what VMs to create

## See Also

- [Example maqet.conf](../config/maqet.conf.example)
- [VM Configuration Guide](vm-configuration.md)
- [CLI Reference](cli-reference.md)
