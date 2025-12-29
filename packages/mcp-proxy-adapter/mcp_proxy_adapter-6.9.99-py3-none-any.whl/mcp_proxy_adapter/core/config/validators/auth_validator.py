"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Authentication and authorization configuration validator.
"""

from __future__ import annotations

from typing import List

from .base_validator import BaseValidator, ValidationError
from mcp_proxy_adapter.core.role_utils import RoleUtils
from ..simple_config import SimpleConfigModel


class AuthValidator(BaseValidator):
    """Validator for authentication and authorization configuration."""

    def validate(self, model: SimpleConfigModel) -> List[ValidationError]:
        """
        Validate authentication and authorization configuration.
        
        Args:
            model: Configuration model
            
        Returns:
            List of validation errors for auth section
        """
        errors: List[ValidationError] = []
        a = model.auth
        
        if a.use_roles and not a.use_token:
            errors.append(
                ValidationError("auth.use_roles requires auth.use_token to be true")
            )
        
        if a.use_token and not a.tokens:
            errors.append(
                ValidationError(
                    "auth.tokens must be provided when auth.use_token is true"
                )
            )
        
        # Validate roles in tokens using mcp_security_framework
        if a.tokens:
            for token, roles in a.tokens.items():
                if not isinstance(roles, list):
                    errors.append(
                        ValidationError(
                            f"auth.tokens['{token}'] must be a list of roles"
                        )
                    )
                    continue
                
                for role in roles:
                    if not isinstance(role, str):
                        errors.append(
                            ValidationError(
                                f"auth.tokens['{token}'] contains non-string role: {role}"
                            )
                        )
                        continue
                    
                    try:
                        if not RoleUtils.validate_single_role(role):
                            valid_roles = RoleUtils.get_valid_roles()
                            valid_roles_str = (
                                ", ".join(valid_roles) if valid_roles else "none available"
                            )
                            errors.append(
                                ValidationError(
                                    f"auth.tokens['{token}'] contains unknown role '{role}'. "
                                    f"Valid roles: {valid_roles_str}"
                                )
                            )
                    except Exception as ex:
                        errors.append(
                            ValidationError(
                                f"auth.tokens['{token}'] role validation error for '{role}': {ex}"
                            )
                        )
        
        # Validate roles in auth.roles
        if a.roles:
            for role_name, permissions in a.roles.items():
                if not isinstance(permissions, list):
                    errors.append(
                        ValidationError(
                            f"auth.roles['{role_name}'] must be a list of permissions"
                        )
                    )
                    continue
                
                try:
                    if not RoleUtils.validate_single_role(role_name):
                        valid_roles = RoleUtils.get_valid_roles()
                        valid_roles_str = (
                            ", ".join(valid_roles) if valid_roles else "none available"
                        )
                        errors.append(
                            ValidationError(
                                f"auth.roles contains unknown role '{role_name}'. "
                                f"Valid roles: {valid_roles_str}"
                            )
                        )
                except Exception as ex:
                    errors.append(
                        ValidationError(
                            f"auth.roles role validation error for '{role_name}': {ex}"
                        )
                    )
        
        return errors

