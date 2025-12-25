"""Output formatters for CLI results.

This module implements the Strategy pattern for output formatting,
replacing the complex if-else ladder in __main__.py with composable
formatter classes.

Each formatter class implements the OutputFormatter interface and
handles a specific output format (JSON, YAML, plain text, table).
"""

import json
import sys
from abc import ABC, abstractmethod
from typing import Any

# Optional dependencies - imported with fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False

try:
    from .state import VMInstance
    from dataclasses import asdict, is_dataclass
    VMINSTANCE_AVAILABLE = True
except ImportError:
    VMINSTANCE_AVAILABLE = False
    VMInstance = None
    asdict = None

    def is_dataclass(x):
        """Fallback is_dataclass when dataclasses module unavailable."""
        return False


# Shared utility functions for VMInstance handling
def _is_vminstance(obj: Any) -> bool:
    """Check if object is a VMInstance.

    Args:
        obj: Object to check

    Returns:
        True if obj is a VMInstance, False otherwise
    """
    return VMINSTANCE_AVAILABLE and isinstance(obj, VMInstance)


def _vminstance_to_dict(vm: Any) -> dict:
    """Convert VMInstance to dictionary.

    Args:
        vm: VMInstance object to convert

    Returns:
        Dictionary representation of VMInstance
    """
    if not VMINSTANCE_AVAILABLE:
        return {}

    if asdict is not None:
        return asdict(vm)
    else:
        # Fallback: manually extract key fields
        return {
            "id": vm.id,
            "name": vm.name,
            "status": vm.status,
            "pid": vm.pid,
        }


class OutputFormatter(ABC):
    """Base class for output formatters.

    All formatter implementations must provide a format() method
    that takes a result of any type and prints it to stdout.
    """

    @abstractmethod
    def format(self, result: Any) -> None:
        """Format and print the result to stdout.

        Args:
            result: The data to format and print
        """
        pass


class AutoFormatter(OutputFormatter):
    """Auto-detect format based on data type with clean output.

    This is the default formatter when no specific format is requested.
    It inspects the result type and chooses an appropriate representation:
    - Strings: printed as-is
    - VMInstance (single): ID only (e.g., "vm-123")
    - VMInstance (list): IDs, one per line
    - Dicts: JSON with indentation (empty QMP returns suppressed)
    - Lists: items printed one per line (JSON for complex items)
    - Booleans: silent on True, "FAILED" on False
    - Other: str() representation

    Note: VMInstance support requires the state module. Falls back gracefully
    if not available.
    """

    def format(self, result: Any) -> None:
        """Format output based on automatic type detection with clean output."""
        if isinstance(result, str):
            print(result)
        elif _is_vminstance(result):
            # Concise VMInstance output: just ID
            print(result.id)
        elif isinstance(result, bool):
            # Silent success for True, show failure for False
            if not result:
                print("FAILED")
            # True returns nothing (silent success)
        elif isinstance(result, dict):
            # Suppress empty QMP returns
            if result == {"return": {}}:
                return  # Silent success
            print(json.dumps(result, indent=2))
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, str):
                    print(item)
                elif _is_vminstance(item):
                    # Handle VMInstance in lists - concise format (ID only)
                    print(item.id)
                elif isinstance(item, dict):
                    # Suppress empty QMP returns in lists
                    if item == {"return": {}}:
                        continue
                    print(json.dumps(item, indent=2))
                else:
                    # For other types, attempt JSON serialization with fallback
                    try:
                        print(json.dumps(item, indent=2))
                    except TypeError:
                        # Fallback for non-serializable objects
                        print(str(item))
        else:
            print(result)


class JSONFormatter(OutputFormatter):
    """JSON output format.

    Outputs results as properly formatted JSON with 2-space indentation.
    VMInstance objects and dataclasses are automatically converted to dicts.
    Non-dict/list results are wrapped in a {"result": value} structure.

    Note: VMInstance support requires the state module. Falls back gracefully
    if not available.
    """

    def format(self, result: Any) -> None:
        """Format output as JSON."""
        # Handle VMInstance objects by converting to dict
        if _is_vminstance(result):
            print(json.dumps(_vminstance_to_dict(result), indent=2, default=str))
        elif isinstance(result, list):
            # Check if list contains VMInstance objects
            converted_list = []
            for item in result:
                if _is_vminstance(item):
                    converted_list.append(_vminstance_to_dict(item))
                else:
                    converted_list.append(item)
            print(json.dumps(converted_list, indent=2, default=str))
        elif isinstance(result, dict):
            print(json.dumps(result, indent=2, default=str))
        else:
            # For other types, check if dataclass and convert
            if is_dataclass(result) and not isinstance(result, type):
                print(json.dumps(asdict(result), indent=2, default=str))
            else:
                print(json.dumps({"result": str(result)}, indent=2))


class YAMLFormatter(OutputFormatter):
    """YAML output format.

    Requires PyYAML to be installed. Outputs results as YAML with
    block-style formatting (default_flow_style=False).
    Non-dict/list results are wrapped in a {"result": value} structure.
    """

    def format(self, result: Any) -> None:
        """Format output as YAML.

        Raises:
            SystemExit: If PyYAML is not installed
        """
        if not YAML_AVAILABLE:
            print("Error: PyYAML not installed. Install with: pip install PyYAML",
                  file=sys.stderr)
            sys.exit(1)

        if isinstance(result, (dict, list)):
            print(yaml.dump(result, default_flow_style=False))
        else:
            print(yaml.dump({"result": str(result)}, default_flow_style=False))


class PlainFormatter(OutputFormatter):
    """Plain text output format.

    Produces human-readable plain text output without JSON/YAML decoration:
    - VMInstance (single): key-value pairs with detailed view
    - VMInstance (list): IDs only, one per line
    - Dicts: key: value pairs, one per line
    - Lists: items, one per line
    - Other: str() representation

    Note: VMInstance support requires the state module. Falls back gracefully
    if not available.
    """

    def format(self, result: Any) -> None:
        """Format output as plain text."""
        if _is_vminstance(result):
            # Format VMInstance as key-value pairs (detailed view)
            vm_dict = _vminstance_to_dict(result)
            for key, value in vm_dict.items():
                if value is not None:  # Skip None values for cleaner output
                    print(f"{key}: {value}")
        elif isinstance(result, dict):
            for key, value in result.items():
                print(f"{key}: {value}")
        elif isinstance(result, list):
            for item in result:
                if _is_vminstance(item):
                    # For lists of VMs, just show IDs (concise)
                    print(item.id)
                else:
                    print(item)
        else:
            print(result)


class TableFormatter(OutputFormatter):
    """Table format for lists of dicts using tabulate library (with fallback).

    Uses the tabulate library if available for improved table formatting.
    Falls back to custom formatter if tabulate is not installed.

    Produces ASCII table output with headers and aligned columns.
    Particularly useful for VM listings and status commands.

    VMInstance objects are automatically converted to dicts for table display.
    Both single VMInstance and lists of VMInstance objects are supported.

    Example output:
        name    | status  | pid
        --------|---------|-----
        myvm    | running | 1234
        testvm  | stopped | None

    Note: VMInstance support requires the state module. Falls back gracefully
    if not available.
    """

    def __init__(self) -> None:
        """Initialize formatter and check for tabulate availability."""
        self._has_tabulate = TABULATE_AVAILABLE

    def format(self, result: Any) -> None:
        """Format output as ASCII table.

        Args:
            result: List of dicts (or single dict) to format as table
        """
        # Convert VMInstance objects to dicts
        if _is_vminstance(result):
            result = [_vminstance_to_dict(result)]
        elif isinstance(result, list) and result and _is_vminstance(result[0]):
            result = [_vminstance_to_dict(vm) for vm in result]

        # Now handle as before
        if isinstance(result, list) and result and isinstance(result[0], dict):
            self._print_table(result)
        elif isinstance(result, dict):
            self._print_table([result])
        else:
            print(result)

    def _print_table(self, data: list) -> None:
        """Print data as formatted table.

        Uses tabulate library if available, falls back to custom formatter.

        Args:
            data: List of dictionaries with consistent keys
        """
        if not data:
            return

        if self._has_tabulate:
            self._print_table_tabulate(data)
        else:
            self._print_table_custom(data)

    def _print_table_tabulate(self, data: list) -> None:
        """Print table using tabulate library.

        Args:
            data: List of dictionaries to format as table
        """
        # Get all keys across all dicts (handles inconsistent keys)
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        headers = sorted(all_keys)

        # Convert to list of lists for tabulate
        rows = []
        for item in data:
            row = [item.get(key, "") for key in headers]
            rows.append(row)

        # Print with pipe table format (includes | separators)
        print(tabulate.tabulate(rows, headers=headers, tablefmt="pipe"))

    def _print_table_custom(self, data: list) -> None:
        """Print table using custom formatter (fallback).

        Args:
            data: List of dictionaries with consistent keys
        """
        # Get all keys across all dicts (handles inconsistent keys)
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        headers = sorted(all_keys)

        # Calculate column widths based on both headers and data
        col_widths = {key: len(key) for key in headers}
        for item in data:
            for key in headers:
                value = str(item.get(key, ""))
                col_widths[key] = max(col_widths[key], len(value))

        # Print header row
        header_row = " | ".join(key.ljust(col_widths[key]) for key in headers)
        print(header_row)
        print("-" * len(header_row))

        # Print data rows
        for item in data:
            row = " | ".join(
                str(item.get(key, "")).ljust(col_widths[key]) for key in headers
            )
            print(row)


class FormatterFactory:
    """Factory for creating formatters.

    This class manages the registry of available formatters and
    provides methods to create formatter instances by name.

    New formatters can be registered at runtime using register().
    """

    _formatters = {
        "auto": AutoFormatter,
        "json": JSONFormatter,
        "yaml": YAMLFormatter,
        "plain": PlainFormatter,
        "table": TableFormatter,
    }

    @classmethod
    def create(cls, format_type: str) -> OutputFormatter:
        """Create formatter instance by type name.

        Args:
            format_type: Name of the formatter to create
                        (auto, json, yaml, plain, table)

        Returns:
            OutputFormatter instance for the requested type

        Raises:
            ValueError: If format_type is not registered
        """
        formatter_class = cls._formatters.get(format_type)
        if not formatter_class:
            raise ValueError(
                f"Unknown format '{format_type}'. "
                f"Valid formats: {', '.join(cls._formatters.keys())}"
            )
        return formatter_class()

    @classmethod
    def register(cls, name: str, formatter_class: type) -> None:
        """Register a new formatter type.

        This allows external code to add custom formatters to the factory.

        Args:
            name: Name to register the formatter under
            formatter_class: Class implementing OutputFormatter interface

        Example:
            class XMLFormatter(OutputFormatter):
                def format(self, result):
                    # Implementation
                    pass

            FormatterFactory.register("xml", XMLFormatter)
        """
        cls._formatters[name] = formatter_class
