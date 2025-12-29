"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Server configuration section validator.
"""

from __future__ import annotations

from typing import List, Dict, Any

from .base_validator import BaseValidator, ValidationError
from .ssl_validator import SSLValidator
from .certificate_validator_helper import validate_certificate_files
from mcp_proxy_adapter.core.role_utils import RoleUtils
from ..simple_config import SimpleConfigModel


class ServerValidator(BaseValidator):
    """Validator for server configuration section."""

    def __init__(self, config_path: str | None = None):
        """Initialize server validator."""
        super().__init__(config_path)
        self.ssl_validator = SSLValidator(config_path)

    def validate(self, model: SimpleConfigModel) -> List[ValidationError]:
        """
        Validate server configuration section.
        
        Args:
            model: Configuration model
            
        Returns:
            List of validation errors for server section
        """
        errors: List[ValidationError] = []
        s = model.server
        
        # Basic field validation
        if not s.host:
            errors.append(ValidationError("server.host is required"))
        if not isinstance(s.port, int):  # type: ignore[unreachable]
            errors.append(ValidationError("server.port must be integer"))
        if s.protocol not in ("http", "https", "mtls"):
            errors.append(
                ValidationError("server.protocol must be one of: http, https, mtls")
            )
        if not s.servername:
            errors.append(ValidationError("server.servername is required"))
        
        # Protocol-specific SSL requirements
        if s.protocol in ("https", "mtls"):
            if not s.ssl:
                errors.append(
                    ValidationError("server.ssl is required for https/mtls protocols")
                )
            else:
                if s.protocol == "mtls":
                    if not s.ssl.cert:
                        errors.append(
                            ValidationError(
                                "server.ssl.cert is required for mtls protocol"
                            )
                        )
                    if not s.ssl.key:
                        errors.append(
                            ValidationError(
                                "server.ssl.key is required for mtls protocol"
                            )
                        )
                elif s.protocol == "https":
                    if s.ssl.key and not s.ssl.cert:
                        errors.append(
                            ValidationError(
                                "server.ssl.key is specified but server.ssl.cert is missing for https protocol"
                            )
                        )
                    if s.ssl.cert and not s.ssl.key:
                        errors.append(
                            ValidationError(
                                "server.ssl.cert is specified but server.ssl.key is missing for https protocol"
                            )
                        )
                
                # Validate SSL files (existence, accessibility, format)
                errors.extend(
                    self.ssl_validator.validate_ssl_files(s.ssl, "server", enabled=True)
                )
        
        # Validate certificate validity if files exist
        cert_file = s.ssl.cert if s.ssl else None
        key_file = s.ssl.key if s.ssl else None
        ca_cert_file = s.ssl.ca if s.ssl else None
        crl_file = s.ssl.crl if s.ssl else None
        
        cert_path = self._resolve_path(cert_file) if cert_file else None
        key_path = self._resolve_path(key_file) if key_file else None
        ca_cert_path = self._resolve_path(ca_cert_file) if ca_cert_file else None
        crl_path = self._resolve_path(crl_file) if crl_file else None
        
        # Validate certificate files
        if cert_path or key_path:
            cert_label = "server.ssl.cert" if s.ssl else "server.cert_file"
            key_label = "server.ssl.key" if s.ssl else "server.key_file"
            ca_label = "server.ssl.ca" if s.ssl else "server.ca_cert_file"
            crl_label = "server.ssl.crl" if s.ssl else "server.crl_file"
            
            errors.extend(
                validate_certificate_files(
                    cert_path,
                    key_path,
                    ca_cert_path,
                    crl_path,
                    cert_label,
                    key_label,
                    ca_label,
                    crl_label,
                    s.protocol,
                )
            )
        
        # Validate roles in server.rules using mcp_security_framework
        if s.rules:
            errors.extend(self._validate_server_rules(s.rules))
        
        return errors
    
    def _validate_server_rules(self, rules: Dict[str, Any]) -> List[ValidationError]:
        """Validate server.rules section using mcp_security_framework."""
        errors: List[ValidationError] = []
        
        if not isinstance(rules, dict):
            errors.append(ValidationError("server.rules must be a dictionary"))
            return errors
        
        # Validate allow section
        if "allow" in rules:
            allow = rules["allow"]
            if not isinstance(allow, list):
                errors.append(ValidationError("server.rules.allow must be a list"))
            else:
                for idx, rule_item in enumerate(allow):
                    if not isinstance(rule_item, dict):
                        errors.append(
                            ValidationError(
                                f"server.rules.allow[{idx}] must be a dictionary"
                            )
                        )
                        continue
                    
                    role = rule_item.get("role")
                    if not role:
                        errors.append(
                            ValidationError(f"server.rules.allow[{idx}].role is required")
                        )
                        continue
                    
                    if not isinstance(role, str):
                        errors.append(
                            ValidationError(
                                f"server.rules.allow[{idx}].role must be a string"
                            )
                        )
                        continue
                    
                    # Validate role using mcp_security_framework
                    try:
                        if not RoleUtils.validate_single_role(role):
                            valid_roles = RoleUtils.get_valid_roles()
                            valid_roles_str = (
                                ", ".join(valid_roles) if valid_roles else "none available"
                            )
                            errors.append(
                                ValidationError(
                                    f"server.rules.allow[{idx}].role contains unknown role '{role}'. "
                                    f"Valid roles: {valid_roles_str}"
                                )
                            )
                    except Exception as ex:
                        errors.append(
                            ValidationError(
                                f"server.rules.allow[{idx}].role validation error for '{role}': {ex}"
                            )
                        )
        
        # Validate deny section
        if "deny" in rules:
            deny = rules["deny"]
            if not isinstance(deny, list):
                errors.append(ValidationError("server.rules.deny must be a list"))
            else:
                for idx, role in enumerate(deny):
                    if not isinstance(role, str):
                        errors.append(
                            ValidationError(f"server.rules.deny[{idx}] must be a string")
                        )
                        continue
                    
                    # Validate role using mcp_security_framework
                    try:
                        if not RoleUtils.validate_single_role(role):
                            valid_roles = RoleUtils.get_valid_roles()
                            valid_roles_str = (
                                ", ".join(valid_roles) if valid_roles else "none available"
                            )
                            errors.append(
                                ValidationError(
                                    f"server.rules.deny[{idx}] contains unknown role '{role}'. "
                                    f"Valid roles: {valid_roles_str}"
                                )
                            )
                    except Exception as ex:
                        errors.append(
                            ValidationError(
                                f"server.rules.deny[{idx}] validation error for '{role}': {ex}"
                            )
                        )
        
        return errors

