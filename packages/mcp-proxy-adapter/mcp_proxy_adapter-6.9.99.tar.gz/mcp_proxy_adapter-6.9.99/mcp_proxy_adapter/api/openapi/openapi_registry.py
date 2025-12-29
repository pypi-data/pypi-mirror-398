"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Registry for OpenAPI generators.
"""

from typing import Dict, Callable, Optional, List

from mcp_proxy_adapter.core.logging import get_global_logger


class OpenAPIRegistry:
    """Registry for OpenAPI generators."""

    def __init__(self):
        """Initialize OpenAPI registry."""
        self.logger = get_global_logger()
        self._generators: Dict[str, Callable] = {}

    def register_generator(self, name: str, generator: Callable) -> None:
        """
        Register an OpenAPI generator.

        Args:
            name: Generator name
            generator: Generator function
        """
        self._generators[name] = generator
        self.logger.debug(f"Registered OpenAPI generator: {name}")

    def get_generator(self, name: str) -> Optional[Callable]:
        """
        Get an OpenAPI generator by name.

        Args:
            name: Generator name

        Returns:
            Generator function or None if not found
        """
        return self._generators.get(name)

    def list_generators(self) -> List[str]:
        """
        List all registered generators.

        Returns:
            List of generator names
        """
        return list(self._generators.keys())



# Global registry instance
_registry = OpenAPIRegistry()






