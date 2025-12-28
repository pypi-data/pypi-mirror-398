import logging
import os
import shlex
import signal
import subprocess
from dataclasses import dataclass

from maqet.logger import LOG
from maqet.utils.subprocess_utils import communicate_with_limit


@dataclass(frozen=True)
class CommandResult:
    """Result of shell command execution (immutable).

    This represents a completed command's result and should not be modified
    after creation. The immutability ensures the result remains an accurate
    historical record.

    Attributes:
        stdout: Standard output from command (UTF-8 decoded)
        stderr: Standard error from command (UTF-8 decoded)
        rc: Return code from command

    Note:
        This class is currently not used in production code. It was created
        as part of security hardening (replacing shell=True with shell=False).
        Future code needing safe command execution should use shell_command().
    """
    stdout: str
    stderr: str
    rc: int

    @property
    def success(self) -> bool:
        """Check if command succeeded (return code 0)."""
        return self.rc == 0


def shell_command(command: str, verbose: bool = True) -> CommandResult:
    """Execute shell command safely without shell=True.

    This function uses shlex.split() to parse commands safely, preventing
    shell injection attacks. Commands are executed directly without invoking
    a shell, making metacharacters (;, |, &, etc.) literal arguments rather
    than command separators.

    Args:
        command: Command string to execute (e.g., "ls -la /tmp")
        verbose: Enable verbose logging (default: True)

    Returns:
        CommandResult with stdout, stderr, and return code

    Raises:
        ValueError: If command syntax is invalid or command is empty
        KeyboardInterrupt: If user interrupts execution (Ctrl+C)

    Examples:
        >>> result = shell_command("echo hello")
        >>> assert result.success
        >>> assert "hello" in result.stdout

        >>> result = shell_command("ls /nonexistent")
        >>> assert not result.success
        >>> assert result.rc != 0

    Security:
        This function prevents command injection by using shlex.split() to
        parse arguments and executing with shell=False. Malicious input like
        "ls; rm -rf /" will attempt to execute 'ls' with literal arguments
        ';', 'rm', '-rf', '/' rather than executing two separate commands.
    """
    # Parse command safely - raises ValueError if malformed
    # shlex.split() handles whitespace normalization correctly
    try:
        cmd_args = shlex.split(command)
    except ValueError as e:
        raise ValueError(
            f"Invalid command syntax: {e}\n"
            f"Command: {command!r}\n"
            f"Hint: Check for unclosed quotes or unmatched brackets"
        )

    if not cmd_args:
        raise ValueError(
            f"Empty command after parsing\n"
            f"Input: {command!r}\n"
            f"Hint: Command contains only whitespace"
        )

    # Execute without shell - SAFE from injection
    proc = subprocess.Popen(
        cmd_args,  # Array of arguments, not string
        shell=False,  # CRITICAL: Prevents shell injection
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )

    try:
        # Use output-limited communicate to prevent memory exhaustion
        stdout, stderr = communicate_with_limit(proc)
    except KeyboardInterrupt:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait()
        raise

    output = CommandResult(
        stdout=stdout.decode('utf-8', errors='replace').strip("\n"),
        stderr=stderr.decode('utf-8', errors='replace').strip("\n"),
        rc=proc.returncode
    )

    message = f"command `{command}` returned {output}"

    if verbose:
        level = logging.DEBUG
        if output.stderr != '':
            level = logging.WARNING
        if output.rc != 0:
            level = logging.ERROR

        LOG.log(level, message)

    return output
