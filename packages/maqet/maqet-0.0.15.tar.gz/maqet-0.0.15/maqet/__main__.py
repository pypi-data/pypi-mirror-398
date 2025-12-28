#!/usr/bin/env python3
"""
MAQET CLI Entry Point.

Main CLI interface that uses the unified API generation system.
"""

import argparse
import sys
import traceback

from .__version__ import __version__
from .constants import ExitCode
from .maqet import Maqet


def _preparse_directory_flags():
    """
    Pre-parse directory flags and special flags before creating Maqet instance.

    Uses a minimal parser that only extracts directory flags and special flags
    without interfering with the full CLI parser created later.

    Returns:
        dict: Dictionary with 'data_dir', 'config_dir', 'runtime_dir', 'force_migrate', 'no_auto_cleanup' or None for each
    """
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--maqet-data-dir", dest="data_dir", default=None)
    parser.add_argument("--maqet-config-dir", dest="config_dir", default=None)
    parser.add_argument("--maqet-runtime-dir", dest="runtime_dir", default=None)
    parser.add_argument("--migrate-force", dest="force_migrate", action="store_true", default=False)
    parser.add_argument("--force-migrate", dest="force_migrate_deprecated", action="store_true", default=False, help=argparse.SUPPRESS)
    parser.add_argument("--no-auto-cleanup", dest="no_auto_cleanup", action="store_true", default=False)

    # Parse only known args to avoid errors from other flags
    args, _ = parser.parse_known_args()

    return {
        "data_dir": args.data_dir,
        "config_dir": args.config_dir,
        "runtime_dir": args.runtime_dir,
        "force_migrate": args.force_migrate,
        "force_migrate_deprecated": args.force_migrate_deprecated,
        "no_auto_cleanup": args.no_auto_cleanup,
    }


def main():
    """Execute the main CLI entry point."""
    # Check for --version flag first (before creating Maqet instance)
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"MAQET version {__version__}")
        return ExitCode.SUCCESS

    # Check for debug mode - this enables full tracebacks on errors
    # Note: --debug is different from -v/--verbose which controls log verbosity
    # --debug affects error reporting, -v affects logging levels
    debug_mode = "--debug" in sys.argv
    if debug_mode:
        sys.argv.remove("--debug")

    # Check for --no-auto-cleanup flag and remove it from argv
    # (it will be re-parsed by _preparse_directory_flags())
    no_auto_cleanup = "--no-auto-cleanup" in sys.argv
    if no_auto_cleanup:
        sys.argv.remove("--no-auto-cleanup")

    # Check for output format
    output_format = "auto"
    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]
            sys.argv.pop(idx)  # Remove --format
            sys.argv.pop(idx)  # Remove format value

    try:
        # Pre-parse directory flags and special flags
        cli_flags = _preparse_directory_flags()

        # Handle deprecated --force-migrate flag
        if cli_flags.get("force_migrate_deprecated"):
            print("WARNING: --force-migrate is deprecated. Use --migrate-force instead.", file=sys.stderr)
            cli_flags["force_migrate"] = True

        # Handle --migrate-force flag (must be done before Maqet initialization)
        if cli_flags["force_migrate"]:
            # Import StateManager and ConfigManager to manually run migrations
            from .state import StateManager
            from .managers import ConfigManager

            print("Force migration requested. Creating database backup and applying migrations...")

            # Use ConfigManager to resolve directories with precedence
            config_mgr = ConfigManager(
                data_dir=cli_flags["data_dir"],
                config_dir=cli_flags["config_dir"],
                runtime_dir=cli_flags["runtime_dir"],
            )

            state_manager = StateManager(
                data_dir=config_mgr.get_data_dir(),
                config_dir=config_mgr.get_config_dir(),
                runtime_dir=config_mgr.get_runtime_dir(),
                auto_migrate=False,  # Disable auto-migration
            )

            try:
                if state_manager._needs_migration():
                    print("Database schema upgrade required. Applying migrations...")
                    state_manager.run_migrations()
                    print("Migration completed successfully.")
                else:
                    print("Database schema is already up to date.")
                return ExitCode.SUCCESS
            except Exception as e:
                print(f"Migration failed: {e}", file=sys.stderr)
                print("Your data is safe (backup created).", file=sys.stderr)
                return ExitCode.FAILURE

        # Initialize Maqet with CLI directory overrides
        # ConfigManager handles precedence: CLI > config file > XDG defaults
        maqet = Maqet(
            data_dir=cli_flags["data_dir"],
            config_dir=cli_flags["config_dir"],
            runtime_dir=cli_flags["runtime_dir"],
            auto_cleanup=not cli_flags["no_auto_cleanup"],
        )
        result = maqet.cli()

        # Handle CLI output based on format
        _format_output(result, output_format)

        return ExitCode.SUCCESS

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(ExitCode.TIMEOUT)  # Use TIMEOUT for interruption

    except Exception as e:
        if debug_mode:
            # Print full traceback in debug mode
            print("\n=== Debug Traceback ===", file=sys.stderr)
            traceback.print_exc()
            print("=" * 23, file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
            print("Run with --debug for full traceback", file=sys.stderr)
        sys.exit(ExitCode.FAILURE)


def _format_output(result, format_type: str = "auto"):
    """
    Format and print output using FormatterFactory.

    Args:
        result: Result data to format
        format_type: Output format (auto, json, yaml, plain, table)
    """
    if result is None:
        return

    from .formatters import FormatterFactory

    try:
        formatter = FormatterFactory.create(format_type)
        formatter.format(result)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(ExitCode.INVALID_ARGS)


if __name__ == "__main__":
    main()
