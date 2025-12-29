"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Authentication data models for MCP Proxy Adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AuthValidationResult:
    """
    Represents the outcome of an authentication check.

    Attributes:
        is_valid: Indicates successful authentication.
        error_code: JSON-RPC error code when validation fails.
        error_message: Human readable error description.
        roles: Collection of extracted roles.
    """

    is_valid: bool
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    roles: List[str] = field(default_factory=list)

    def with_error(self, code: int, message: str) -> "AuthValidationResult":
        """
        Produce a new validation result in error state.

        Args:
            code: JSON-RPC error code.
            message: Explanation of the failure.

        Returns:
            AuthValidationResult: New instance containing error data.
        """
        return AuthValidationResult(
            is_valid=False,
            error_code=code,
            error_message=message,
            roles=self.roles.copy(),
        )
