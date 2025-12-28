"""
Base Generator

Common functionality for all API generators.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..api import APIMethodMetadata, APIRegistry


class BaseGenerator(ABC):
    """
    Base class for all API generators.

    Provides common functionality for converting method metadata
    into different interface types (CLI, Python API, etc.).
    """

    def __init__(self, maqet_instance: Any, registry: APIRegistry):
        """
        Initialize generator.

        Args:
            maqet_instance: Instance of Maqet class
            registry: API registry containing method metadata
        """
        self.maqet_instance = maqet_instance
        self.registry = registry

    def get_method_by_name(
        self, method_name: str
    ) -> Optional[APIMethodMetadata]:
        """
        Get method metadata by name.

        Args:
            method_name: Method name to look up

        Returns:
            Method metadata or None if not found
        """
        full_name = f"{self.maqet_instance.__class__.__name__}.{method_name}"
        return self.registry.get_method(full_name)

    def convert_parameter_value(
        self, param: inspect.Parameter, value: str
    ) -> Any:
        """
        Convert string value to appropriate type based on parameter annotation.

        Args:
            param: Parameter metadata
            value: String value to convert

        Returns:
            Converted value
        """
        if param.annotation == bool or param.annotation == "bool":
            return value.lower() in ("true", "1", "yes", "on")
        elif param.annotation == int or param.annotation == "int":
            return int(value)
        elif param.annotation == float or param.annotation == "float":
            return float(value)
        elif param.annotation == list or param.annotation == "list":
            # Handle comma-separated lists
            return [item.strip() for item in value.split(",")]
        else:
            # Default to string
            return value

    def validate_required_parameters(
        self, metadata: APIMethodMetadata, provided_params: Dict[str, Any]
    ) -> List[str]:
        """
        Validate that all required parameters are provided.

        Args:
            metadata: Method metadata
            provided_params: Parameters provided by user

        Returns:
            List of missing parameter names
        """
        missing = []
        for param_name in metadata.required_parameters:
            if param_name not in provided_params:
                missing.append(param_name)
        return missing

    @abstractmethod
    def generate(self) -> Any:
        """
        Generate the interface (CLI parser, Python API, etc.).

        Returns:
            Generated interface object
        """
        pass
