"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Base validator class with common functionality.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ValidationError:
    """
    Validation error for configuration validation.
    
    Attributes:
        message: Error message describing the validation failure
    """
    message: str


class BaseValidator:
    """Base class for configuration validators with common path resolution."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize validator with optional config file path for resolving relative paths.
        
        Args:
            config_path: Path to configuration file (used to resolve relative file paths)
        """
        self.config_path = Path(config_path) if config_path else None
        self.config_dir = self.config_path.parent if self.config_path else Path.cwd()

    def _resolve_path(self, file_path: Optional[str]) -> Optional[Path]:
        """
        Resolve file path relative to config file directory.
        
        Handles both absolute paths (e.g., /etc/prgn/key.pem) and relative paths.
        Absolute paths are returned as-is, relative paths are resolved relative to
        the configuration file's directory.
        
        Args:
            file_path: File path (can be relative or absolute)
                      Examples:
                      - Absolute: "/etc/prgn/key.pem"
                      - Relative: "mtls_certificates/server/test-server.crt"
                      - Relative: "./certs/cert.pem"
            
        Returns:
            Resolved Path object or None if file_path is None
        """
        if not file_path:
            return None
        path = Path(file_path)
        # If path is absolute (starts with /), return as-is
        if path.is_absolute():
            return path
        # Otherwise, resolve relative to config file directory
        return (self.config_dir / path).resolve()

