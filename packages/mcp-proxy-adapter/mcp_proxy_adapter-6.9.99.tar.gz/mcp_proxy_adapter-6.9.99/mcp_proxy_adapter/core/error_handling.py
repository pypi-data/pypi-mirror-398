"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Error handling utilities and decorators for command handlers.
"""

from functools import wraps
from typing import Callable, Any

from ..commands.result import CommandResult, ErrorResult, SuccessResult
from ..core.logging import get_global_logger


def handle_command_errors(
    operation_name: str,
    log_success: bool = True,
):
    """
    Decorator for handling errors in command handlers.

    Args:
        operation_name: Name of operation for logging
        log_success: Whether to log successful operations

    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., CommandResult]) -> Callable[..., CommandResult]:
        """
        Decorator factory for async command handlers.

        Args:
            func: Function to wrap.

        Returns:
            Wrapped coroutine with error handling.
        """

        @wraps(func)
        async def wrapper(*args, **kwargs) -> CommandResult:
            """Execute wrapped async function with logging and error handling."""
            try:
                result = await func(*args, **kwargs)
                if log_success and isinstance(result, SuccessResult):
                    get_global_logger().info(
                        f"{operation_name} completed successfully"
                    )
                return result
            except Exception as e:
                get_global_logger().error(f"{operation_name} failed: {e}")
                return ErrorResult(
                    message=f"{operation_name} failed: {str(e)}"
                )
        return wrapper
    return decorator


def handle_sync_command_errors(
    operation_name: str,
    log_success: bool = True,
):
    """
    Decorator for handling errors in synchronous command handlers.

    Args:
        operation_name: Name of operation for logging
        log_success: Whether to log successful operations

    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., CommandResult]) -> Callable[..., CommandResult]:
        """
        Decorator factory for sync command handlers.

        Args:
            func: Function to wrap.

        Returns:
            Wrapped function with error handling.
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> CommandResult:
            """Execute wrapped sync function with logging and error handling."""
            try:
                result = func(*args, **kwargs)
                if log_success and isinstance(result, SuccessResult):
                    get_global_logger().info(
                        f"{operation_name} completed successfully"
                    )
                return result
            except Exception as e:
                get_global_logger().error(f"{operation_name} failed: {e}")
                return ErrorResult(
                    message=f"{operation_name} failed: {str(e)}"
                )
        return wrapper
    return decorator

