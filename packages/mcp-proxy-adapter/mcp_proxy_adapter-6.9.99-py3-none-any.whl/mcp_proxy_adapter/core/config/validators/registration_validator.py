"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Registration configuration section validator.
"""

from __future__ import annotations

from typing import List
import uuid

from .base_validator import BaseValidator, ValidationError
from .ssl_validator import SSLValidator
from .certificate_validator_helper import validate_certificate_files
from ..simple_config import SimpleConfigModel


class RegistrationValidator(BaseValidator):
    """Validator for registration configuration section."""

    def __init__(self, config_path: str | None = None):
        """Initialize registration validator."""
        super().__init__(config_path)
        self.ssl_validator = SSLValidator(config_path)

    def validate(self, model: SimpleConfigModel) -> List[ValidationError]:
        """
        Validate registration configuration (for registering with proxy server).

        Args:
            model: Configuration model

        Returns:
            List of validation errors for registration section
        """
        errors: List[ValidationError] = []
        r = model.registration

        if r.enabled:
            if r.protocol not in ("http", "https", "mtls"):
                errors.append(
                    ValidationError(
                        "registration.protocol must be one of: http, https, mtls"
                    )
                )

            # Validate server_id if provided
            if r.server_id is not None:
                if not isinstance(r.server_id, str):
                    errors.append(
                        ValidationError("registration.server_id must be a string")
                    )
                else:
                    if not r.server_id.strip():
                        errors.append(
                            ValidationError("registration.server_id cannot be empty")
                        )

            # Validate instance_uuid (required when enabled=True, must be UUID4)
            if r.instance_uuid is None:
                errors.append(
                    ValidationError(
                        "registration.instance_uuid is required when registration.enabled=true"
                    )
                )
            else:
                if not isinstance(r.instance_uuid, str):
                    errors.append(
                        ValidationError("registration.instance_uuid must be a string")
                    )
                else:
                    if not r.instance_uuid.strip():
                        errors.append(
                            ValidationError(
                                "registration.instance_uuid cannot be empty"
                            )
                        )
                    else:
                        # Validate UUID4 format
                        try:
                            uuid_obj = uuid.UUID(r.instance_uuid)
                            if uuid_obj.version != 4:
                                errors.append(
                                    ValidationError(
                                        f"registration.instance_uuid must be a valid UUID4, got UUID version {uuid_obj.version}"
                                    )
                                )
                        except ValueError as e:
                            errors.append(
                                ValidationError(
                                    f"registration.instance_uuid must be a valid UUID4 format: {str(e)}"
                                )
                            )

            # Protocol-specific SSL requirements
            if r.protocol in ("https", "mtls"):
                if not r.ssl:
                    errors.append(
                        ValidationError(
                            "registration.ssl is required for https/mtls protocols when enabled"
                        )
                    )
                else:
                    if r.protocol == "mtls":
                        if not r.ssl.cert:
                            errors.append(
                                ValidationError(
                                    "registration.ssl.cert is required for mtls protocol when enabled"
                                )
                            )
                        if not r.ssl.key:
                            errors.append(
                                ValidationError(
                                    "registration.ssl.key is required for mtls protocol when enabled"
                                )
                            )
                        if not r.ssl.ca:
                            errors.append(
                                ValidationError(
                                    "registration.ssl.ca is required for mtls protocol when enabled"
                                )
                            )
                    elif r.protocol == "https":
                        if r.ssl.key and not r.ssl.cert:
                            errors.append(
                                ValidationError(
                                    "registration.ssl.key is specified but registration.ssl.cert is missing for https protocol"
                                )
                            )
                        if r.ssl.cert and not r.ssl.key:
                            errors.append(
                                ValidationError(
                                    "registration.ssl.cert is specified but registration.ssl.key is missing for https protocol"
                                )
                            )

                    # Validate SSL files (existence, accessibility, format)
                    errors.extend(
                        self.ssl_validator.validate_ssl_files(
                            r.ssl, "registration", enabled=r.enabled
                        )
                    )

            # Validate certificate validity if files exist
            reg_cert_file = r.ssl.cert if r.ssl else None
            reg_key_file = r.ssl.key if r.ssl else None
            reg_ca_cert_file = r.ssl.ca if r.ssl else None
            reg_crl_file = r.ssl.crl if r.ssl else None

            reg_cert_path = self._resolve_path(reg_cert_file) if reg_cert_file else None
            reg_key_path = self._resolve_path(reg_key_file) if reg_key_file else None
            reg_ca_cert_path = (
                self._resolve_path(reg_ca_cert_file) if reg_ca_cert_file else None
            )
            reg_crl_path = self._resolve_path(reg_crl_file) if reg_crl_file else None

            if reg_cert_path or reg_key_path:
                errors.extend(
                    validate_certificate_files(
                        reg_cert_path,
                        reg_key_path,
                        reg_ca_cert_path,
                        reg_crl_path,
                        "registration.ssl.cert",
                        "registration.ssl.key",
                        "registration.ssl.ca",
                        "registration.ssl.crl",
                        r.protocol,
                    )
                )

            # Validate heartbeat_interval (required if registration is enabled)
            if not isinstance(r.heartbeat_interval, int) or r.heartbeat_interval <= 0:
                errors.append(
                    ValidationError(
                        "registration.heartbeat_interval must be a positive integer when registration.enabled=true"
                    )
                )

            # Heartbeat - validate URL (required)
            if not r.heartbeat.url:
                errors.append(
                    ValidationError(
                        "registration.heartbeat.url is required when registration.enabled=true"
                    )
                )
            elif not isinstance(r.heartbeat.url, str) or not r.heartbeat.url.strip():
                errors.append(
                    ValidationError(
                        "registration.heartbeat.url must be a non-empty string"
                    )
                )
            else:
                # Validate protocol consistency: URL scheme must match protocol
                if r.protocol in ("https", "mtls") and not r.heartbeat.url.startswith(
                    "https://"
                ):
                    errors.append(
                        ValidationError(
                            f"registration.heartbeat.url must use https:// scheme when registration.protocol is {r.protocol}"
                        )
                    )
                elif r.protocol == "http" and not r.heartbeat.url.startswith("http://"):
                    errors.append(
                        ValidationError(
                            "registration.heartbeat.url must use http:// scheme when registration.protocol is http"
                        )
                    )

            if not isinstance(r.heartbeat.interval, int) or r.heartbeat.interval <= 0:
                errors.append(
                    ValidationError(
                        "registration.heartbeat.interval must be positive integer"
                    )
                )

            # Registration URLs - validate URLs (required)
            if not r.register_url:
                errors.append(
                    ValidationError(
                        "registration.register_url is required when registration.enabled=true"
                    )
                )
            elif not isinstance(r.register_url, str) or not r.register_url.strip():
                errors.append(
                    ValidationError(
                        "registration.register_url must be a non-empty string"
                    )
                )
            else:
                # Validate protocol consistency: URL scheme must match protocol
                if r.protocol in ("https", "mtls") and not r.register_url.startswith(
                    "https://"
                ):
                    errors.append(
                        ValidationError(
                            f"registration.register_url must use https:// scheme when registration.protocol is {r.protocol}"
                        )
                    )
                elif r.protocol == "http" and not r.register_url.startswith("http://"):
                    errors.append(
                        ValidationError(
                            "registration.register_url must use http:// scheme when registration.protocol is http"
                        )
                    )

            if not r.unregister_url:
                errors.append(
                    ValidationError(
                        "registration.unregister_url is required when registration.enabled=true"
                    )
                )
            elif not isinstance(r.unregister_url, str) or not r.unregister_url.strip():
                errors.append(
                    ValidationError(
                        "registration.unregister_url must be a non-empty string"
                    )
                )
            else:
                # Validate protocol consistency: URL scheme must match protocol
                if r.protocol in ("https", "mtls") and not r.unregister_url.startswith(
                    "https://"
                ):
                    errors.append(
                        ValidationError(
                            f"registration.unregister_url must use https:// scheme when registration.protocol is {r.protocol}"
                        )
                    )
                elif r.protocol == "http" and not r.unregister_url.startswith(
                    "http://"
                ):
                    errors.append(
                        ValidationError(
                            "registration.unregister_url must use http:// scheme when registration.protocol is http"
                        )
                    )

        return errors
