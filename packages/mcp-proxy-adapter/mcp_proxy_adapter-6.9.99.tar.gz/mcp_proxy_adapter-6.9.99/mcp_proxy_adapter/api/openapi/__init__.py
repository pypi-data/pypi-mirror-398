"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

OpenAPI schema generation package for MCP Proxy Adapter.
"""

from .openapi_generator import CustomOpenAPIGenerator
from .schema_loader import SchemaLoader
from .command_integration import CommandIntegrator
from .openapi_registry import OpenAPIRegistry

__all__ = [
    "CustomOpenAPIGenerator",
    "SchemaLoader",
    "CommandIntegrator",
    "OpenAPIRegistry",
    "custom_openapi",
    "custom_openapi_with_fallback",
]
