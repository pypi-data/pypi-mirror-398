"""
Tests for date utilities.
"""

from datetime import datetime, timezone, timedelta
import pytest

from mcp_proxy_adapter.core.date_utils import (
    parse_certificate_expiry_date,
    calculate_days_until_expiry,
    is_certificate_expired,
    determine_expiry_status,
)


class TestParseCertificateExpiryDate:
    """Tests for parse_certificate_expiry_date function."""

    def test_parse_iso_format_with_z(self):
        """Test parsing ISO format with Z timezone."""
        expiry_date = "2025-12-31T23:59:59Z"
        dt, error = parse_certificate_expiry_date(expiry_date)
        assert error is None
        assert dt is not None
        assert isinstance(dt, datetime)

    def test_parse_iso_format_with_timezone(self):
        """Test parsing ISO format with timezone offset."""
        expiry_date = "2025-12-31T23:59:59+00:00"
        dt, error = parse_certificate_expiry_date(expiry_date)
        assert error is None
        assert dt is not None

    def test_parse_invalid_format(self):
        """Test parsing invalid date format."""
        expiry_date = "invalid date"
        dt, error = parse_certificate_expiry_date(expiry_date)
        assert dt is None
        assert error is not None
        assert "invalid" in error.lower()


class TestCalculateDaysUntilExpiry:
    """Tests for calculate_days_until_expiry function."""

    def test_future_date(self):
        """Test calculation for future date."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        days, error = calculate_days_until_expiry(future_date)
        assert error is None
        assert days is not None
        assert 29 <= days <= 31  # Allow some margin for execution time

    def test_past_date(self):
        """Test calculation for past date."""
        past_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        days, error = calculate_days_until_expiry(past_date)
        assert error is None
        assert days is not None
        assert days < 0

    def test_invalid_date(self):
        """Test calculation with invalid date."""
        days, error = calculate_days_until_expiry("invalid date")
        assert days is None
        assert error is not None


class TestIsCertificateExpired:
    """Tests for is_certificate_expired function."""

    def test_not_expired(self):
        """Test check for non-expired certificate."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        is_expired, error = is_certificate_expired(future_date)
        assert error is None
        assert is_expired is False

    def test_expired(self):
        """Test check for expired certificate."""
        past_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        is_expired, error = is_certificate_expired(past_date)
        assert error is None
        assert is_expired is True

    def test_invalid_date(self):
        """Test check with invalid date."""
        is_expired, error = is_certificate_expired("invalid date")
        assert is_expired is None
        assert error is not None


class TestDetermineExpiryStatus:
    """Tests for determine_expiry_status function."""

    def test_healthy_status(self):
        """Test determination of healthy status."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
        status, days, error = determine_expiry_status(future_date, warning_days=30, critical_days=7)
        assert error is None
        assert status == "healthy"
        assert days is not None
        assert days > 30

    def test_warning_status(self):
        """Test determination of warning status."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()
        status, days, error = determine_expiry_status(future_date, warning_days=30, critical_days=7)
        assert error is None
        assert status == "warning"
        assert days is not None
        assert 7 < days <= 30

    def test_critical_status(self):
        """Test determination of critical status."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        status, days, error = determine_expiry_status(future_date, warning_days=30, critical_days=7)
        assert error is None
        assert status == "critical"
        assert days is not None
        assert 0 < days <= 7

    def test_expired_status(self):
        """Test determination of expired status."""
        past_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        status, days, error = determine_expiry_status(past_date, warning_days=30, critical_days=7)
        assert error is None
        assert status == "expired"
        assert days is not None
        assert days < 0

    def test_invalid_date(self):
        """Test determination with invalid date."""
        status, days, error = determine_expiry_status("invalid date")
        assert status is None
        assert days is None
        assert error is not None

