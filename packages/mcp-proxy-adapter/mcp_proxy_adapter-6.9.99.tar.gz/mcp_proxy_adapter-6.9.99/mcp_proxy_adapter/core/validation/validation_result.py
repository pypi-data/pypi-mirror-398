"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Validation result classes for MCP Proxy Adapter configuration validation.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Union


class ValidationLevel(str, Enum):
    """Validation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    level: Union[ValidationLevel, str]
    message: str
    section: Optional[str] = None
    key: Optional[str] = None
    suggestion: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize level value to ValidationLevel enum."""
        if isinstance(self.level, str) and not isinstance(self.level, ValidationLevel):
            self.level = ValidationLevel(self.level.lower())
