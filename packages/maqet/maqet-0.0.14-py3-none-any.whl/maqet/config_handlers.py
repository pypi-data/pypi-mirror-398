"""
Configuration Handlers for Machine Setup

Provides an extensible handler-based system for processing VM configuration.
Each configuration key can have a dedicated handler method.

Supports both global registry (backward compatibility) and instance-based
registry (for parallel tests and multiple Machine instances).
"""

import inspect
from typing import Any, Callable, Dict, List, Optional

from .exceptions import ConfigurationError
from .logger import LOG


class QEMUArgumentFormatter:
    """
    Formats nested data structures as QEMU command-line arguments.

    Uses Visitor pattern for type-specific formatting.

    Handles all format types:
    - Format 1 (key only):     'foo' -> 'foo'
    - Format 2 (key-value):    {'a': 1, 'b': 2} -> 'a=1,b=2'
    - Format 3 (nested):       {'bar': {'baz': 42}} -> 'bar.baz=42'
    - Format 4 (list):         ['opt1', 'opt2'] -> 'opt1,opt2'

    Examples:
        >>> formatter = QEMUArgumentFormatter()
        >>> formatter.format({'mem-path': '/dev/hugepages', 'size': '8G'})
        'mem-path=/dev/hugepages,size=8G'

        >>> formatter.format({'numa': {'node': {'nodeid': 0, 'cpus': '0-3'}}})
        'numa.node.nodeid=0,numa.node.cpus=0-3'
    """

    def __init__(self, separator: str = ",", assignment: str = "=", nesting: str = "."):
        """
        Initialize formatter with custom separators.

        Args:
            separator: Separator between key-value pairs (default: ',')
            assignment: Assignment operator (default: '=')
            nesting: Nesting separator (default: '.')
        """
        self.sep = separator
        self.assign = assignment
        self.nest = nesting

    def format(self, value, stack: List[str] = None) -> str:
        """
        Format value using visitor pattern dispatch.

        Args:
            value: Value to format (any type)
            stack: Current nesting stack (internal use)

        Returns:
            Formatted QEMU argument string
        """
        if stack is None:
            stack = []

        # Dispatch to type-specific handlers
        if value is None or (isinstance(value, dict) and not value):
            return self._handle_empty(stack)

        if isinstance(value, (str, int, float, bool)):
            return self._handle_primitive(value, stack)

        if isinstance(value, list):
            return self._handle_list(value, stack)

        if isinstance(value, dict):
            return self._handle_dict(value, stack)

        # Fallback for unknown types
        return str(value)

    def _handle_empty(self, stack: List[str]) -> str:
        """Handle None or empty dict - format as key only."""
        return self.nest.join(stack) if stack else ""

    def _handle_primitive(self, value, stack: List[str]) -> str:
        """Handle primitive types (str, int, float, bool)."""
        if stack:
            key = self.nest.join(stack)
            return f"{key}{self.assign}{value}"
        return str(value)

    def _handle_list(self, items: List, stack: List[str]) -> str:
        """Handle list - format each item and join."""
        parts = []
        for item in items:
            if isinstance(item, (list, dict)):
                # Nested structure: recurse
                formatted = self.format(item, stack)
                if formatted:
                    parts.append(formatted)
            else:
                # Simple value in list
                if stack:
                    parts.append(self.nest.join(stack) + f".{item}")
                else:
                    parts.append(str(item))
        return self.sep.join(parts)

    def _handle_dict(self, mapping: Dict, stack: List[str]) -> str:
        """Handle dict - recurse into nested structure."""
        parts = []
        for key, value in mapping.items():
            new_stack = stack + [key]

            # Special case: empty value means key-only format
            if value is None or (isinstance(value, dict) and not value):
                parts.append(self.nest.join(new_stack))
            else:
                parts.append(self.format(value, new_stack))

        return self.sep.join(parts)


# Arguments that should appear only once in QEMU command line
# Multiple instances cause undefined behavior or conflicts
SINGLE_INSTANCE_ARGS = frozenset({
    'display',    # Display backend (gtk, sdl, vnc, etc.)
    'vga',        # VGA adapter type
    'm',          # Memory size
    'smp',        # CPU topology (sockets, cores, threads)
    'machine',    # Machine type (pc, q35, virt, etc.)
    'cpu',        # CPU model
    'kernel',     # Kernel image path
    'initrd',     # Initial ramdisk path
    'append',     # Kernel command line
})


class ConfigHandlerRegistry:
    """Registry for configuration handlers."""

    def __init__(self):
        """Initialize the handler registry."""
        self._handlers: Dict[str, Callable] = {}

    def register_handler(self, config_key: str, handler: Callable):
        """
        Register a configuration handler.

        Args:
            config_key: Configuration key to handle
            handler: Handler function
        """
        self._handlers[config_key] = handler
        LOG.debug(f"Registered config handler for '{config_key}'")

    def get_handler(self, config_key: str) -> Optional[Callable]:
        """
        Get handler for configuration key.

        Args:
            config_key: Configuration key

        Returns:
            Handler function or None if not found
        """
        return self._handlers.get(config_key)

    def get_registered_keys(self) -> List[str]:
        """Get list of all registered configuration keys."""
        return list(self._handlers.keys())

    def register_from_instance(self, instance: Any) -> None:
        """
        Register all @config_handler decorated methods from an instance.

        This enables instance-based registries where each ConfigurableMachine
        has its own registry, allowing for:
        - Parallel test execution without registry pollution
        - Multiple Machine instances with different handlers
        - Thread-safe operation

        Args:
            instance: Object instance to scan for @config_handler decorated methods

        Example:
            registry = ConfigHandlerRegistry()
            machine = ConfigurableMachine()
            registry.register_from_instance(machine)
        """
        # Get the class of the instance
        cls = instance.__class__

        # Scan for decorated methods
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if hasattr(method, "_config_handler_key"):
                key = method._config_handler_key
                # Bind method to instance
                bound_method = getattr(instance, name)
                self.register_handler(key, bound_method)


# DEPRECATED: Global registry kept for backward compatibility only.
# Use instance._config_handler_registry instead.
# Removal planned for v2.0. See: specs/fix-global-config-handler-state.md
_config_registry = ConfigHandlerRegistry()


def config_handler(config_key: str):
    """
    Decorator to mark configuration handlers.

    Stores metadata on the function for instance-based registration.
    When ConfigurableMachine is instantiated, __init__ calls
    register_from_instance() to scan for @config_handler methods and
    register them to the instance-specific registry.

    This enables per-instance handler isolation for:
    - Parallel test execution without registry pollution
    - Multiple Machine instances with different handlers
    - Thread-safe operation

    Args:
        config_key: Configuration key this handler processes

    Example:
        @config_handler("memory")
        def handle_memory(self, value):
            self._qemu_machine.add_args("-m", value)

    Raises:
        TypeError: If decorator is applied to a non-method (function without
                   'self' or 'cls' as first parameter)

    Note:
        Registration happens via register_from_instance() in
        ConfigurableMachine.__init__, not at decoration time.
        See: specs/fix-global-config-handler-state.md
    """

    def decorator(func: Callable):
        # Validate that this is a method with 'self' or 'cls' parameter
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        if not params or params[0] not in ('self', 'cls'):
            raise TypeError(
                f"@config_handler can only decorate instance or class methods. "
                f"Function '{func.__name__}' has parameters: {params}"
            )

        # Store metadata on function for instance registration
        func._config_handler_key = config_key

        # Instance registration happens in ConfigurableMachine.__init__
        # via self._config_handler_registry.register_from_instance(self)
        # Global registration removed to fix global state issue

        return func

    return decorator


class ConfigurableMachine:
    """
    Mixin class providing extensible configuration handling.

    Classes that inherit from this can use @config_handler decorators
    to define how different configuration keys are processed.

    Now supports instance-based config handler registries for:
    - Parallel test execution without registry pollution
    - Multiple Machine instances with different handlers
    - Thread-safe operation

    # NOTE: Good - decorator-based handler registration (@config_handler) is
    # clean
    #       and allows adding new config keys without modifying core code.
    #       Very maintainable and extensible pattern.
    # NOTE: Validates handlers exist for keys and fails fast on critical key
    # errors.
    # Warnings are issued for unhandled keys to help identify typos/deprecated
    # keys.
    """

    # Critical configuration keys that must be processed successfully
    # Errors in these keys will cause VM creation to fail immediately
    CRITICAL_CONFIG_KEYS = {
        "binary",  # QEMU binary path - VM cannot start without it
        "storage",  # Storage configuration - must succeed to avoid data loss
        "arguments",  # Core QEMU arguments - failures could break VM
    }

    def __init__(self, *args, **kwargs):
        """
        Initialize ConfigurableMachine with instance-specific config registry.

        Creates an isolated config handler registry for this instance,
        preventing cross-contamination between instances and enabling
        parallel test execution.
        """
        # Call parent __init__ if it exists (for multiple inheritance)
        super().__init__(*args, **kwargs)

        # Create instance-specific config handler registry
        self._config_handler_registry = ConfigHandlerRegistry()
        self._config_handler_registry.register_from_instance(self)

        # Create QEMU argument formatter instance
        self._formatter = QEMUArgumentFormatter()

    def process_configuration(self, config_data: Dict[str, Any]):
        """
        Process configuration data using registered handlers.

        Uses instance-specific registry (falls back to global for compatibility).

        Args:
            config_data: Configuration dictionary

        Validates that handlers exist for all keys and fails fast on errors
        for critical keys. Warns about unhandled keys that might be typos.
        """
        processed_keys = []

        # Use instance-specific registry (falls back to global if not available)
        registry = getattr(self, '_config_handler_registry', _config_registry)

        # Identify unhandled keys to warn about potential typos or deprecated
        # keys
        all_keys = set(config_data.keys())
        registered_keys = set(registry.get_registered_keys())
        unhandled_keys = all_keys - registered_keys

        # Warn about unhandled keys (potential typos/deprecated keys)
        if unhandled_keys:
            LOG.warning(
                f"Configuration contains unhandled keys (potential typos or deprecated): "
                f"{', '.join(sorted(unhandled_keys))}. "
                f"Valid keys: {', '.join(sorted(registered_keys))}"
            )

        # Iterate over a list of items to allow handlers to modify config_data
        for config_key, config_value in list(config_data.items()):
            handler = registry.get_handler(config_key)
            if handler:
                try:
                    # Check if handler is bound method or unbound function
                    # Instance registry: bound methods (already have self)
                    # Global registry: unbound functions (need self passed)
                    if hasattr(handler, '__self__'):
                        # Bound method - call directly
                        handler(config_value)
                    else:
                        # Unbound function - pass self explicitly
                        handler(self, config_value)
                    processed_keys.append(config_key)
                    LOG.debug(
                        f"Processed config key '{config_key}' with handler"
                    )
                except Exception as e:
                    # Fail fast for critical configuration keys
                    if config_key in self.CRITICAL_CONFIG_KEYS:
                        LOG.error(
                            f"Critical config key '{
                                config_key}' failed to process: {e}. "
                            f"VM creation cannot continue with invalid {
                                config_key} configuration."
                        )
                        # Re-raise exception to stop VM creation immediately
                        raise
                    else:
                        # Non-critical keys can fail with warnings
                        LOG.warning(
                            f"Error processing config key '{config_key}': {e}"
                        )
            else:
                LOG.debug(
                    f"No handler for config key '{config_key}', ignoring"
                )

        LOG.debug(f"Processed configuration keys: {processed_keys}")
        return processed_keys

    def get_unhandled_keys(self, config_data: Dict[str, Any]) -> List[str]:
        """
        Get list of configuration keys that have no registered handlers.

        Uses instance-specific registry (falls back to global for compatibility).

        Useful for identifying typos or deprecated keys in configurations.

        Args:
            config_data: Configuration dictionary

        Returns:
            List of unhandled configuration keys (sorted)
        """
        # Use instance-specific registry (falls back to global if not available)
        registry = getattr(self, '_config_handler_registry', _config_registry)

        all_keys = set(config_data.keys())
        registered_keys = set(registry.get_registered_keys())
        unhandled_keys = all_keys - registered_keys
        return sorted(list(unhandled_keys))

    @config_handler("binary")
    def handle_binary(self, binary: str):
        """
        Handle QEMU binary path configuration.

        The binary path is already stored in config_data and used by
        _create_qemu_machine(). This handler just registers 'binary' as
        a valid configuration key to prevent warnings.
        """
        # Binary path is used directly from config_data in machine.py
        # No additional processing needed here
        pass

    @config_handler("memory")
    def handle_memory(self, memory: str):
        """Handle memory configuration."""
        if hasattr(self, "_qemu_machine") and self._qemu_machine:
            self._qemu_machine.add_args("-m", memory)

    @config_handler("cpu")
    def handle_cpu(self, cpu: int):
        """Handle CPU configuration."""
        if hasattr(self, "_qemu_machine") and self._qemu_machine:
            self._qemu_machine.add_args("-smp", str(cpu))

    @config_handler("display")
    def handle_display(self, display: str):
        """Handle display configuration."""
        if hasattr(self, "_qemu_machine") and self._qemu_machine:
            self._qemu_machine.add_args("-display", display)

    @config_handler("vga")
    def handle_vga(self, vga: str):
        """Handle VGA configuration."""
        if hasattr(self, "_qemu_machine") and self._qemu_machine:
            self._qemu_machine.add_args("-vga", vga)

    @config_handler("args")
    def handle_args(self, args: List[str]):
        """Handle additional QEMU arguments (simple list format)."""
        if hasattr(self, "_qemu_machine") and self._qemu_machine and args:
            self._qemu_machine.add_args(*args)

    @staticmethod
    def _format_nested_value(value, stack=None):
        """
        DEPRECATED: Use QEMUArgumentFormatter.format() instead.

        Recursively format nested dicts/lists as QEMU suboptions.

        This method is kept for backward compatibility with existing tests.
        New code should use the QEMUArgumentFormatter class directly.

        Args:
            value: Value to format (dict, list, or primitive)
            stack: Current nesting path for dot notation (e.g., ['device', 'net'])

        Returns:
            Formatted string suitable for QEMU arguments

        Format Examples:
            Format 1 (key only):
                value: 'foo' -> 'foo'

            Format 2 (key-value):
                value: {'a': 1, 'b': 2} -> 'a=1,b=2'

            Format 3 (nested key-values):
                value: {'bar': 42, 'baz': 42} -> 'bar=42,baz=42'

            Format 4 (value and key-values - handled by caller):
                {display: 'gtk', 'zoom-to-fit': 'on'} -> 'gtk,zoom-to-fit=on'
                This is handled in handle_arguments() for multi-key dicts

            Format 5 (deep nesting):
                {'bar': {'baz': {'spam': 1}}} -> 'bar.baz.spam=1'

            Empty nested values (key without value):
                {'gtk': None} -> 'gtk'
                {'gtk': {}} -> 'gtk'
        """
        # Delegate to QEMUArgumentFormatter for backward compatibility
        formatter = QEMUArgumentFormatter()
        return formatter.format(value, stack)

    @config_handler("arguments")
    def handle_arguments(self, arguments: List):
        """
        Handle structured QEMU arguments from config.

        Implements whitelist-based deduplication for single-instance arguments
        to prevent undefined behavior from conflicts.

        Args:
            arguments: List of dicts or strings representing QEMU arguments
                Examples:
                - {smp: 2} -> -smp 2
                - {m: "2G"} -> -m 2G
                - {enable-kvm: null} -> -enable-kvm
                - "enable-kvm" -> -enable-kvm

        Raises:
            ConfigurationError: If duplicate single-instance argument detected
        """
        if not hasattr(self, "_qemu_machine") or not self._qemu_machine:
            return

        if not arguments:
            return

        # Track which single-instance arguments have been seen
        seen_single_instance = {}  # arg_name -> first occurrence index

        # Collect keys to mark in config_data (done after iteration to avoid
        # RuntimeError)
        config_updates = {}

        # Process arguments
        for idx, arg_item in enumerate(arguments):
            if isinstance(arg_item, dict):
                # Extract argument name (first key in dict)
                if not arg_item:
                    continue

                # Get first key as argument name
                arg_name = next(iter(arg_item.keys()))

                # Check if this is a single-instance argument
                if arg_name in SINGLE_INSTANCE_ARGS:
                    if arg_name in seen_single_instance:
                        # Duplicate detected - provide helpful error
                        first_idx = seen_single_instance[arg_name]
                        raise ConfigurationError(
                            f"Duplicate single-instance argument '-{arg_name}' detected.\n"
                            f"First occurrence: arguments[{first_idx}]\n"
                            f"Duplicate occurrence: arguments[{idx}]\n"
                            f"\n"
                            f"QEMU allows only one '-{arg_name}' argument per VM.\n"
                            f"Please remove one of the conflicting definitions.\n"
                            f"\n"
                            f"Single-instance arguments: {', '.join(sorted(SINGLE_INSTANCE_ARGS))}\n"
                            f"Multi-instance arguments (can appear multiple times): "
                            f"device, drive, netdev, chardev, object"
                        )
                    else:
                        # First occurrence - track it
                        seen_single_instance[arg_name] = idx

                # Check if this is a multi-key dict (Format 4)
                # Example: {display: gtk, zoom-to-fit: on} → -display gtk,zoom-to-fit=on
                if len(arg_item) > 1:
                    # Multi-key dict: first key is arg name, its value is positional,
                    # remaining keys are suboptions
                    items = list(arg_item.items())
                    first_key, first_value = items[0]
                    arg_name = f"-{first_key}"

                    # Build argument value: positional_value,key1=val1,key2=val2
                    parts = []

                    # Add first value as positional (if not None)
                    if first_value is not None:
                        if isinstance(first_value, (dict, list)):
                            parts.append(
                                self._formatter.format(first_value)
                            )
                        else:
                            parts.append(str(first_value))

                    # Add remaining key=value pairs as suboptions
                    for key, value in items[1:]:
                        if value is None or (isinstance(value, dict) and not value):
                            # Empty value: add key without assignment
                            parts.append(key)
                        elif isinstance(value, (dict, list)):
                            # Nested value: format recursively with stack context
                            # This ensures lists use dot notation: key.item1,key.item2
                            formatted = self._formatter.format(value, stack=[key])
                            if formatted:
                                parts.append(formatted)
                        else:
                            parts.append(f"{key}={value}")

                    # Add the complete argument
                    if parts:
                        self._qemu_machine.add_args(arg_name, ",".join(parts))
                    else:
                        self._qemu_machine.add_args(arg_name)

                    # Collect config updates to prevent defaults (from first key only)
                    if first_key == "m":
                        config_updates["memory"] = str(first_value)
                    elif first_key == "smp":
                        config_updates["cpu"] = first_value

                else:
                    # Single-key dict format: {key: value} or {key: null}
                    for key, value in arg_item.items():
                        # Convert key to QEMU argument format (add - prefix)
                        arg_name = f"-{key}"

                        if value is None:
                            # Format 1: Flag argument (e.g., {enable-kvm: null} → -enable-kvm)
                            self._qemu_machine.add_args(arg_name)
                        elif isinstance(value, dict):
                            # Check for Format 4 alternative syntax:
                            # {display: {gtk: null, zoom-to-fit: on}} should behave like
                            # {display: gtk, zoom-to-fit: on}
                            # i.e., first key with empty value becomes positional
                            if len(value) > 1:
                                items = list(value.items())
                                first_nested_key, first_nested_value = items[0]

                                if first_nested_value is None or (isinstance(first_nested_value, dict) and not first_nested_value):
                                    # First nested key has empty value: treat as positional
                                    # Example: {display: {gtk: null, zoom-to-fit: on}} → -display gtk,zoom-to-fit=on
                                    parts = [first_nested_key]

                                    # Add remaining key=value pairs
                                    for nested_key, nested_value in items[1:]:
                                        if nested_value is None or (isinstance(nested_value, dict) and not nested_value):
                                            parts.append(nested_key)
                                        elif isinstance(nested_value, (dict, list)):
                                            # Use stack context for dot notation
                                            formatted = self._formatter.format(nested_value, stack=[nested_key])
                                            if formatted:
                                                parts.append(formatted)
                                        else:
                                            parts.append(f"{nested_key}={nested_value}")

                                    self._qemu_machine.add_args(arg_name, ",".join(parts))
                                else:
                                    # Regular nested dict: Format 3 or Format 5
                                    # Example: {foo: {bar: 42, baz: 42}} → -foo bar=42,baz=42
                                    formatted = self._formatter.format(value)
                                    if formatted:
                                        self._qemu_machine.add_args(arg_name, formatted)
                                    else:
                                        self._qemu_machine.add_args(arg_name)
                            else:
                                # Single-key nested dict: Format 3 or Format 5
                                # Example: {display: {gtk: null}} → -display gtk
                                formatted = self._formatter.format(value)
                                if formatted:
                                    self._qemu_machine.add_args(arg_name, formatted)
                                else:
                                    self._qemu_machine.add_args(arg_name)
                        elif isinstance(value, list):
                            # List: format as comma-separated values
                            # Example: {arg: [foo, bar]} → -arg foo,bar
                            formatted = self._formatter.format(value)
                            if formatted:
                                self._qemu_machine.add_args(arg_name, formatted)
                            else:
                                self._qemu_machine.add_args(arg_name)
                        else:
                            # Format 2: Simple value (string/int)
                            # Example: {smp: 2} → -smp 2
                            self._qemu_machine.add_args(arg_name, str(value))

                        # Collect config updates to prevent defaults
                        if key == "m":
                            config_updates["memory"] = str(value)
                        elif key == "smp":
                            config_updates["cpu"] = value

            elif isinstance(arg_item, str):
                # String format: "enable-kvm" -> -enable-kvm
                arg_name = (
                    f"-{arg_item}"
                    if not arg_item.startswith("-")
                    else arg_item
                )
                self._qemu_machine.add_args(arg_name)
            else:
                LOG.warning(
                    f"Invalid argument format: {arg_item}. "
                    "Expected dict or string."
                )

        # Apply config updates after iteration to prevent RuntimeError
        if hasattr(self, "config_data") and config_updates:
            self.config_data.update(config_updates)

    @config_handler("storage")
    def handle_storage(self, storage_config: List[Dict[str, Any]]):
        """Handle storage configuration using storage manager."""
        # This will be handled by the storage manager integration
        if hasattr(self, "_add_storage_devices"):
            self._add_storage_devices()

    def apply_default_configuration(self):
        """
        Apply minimal required configuration for maqet functionality.

        Philosophy: Provide mechanism, not policy (Unix philosophy).

        QEMU has perfectly good defaults. Maqet only adds arguments required
        for maqet itself to function (QMP socket, console setup).

        All other configuration comes from:
        1. User config (explicit)
        2. QEMU's own defaults (implicit)

        No opinionated defaults for memory, CPU, network, display, etc.
        Users configure these explicitly if they want something different
        from QEMU's defaults.

        QEMU defaults (when no arguments provided):
        - Memory: Architecture-specific default (typically 128MB)
        - CPU: 1 core
        - Display: GTK/SDL if available, else none
        - Network: None (no network by default)
        - VGA: Default VGA for architecture
        """
        # NOTE: QMP socket and console setup are handled by
        # MaqetQEMUMachine._base_args - these are required for maqet to
        # communicate with QEMU and are not "policy" defaults.
        pass


def register_config_handler(config_key: str, handler: Callable):
    """
    DEPRECATED: Use instance._config_handler_registry.register_handler() instead.
    Will be removed in v2.0.
    """
    import warnings
    warnings.warn(
        "register_config_handler() is deprecated. "
        "Use instance._config_handler_registry.register_handler()",
        DeprecationWarning,
        stacklevel=2
    )
    _config_registry.register_handler(config_key, handler)


def get_registered_config_keys() -> List[str]:
    """
    DEPRECATED: Use instance._config_handler_registry.get_registered_keys() instead.
    Will be removed in v2.0.
    """
    import warnings
    warnings.warn(
        "get_registered_config_keys() is deprecated. "
        "Use instance._config_handler_registry.get_registered_keys()",
        DeprecationWarning,
        stacklevel=2
    )
    return _config_registry.get_registered_keys()


def get_registered_handlers() -> List[str]:
    """
    DEPRECATED: Use sorted(instance._config_handler_registry.get_registered_keys()) instead.
    Will be removed in v2.0.
    """
    import warnings
    warnings.warn(
        "get_registered_handlers() is deprecated. "
        "Use sorted(instance._config_handler_registry.get_registered_keys())",
        DeprecationWarning,
        stacklevel=2
    )
    return sorted(_config_registry.get_registered_keys())


def validate_critical_handlers() -> None:
    """
    DEPRECATED: Use instance._config_handler_registry.get_registered_keys() for validation.
    Will be removed in v2.0.
    """
    import warnings
    warnings.warn(
        "validate_critical_handlers() is deprecated. "
        "Use instance._config_handler_registry.get_registered_keys()",
        DeprecationWarning,
        stacklevel=2
    )
    critical = ['binary', 'storage', 'arguments']
    registered = set(_config_registry.get_registered_keys())
    missing = [h for h in critical if h not in registered]

    if missing:
        raise RuntimeError(
            f"Missing critical config handlers: {', '.join(missing)}. "
            f"This indicates a code registration issue. "
            f"Registered handlers: {', '.join(sorted(registered))}"
        )
