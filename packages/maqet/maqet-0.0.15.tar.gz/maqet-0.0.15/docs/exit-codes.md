# Exit Codes and Error Handling

Maqet uses consistent exit codes across all commands to enable reliable automation without the need for post-operation verification.

## Standard Exit Codes

| Code | Name | Meaning | When to Use |
|------|------|---------|-------------|
| 0 | SUCCESS | Operation completed successfully | VM started, snapshot created, etc. |
| 1 | FAILURE | Operation failed, state may be inconsistent | QEMU crashed, database error, unexpected failure |
| 2 | TIMEOUT | Operation timed out but may complete async | VM didn't become ready within timeout period |
| 3 | INVALID_ARGS | Invalid arguments or preconditions not met | VM doesn't exist, invalid configuration |
| 4 | PERMISSION_DENIED | Insufficient permissions | Cannot write to data directory, permission error |

## Exit Code Conventions

### SUCCESS (0)

Returned when the operation completes successfully.

```bash
$ maqet ls
test-vm    stopped

$ echo $?
0
```

### FAILURE (1)

Returned when an operation fails and the VM state may be inconsistent. This includes:

- QEMU process failures
- Database errors
- Unexpected exceptions
- General errors that don't fit other categories

```bash
$ maqet start broken-vm --wait
Error executing start: QEMU failed to start

$ echo $?
1
```

### TIMEOUT (2)

Returned when an operation times out, but may still complete asynchronously in the background.

```bash
$ maqet start slow-vm --wait --wait-for=ssh-ready --timeout=10
Error executing start: Operation timed out after 10s

$ echo $?
2  # VM may still be booting, check with: maqet status slow-vm
```

### INVALID_ARGS (3)

Returned when:

- VM doesn't exist
- Snapshot doesn't exist
- Configuration file not found
- Configuration validation fails
- Invalid argument combinations

```bash
$ maqet start nonexistent-vm
Error executing start: VM 'nonexistent-vm' not found

$ echo $?
3
```

### PERMISSION_DENIED (4)

Returned when the operation fails due to insufficient permissions:

- Cannot create socket files
- Cannot write to data directory
- Cannot read configuration files

```bash
$ maqet start test-vm
Error executing start: Permission denied: cannot create socket /var/run/maqet/test-vm.sock

$ echo $?
4
```

## Usage Examples

### Basic Error Handling

```bash
#!/bin/bash

if maqet start my-vm --wait; then
    echo "VM started successfully"
else
    exit_code=$?
    case $exit_code in
        1)
            echo "VM failed to start"
            maqet logs my-vm  # Check logs
            ;;
        2)
            echo "VM start timed out (may still be booting)"
            sleep 10
            maqet status my-vm  # Check if it started
            ;;
        3)
            echo "Invalid VM configuration or VM doesn't exist"
            ;;
        4)
            echo "Permission denied"
            ;;
    esac
    exit $exit_code
fi
```

### Automation Without Verification

With reliable exit codes, you no longer need "trust but verify" patterns:

```bash
# Before: Trust but verify
maqet start my-vm
if ! pgrep -f "qemu.*my-vm" > /dev/null; then
    echo "VM didn't actually start"
    exit 1
fi

# After: Trust exit codes
if ! maqet start my-vm --wait; then
    echo "VM failed to start (exit code: $?)"
    exit 1
fi
```

### Timeout Handling

Distinguish between failures and timeouts:

```bash
#!/bin/bash

maqet start build-vm --wait --timeout=60

case $? in
    0)
        echo "VM ready"
        ;;
    1)
        echo "VM failed to start"
        exit 1
        ;;
    2)
        echo "VM start timed out, giving it more time..."
        sleep 30
        if maqet status build-vm | grep -q "running"; then
            echo "VM is now running"
        else
            echo "VM failed to start"
            exit 1
        fi
        ;;
esac
```

### Pipeline Integration

Use exit codes in CI/CD pipelines:

```bash
set -e  # Exit on any error

# Start VM (will exit with appropriate code on failure)
maqet start test-vm --wait --timeout=120

# Run tests
maqet ssh test-vm -- ./run-tests.sh

# Create snapshot on success
maqet snapshot create test-vm tests-passed

# Stop VM
maqet stop test-vm
```

### Error Type Detection

```bash
#!/bin/bash

maqet snapshot restore my-vm nonexistent-snap

exit_code=$?

if [ $exit_code -eq 3 ]; then
    echo "Snapshot doesn't exist, creating fresh VM instead..."
    maqet start my-vm
elif [ $exit_code -ne 0 ]; then
    echo "Unexpected error (exit code: $exit_code)"
    exit $exit_code
fi
```

## Structured Error Output (JSON)

For machine-readable output, use the `--format=json` flag:

```bash
$ maqet start nonexistent-vm --format=json
{
  "status": "error",
  "code": 1,
  "command": "start",
  "error": "VM 'nonexistent-vm' not found",
  "suggestions": [
    "List available VMs: maqet ls",
    "Create VM: maqet add --name nonexistent-vm <vm-config.yaml>",
    "Check for typos in VM name"
  ]
}

$ echo $?
1
```

Parse with jq:

```bash
#!/bin/bash

output=$(maqet start my-vm --format=json 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
    error=$(echo "$output" | jq -r '.error')
    suggestions=$(echo "$output" | jq -r '.suggestions[]')

    echo "Error: $error"
    echo "Suggestions:"
    echo "$suggestions"

    exit $exit_code
fi
```

## Command-Specific Exit Codes

### start command

```bash
maqet start <vm> [--wait] [--wait-for=<condition>] [--timeout=<seconds>]
```

| Exit Code | Scenario |
|-----------|----------|
| 0 | VM started successfully |
| 1 | QEMU failed to spawn or crashed |
| 2 | Timeout waiting for condition |
| 3 | VM doesn't exist or config invalid |
| 4 | Permission denied (socket, log files) |

### stop command

```bash
maqet stop <vm> [--timeout=<seconds>] [--force]
```

| Exit Code | Scenario |
|-----------|----------|
| 0 | VM stopped successfully |
| 1 | Cannot communicate with VM or stop failed |
| 2 | Graceful shutdown timed out (force-killed) |
| 3 | VM is not running |

### status command

```bash
maqet status <vm> [--format=json]
```

| Exit Code | Scenario |
|-----------|----------|
| 0 | Status retrieved successfully |
| 1 | Cannot access state database |
| 3 | VM doesn't exist |

### snapshot commands

```bash
maqet snapshot {create,restore,list,delete} <vm> [<snapshot>]
```

| Exit Code | Scenario |
|-----------|----------|
| 0 | Operation completed successfully |
| 1 | Snapshot operation failed |
| 3 | VM or snapshot doesn't exist |

## Exception to Exit Code Mapping

Internally, maqet maps exception types to exit codes:

| Exception Type | Exit Code | Examples |
|----------------|-----------|----------|
| VMNotFoundError | 3 | VM doesn't exist |
| VMAlreadyExistsError | 3 | Duplicate VM name |
| SnapshotNotFoundError | 3 | Snapshot doesn't exist |
| ConfigFileNotFoundError | 3 | Config file missing |
| ConfigValidationError | 3 | Invalid configuration |
| WaitTimeout | 2 | Operation timed out |
| SecurityError | 4 | Security violation |
| PermissionError | 4 | Permission denied |
| DatabaseLockError | 1 | Database locked |
| MaqetError (generic) | 1 | General failures |

## Best Practices

1. **Always check exit codes** in automation scripts
2. **Use appropriate timeouts** for operations that may take time
3. **Distinguish between failure types** (failure vs timeout vs invalid args)
4. **Use --format=json** for structured error information in scripts
5. **Handle timeouts gracefully** - VM may still complete in background
6. **Don't suppress errors** - let exit codes propagate to calling scripts

## Troubleshooting

### My script always exits with 1

Check if you're catching specific error types. Generic MaqetError maps to exit code 1.

### Timeout is treated as failure

Use case statements to distinguish exit code 2 (timeout) from exit code 1 (failure).

### Exit code is different in CLI vs Python API

Python API raises exceptions. CLI converts exceptions to exit codes. Check the exception type.

## See Also

- [Error Reporting API](api/error-reporting.md) - Structured error reporting
- [Error Messages](api/error-messages.md) - Actionable error messages
- [Exceptions](api/exceptions.md) - Exception hierarchy
