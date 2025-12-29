"""
Tests for validation utilities.
"""

import pytest

from mcp_proxy_adapter.core.validation_utils import (
    validate_non_empty_string,
    validate_positive_integer,
    validate_non_negative_integer,
    validate_file_path,
    validate_list_not_empty,
    validate_dict_not_empty,
    validate_key_size,
    validate_days_comparison,
)


class TestValidateNonEmptyString:
    """Tests for validate_non_empty_string function."""

    def test_valid_string(self):
        """Test validation of valid string."""
        error = validate_non_empty_string("test")
        assert error is None

    def test_empty_string(self):
        """Test validation of empty string."""
        error = validate_non_empty_string("")
        assert error is not None
        assert "cannot be empty" in error.message

    def test_whitespace_string(self):
        """Test validation of whitespace-only string."""
        error = validate_non_empty_string("   ")
        assert error is not None

    def test_none_value(self):
        """Test validation of None value."""
        error = validate_non_empty_string(None)
        assert error is not None

    def test_custom_field_name(self):
        """Test with custom field name."""
        error = validate_non_empty_string("", field_name="Common name")
        assert error is not None
        assert "Common name" in error.message


class TestValidatePositiveInteger:
    """Tests for validate_positive_integer function."""

    def test_valid_positive_integer(self):
        """Test validation of valid positive integer."""
        error = validate_positive_integer(5)
        assert error is None

    def test_zero(self):
        """Test validation of zero."""
        error = validate_positive_integer(0)
        assert error is not None

    def test_negative_integer(self):
        """Test validation of negative integer."""
        error = validate_positive_integer(-1)
        assert error is not None

    def test_not_integer(self):
        """Test validation of non-integer value."""
        error = validate_positive_integer("5")
        assert error is not None

    def test_custom_field_name(self):
        """Test with custom field name."""
        error = validate_positive_integer(0, field_name="Validity days")
        assert error is not None
        assert "Validity days" in error.message


class TestValidateNonNegativeInteger:
    """Tests for validate_non_negative_integer function."""

    def test_valid_positive_integer(self):
        """Test validation of valid positive integer."""
        error = validate_non_negative_integer(5)
        assert error is None

    def test_zero(self):
        """Test validation of zero."""
        error = validate_non_negative_integer(0)
        assert error is None

    def test_negative_integer(self):
        """Test validation of negative integer."""
        error = validate_non_negative_integer(-1)
        assert error is not None


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_path(self):
        """Test validation of valid path."""
        error = validate_file_path("/path/to/file.txt")
        assert error is None

    def test_empty_path(self):
        """Test validation of empty path."""
        error = validate_file_path("")
        assert error is not None

    def test_none_path(self):
        """Test validation of None path."""
        error = validate_file_path(None)
        assert error is not None

    def test_custom_field_name(self):
        """Test with custom field name."""
        error = validate_file_path(None, field_name="CA certificate path")
        assert error is not None
        assert "CA certificate path" in error.message


class TestValidateListNotEmpty:
    """Tests for validate_list_not_empty function."""

    def test_valid_list(self):
        """Test validation of valid non-empty list."""
        error = validate_list_not_empty([1, 2, 3])
        assert error is None

    def test_empty_list(self):
        """Test validation of empty list."""
        error = validate_list_not_empty([])
        assert error is not None

    def test_none_list(self):
        """Test validation of None list."""
        error = validate_list_not_empty(None)
        assert error is not None

    def test_not_list(self):
        """Test validation of non-list value."""
        error = validate_list_not_empty("not a list")
        assert error is not None


class TestValidateDictNotEmpty:
    """Tests for validate_dict_not_empty function."""

    def test_valid_dict(self):
        """Test validation of valid non-empty dict."""
        error = validate_dict_not_empty({"key": "value"})
        assert error is None

    def test_empty_dict(self):
        """Test validation of empty dict."""
        error = validate_dict_not_empty({})
        assert error is not None

    def test_none_dict(self):
        """Test validation of None dict."""
        error = validate_dict_not_empty(None)
        assert error is not None


class TestValidateKeySize:
    """Tests for validate_key_size function."""

    def test_valid_key_size(self):
        """Test validation of valid key size."""
        error = validate_key_size(2048)
        assert error is None

    def test_minimum_key_size(self):
        """Test validation of minimum key size."""
        error = validate_key_size(1024)
        assert error is None

    def test_too_small_key_size(self):
        """Test validation of too small key size."""
        error = validate_key_size(512)
        assert error is not None
        assert "at least 1024" in error.message

    def test_too_large_key_size(self):
        """Test validation of too large key size."""
        error = validate_key_size(16384)
        assert error is not None
        assert "not exceed 8192" in error.message


class TestValidateDaysComparison:
    """Tests for validate_days_comparison function."""

    def test_valid_comparison(self):
        """Test validation of valid days comparison."""
        error = validate_days_comparison(30, 7)
        assert error is None

    def test_equal_days(self):
        """Test validation when days are equal."""
        error = validate_days_comparison(30, 30)
        assert error is not None

    def test_warning_less_than_critical(self):
        """Test validation when warning is less than critical."""
        error = validate_days_comparison(7, 30)
        assert error is not None

