"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Token validation helpers for MCP Proxy Adapter.
"""

from __future__ import annotations

import logging
from typing import Optional

from .models import AuthValidationResult


class TokenValidator:
    """
    Validates API and JWT tokens.

    Keeps token specific logic outside of the main auth validator module.
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Create a new token validator instance.

        Args:
            logger: Optional logger instance for diagnostics.
        """
        self._logger = logger or logging.getLogger(__name__)

    def validate(self, token: Optional[str], token_type: str = "jwt") -> AuthValidationResult:
        """
        Validate provided token by type.

        Args:
            token: Token string.
            token_type: Supported types: "jwt" or "api".

        Returns:
            AuthValidationResult describing validation outcome.
        """
        if not token:
            return AuthValidationResult(
                is_valid=False,
                error_code=-32011,
                error_message="Token not provided",
            )

        if token_type == "jwt":
            return self._validate_jwt_token(token)
        if token_type == "api":
            return self._validate_api_token(token)

        return AuthValidationResult(
            is_valid=False,
            error_code=-32602,
            error_message=f"Unsupported token type: {token_type}",
        )

    def _validate_jwt_token(self, token: str) -> AuthValidationResult:
        """
        Perform lightweight JWT validation.

        Args:
            token: JWT token string.
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return AuthValidationResult(
                    is_valid=False,
                    error_code=-32004,
                    error_message="Invalid JWT token format",
                )

            return AuthValidationResult(is_valid=True, roles=[])

        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("JWT validation error: %s", exc)
            return AuthValidationResult(
                is_valid=False,
                error_code=-32004,
                error_message=f"JWT validation failed: {exc}",
            )

    def _validate_api_token(self, token: str) -> AuthValidationResult:
        """
        Validate API token (placeholder).

        Args:
            token: API token string.
        """
        try:
            if not token:
                return AuthValidationResult(
                    is_valid=False,
                    error_code=-32011,
                    error_message="API token not found",
                )

            return AuthValidationResult(is_valid=True, roles=[])

        except Exception as exc:  # pylint: disable=broad-except
            self._logger.error("API token validation error: %s", exc)
            return AuthValidationResult(
                is_valid=False,
                error_code=-32004,
                error_message=f"API token validation failed: {exc}",
            )
