"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

JSON utilities for common JSON file operations.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..commands.result import ErrorResult


def save_json_file(
    data: Dict[str, Any],
    file_path: str,
    indent: int = 2,
) -> Tuple[bool, Optional[ErrorResult]]:
    """
    Save data to JSON file.

    Args:
        data: Data to save
        file_path: Path to JSON file
        indent: JSON indentation level

    Returns:
        Tuple of (success, error_result)
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=indent)
        return True, None
    except Exception as e:
        return False, ErrorResult(message=f"Failed to save JSON file: {str(e)}")


def load_json_file(
    file_path: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[ErrorResult]]:
    """
    Load data from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Tuple of (data, error_result)
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, ErrorResult(message=f"JSON file not found: {file_path}")
    except json.JSONDecodeError as e:
        return None, ErrorResult(message=f"Invalid JSON in file: {str(e)}")
    except Exception as e:
        return None, ErrorResult(message=f"Failed to load JSON file: {str(e)}")


def parse_json_string(
    json_string: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[ErrorResult]]:
    """
    Parse JSON string.

    Args:
        json_string: JSON string to parse

    Returns:
        Tuple of (data, error_result)
    """
    try:
        return json.loads(json_string), None
    except json.JSONDecodeError as e:
        return None, ErrorResult(message=f"Invalid JSON string: {str(e)}")
    except Exception as e:
        return None, ErrorResult(message=f"Failed to parse JSON string: {str(e)}")

