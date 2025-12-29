"""
Tests for JSON utilities.
"""

import json
import tempfile
import os
import pytest

from mcp_proxy_adapter.core.json_utils import (
    save_json_file,
    load_json_file,
    parse_json_string,
)


class TestSaveJsonFile:
    """Tests for save_json_file function."""

    def test_save_json_file(self):
        """Test saving JSON file."""
        data = {"key": "value", "number": 42}
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            success, error = save_json_file(data, temp_path)
            assert success is True
            assert error is None

            # Verify file was created and contains correct data
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data == data
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_json_file_creates_directory(self):
        """Test that save_json_file creates parent directory."""
        data = {"key": "value"}
        with tempfile.TemporaryDirectory() as base_dir:
            nested_path = os.path.join(base_dir, "nested", "dir", "file.json")
            success, error = save_json_file(data, nested_path)
            assert success is True
            assert error is None
            assert os.path.exists(nested_path)

    def test_save_json_file_custom_indent(self):
        """Test saving JSON file with custom indent."""
        data = {"key": "value"}
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            success, error = save_json_file(data, temp_path, indent=4)
            assert success is True
            assert error is None

            # Verify indent was used
            with open(temp_path, 'r') as f:
                content = f.read()
            assert content.count('\n') > 0  # Should have newlines with indent
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestLoadJsonFile:
    """Tests for load_json_file function."""

    def test_load_json_file(self):
        """Test loading JSON file."""
        data = {"key": "value", "number": 42}
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            loaded_data, error = load_json_file(temp_path)
            assert error is None
            assert loaded_data == data
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        loaded_data, error = load_json_file("/nonexistent/file.json")
        assert loaded_data is None
        assert error is not None
        assert "not found" in error.message.lower()

    def test_load_invalid_json(self):
        """Test loading file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("invalid json content {")
            temp_path = f.name

        try:
            loaded_data, error = load_json_file(temp_path)
            assert loaded_data is None
            assert error is not None
            assert "invalid json" in error.message.lower()
        finally:
            os.unlink(temp_path)


class TestParseJsonString:
    """Tests for parse_json_string function."""

    def test_parse_valid_json_string(self):
        """Test parsing valid JSON string."""
        json_string = '{"key": "value", "number": 42}'
        data, error = parse_json_string(json_string)
        assert error is None
        assert data == {"key": "value", "number": 42}

    def test_parse_invalid_json_string(self):
        """Test parsing invalid JSON string."""
        json_string = '{"key": "value"'
        data, error = parse_json_string(json_string)
        assert data is None
        assert error is not None
        assert "invalid json" in error.message.lower()

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        data, error = parse_json_string("")
        assert data is None
        assert error is not None

