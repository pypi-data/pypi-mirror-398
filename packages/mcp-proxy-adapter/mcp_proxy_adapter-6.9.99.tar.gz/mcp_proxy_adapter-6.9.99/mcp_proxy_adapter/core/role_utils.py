"""
Role Utilities

This module provides utilities for working with roles extracted from certificates.
Uses mcp_security_framework CertificateRole enum for validation and normalization.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
Version: 2.0.0
"""

import logging
from typing import List, Optional

# Import mcp_security_framework
try:
    from mcp_security_framework.schemas.models import CertificateRole
    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False
    CertificateRole = None

logger = logging.getLogger(__name__)


class RoleUtils:
    """
    Utilities for working with roles from certificates.

    Uses mcp_security_framework CertificateRole enum for validation and normalization.
    Provides methods for extracting, comparing, validating, and normalizing roles.
    """

    # Custom OID for roles in certificates (matches mcp_security_framework)
    ROLE_EXTENSION_OID = "1.3.6.1.4.1.99999.1.1"

    @staticmethod
    def validate_single_role(role: str) -> bool:
        """
        Validate a single role using CertificateRole enum.

        Args:
            role: Role string to validate

        Returns:
            True if role is valid, False otherwise
        """
        if not SECURITY_FRAMEWORK_AVAILABLE:
            logger.warning("mcp_security_framework not available, using basic validation")
            return RoleUtils._validate_single_role_fallback(role)

        if not isinstance(role, str):
            return False

        if not role.strip():
            return False

        try:
            # Use CertificateRole enum for validation
            CertificateRole.from_string(role)
            return True
        except ValueError:
            return False

    @staticmethod
    def _validate_single_role_fallback(role: str) -> bool:
        """Fallback validation when framework is not available."""
        if not isinstance(role, str):
            return False

        if not role.strip():
            return False

        # Basic character validation
        valid_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        )
        role_chars = set(role.lower())

        if not role_chars.issubset(valid_chars):
            return False

        if len(role) < 1 or len(role) > 50:
            return False

        return True

    @staticmethod
    def normalize_role(role: str) -> str:
        """
        Normalize role string using CertificateRole enum.

        Args:
            role: Role string to normalize

        Returns:
            Normalized role string (lowercase, validated)
        """
        if not role:
            return ""

        if not SECURITY_FRAMEWORK_AVAILABLE:
            logger.warning("mcp_security_framework not available, using basic normalization")
            return RoleUtils._normalize_role_fallback(role)

        try:
            # Use CertificateRole enum for normalization
            role_enum = CertificateRole.from_string(role)
            return role_enum.value  # Already lowercase
        except ValueError:
            # Invalid role, return normalized lowercase version
            logger.warning(f"Invalid role '{role}', returning normalized lowercase version")
            return role.lower().strip()

    @staticmethod
    def _normalize_role_fallback(role: str) -> str:
        """Fallback normalization when framework is not available."""
        if not role:
            return ""

        # Convert to lowercase and trim whitespace
        normalized = role.lower().strip()

        # Replace multiple spaces with single space
        normalized = " ".join(normalized.split())

        # Replace spaces with hyphens
        normalized = normalized.replace(" ", "-")

        return normalized

    @staticmethod
    def normalize_roles(roles: List[str]) -> List[str]:
        """
        Normalize list of roles using CertificateRole enum.

        Args:
            roles: List of roles to normalize

        Returns:
            List of normalized roles (validated, lowercase, duplicates removed)
        """
        if not roles:
            return []

        if not SECURITY_FRAMEWORK_AVAILABLE:
            logger.warning("mcp_security_framework not available, using basic normalization")
            return RoleUtils._normalize_roles_fallback(roles)

        normalized = []
        for role in roles:
            try:
                # Use CertificateRole enum for validation and normalization
                role_enum = CertificateRole.from_string(role)
                normalized_role = role_enum.value  # Already lowercase
                if normalized_role not in normalized:
                    normalized.append(normalized_role)
            except ValueError:
                # Skip invalid roles
                logger.warning(f"Invalid role '{role}' skipped during normalization")
                continue

        return normalized

    @staticmethod
    def _normalize_roles_fallback(roles: List[str]) -> List[str]:
        """Fallback normalization when framework is not available."""
        if not roles:
            return []

        normalized = []
        for role in roles:
            normalized_role = RoleUtils._normalize_role_fallback(role)
            if normalized_role and normalized_role not in normalized:
                normalized.append(normalized_role)

        return normalized

    @staticmethod
    def get_valid_roles() -> List[str]:
        """
        Get list of all valid roles from CertificateRole enum.

        Returns:
            List of valid role strings
        """
        if not SECURITY_FRAMEWORK_AVAILABLE:
            logger.warning("mcp_security_framework not available, cannot get valid roles")
            return []

        return [role.value for role in CertificateRole]

    @staticmethod
    def get_default_role() -> str:
        """
        Get default role from CertificateRole enum.

        Returns:
            Default role string ("other")
        """
        if not SECURITY_FRAMEWORK_AVAILABLE:
            logger.warning("mcp_security_framework not available, returning 'other' as default")
            return "other"

        return CertificateRole.get_default_role().value
