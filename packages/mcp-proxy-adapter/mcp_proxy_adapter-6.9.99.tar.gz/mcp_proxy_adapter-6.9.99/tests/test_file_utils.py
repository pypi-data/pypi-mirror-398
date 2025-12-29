"""
Tests for file utilities.
"""

import os
import tempfile
from pathlib import Path
import pytest

from mcp_proxy_adapter.core.file_utils import (
    validate_file_exists,
    validate_file_not_empty,
    ensure_directory_exists,
)


class TestValidateFileExists:
    """Tests for validate_file_exists function."""

    def test_file_exists(self):
        """Test validation of existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            exists, error = validate_file_exists(temp_path)
            assert exists is True
            assert error is None
        finally:
            os.unlink(temp_path)

    def test_file_not_exists(self):
        """Test validation of non-existing file."""
        exists, error = validate_file_exists("/nonexistent/file.txt")
        assert exists is False
        assert error is not None
        assert "not found" in error.message.lower()

    def test_file_not_exists_no_error(self):
        """Test validation without error return."""
        exists, error = validate_file_exists("/nonexistent/file.txt", return_error=False)
        assert exists is False
        assert error is None

    def test_directory_not_file(self):
        """Test that directory is not considered a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exists, error = validate_file_exists(temp_dir)
            assert exists is False
            assert error is not None
            assert "not a file" in error.message.lower()

    def test_custom_file_type(self):
        """Test with custom file type."""
        exists, error = validate_file_exists("/nonexistent/cert.pem", file_type="certificate")
        assert exists is False
        assert error is not None
        assert "certificate" in error.message.lower()


class TestValidateFileNotEmpty:
    """Tests for validate_file_not_empty function."""

    def test_file_not_empty(self):
        """Test validation of non-empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            is_valid, error = validate_file_not_empty(temp_path)
            assert is_valid is True
            assert error is None
        finally:
            os.unlink(temp_path)

    def test_file_empty(self):
        """Test validation of empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            is_valid, error = validate_file_not_empty(temp_path)
            assert is_valid is False
            assert error is not None
            assert "empty" in error.message.lower()
        finally:
            os.unlink(temp_path)

    def test_file_not_exists(self):
        """Test validation of non-existing file."""
        is_valid, error = validate_file_not_empty("/nonexistent/file.txt")
        assert is_valid is False
        assert error is not None


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists function."""

    def test_directory_exists(self):
        """Test that existing directory is handled correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            success, error = ensure_directory_exists(temp_dir)
            assert success is True
            assert error is None

    def test_directory_created(self):
        """Test that non-existing directory is created."""
        with tempfile.TemporaryDirectory() as base_dir:
            new_dir = os.path.join(base_dir, "new", "nested", "directory")
            success, error = ensure_directory_exists(new_dir)
            assert success is True
            assert error is None
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)

