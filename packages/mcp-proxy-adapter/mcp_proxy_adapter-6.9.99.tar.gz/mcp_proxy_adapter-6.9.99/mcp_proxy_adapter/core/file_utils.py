"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

File utilities for common file operations.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

from ..commands.result import ErrorResult


def validate_file_exists(
    file_path: str,
    file_type: str = "file",
    return_error: bool = True,
) -> Tuple[bool, Optional[ErrorResult]]:
    """
    Validate that file exists and is readable.

    Args:
        file_path: Path to file
        file_type: Type of file for error message (e.g., "certificate", "key")
        return_error: If True, return ErrorResult on failure

    Returns:
        Tuple of (exists, error_result)
    """
    path = Path(file_path)

    if not path.exists():
        if return_error:
            return False, ErrorResult(
                message=f"{file_type.capitalize()} file not found: {file_path}"
            )
        return False, None

    if not path.is_file():
        if return_error:
            return False, ErrorResult(
                message=f"Path is not a file: {file_path}"
            )
        return False, None

    if not os.access(file_path, os.R_OK):
        if return_error:
            return False, ErrorResult(
                message=f"{file_type.capitalize()} file is not readable: {file_path}"
            )
        return False, None

    return True, None


def validate_file_not_empty(file_path: str) -> Tuple[bool, Optional[ErrorResult]]:
    """
    Validate that file exists and is not empty.

    Args:
        file_path: Path to file

    Returns:
        Tuple of (is_valid, error_result)
    """
    exists, error = validate_file_exists(file_path)
    if not exists:
        return False, error

    try:
        with open(file_path, "rb") as f:
            data = f.read()
            if not data:
                return False, ErrorResult(
                    message=f"File is empty: {file_path}"
                )
        return True, None
    except Exception as e:
        return False, ErrorResult(
            message=f"Failed to read file: {str(e)}"
        )


def ensure_directory_exists(directory_path: str) -> Tuple[bool, Optional[ErrorResult]]:
    """
    Ensure that directory exists, create if it doesn't.

    Args:
        directory_path: Path to directory

    Returns:
        Tuple of (success, error_result)
    """
    try:
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return True, None
    except Exception as e:
        return False, ErrorResult(
            message=f"Failed to create directory: {str(e)}"
        )

