"""
Python API Generator

Provides clean Python API access to decorated methods.
"""

import inspect
from typing import Any, Dict, Optional

from ..api import APIMethodMetadata, APIRegistry
from .base_generator import BaseGenerator


class PythonAPIGenerator(BaseGenerator):
    """
    Provides programmatic access to @api_method decorated methods.

    This generator enables clean Python API usage where methods can be
    called directly with proper validation and error handling.
    """

    def __init__(self, maqet_instance: Any, registry: APIRegistry):
        """
        Initialize Python API generator.

        Args:
            maqet_instance: Instance of Maqet class
            registry: API registry containing method metadata
        """
        super().__init__(maqet_instance, registry)

    def generate(self) -> "PythonAPIInterface":
        """
        Generate Python API interface.

        Returns:
            Python API interface object
        """
        return PythonAPIInterface(self.maqet_instance, self.registry)

    def execute_method(self, method_name: str, *args, **kwargs) -> Any:
        """
        Execute a method by name with validation.

        Args:
            method_name: Name of method to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Method execution result

        Raises:
            ValueError: If method not found or invalid parameters
            TypeError: If parameter types are incorrect
        """
        # Get method metadata
        metadata = self.get_method_by_name(method_name)
        if not metadata:
            raise ValueError(f"Method '{method_name}' not found")

        # Convert positional args to kwargs for validation
        combined_kwargs = self._combine_args_kwargs(metadata, args, kwargs)

        # Validate parameters
        self._validate_parameters(metadata, combined_kwargs)

        # Get the actual method from the instance
        method = getattr(self.maqet_instance, method_name)

        # Execute method with original args and kwargs
        return method(*args, **kwargs)

    def _validate_parameters(
        self, metadata: APIMethodMetadata, kwargs: Dict[str, Any]
    ) -> None:
        """
        Validate method parameters.

        Args:
            metadata: Method metadata
            kwargs: Parameters provided by user

        Raises:
            ValueError: If required parameters missing or unknown parameters provided
        """
        # Check for missing required parameters
        missing = self.validate_required_parameters(metadata, kwargs)
        if missing:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing)}"
            )

        # Check for unknown parameters only if there's no **kwargs parameter
        has_var_keyword = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in metadata.parameters.values()
        )

        if not has_var_keyword:
            valid_params = set(metadata.parameters.keys())
            provided_params = set(kwargs.keys())
            unknown = provided_params - valid_params
            if unknown:
                raise ValueError(f"Unknown parameters: {', '.join(unknown)}")

        # Type validation could be added here if needed

    def _combine_args_kwargs(
        self, metadata: APIMethodMetadata, args: tuple, kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine positional and keyword arguments into a single kwargs dict for validation.

        Args:
            metadata: Method metadata
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Combined arguments as kwargs dict

        Raises:
            ValueError: If too many positional arguments provided
        """
        combined = kwargs.copy()

        # Get parameter names in order (excluding 'self')
        param_names = list(metadata.parameters.keys())

        # Map positional args to parameter names
        if len(args) > len(param_names):
            raise ValueError(
                f"Too many positional arguments: expected {len(param_names)}, got {len(args)}"
            )

        for i, arg_value in enumerate(args):
            param_name = param_names[i]
            if param_name in combined:
                raise ValueError(
                    f"Parameter '{param_name}' specified both positionally and as keyword argument"
                )
            combined[param_name] = arg_value

        return combined


class PythonAPIInterface:
    """
    Dynamic Python API interface that provides direct method access.

    This class dynamically creates methods based on registered API methods,
    allowing for clean Python usage like:

        api = PythonAPIInterface(maqet_instance, registry)
        api.start("myvm", detach=True)
        api.stop("myvm")
    """

    def __init__(self, maqet_instance: Any, registry: APIRegistry):
        """
        Initialize Python API interface.

        Args:
            maqet_instance: Instance of Maqet class
            registry: API registry containing method metadata
        """
        self.maqet_instance = maqet_instance
        self.registry = registry
        self.generator = PythonAPIGenerator(maqet_instance, registry)

    def __getattr__(self, name: str) -> Any:
        """
        Dynamically provide access to API methods.

        Args:
            name: Method name

        Returns:
            Callable method

        Raises:
            AttributeError: If method not found
        """
        # Check if this is a registered API method
        metadata = self.generator.get_method_by_name(name)
        if metadata:
            return lambda *args, **kwargs: self.generator.execute_method(
                name, *args, **kwargs
            )

        # Check if it's a direct attribute on the instance
        if hasattr(self.maqet_instance, name):
            return getattr(self.maqet_instance, name)

        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def list_methods(self) -> Dict[str, str]:
        """
        List all available API methods.

        Returns:
            Dictionary mapping method names to descriptions
        """
        methods = {}
        for metadata in self.registry.get_all_methods():
            if metadata.owner_class == self.maqet_instance.__class__.__name__:
                methods[metadata.name] = metadata.description
        return methods

    def get_method_help(self, method_name: str) -> Optional[str]:
        """
        Get help text for a method.

        Args:
            method_name: Method name

        Returns:
            Help text or None if method not found
        """
        metadata = self.generator.get_method_by_name(method_name)
        if not metadata:
            return None

        help_text = f"{metadata.name}: {metadata.description}\n\n"

        # Add parameters
        if metadata.parameters:
            help_text += "Parameters:\n"
            for param_name, param in metadata.parameters.items():
                required = param.default == param.empty
                default_text = (
                    f" (default: {param.default})"
                    if not required
                    else " (required)"
                )
                help_text += f"  {param_name}{default_text}\n"

        # Add examples
        if metadata.examples:
            help_text += "\nExamples:\n"
            for example in metadata.examples:
                help_text += f"  {example}\n"

        return help_text.strip()
