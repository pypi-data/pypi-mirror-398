"""
CLI Generator

Automatically generates argparse CLI commands from @api_method decorated methods.

This module implements the CLI interface generation component of MAQET's unified API system.
It takes method metadata and creates a complete command-line interface with proper argument
parsing, help text, and command routing.

The CLIGenerator converts Python method signatures into argparse subcommands, handling:
- Required and optional parameters
- Type conversion (str, int, bool, list)
- Default values and help text
- Command examples and documentation
- Error handling and validation

Path Handling:
- Functions accept Union[str, Path] for path parameters
- Internally uses pathlib.Path objects for all path operations
- Converts to str only when calling external APIs (subprocess, argparse)

Example:
    @api_method(cli_name="start", description="Start VM")
    def start(self, vm_id: str, detach: bool = False):
        pass

    Becomes CLI command:
    $ maqet start myvm --detach
"""

import argparse
import inspect
import logging
import sys
from pathlib import Path
from typing import Any, List, Optional, Union, get_args, get_origin

from ..api import APIMethodMetadata, APIRegistry
from ..config import RuntimeConfig
from ..constants import ExitCode
from ..exceptions import (
    VMNotFoundError,
    VMAlreadyExistsError,
    ConfigFileNotFoundError,
    ConfigValidationError,
    InvalidConfigurationError,
    SecurityError,
    SnapshotNotFoundError,
    WaitTimeout,
)
from ..logger import configure_file_logging, set_verbosity
from .base_generator import BaseGenerator

LOG = logging.getLogger(__name__)


class CLIGenerator(BaseGenerator):
    """
    Generates CLI commands from @api_method decorated methods.

    This generator creates an argparse-based CLI that automatically
    maps CLI arguments to method parameters and executes the appropriate
    method on the Maqet instance.

    Key Features:
    - Automatic subcommand generation from method metadata
    - Type-aware argument parsing (bool flags, optional args, etc.)
    - Built-in help generation with examples and descriptions
    - Global options support (--verbose, --config-dir, etc.)
    - Proper error handling and user feedback

    Usage:
        generator = CLIGenerator(maqet_instance, API_REGISTRY)
        result = generator.run(sys.argv[1:])

    The generator automatically creates CLI commands like:
    - maqet add config.yaml --name myvm
    - maqet start myvm --detach
    - maqet qmp myvm system_powerdown
    """

    def __init__(self, maqet_instance: Any, registry: APIRegistry):
        """
        Initialize CLI generator.

        Args:
            maqet_instance: Instance of Maqet class
            registry: API registry containing method metadata
        """
        super().__init__(maqet_instance, registry)
        self.parser: Optional[argparse.ArgumentParser] = None
        # Load runtime configuration for defaults
        self.runtime_config = RuntimeConfig()

    def generate(self) -> argparse.ArgumentParser:
        """
        Generate argparse CLI from registered methods.

        Returns:
            Configured ArgumentParser
        """
        # Create parent parser with global options for subparsers
        # This allows global options AFTER subcommands (e.g., maqet ls -v)
        self.global_parent = argparse.ArgumentParser(add_help=False)
        self._add_global_options_to_parent()

        # Create main parser with global options at top level
        # This allows global options BEFORE subcommands (e.g., maqet -v ls)
        self.parser = argparse.ArgumentParser(
            prog="maqet",
            description="MAQET - M4x0n's QEMU Tool for VM management",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # Add global options directly to main parser (for before subcommand)
        self._add_global_options_to_main()

        # Add subcommands
        subparsers = self.parser.add_subparsers(
            dest="command", help="Available commands", metavar="COMMAND"
        )

        # Group methods by parent (None for top-level, string for nested)
        parent_groups = {}
        for category in self.registry.get_categories():
            methods = self.registry.get_by_category(category)
            for metadata in methods:
                if not metadata.hidden:
                    parent = metadata.parent
                    if parent not in parent_groups:
                        parent_groups[parent] = []
                    parent_groups[parent].append(metadata)

        # Add top-level commands (parent=None)
        if None in parent_groups:
            for metadata in parent_groups[None]:
                self._add_subcommand(subparsers, metadata)

        # Add parent commands with nested subcommands
        for parent, child_methods in parent_groups.items():
            if parent is not None:
                self._add_parent_command(subparsers, parent, child_methods)

        return self.parser

    def run(self, args: Optional[List[str]] = None) -> Any:
        """
        Parse arguments and execute the appropriate method.

        Args:
            args: Command line arguments (defaults to sys.argv[1:])

        Returns:
            Result of method execution
        """
        if self.parser is None:
            self.generate()

        parsed_args = self.parser.parse_args(args)

        # Configure logging based on verbosity flags
        self._configure_logging(parsed_args)

        if not hasattr(parsed_args, "command") or parsed_args.command is None:
            self.parser.print_help()
            sys.exit(ExitCode.INVALID_ARGS)

        # Determine which command to execute (handle nested subcommands)
        command_name = parsed_args.command

        # Check if this is a nested subcommand
        if hasattr(parsed_args, "subcommand") and parsed_args.subcommand:
            # This is a nested command (e.g., maqet qmp pause)
            metadata = self.registry.get_by_cli_name(parsed_args.subcommand)
            if not metadata:
                print(
                    f"Error: Unknown subcommand '{parsed_args.subcommand}'",
                    file=sys.stderr,
                )
                sys.exit(ExitCode.INVALID_ARGS)
        else:
            # This is a top-level command (e.g., maqet start)
            metadata = self.registry.get_by_cli_name(command_name)
            if not metadata:
                print(
                    f"Error: Unknown command '{command_name}'",
                    file=sys.stderr,
                )
                sys.exit(ExitCode.INVALID_ARGS)

        # Execute method
        try:
            result = self._execute_method(metadata, parsed_args)
            return result
        except Exception as e:
            cmd_display = (
                f"{command_name} {parsed_args.subcommand}"
                if hasattr(parsed_args, "subcommand") and parsed_args.subcommand
                else command_name
            )
            # Map exceptions to exit codes
            exit_code = self._get_exit_code_for_exception(e)
            print(
                f"Error executing {cmd_display}: {e}", file=sys.stderr
            )
            sys.exit(exit_code)

    def _add_global_options(self, parser: argparse.ArgumentParser) -> None:
        """
        Add global CLI options to any parser.

        These options are available both before and after subcommands.
        Defaults are loaded from maqet.conf if available.

        Args:
            parser: ArgumentParser to add options to
        """
        # Get defaults from runtime config
        verbosity_default = self.runtime_config.get_verbosity()
        config_dir_default = self.runtime_config.get_config_dir()
        data_dir_default = self.runtime_config.get_data_dir()
        runtime_dir_default = self.runtime_config.get_runtime_dir()
        log_file_default = self.runtime_config.get_log_file()

        # Build help messages that show config file source
        config_source = (
            f" (from {self.runtime_config.config_file_path})"
            if self.runtime_config.config_file_path
            else ""
        )

        parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=verbosity_default,
            help=f"Increase verbosity: -v=warnings+errors, -vv=info, -vvv=debug "
            f"(default: {verbosity_default}=errors only{config_source})",
        )
        # Directory flags are pre-parsed in __main__.py before Maqet creation
        # to allow proper CLI > config file > XDG precedence order
        parser.add_argument(
            "--maqet-config-dir",
            default=config_dir_default,
            help="Override maqet's config directory path"
            + (f" (default: {config_dir_default})" if config_dir_default else ""),
        )
        parser.add_argument(
            "--maqet-data-dir",
            default=data_dir_default,
            help="Override maqet's data directory path"
            + (f" (default: {data_dir_default})" if data_dir_default else ""),
        )
        parser.add_argument(
            "--maqet-runtime-dir",
            default=runtime_dir_default,
            help="Override maqet's runtime directory path"
            + (f" (default: {runtime_dir_default})" if runtime_dir_default else ""),
        )
        parser.add_argument(
            "--log-file",
            default=log_file_default,
            help="Enable file logging to specified path"
            + (f" (default: {log_file_default})" if log_file_default else ""),
        )

    def _add_global_options_to_parent(self) -> None:
        """
        Add global CLI options to parent parser (inherited by all subcommands).
        """
        self._add_global_options(self.global_parent)

    def _add_global_options_to_main(self) -> None:
        """
        Add global CLI options to main parser (before subcommand).
        """
        self._add_global_options(self.parser)

    def _configure_logging(self, args: argparse.Namespace) -> None:
        """
        Configure logging based on CLI arguments.

        Verbosity mapping:
        - 0 (no -v):    ERROR level (default, errors only)
        - 1 (-v):       WARNING level (shows warnings + errors)
        - 2 (-vv):      INFO level
        - 3+ (-vvv+):   DEBUG level

        Args:
            args: Parsed command line arguments
        """
        verbosity = getattr(args, "verbose", 0)

        # Direct mapping: verbosity count = logger level
        set_verbosity(verbosity)

        # File logging setup (unchanged)
        log_file = getattr(args, "log_file", None)
        if log_file:
            from pathlib import Path

            configure_file_logging(Path(log_file))

    def _add_subcommand(
        self,
        subparsers: argparse._SubParsersAction,
        metadata: APIMethodMetadata,
    ) -> None:
        """
        Add a subcommand for a method.

        Args:
            subparsers: Argparse subparsers object
            metadata: Method metadata
        """
        # Create subparser with global parent to inherit global options
        sub = subparsers.add_parser(
            metadata.cli_name,
            help=metadata.description,
            description=metadata.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[self.global_parent],
        )

        # Add aliases if specified
        for alias in metadata.aliases:
            subparsers._name_parser_map[alias] = sub

        # Add method parameters as arguments (excluding **kwargs)
        for param_name, param in metadata.parameters.items():
            if param.kind != inspect.Parameter.VAR_KEYWORD:  # Skip **kwargs
                self._add_parameter_argument(sub, metadata, param_name, param)

        # Special handling for apply command: add common config parameters
        if metadata.cli_name == "apply":
            self._add_apply_config_parameters(sub)

        # Add examples to help if available
        if metadata.examples:
            examples_text = "\nExamples:\n" + "\n".join(
                f"  {example}" for example in metadata.examples
            )
            sub.epilog = examples_text

    def _add_parent_command(
        self,
        subparsers: argparse._SubParsersAction,
        parent_name: str,
        child_methods: List[APIMethodMetadata],
    ) -> None:
        """
        Add a parent command with nested subcommands.

        Args:
            subparsers: Argparse subparsers object
            parent_name: Name of the parent command (e.g., 'qmp')
            child_methods: List of child method metadata
        """
        # Create parent subparser with global parent to inherit global options
        parent_parser = subparsers.add_parser(
            parent_name,
            help=f"{parent_name.upper()} subcommands",
            description=f"{parent_name.upper()} subcommands",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[self.global_parent],
        )

        # Add nested subparsers for child commands
        child_subparsers = parent_parser.add_subparsers(
            dest="subcommand",
            help="Available subcommands",
            metavar="SUBCOMMAND",
        )

        # Add each child method as a nested subcommand
        for metadata in child_methods:
            self._add_subcommand(child_subparsers, metadata)

    def _add_parameter_argument(
        self,
        parser: argparse.ArgumentParser,
        metadata: APIMethodMetadata,
        param_name: str,
        param: inspect.Parameter,
    ) -> None:
        """
        Add an argument for a method parameter.

        Args:
            parser: Argument parser
            metadata: Method metadata for context
            param_name: Parameter name
            param: Parameter metadata
        """
        # Determine argument properties
        is_required = param.default == inspect.Parameter.empty
        arg_name = param_name.replace("_", "-")

        # Check for Union[str, List[str]] type for multiple files support
        is_multiple_files = self._is_multiple_files_param(param)

        # Special handling for vm_id parameters - make them positional for
        # better UX
        is_vm_id_param = param_name == "vm_id"

        # For rm command, vm_id should be optional positional since it has
        # --all alternative
        is_rm_command = metadata.cli_name == "rm"

        # Special handling for VAR_POSITIONAL parameters (*args)
        is_var_positional = param.kind == inspect.Parameter.VAR_POSITIONAL

        if param.annotation == bool:
            # Boolean flags
            if is_required:
                # Required boolean (rare case)
                parser.add_argument(
                    f"--{arg_name}",
                    action="store_true",
                    required=True,
                    help=f"{param_name} (required boolean flag)",
                )
            else:
                # Optional boolean flag
                default_value = (
                    param.default
                    if param.default != inspect.Parameter.empty
                    else False
                )
                parser.add_argument(
                    f"--{arg_name}",
                    action=(
                        "store_true" if not default_value else "store_false"
                    ),
                    default=default_value,
                    help=f"{param_name} (default: {default_value})",
                )
        elif is_multiple_files:
            # Multiple files parameter (Union[str, List[str]])
            if is_required:
                parser.add_argument(
                    param_name,
                    nargs="+",
                    help=f"{param_name} (one or more files)",
                )
            else:
                parser.add_argument(
                    f"--{arg_name}",
                    nargs="*",
                    default=param.default,
                    help=f"{param_name} (one or more files, default: {
                        param.default})",
                )
        elif is_vm_id_param:
            # Special handling for vm_id parameters - make them positional for
            # better UX
            if is_rm_command:
                # For rm command, vm_id is optional positional since --all is
                # alternative
                parser.add_argument(
                    param_name,
                    nargs="?",
                    default=param.default,
                    help=f"{
                        param_name} (VM name or ID, optional when using --all)",
                )
            elif is_required:
                # Regular required vm_id (for start, stop, status, etc.)
                parser.add_argument(
                    param_name, help=f"{param_name} (VM name or ID, required)"
                )
            else:
                # Optional vm_id but still positional
                parser.add_argument(
                    param_name,
                    nargs="?",
                    default=param.default,
                    help=f"{param_name} (VM name or ID, optional)",
                )
        elif is_var_positional:
            # VAR_POSITIONAL parameters (*args) - use nargs='*' for zero or
            # more
            parser.add_argument(
                param_name,
                nargs="*",
                help=f"{param_name} (zero or more values)",
            )
        elif is_required:
            # Required positional argument
            # Extract type from annotation for proper parsing
            arg_type = self._get_arg_type(param)
            if arg_type:
                parser.add_argument(
                    param_name, type=arg_type, help=f"{param_name} (required)"
                )
            else:
                parser.add_argument(param_name, help=f"{param_name} (required)")
        else:
            # Optional argument with default
            # Extract type from annotation for proper parsing
            arg_type = self._get_arg_type(param)
            if arg_type:
                parser.add_argument(
                    f"--{arg_name}",
                    type=arg_type,
                    default=param.default,
                    help=f"{param_name} (default: {param.default})",
                )
            else:
                parser.add_argument(
                    f"--{arg_name}",
                    default=param.default,
                    help=f"{param_name} (default: {param.default})",
                )

    def _get_arg_type(self, param: inspect.Parameter) -> Optional[type]:
        """
        Extract concrete type from parameter annotation for argparse.

        Handles Optional[T] by extracting T, and returns basic types
        that argparse can handle (int, float, str).

        Args:
            param: Parameter to extract type from

        Returns:
            Type for argparse, or None if no type annotation or complex type
        """
        if param.annotation == inspect.Parameter.empty:
            return None

        # Handle Optional[T] (which is Union[T, None])
        origin = get_origin(param.annotation)
        if origin is Union:
            args = get_args(param.annotation)
            # Filter out NoneType from Optional[T]
            non_none_types = [arg for arg in args if arg is not type(None)]
            if len(non_none_types) == 1:
                # This is Optional[T], use T
                annotation = non_none_types[0]
            else:
                # Complex union, can't determine single type
                return None
        else:
            annotation = param.annotation

        # Return basic types that argparse supports
        if annotation in (int, float, str):
            return annotation

        return None

    def _is_multiple_files_param(self, param: inspect.Parameter) -> bool:
        """
        Check if parameter accepts multiple files (Union[str, List[str]]).

        Args:
            param: Parameter to check

        Returns:
            True if parameter accepts multiple files
        """
        if param.annotation == inspect.Parameter.empty:
            return False

        # Check for Union[str, List[str]] or similar patterns
        origin = get_origin(param.annotation)
        if origin is Union:
            args = get_args(param.annotation)
            # Check for Union[str, List[str]] pattern
            has_str = str in args
            has_list_str = any(
                get_origin(arg) is list and get_args(arg) == (str,)
                for arg in args
            )
            return has_str and has_list_str

        return False

    def _execute_method(
        self, metadata: APIMethodMetadata, args: argparse.Namespace
    ) -> Any:
        """
        Execute a method with parsed arguments.

        Args:
            metadata: Method metadata
            args: Parsed command line arguments

        Returns:
            Method execution result
        """
        # Extract method parameters from parsed args
        method_kwargs = {}
        method_args = []

        # Check if method has VAR_POSITIONAL (*args) parameter
        has_var_positional = any(
            param.kind == inspect.Parameter.VAR_POSITIONAL
            for param in metadata.parameters.values()
        )

        # Collect positional parameters that come before VAR_POSITIONAL
        positional_params = []
        for param_name, param in metadata.parameters.items():
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                positional_params.append((param_name, param))
            elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                break  # Stop when we hit VAR_POSITIONAL

        for param_name, param in metadata.parameters.items():
            # Skip **kwargs parameters
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                continue

            # Convert parameter names (dashes to underscores)
            arg_name = param_name.replace("_", "-")

            # Get value from args
            if hasattr(args, param_name):
                value = getattr(args, param_name)
            elif hasattr(args, arg_name):
                value = getattr(args, arg_name.replace("-", "_"))
            else:
                continue

            if value is not None:
                # Handle VAR_POSITIONAL parameters (*args) specially
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    # For *args parameters, extend the args list
                    if isinstance(value, list):
                        method_args.extend(value)
                    else:
                        method_args.append(value)
                elif (
                    param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                    and has_var_positional
                ):
                    # When method has VAR_POSITIONAL, regular positional params
                    # must go in method_args to avoid "multiple values" error
                    method_args.insert(0, value)
                else:
                    # Everything else goes in kwargs
                    method_kwargs[param_name] = value

        # Special handling for apply command: collect config parameters as
        # kwargs
        if metadata.cli_name == "apply":
            config_params = {}
            for param_name in ["memory", "cpu", "binary", "enable_kvm"]:
                arg_name = param_name.replace("_", "-")
                if hasattr(args, arg_name.replace("-", "_")):
                    value = getattr(args, arg_name.replace("-", "_"))
                    if value is not None:
                        config_params[param_name] = value

            # Add config parameters to method kwargs
            method_kwargs.update(config_params)

        # Resolve config file paths to absolute paths for consistent handling
        if "config" in method_kwargs and method_kwargs["config"] is not None:

            config = method_kwargs["config"]
            if isinstance(config, str):
                # Single config file - resolve to absolute path
                method_kwargs["config"] = str(Path(config).resolve())
            elif isinstance(config, list):
                # Multiple config files - resolve each to absolute path
                method_kwargs["config"] = [str(Path(c).resolve()) for c in config]

        # Execute method directly
        method = getattr(self.maqet_instance, metadata.name)

        # Execute method with both positional and keyword arguments
        return method(*method_args, **method_kwargs)

    def _add_apply_config_parameters(
        self, parser: argparse.ArgumentParser
    ) -> None:
        """
        Add common configuration parameters for the apply command.

        Args:
            parser: Argument parser for the apply subcommand
        """
        # Memory configuration
        parser.add_argument(
            "--memory", type=str, help="VM memory size (e.g., 2G, 4096M)"
        )

        # CPU configuration
        parser.add_argument("--cpu", type=int, help="Number of CPU cores")

        # Binary path
        parser.add_argument("--binary", type=str, help="Path to QEMU binary")

        # KVM enablement
        parser.add_argument(
            "--enable-kvm", action="store_true", help="Enable KVM acceleration"
        )

    def _get_exit_code_for_exception(self, exception: Exception) -> int:
        """
        Map exception types to appropriate exit codes.

        This method implements the exit code convention for consistent
        error reporting across all maqet commands.

        Args:
            exception: Exception that was raised

        Returns:
            Appropriate exit code based on exception type

        Exit Code Mapping:
            - ExitCode.INVALID_ARGS (3): Invalid arguments or preconditions not met
              * VMNotFoundError
              * VMAlreadyExistsError
              * SnapshotNotFoundError
              * ConfigFileNotFoundError
              * ConfigValidationError
              * InvalidConfigurationError
            - ExitCode.PERMISSION_DENIED (4): Permission errors
              * SecurityError
              * PermissionError
              * OSError with permission-related errno
            - ExitCode.TIMEOUT (2): Timeout conditions
              * WaitTimeout
            - ExitCode.FAILURE (1): All other errors
              * DatabaseLockError
              * MaqetError
              * Unexpected exceptions
        """
        # INVALID_ARGS (3): Invalid arguments or preconditions not met
        if isinstance(exception, (
            VMNotFoundError,
            VMAlreadyExistsError,
            SnapshotNotFoundError,
            ConfigFileNotFoundError,
            ConfigValidationError,
            InvalidConfigurationError,
        )):
            return ExitCode.INVALID_ARGS

        # PERMISSION_DENIED (4): Permission-related errors
        if isinstance(exception, (SecurityError, PermissionError)):
            return ExitCode.PERMISSION_DENIED

        # Check for OSError with permission-related errno
        if isinstance(exception, OSError):
            import errno
            if exception.errno in (errno.EACCES, errno.EPERM):
                return ExitCode.PERMISSION_DENIED

        # TIMEOUT (2): Timeout conditions
        if isinstance(exception, WaitTimeout):
            return ExitCode.TIMEOUT

        # FAILURE (1): Database locks and other failures
        # Default for all other MaqetError and unexpected exceptions
        return ExitCode.FAILURE
