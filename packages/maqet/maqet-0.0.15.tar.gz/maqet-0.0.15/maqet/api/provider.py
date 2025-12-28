"""
API Registry provider abstraction for testability.

Separates "what" (registry) from "how" (initialization).
This enables different initialization strategies for production vs testing:
- Production: singleton global registry
- Testing: worker-scoped registry for parallel test isolation
"""

from typing import Protocol, Optional
from maqet.api.registry import APIRegistry


class APIRegistryProvider(Protocol):
    """Protocol for providing API registry instances."""

    def get_registry(self) -> APIRegistry:
        """Get or create registry for current context."""
        ...


class ProductionRegistryProvider:
    """Production provider: singleton global registry."""

    def get_registry(self) -> APIRegistry:
        """Return global singleton registry."""
        from maqet.api import API_REGISTRY
        return API_REGISTRY


class WorkerScopedRegistryProvider:
    """Test provider: one registry per worker process."""

    def __init__(self):
        """Initialize provider with no registry."""
        self._registry: Optional[APIRegistry] = None

    def get_registry(self) -> APIRegistry:
        """Get or create worker-scoped registry."""
        if self._registry is None:
            import inspect
            from maqet.maqet import Maqet
            from maqet.api.metadata import APIMethodMetadata

            self._registry = APIRegistry()

            # Register Maqet methods to this specific registry instance
            for name, method in inspect.getmembers(Maqet, predicate=inspect.isfunction):
                if hasattr(method, "_api_metadata"):
                    metadata: APIMethodMetadata = method._api_metadata
                    # Set the owner class now that we know it
                    metadata.owner_class = Maqet.__name__
                    # Register with our worker-scoped registry
                    self._registry.register(metadata)

        return self._registry
