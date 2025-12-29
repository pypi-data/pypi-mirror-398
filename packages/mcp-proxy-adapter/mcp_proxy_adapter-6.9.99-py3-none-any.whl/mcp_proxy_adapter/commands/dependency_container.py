"""
Module for dependency injection container implementation.

This module provides a container for registering and resolving dependencies
for command instances in the microservice.
"""

from typing import TypeVar, Dict, Any, Callable, Optional

T = TypeVar("T")


class DependencyContainer:
    """
    Container for managing dependencies.

    This class provides functionality to register, resolve, and manage
    dependencies that can be injected into command instances.
    """

    def __init__(self):
        """Initialize dependency container."""
        self._dependencies: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._singletons: Dict[str, Any] = {}





    def clear(self) -> None:
        """Clear all registered dependencies."""
        self._dependencies.clear()
        self._factories.clear()
        self._singletons.clear()



# Global dependency container instance
container = DependencyContainer()
