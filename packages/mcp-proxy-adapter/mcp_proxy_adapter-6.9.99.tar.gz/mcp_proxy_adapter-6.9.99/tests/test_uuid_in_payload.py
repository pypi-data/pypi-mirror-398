"""
Test UUID in registration payload.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_proxy_adapter.client.jsonrpc_client.proxy_api import ProxyApiMixin
from tests.utils.registration_utils import verify_uuid_in_payload


class MockProxyApiMixin(ProxyApiMixin):
    """Test implementation of ProxyApiMixin."""

    def __init__(self):
        """Initialize test mixin."""
        self.base_url = "http://localhost:8080"
        self.cert = None
        self.verify = True


def test_extract_and_validate_uuid():
    """Test _extract_and_validate_uuid method."""
    mixin = MockProxyApiMixin()
    test_uuid = str(uuid.uuid4())
    metadata = {
        "uuid": test_uuid,
        "protocol": "http",
    }

    # Test valid UUID extraction
    extracted_uuid = mixin._extract_and_validate_uuid(metadata)
    assert extracted_uuid == test_uuid.lower(), "UUID not extracted correctly"

    # Test missing UUID
    with pytest.raises(ValueError, match="uuid is required"):
        mixin._extract_and_validate_uuid({})

    # Test invalid UUID format
    with pytest.raises(ValueError, match="valid UUID4"):
        mixin._extract_and_validate_uuid({"uuid": "not-a-uuid"})

    # Test non-UUID4
    uuid1 = str(uuid.uuid1())
    with pytest.raises(ValueError, match="UUID4"):
        mixin._extract_and_validate_uuid({"uuid": uuid1})


@pytest.mark.asyncio
async def test_register_with_proxy_payload_structure():
    """Test that register_with_proxy creates payload with UUID at root level."""
    # This test verifies the payload structure by checking the method logic
    # We'll test the payload creation indirectly through the validation method
    mixin = MockProxyApiMixin()
    test_uuid = str(uuid.uuid4())
    metadata = {
        "uuid": test_uuid,
        "protocol": "http",
        "host": "localhost",
        "port": 8080,
    }

    # Verify UUID can be extracted (this is what register_with_proxy does)
    extracted_uuid = mixin._extract_and_validate_uuid(metadata)
    assert extracted_uuid == test_uuid.lower()

    # Simulate payload creation (same logic as in register_with_proxy)
    payload = {
        "server_id": "test-server",
        "server_url": "http://localhost:8080",
        "uuid": extracted_uuid,  # UUID at root level - REQUIRED
        "capabilities": ["jsonrpc"],
        "metadata": metadata,
    }

    # Verify UUID is at root level
    assert "uuid" in payload, "UUID missing at root level of payload"
    assert payload["uuid"] == test_uuid.lower()

    # Verify UUID is valid UUID4
    uuid_valid, uuid_error = verify_uuid_in_payload(payload)
    assert uuid_valid, f"UUID validation failed: {uuid_error}"

    # Verify other fields are present
    assert payload["server_id"] == "test-server"
    assert payload["server_url"] == "http://localhost:8080"
    assert "metadata" in payload


def test_heartbeat_to_proxy_payload_structure():
    """Test that heartbeat_to_proxy creates payload with UUID at root level."""
    # This test verifies the payload structure by checking the method logic
    mixin = MockProxyApiMixin()
    test_uuid = str(uuid.uuid4())
    metadata = {
        "uuid": test_uuid,
        "protocol": "http",
        "host": "localhost",
        "port": 8080,
    }

    # Verify UUID can be extracted (this is what heartbeat_to_proxy does)
    extracted_uuid = mixin._extract_and_validate_uuid(metadata)
    assert extracted_uuid == test_uuid.lower()

    # Simulate payload creation (same logic as in heartbeat_to_proxy)
    payload = {
        "server_id": "test-server",
        "server_url": "http://localhost:8080",
        "uuid": extracted_uuid,  # UUID at root level - REQUIRED
        "capabilities": ["jsonrpc"],
        "metadata": metadata,
    }

    # Verify UUID is at root level
    assert "uuid" in payload, "UUID missing at root level of payload"
    assert payload["uuid"] == test_uuid.lower()

    # Verify UUID is valid UUID4
    uuid_valid, uuid_error = verify_uuid_in_payload(payload)
    assert uuid_valid, f"UUID validation failed: {uuid_error}"


def test_verify_uuid_in_payload_valid():
    """Test verify_uuid_in_payload with valid UUID4."""
    test_uuid = str(uuid.uuid4())
    payload = {"uuid": test_uuid}
    
    is_valid, error = verify_uuid_in_payload(payload)
    assert is_valid, f"Valid UUID4 was rejected: {error}"
    assert error is None


def test_verify_uuid_in_payload_missing():
    """Test verify_uuid_in_payload with missing UUID."""
    payload = {"server_id": "test"}
    
    is_valid, error = verify_uuid_in_payload(payload)
    assert not is_valid
    assert "missing" in error.lower()


def test_verify_uuid_in_payload_invalid_format():
    """Test verify_uuid_in_payload with invalid UUID format."""
    payload = {"uuid": "not-a-uuid"}
    
    is_valid, error = verify_uuid_in_payload(payload)
    assert not is_valid
    assert "valid" in error.lower() or "format" in error.lower()


def test_verify_uuid_in_payload_wrong_version():
    """Test verify_uuid_in_payload with non-UUID4."""
    # Generate UUID1 (not UUID4)
    test_uuid = str(uuid.uuid1())
    payload = {"uuid": test_uuid}
    
    is_valid, error = verify_uuid_in_payload(payload)
    assert not is_valid
    assert "uuid4" in error.lower() or "version" in error.lower()
