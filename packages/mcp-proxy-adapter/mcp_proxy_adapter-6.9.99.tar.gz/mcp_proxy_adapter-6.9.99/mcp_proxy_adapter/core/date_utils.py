"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Date utilities for certificate expiry date operations.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple


def parse_certificate_expiry_date(
    expiry_date: str,
) -> Tuple[Optional[datetime], Optional[str]]:
    """
    Parse certificate expiry date string to datetime.

    Args:
        expiry_date: Expiry date string (ISO format)

    Returns:
        Tuple of (datetime, error_message)
    """
    try:
        # Handle both Z and +00:00 timezone formats
        normalized_date = expiry_date.replace("Z", "+00:00")
        expiry_datetime = datetime.fromisoformat(normalized_date)
        return expiry_datetime, None
    except ValueError as e:
        return None, f"Invalid expiry date format: {str(e)}"
    except Exception as e:
        return None, f"Failed to parse expiry date: {str(e)}"


def calculate_days_until_expiry(
    expiry_date: str,
) -> Tuple[Optional[int], Optional[str]]:
    """
    Calculate days until certificate expiry.

    Args:
        expiry_date: Expiry date string (ISO format)

    Returns:
        Tuple of (days_until_expiry, error_message)
    """
    expiry_datetime, error = parse_certificate_expiry_date(expiry_date)
    if error:
        return None, error

    if expiry_datetime is None:
        return None, "Failed to parse expiry date"

    try:
        # Use timezone-aware datetime for calculation
        now = datetime.now(expiry_datetime.tzinfo if expiry_datetime.tzinfo else timezone.utc)
        if expiry_datetime.tzinfo is None:
            expiry_datetime = expiry_datetime.replace(tzinfo=timezone.utc)

        days_until_expiry = (expiry_datetime - now).days
        return days_until_expiry, None
    except Exception as e:
        return None, f"Failed to calculate days until expiry: {str(e)}"


def is_certificate_expired(expiry_date: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Check if certificate is expired.

    Args:
        expiry_date: Expiry date string (ISO format)

    Returns:
        Tuple of (is_expired, error_message)
    """
    days_until_expiry, error = calculate_days_until_expiry(expiry_date)
    if error:
        return None, error

    if days_until_expiry is None:
        return None, "Failed to calculate days until expiry"

    return days_until_expiry < 0, None


def determine_expiry_status(
    expiry_date: str,
    warning_days: int = 30,
    critical_days: int = 7,
) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Determine certificate expiry status based on thresholds.

    Args:
        expiry_date: Expiry date string (ISO format)
        warning_days: Days before expiry to start warning
        critical_days: Days before expiry for critical status

    Returns:
        Tuple of (status, days_until_expiry, error_message)
        Status can be: "expired", "critical", "warning", "healthy"
    """
    days_until_expiry, error = calculate_days_until_expiry(expiry_date)
    if error:
        return None, None, error

    if days_until_expiry is None:
        return None, None, "Failed to calculate days until expiry"

    if days_until_expiry < 0:
        return "expired", days_until_expiry, None
    elif days_until_expiry <= critical_days:
        return "critical", days_until_expiry, None
    elif days_until_expiry <= warning_days:
        return "warning", days_until_expiry, None
    else:
        return "healthy", days_until_expiry, None

