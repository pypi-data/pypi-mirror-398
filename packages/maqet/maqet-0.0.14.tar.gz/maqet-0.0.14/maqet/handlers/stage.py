# from subprocess import check_output
import os
import signal
import subprocess
import tempfile
from pathlib import Path
from time import sleep

from maqet.handlers.base import Handler, HandlerError
from maqet.logger import LOG
from maqet.qmp import commands as qmp_commands
from maqet.qmp.keyboard import KeyboardEmulator as kb


class StageHandler(Handler):
    """
    Handles execution of pipeline stages. Methods are tasks
    """


@StageHandler.method
def launch(state: dict):
    state.vm.launch()


@StageHandler.method
def shutdown(state,
             hard: bool = False,
             timeout: int = 30) -> None:
    state.vm.shutdown(hard=hard, timeout=timeout)


@StageHandler.method
def wait_for_input(state, prompt: str = ""):
    input(prompt)


@StageHandler.method
def wait_for_shutdown(state):
    while state.vm.is_running():
        sleep(3)


@StageHandler.method
def qmp_key(state, keys: [str],
            hold_time: int = 1,
            **kwargs):
    command = kb.press_keys(*keys, hold_time=hold_time)
    qmp_run_command(state.vm, **command)


def qmp_run_command(vm,
                    command: str,
                    arguments: dict = None):
    r = vm.qmp(cmd=command,
               args_dict=arguments)
    LOG.info(f"QMP: {command} {arguments} {r}")


@StageHandler.method
def qmp_type(state, text, type_delay: int = 10,
             hold_time: int = 1, ** kwargs):
    for command in kb.type_string(string=text,
                                  hold_time=hold_time):
        qmp_run_command(state.vm, **command)
        sleep(type_delay/1000)


@StageHandler.method
def qmp(state,
        cmd: str = None,
        args_dict: dict = None,
        command: str = None,
        arguments: dict = None):
    # Support both old and new parameter names for backward compatibility
    command = command or cmd
    arguments = arguments or args_dict
    qmp_run_command(
        vm=state.vm,
        command=command,
        arguments=arguments
    )


@StageHandler.method
def qmp_screendump(state, filename: str):
    command = qmp_commands.qmp_screendump(filename)
    qmp_run_command(state.vm, **command)


@StageHandler.method
def qmp_stop(state):
    command = qmp_commands.qmp_stop()
    qmp_run_command(state.vm, **command)


@StageHandler.method
def qmp_cont(state):
    command = qmp_commands.qmp_cont()
    qmp_run_command(state.vm, **command)


@StageHandler.method
def qmp_pmemsave(state, filename: str):
    # Get the memory size from the machine's memory attribute
    size_bytes = state.vm.memory
    # Set address to 0 to dump all memory
    address = 0
    command = qmp_commands.qmp_pmemsave(address, size_bytes, filename)
    qmp_run_command(state.vm, **command)


@StageHandler.method
def wait(state, time: float):
    sleep(float(time))


@StageHandler.method
def bash(state, script: str, silent=False, blocking=True, fatal=True, **kwargs):
    LOG.debug(f"Executing bash script: {script}")

    if not blocking:
        raise HandlerError(
            "Non-blocking bash tasks are not currently supported.")

    process = None
    script_path = None
    try:
        # For silent execution, redirect stdout and stderr
        stdout = subprocess.DEVNULL if silent else None
        stderr = subprocess.DEVNULL if silent else None

        # SECURITY: Write script to temporary file to avoid shell=True vulnerability
        # This prevents command injection attacks
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script)
            script_path = Path(f.name)

        # Set secure permissions (owner read+execute only)
        script_path.chmod(0o500)

        # Use Popen for better control over signal handling
        # Execute with explicit bash interpreter (shell=False) - SAFE
        process = subprocess.Popen(
            ['/bin/bash', str(script_path)],
            shell=False,
            stdout=stdout,
            stderr=stderr
        )

        # Wait for the process to complete
        returncode = process.wait()

        if fatal and returncode != 0:
            raise subprocess.CalledProcessError(returncode, script)

        LOG.debug(f"Bash script exited with return code {returncode}")

    except subprocess.CalledProcessError as e:
        LOG.critical(f"A critical error occurred in a bash script, which exited with code {
                     e.returncode}.")
        LOG.critical(f"Script: {script}")
        # The exception will be caught by the main loop, which will shut down the VM
        raise HandlerError(f"Bash script failed with exit code {e.returncode}")
    except FileNotFoundError:
        raise HandlerError(
            "Could not find the specified shell or command to execute the script.")
    except KeyboardInterrupt:
        LOG.info("Bash script interrupted by user (Ctrl+C)")
        if process:
            try:
                # Immediately send SIGKILL to the entire process group for immediate termination
                os.killpg(process.pid, signal.SIGKILL)
                # Wait briefly for the process to die
                process.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                # Process might already be dead
                pass
        raise
    finally:
        # Clean up temporary script file
        if script_path:
            try:
                script_path.unlink(missing_ok=True)
            except Exception as e:
                LOG.warning(f"Failed to cleanup temp script {script_path}: {e}")


@StageHandler.method
def echo(state, text: str):
    print(text)


@StageHandler.method
def snapshot(state, drive: str, name: str,
             overwrite: bool = False, **kwargs):
    if drive not in state.storage:
        raise HandlerError(f"Drive {drive} not exists")

    state.storage[drive].snapshot(name, overwrite)


@StageHandler.method
def device_add(state, driver: str, id: str, **kwargs):
    """Adds a device to the VM using QMP."""
    command = qmp_commands.qmp_device_add(driver, id, **kwargs)
    qmp_run_command(state.vm, **command)


@StageHandler.method
def device_del(state, id: str):
    """Removes a device from the VM using QMP."""
    command = qmp_commands.qmp_device_del(id)
    qmp_run_command(state.vm, **command)
