"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Result class for certificate operations.
"""

from typing import Dict, List, Optional, Any


class CertificateResult:
    """
    Result class for certificate operations.

    Contains certificate information and operation status.
    """

    def __init__(
        self,
        cert_path: str,
        cert_type: str,
        common_name: str,
        roles: Optional[List[str]] = None,
        expiry_date: Optional[str] = None,
        serial_number: Optional[str] = None,
        status: str = "valid",
        error: Optional[str] = None,
    ):
        """
        Initialize certificate result.

        Args:
            cert_path: Path to certificate file
            cert_type: Type of certificate (CA, server, client)
            common_name: Common name of the certificate
            roles: List of roles assigned to certificate
            expiry_date: Certificate expiry date
            serial_number: Certificate serial number
            status: Certificate status (valid, expired, revoked, error)
            error: Error message if any
        """
        self.cert_path = cert_path
        self.cert_type = cert_type
        self.common_name = common_name
        self.roles = roles or []
        self.expiry_date = expiry_date
        self.serial_number = serial_number
        self.status = status
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format.

        Returns:
            Dictionary representation
        """
        return {
            "cert_path": self.cert_path,
            "cert_type": self.cert_type,
            "common_name": self.common_name,
            "roles": self.roles,
            "expiry_date": self.expiry_date,
            "serial_number": self.serial_number,
            "status": self.status,
            "error": self.error,
        }

