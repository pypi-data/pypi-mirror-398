"""
API Method Metadata.

Data structures for capturing metadata about decorated API methods
to enable automatic CLI and Python API generation.
"""

import inspect
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class APIMethodMetadata:
    """
    Metadata captured from @api_method decorated functions.

    This data structure contains all the information needed by generators to create
    CLI commands and Python API methods from a single decorated method definition.

    Attributes:
        name: Original method name (e.g., 'start_vm')
        function: The actual callable function
        owner_class: Class that owns this method (e.g., 'Maqet')
        cli_name: CLI command name (e.g., 'start-vm', defaults to name with dashes)
        description: Human-readable description for help text
        signature: Function signature for parameter validation
        category: Grouping category ('vm', 'qmp', 'storage', 'system')
        requires_vm: Whether this method requires a VM identifier
        examples: List of usage examples for documentation
        aliases: Alternative CLI command names
        hidden: Whether to hide from CLI help (for internal methods)
        parent: Parent command name for nested subcommands (e.g., 'qmp')

    Example:
        >>> metadata = APIMethodMetadata(
        ...     name='start',
        ...     function=start_method,
        ...     owner_class='Maqet',
        ...     cli_name='start',
        ...     description='Start a virtual machine',
        ...     signature=inspect.signature(start_method),
        ...     category='vm',
        ...     requires_vm=True
        ... )
    """

    name: str
    function: Callable
    owner_class: str
    cli_name: Optional[str]
    description: str
    signature: inspect.Signature
    category: str
    requires_vm: bool = False
    examples: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    hidden: bool = False
    parent: Optional[str] = None

    def __post_init__(self) -> None:
        """
        Set defaults and validate metadata after initialization.

        Automatically converts method names to CLI-friendly format
        (underscores become dashes) if cli_name is not explicitly set.
        """
        if self.cli_name is None:
            self.cli_name = self.name.replace("_", "-")

    @property
    def full_name(self) -> str:
        """
        Get fully qualified method name including class.

        Returns:
            Full method name in format "ClassName.method_name"

        Example:
            >>> metadata.full_name
            'Maqet.start'
        """
        return f"{self.owner_class}.{self.name}"

    @property
    def parameters(self) -> Dict[str, inspect.Parameter]:
        """
        Get method parameters excluding 'self'.

        Returns:
            Dictionary of parameter names to inspect.Parameter objects,
            with 'self' parameter filtered out for instance methods.

        Example:
            >>> params = metadata.parameters
            >>> list(params.keys())
            ['vm_id', 'detach', 'wait']
        """
        params = dict(self.signature.parameters)
        params.pop("self", None)
        return params

    @property
    def required_parameters(self) -> List[str]:
        """
        Get list of required parameter names.

        Returns:
            List of parameter names that have no default value
            and are therefore required when calling the method.
            Excludes VAR_POSITIONAL (*args) and VAR_KEYWORD (**kwargs)
            parameters as they are always optional.

        Example:
            >>> metadata.required_parameters
            ['vm_id']
        """
        required = []
        for name, param in self.parameters.items():
            # Skip *args and **kwargs parameters - they're always optional
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            if param.default == inspect.Parameter.empty:
                required.append(name)
        return required

    @property
    def optional_parameters(self) -> List[str]:
        """
        Get list of optional parameter names.

        Returns:
            List of parameter names that have default values
            and are therefore optional when calling the method.

        Example:
            >>> metadata.optional_parameters
            ['detach', 'wait']
        """
        optional = []
        for name, param in self.parameters.items():
            if param.default != inspect.Parameter.empty:
                optional.append(name)
        return optional
