#!/usr/bin/env python3
"""
Test UUID transmission in proxy registration
"""
import json
import uuid
import asyncio
from unittest.mock import AsyncMock, patch

# Skip this file in pytest runs - it's a standalone script
import pytest
pytest.skip("Standalone scenario", allow_module_level=True)

from mcp_proxy_adapter.core.proxy_registration import ProxyRegistrationManager

async def test_uuid_transmission():
    """Test that UUID is correctly transmitted in registration"""
    print("🔍 Testing UUID transmission in proxy registration...")
    
    # Test config with UUID at root level
    config_with_root_uuid = {
        "uuid": "123e4567-e89b-42d3-8a56-426614174000",  # Root level UUID
        "proxy_registration": {
            "enabled": True,
            "proxy_url": "http://localhost:3005",
            "server_id": "test-server",
            "server_name": "Test Server",
            "description": "Test server for UUID transmission",
            "version": "1.0.0",
            "heartbeat": {
                "enabled": True,
                "interval": 30,
                "timeout": 10,
                "retry_attempts": 3,
                "retry_delay": 5
            }
        }
    }
    
    # Test config with UUID in proxy_registration section
    config_with_section_uuid = {
        "proxy_registration": {
            "enabled": True,
            "proxy_url": "http://localhost:3005",
            "server_id": "test-server-2",
            "server_name": "Test Server 2",
            "description": "Test server with UUID in section",
            "version": "1.0.0",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",  # Section UUID
            "heartbeat": {
                "enabled": True,
                "interval": 30,
                "timeout": 10,
                "retry_attempts": 3,
                "retry_delay": 5
            }
        }
    }
    
    # Test config without UUID (should fail)
    config_without_uuid = {
        "proxy_registration": {
            "enabled": True,
            "proxy_url": "http://localhost:3005",
            "server_id": "test-server-3",
            "server_name": "Test Server 3",
            "description": "Test server without UUID",
            "version": "1.0.0",
            "heartbeat": {
                "enabled": True,
                "interval": 30,
                "timeout": 10,
                "retry_attempts": 3,
                "retry_delay": 5
            }
        }
    }
    
    # Test 1: UUID at root level
    print("\n1️⃣ Testing UUID at root level...")
    try:
        manager = ProxyRegistrationManager(config_with_root_uuid)
        assert manager.uuid == "123e4567-e89b-42d3-8a56-426614174000"
        print("✅ UUID correctly read from root level")
    except Exception as e:
        print(f"❌ Failed to read UUID from root level: {e}")
        return False
    
    # Test 2: UUID in proxy_registration section
    print("\n2️⃣ Testing UUID in proxy_registration section...")
    try:
        manager = ProxyRegistrationManager(config_with_section_uuid)
        assert manager.uuid == "550e8400-e29b-41d4-a716-446655440000"
        print("✅ UUID correctly read from proxy_registration section")
    except Exception as e:
        print(f"❌ Failed to read UUID from section: {e}")
        return False
    
    # Test 3: No UUID (should fail)
    print("\n3️⃣ Testing missing UUID (should fail)...")
    try:
        manager = ProxyRegistrationManager(config_without_uuid)
        print("❌ Should have failed with missing UUID")
        return False
    except ValueError as e:
        if "uuid is required" in str(e):
            print("✅ Correctly failed with missing UUID")
        else:
            print(f"❌ Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test 4: UUID transmission in registration data
    print("\n4️⃣ Testing UUID transmission in registration data...")
    try:
        manager = ProxyRegistrationManager(config_with_root_uuid)
        manager.set_server_url("http://localhost:8080")
        
        # Mock the registration request to capture the data
        with patch.object(manager, '_make_secure_registration_request') as mock_request:
            mock_request.return_value = (True, {"server_key": "test-key"})
            
            # Call register_server
            result = await manager.register_server()
            
            # Check that the request was made with UUID
            assert mock_request.called
            call_args = mock_request.call_args[0][0]  # First argument (registration_data)
            assert call_args["uuid"] == "123e4567-e89b-42d3-8a56-426614174000"
            print("✅ UUID correctly transmitted in registration data")
            
    except Exception as e:
        print(f"❌ Failed to test UUID transmission: {e}")
        return False
    
    print("\n✅ All UUID transmission tests passed!")
    return True

async def main():
    """Run all tests"""
    print("🚀 Testing UUID transmission in proxy registration...")
    
    success = await test_uuid_transmission()
    
    if success:
        print("\n🎉 All tests passed! UUID transmission is working correctly.")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the UUID transmission logic.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
