"""
API Registry

Registry for tracking all decorated API methods and providing
lookup capabilities for CLI and Python API generation.

Supports both global registry (backward compatibility) and instance-based
registry (for parallel tests and multiple Maqet instances).
"""

import inspect
from typing import Any, Dict, List, Optional

from .metadata import APIMethodMetadata


class APIRegistry:
    """
    Registry for API methods decorated with @api_method.

    This registry enables generators to discover all available methods
    and their metadata for creating CLI commands and Python APIs.

    Can be used as:
    - Global registry (API_REGISTRY) for backward compatibility
    - Instance registry (one per Maqet instance) for isolated registries
    """

    def __init__(self):
        """Initialize the API registry with empty collections."""
        self._methods: Dict[str, APIMethodMetadata] = {}
        self._cli_commands: Dict[str, str] = {}  # cli_name -> full_name
        self._categories: Dict[str, List[str]] = {}  # category -> [full_names]

    def register(self, metadata: APIMethodMetadata) -> None:
        """
        Register a new API method.

        Args:
            metadata: Method metadata to register
        """
        full_name = metadata.full_name
        self._methods[full_name] = metadata

        # Register CLI command mapping
        if metadata.cli_name:
            self._cli_commands[metadata.cli_name] = full_name

        # Register category mapping
        if metadata.category not in self._categories:
            self._categories[metadata.category] = []
        self._categories[metadata.category].append(full_name)

    def get_method(self, full_name: str) -> Optional[APIMethodMetadata]:
        """
        Get method metadata by full name.

        Args:
            full_name: Full method name (e.g., 'Maqet.start')

        Returns:
            Method metadata or None if not found
        """
        return self._methods.get(full_name)

    def get_by_cli_name(self, cli_name: str) -> Optional[APIMethodMetadata]:
        """
        Get method metadata by CLI command name.

        Args:
            cli_name: CLI command name (e.g., 'start')

        Returns:
            Method metadata or None if not found
        """
        full_name = self._cli_commands.get(cli_name)
        return self._methods.get(full_name) if full_name else None

    def get_by_category(self, category: str) -> List[APIMethodMetadata]:
        """
        Get all methods in a category.

        Args:
            category: Category name (e.g., 'vm', 'qmp')

        Returns:
            List of method metadata in the category
        """
        full_names = self._categories.get(category, [])
        return [self._methods[name] for name in full_names]

    def get_all_methods(self) -> List[APIMethodMetadata]:
        """
        Get all registered methods.

        Returns:
            List of all method metadata
        """
        return list(self._methods.values())

    def get_all_methods_dict(self) -> Dict[str, APIMethodMetadata]:
        """
        Get all registered methods as a dictionary.

        Returns:
            Dictionary mapping method names to metadata
        """
        return self._methods.copy()

    def get_all_cli_commands(self) -> Dict[str, APIMethodMetadata]:
        """
        Get all CLI commands and their metadata.

        Returns:
            Dictionary mapping CLI command names to metadata
        """
        return {
            cli_name: self._methods[full_name]
            for cli_name, full_name in self._cli_commands.items()
        }

    def get_categories(self) -> List[str]:
        """
        Get all available categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def clear(self) -> None:
        """Clear all registered methods (mainly for testing)."""
        self._methods.clear()
        self._cli_commands.clear()
        self._categories.clear()

    def register_from_instance(self, instance: Any) -> None:
        """
        Register all @api_method decorated methods from an instance.

        This enables instance-based registries where each Maqet instance
        has its own registry, allowing for:
        - Parallel test execution without registry pollution
        - Multiple Maqet instances with different configurations
        - Thread-safe operation

        Args:
            instance: Object instance to scan for @api_method decorated methods

        Example:
            registry = APIRegistry()
            maqet = Maqet()
            registry.register_from_instance(maqet)
        """
        # Get the class of the instance
        cls = instance.__class__

        # Scan for decorated methods
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if hasattr(method, "_api_metadata"):
                metadata: APIMethodMetadata = method._api_metadata
                # Clone metadata with bound method (instance-specific)
                # Use cls.__name__ if owner_class is not set (for classes that don't inherit AutoRegisterAPI)
                owner_class = metadata.owner_class or cls.__name__
                bound_metadata = APIMethodMetadata(
                    name=metadata.name,
                    function=getattr(instance, name),  # Bound method
                    owner_class=owner_class,
                    cli_name=metadata.cli_name,
                    description=metadata.description,
                    signature=metadata.signature,
                    category=metadata.category,
                    requires_vm=metadata.requires_vm,
                    examples=metadata.examples,
                    aliases=metadata.aliases,
                    hidden=metadata.hidden,
                    parent=metadata.parent,
                )
                self.register(bound_metadata)


# Global registry instance (for backward compatibility)
# New code should prefer instance-based registries via register_from_instance()
API_REGISTRY = APIRegistry()
