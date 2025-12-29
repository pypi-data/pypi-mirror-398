"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Result class for certificate monitoring operations.
"""

from typing import Dict, List, Optional, Any


class CertMonitorResult:
    """
    Result class for certificate monitoring operations.

    Contains monitoring information and operation status.
    """

    def __init__(
        self,
        cert_path: str,
        check_type: str,
        status: str,
        expiry_date: Optional[str] = None,
        days_until_expiry: Optional[int] = None,
        health_score: Optional[int] = None,
        alerts: Optional[List[str]] = None,
        auto_renewal_status: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """
        Initialize certificate monitor result.

        Args:
            cert_path: Path to certificate file
            check_type: Type of check performed (expiry, health, alert, auto_renewal)
            status: Overall status (healthy, warning, critical, error)
            expiry_date: Certificate expiry date
            days_until_expiry: Days until certificate expires
            health_score: Health score (0-100)
            alerts: List of alert messages
            auto_renewal_status: Auto-renewal status
            error: Error message if any
        """
        self.cert_path = cert_path
        self.check_type = check_type
        self.status = status
        self.expiry_date = expiry_date
        self.days_until_expiry = days_until_expiry
        self.health_score = health_score
        self.alerts = alerts or []
        self.auto_renewal_status = auto_renewal_status
        self.error = error

