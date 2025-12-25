"""
MAQET API System

This module implements the unified API generation system that allows
single method definitions to automatically become CLI commands, Python API
methods, REST API endpoints, GraphQL resolvers, and other interfaces.

The system is designed to be extensible - new generators can be added by:
1. Implementing BaseGenerator interface in generators/
2. Reading method metadata from API_REGISTRY
3. Generating appropriate interface code (routes, schemas, etc.)

Example generators:
- CLIGenerator: Creates argparse CLI commands
- PythonAPIGenerator: Creates direct Python method calls
- RestAPIGenerator: Could create FastAPI/Flask routes
- GraphQLGenerator: Could create GraphQL schema and resolvers
- OpenAPIGenerator: Could generate OpenAPI/Swagger documentation
"""

from .decorators import AutoRegisterAPI, api_method, register_class_methods
from .metadata import APIMethodMetadata
from .registry import API_REGISTRY, APIRegistry
from .provider import (
    APIRegistryProvider,
    ProductionRegistryProvider,
    WorkerScopedRegistryProvider,
)

__all__ = [
    "api_method",
    "register_class_methods",
    "AutoRegisterAPI",
    "API_REGISTRY",
    "APIRegistry",
    "APIMethodMetadata",
    "APIRegistryProvider",
    "ProductionRegistryProvider",
    "WorkerScopedRegistryProvider",
]

# NOTE: The system is designed to be easily extensible for new interfaces.
# See module docstring above for implementation guidance.
