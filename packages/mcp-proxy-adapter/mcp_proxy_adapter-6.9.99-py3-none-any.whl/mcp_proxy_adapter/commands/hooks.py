"""
Module for command registration hooks.

This module provides a hook system for registering custom commands
that will be called during system initialization.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Callable, Tuple

from mcp_proxy_adapter.core.logging import get_global_logger


class HookType(Enum):
    """Types of hooks that can be registered."""

    CUSTOM_COMMANDS = "custom_commands"
    BEFORE_INIT = "before_init"
    AFTER_INIT = "after_init"
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    BEFORE_EXECUTION = "before_execution"
    AFTER_EXECUTION = "after_execution"


@dataclass
class HookContext:
    """Context object passed to hook functions."""

    hook_type: HookType
    command_name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    registry: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    standard_processing: bool = True

    def __post_init__(self) -> None:
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class CommandHooks:
    """
    Hook system for command registration.
    """

    def __init__(self) -> None:
        """
        Initialize command hooks.
        """
        self._custom_commands_hooks: List[Callable] = []
        self._before_init_hooks: List[Callable] = []
        self._after_init_hooks: List[Callable] = []
        self._before_command_hooks: List[Callable] = []
        self._after_command_hooks: List[Callable] = []
        # Module paths for auto-registration in child processes (spawn mode)
        # These are stored as strings to avoid pickle issues
        self._auto_register_modules: List[str] = []
        # Hook module paths and function names for reconstruction (Option B)
        # Stored as (module_path, function_name) tuples
        self._hook_modules: List[Tuple[str, str]] = []

    def register_custom_commands_hook(self, hook_func: Callable) -> None:
        """
        Register a hook function for custom commands registration.

        Args:
            hook_func: Function that registers custom commands.
                      Should accept registry as parameter.
                      Can have __auto_import_modules__ attribute (list of module paths)
                      to explicitly specify modules to import in child processes.
        """
        self._custom_commands_hooks.append(hook_func)
        get_global_logger().debug(
            f"Registered custom commands hook: {hook_func.__name__}"
        )

        # Also store module path for auto-registration in child processes (spawn mode)
        # This allows commands to be registered when modules are imported in child processes
        module_path = getattr(hook_func, "__module__", None)
        function_name = getattr(hook_func, "__name__", None)

        if module_path:
            # Store module path for Option A (module-level auto-registration)
            if module_path not in self._auto_register_modules:
                self._auto_register_modules.append(module_path)
                get_global_logger().debug(
                    f"Registered module for auto-import: {module_path}"
                )

            # Store module path and function name for Option B (hook reconstruction)
            if function_name:
                hook_info = (module_path, function_name)
                if hook_info not in self._hook_modules:
                    self._hook_modules.append(hook_info)
                    get_global_logger().debug(
                        f"Registered hook for reconstruction: {module_path}.{function_name}"
                    )

        # CRITICAL FIX: Extract command modules from hook
        # Hook can explicitly specify modules via __auto_import_modules__ attribute
        explicit_modules = getattr(hook_func, "__auto_import_modules__", None)
        if explicit_modules:
            if isinstance(explicit_modules, (list, tuple)):
                for mod_path in explicit_modules:
                    if mod_path and mod_path not in self._auto_register_modules:
                        self._auto_register_modules.append(mod_path)
                        get_global_logger().debug(
                            f"Registered explicit module for auto-import from hook: {mod_path}"
                        )
            elif isinstance(explicit_modules, str):
                if explicit_modules not in self._auto_register_modules:
                    self._auto_register_modules.append(explicit_modules)
                    get_global_logger().debug(
                        f"Registered explicit module for auto-import from hook: {explicit_modules}"
                    )

        # Also try to extract command modules by executing hook with a test registry
        # This captures modules of commands that are actually registered
        try:
            from mcp_proxy_adapter.commands.command_registry import CommandRegistry

            # Create a test registry to capture registered command modules
            test_registry = CommandRegistry()
            # Execute hook to see what commands it registers
            hook_func(test_registry)

            # Extract modules from registered commands
            # Filter out adapter's own modules (they're always available)
            adapter_prefix = "mcp_proxy_adapter."
            for cmd_name, cmd_class in test_registry._commands.items():
                cmd_module = getattr(cmd_class, "__module__", None)
                if (
                    cmd_module
                    and not cmd_module.startswith(adapter_prefix)
                    and cmd_module not in self._auto_register_modules
                ):
                    self._auto_register_modules.append(cmd_module)
                    get_global_logger().debug(
                        f"Auto-detected command module from hook: {cmd_module} (command: {cmd_name})"
                    )
        except Exception as e:
            # If hook execution fails, that's OK - we'll rely on explicit modules or module path
            get_global_logger().debug(
                f"Could not extract command modules from hook {hook_func.__name__}: {e}. "
                f"Using explicit modules or module path only."
            )

    def register_before_init_hook(self, hook_func: Callable) -> None:
        """
        Register a hook function to be called before system initialization.

        Args:
            hook_func: Function to call before initialization.
        """
        self._before_init_hooks.append(hook_func)
        get_global_logger().debug(f"Registered before init hook: {hook_func.__name__}")

    def register_after_init_hook(self, hook_func: Callable) -> None:
        """
        Register a hook function to be called after system initialization.

        Args:
            hook_func: Function to call after initialization.
        """
        self._after_init_hooks.append(hook_func)
        get_global_logger().debug(f"Registered after init hook: {hook_func.__name__}")

    def register_before_command_hook(self, hook_func: Callable) -> None:
        """
        Register a hook function to be called before command execution.

        Args:
            hook_func: Function to call before command execution.
                      Should accept command_name and params as parameters.
        """
        self._before_command_hooks.append(hook_func)
        get_global_logger().debug(
            f"Registered before command hook: {hook_func.__name__}"
        )

    def register_after_command_hook(self, hook_func: Callable) -> None:
        """
        Register a hook function to be called after command execution.

        Args:
            hook_func: Function to call after command execution.
                      Should accept command_name, params, and result as parameters.
        """
        self._after_command_hooks.append(hook_func)
        get_global_logger().debug(
            f"Registered after command hook: {hook_func.__name__}"
        )

    def execute_custom_commands_hooks(self, registry: Any) -> int:
        """
        Execute all registered custom commands hooks.

        Args:
            registry: Command registry instance to pass to hook functions.

        Returns:
            Number of hooks executed successfully.
        """
        executed_count = 0
        for hook_func in self._custom_commands_hooks:
            try:
                hook_func(registry)
                executed_count += 1
                get_global_logger().debug(
                    f"Executed custom commands hook: {hook_func.__name__}"
                )
            except Exception as e:
                get_global_logger().error(
                    f"Failed to execute custom commands hook {hook_func.__name__}: {e}"
                )
        return executed_count

    def execute_before_init_hooks(self) -> int:
        """
        Execute all registered before init hooks.

        Returns:
            Number of hooks executed successfully.
        """
        executed_count = 0
        for hook_func in self._before_init_hooks:
            try:
                hook_func()
                executed_count += 1
                get_global_logger().debug(
                    f"Executed before init hook: {hook_func.__name__}"
                )
            except Exception as e:
                get_global_logger().error(
                    f"Failed to execute before init hook {hook_func.__name__}: {e}"
                )
        return executed_count

    def execute_after_init_hooks(self) -> int:
        """
        Execute all registered after init hooks.

        Returns:
            Number of hooks executed successfully.
        """
        executed_count = 0
        for hook_func in self._after_init_hooks:
            try:
                hook_func()
                executed_count += 1
                get_global_logger().debug(
                    f"Executed after init hook: {hook_func.__name__}"
                )
            except Exception as e:
                get_global_logger().error(
                    f"Failed to execute after init hook {hook_func.__name__}: {e}"
                )
        return executed_count

    def execute_before_command_hooks(
        self, command_name: str, params: Dict[str, Any]
    ) -> None:
        """
        Execute all registered before command hooks.

        Args:
            command_name: Name of the command being executed.
            params: Command parameters.
        """
        for hook_func in self._before_command_hooks:
            try:
                hook_func(command_name, params)
                get_global_logger().debug(
                    f"Executed before command hook: {hook_func.__name__}"
                )
            except Exception as e:
                get_global_logger().error(
                    f"Failed to execute before command hook {hook_func.__name__}: {e}"
                )

    def execute_after_command_hooks(
        self, command_name: str, params: Dict[str, Any], result: Any
    ) -> None:
        """
        Execute all registered after command hooks.

        Args:
            command_name: Name of the command that was executed.
            params: Command parameters.
            result: Command execution result.
        """
        for hook_func in self._after_command_hooks:
            try:
                hook_func(command_name, params, result)
                get_global_logger().debug(
                    f"Executed after command hook: {hook_func.__name__}"
                )
            except Exception as e:
                get_global_logger().error(
                    f"Failed to execute after command hook {hook_func.__name__}: {e}"
                )

    def register_auto_import_module(self, module_path: str) -> None:
        """
        Register a module path for auto-import in child processes.

        This is used to ensure custom commands are registered in child processes
        when using multiprocessing spawn mode (required for CUDA compatibility).

        The adapter will automatically ensure the module's directory is in
        PYTHONPATH for child processes (spawn mode).

        Args:
            module_path: Full module path (e.g., "embed.main" or "embed.commands")
        """
        if module_path and module_path not in self._auto_register_modules:
            self._auto_register_modules.append(module_path)
            get_global_logger().debug(
                f"Registered module for auto-import: {module_path}"
            )

            # Try to ensure module path is available in PYTHONPATH
            # This helps with spawn mode where child processes don't inherit sys.path
            try:
                from mcp_proxy_adapter.core.path_utils import (
                    ensure_module_path_in_syspath,
                )

                if ensure_module_path_in_syspath(module_path):
                    get_global_logger().debug(
                        f"Added module path to PYTHONPATH: {module_path}"
                    )
            except Exception:
                # Path utils may not be available or module not yet importable
                # This is OK - we'll try again in child process
                pass

    def get_auto_import_modules(self) -> List[str]:
        """
        Get list of module paths that should be imported in child processes.

        Returns:
            List of module paths for auto-import
        """
        return self._auto_register_modules.copy()

    def get_hook_modules(self) -> List[Tuple[str, str]]:
        """
        Get list of hook module paths and function names for reconstruction.

        Returns:
            List of (module_path, function_name) tuples
        """
        return self._hook_modules.copy()

    def reconstruct_hooks(self, registry: Any) -> int:
        """
        Reconstruct and execute hooks from stored module paths and function names.

        This is used in child processes (spawn mode) to execute hooks that were
        registered in the main process but cannot be pickled.

        Args:
            registry: Command registry instance to pass to hook functions.

        Returns:
            Number of hooks executed successfully.
        """
        import importlib

        executed_count = 0
        for module_path, function_name in self._hook_modules:
            try:
                module = importlib.import_module(module_path)
                hook_func = getattr(module, function_name, None)
                if hook_func and callable(hook_func):
                    hook_func(registry)
                    executed_count += 1
                    get_global_logger().debug(
                        f"Reconstructed and executed hook: {module_path}.{function_name}"
                    )
                else:
                    get_global_logger().warning(
                        f"Hook function {module_path}.{function_name} not found or not callable"
                    )
            except (ImportError, ModuleNotFoundError) as e:
                get_global_logger().debug(
                    f"Could not import module {module_path} for hook reconstruction: {e}"
                )
            except AttributeError as e:
                get_global_logger().warning(
                    f"Could not find function {function_name} in module {module_path}: {e}"
                )
            except Exception as e:
                get_global_logger().error(
                    f"Failed to reconstruct hook {module_path}.{function_name}: {e}"
                )
        return executed_count


# Global hooks instance
hooks = CommandHooks()


def register_custom_commands_hook(hook_func: Callable) -> None:
    """
    Register a hook function for custom commands registration.

    Args:
        hook_func: Function that registers custom commands.
                  Should accept registry as parameter.
    """
    hooks.register_custom_commands_hook(hook_func)


def register_before_init_hook(hook_func: Callable) -> None:
    """
    Register a hook function to be called before system initialization.

    Args:
        hook_func: Function to call before initialization.
    """
    hooks.register_before_init_hook(hook_func)


def register_after_init_hook(hook_func: Callable) -> None:
    """
    Register a hook function to be called after system initialization.

    Args:
        hook_func: Function to call after initialization.
    """
    hooks.register_after_init_hook(hook_func)


def register_before_command_hook(hook_func: Callable) -> None:
    """
    Register a hook function to be called before command execution.

    Args:
        hook_func: Function to call before command execution.
                  Should accept command_name and params as parameters.
    """
    hooks.register_before_command_hook(hook_func)


def register_after_command_hook(hook_func: Callable) -> None:
    """
    Register a hook function to be called after command execution.

    Args:
        hook_func: Function to call after command execution.
                  Should accept command_name, params, and result as parameters.
    """
    hooks.register_after_command_hook(hook_func)


def register_auto_import_module(module_path: str) -> None:
    """
    Register a module path for auto-import in child processes.

    This is used to ensure custom commands are registered in child processes
    when using multiprocessing spawn mode (required for CUDA compatibility).

    When a module is imported in a child process, it can auto-register commands
    at module level, making them available even though hook functions cannot
    be pickled and transferred to child processes.

    Args:
        module_path: Full module path (e.g., "embed.main" or "embed.commands")

    Example:
        ```python
        # In your application's main.py
        from mcp_proxy_adapter.commands.hooks import register_auto_import_module

        # Register module for auto-import in child processes
        register_auto_import_module("embed.commands")
        ```
    """
    hooks.register_auto_import_module(module_path)
