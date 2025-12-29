"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Helper functions for registration context building.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple


def build_cert_tuple(
    cert_file: Optional[str],
    key_file: Optional[str],
) -> Optional[Tuple[str, str]]:
    """
    Build certificate tuple from file paths.
    
    Args:
        cert_file: Path to certificate file
        key_file: Path to private key file
        
    Returns:
        Tuple of (cert_path, key_path) if both files exist, None otherwise
    """
    if not cert_file or not key_file:
        return None

    cert_path = Path(cert_file)
    key_path = Path(key_file)
    if not cert_path.exists() or not key_path.exists():
        return None

    return (str(cert_path), str(key_path))

