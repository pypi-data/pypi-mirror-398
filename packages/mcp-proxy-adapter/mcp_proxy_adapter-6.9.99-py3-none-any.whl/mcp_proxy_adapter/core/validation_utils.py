"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Validation utilities for common parameter validation.
"""

from typing import Optional, Any, List

from ..commands.result import ErrorResult


def validate_non_empty_string(
    value: Optional[str],
    field_name: str = "Field",
) -> Optional[ErrorResult]:
    """
    Validate that string is not empty.

    Args:
        value: String value to validate
        field_name: Name of field for error message

    Returns:
        ErrorResult if validation fails, None otherwise
    """
    if not value or not value.strip():
        return ErrorResult(message=f"{field_name} cannot be empty")
    return None


def validate_positive_integer(
    value: Any,
    field_name: str = "Value",
) -> Optional[ErrorResult]:
    """
    Validate that value is a positive integer.

    Args:
        value: Value to validate
        field_name: Name of field for error message

    Returns:
        ErrorResult if validation fails, None otherwise
    """
    if not isinstance(value, int) or value <= 0:
        return ErrorResult(message=f"{field_name} must be a positive integer")
    return None


def validate_non_negative_integer(
    value: Any,
    field_name: str = "Value",
) -> Optional[ErrorResult]:
    """
    Validate that value is a non-negative integer.

    Args:
        value: Value to validate
        field_name: Name of field for error message

    Returns:
        ErrorResult if validation fails, None otherwise
    """
    if not isinstance(value, int) or value < 0:
        return ErrorResult(message=f"{field_name} must be a non-negative integer")
    return None


def validate_file_path(
    file_path: Optional[str],
    field_name: str = "File path",
) -> Optional[ErrorResult]:
    """
    Validate that file path is provided.

    Args:
        file_path: File path to validate
        field_name: Name of field for error message

    Returns:
        ErrorResult if validation fails, None otherwise
    """
    if not file_path:
        return ErrorResult(message=f"{field_name} is required")
    return None


def validate_list_not_empty(
    value: Optional[List[Any]],
    field_name: str = "List",
) -> Optional[ErrorResult]:
    """
    Validate that list is not empty.

    Args:
        value: List to validate
        field_name: Name of field for error message

    Returns:
        ErrorResult if validation fails, None otherwise
    """
    if not value or not isinstance(value, list) or len(value) == 0:
        return ErrorResult(message=f"{field_name} cannot be empty")
    return None


def validate_dict_not_empty(
    value: Optional[dict],
    field_name: str = "Dictionary",
) -> Optional[ErrorResult]:
    """
    Validate that dictionary is not empty.

    Args:
        value: Dictionary to validate
        field_name: Name of field for error message

    Returns:
        ErrorResult if validation fails, None otherwise
    """
    if not value or not isinstance(value, dict) or len(value) == 0:
        return ErrorResult(message=f"{field_name} cannot be empty")
    return None


def validate_key_size(key_size: int) -> Optional[ErrorResult]:
    """
    Validate RSA key size.

    Args:
        key_size: Key size in bits

    Returns:
        ErrorResult if validation fails, None otherwise
    """
    if key_size < 1024:
        return ErrorResult(message="Key size must be at least 1024 bits")
    if key_size > 8192:
        return ErrorResult(message="Key size must not exceed 8192 bits")
    return None


def validate_days_comparison(
    warning_days: int,
    critical_days: int,
) -> Optional[ErrorResult]:
    """
    Validate that warning days is greater than critical days.

    Args:
        warning_days: Warning threshold in days
        critical_days: Critical threshold in days

    Returns:
        ErrorResult if validation fails, None otherwise
    """
    if warning_days <= critical_days:
        return ErrorResult(
            message="Warning days must be greater than critical days"
        )
    return None

