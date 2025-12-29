"""
Tests for CLI Validators

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
from mcp_proxy_adapter.cli.validators import (
    ParameterValidator,
    ConfigurationValidator,
    ValidationError
)


class TestParameterValidator:
    """Test cases for ParameterValidator."""
    
    def test_validate_protocol_valid(self):
        """Test validating valid protocols."""
        assert ParameterValidator.validate_protocol('http') is True
        assert ParameterValidator.validate_protocol('https') is True
        assert ParameterValidator.validate_protocol('mtls') is True
    
    def test_validate_protocol_invalid(self):
        """Test validating invalid protocols."""
        with pytest.raises(ValidationError, match="Invalid protocol 'invalid'"):
            ParameterValidator.validate_protocol('invalid')
    
    def test_validate_token_with_protocol_http(self):
        """Test validating token with HTTP protocol."""
        assert ParameterValidator.validate_token_with_protocol(True, 'http') is True
        assert ParameterValidator.validate_token_with_protocol(False, 'http') is True
    
    def test_validate_token_with_protocol_https(self):
        """Test validating token with HTTPS protocol."""
        assert ParameterValidator.validate_token_with_protocol(True, 'https') is True
        assert ParameterValidator.validate_token_with_protocol(False, 'https') is True
    
    def test_validate_token_with_protocol_mtls(self):
        """Test validating token with mTLS protocol."""
        assert ParameterValidator.validate_token_with_protocol(False, 'mtls') is True
        
        with pytest.raises(ValidationError, match="Token authentication is not supported with mTLS protocol"):
            ParameterValidator.validate_token_with_protocol(True, 'mtls')
    
    def test_validate_roles_with_auth_http_token(self):
        """Test validating roles with HTTP and token."""
        assert ParameterValidator.validate_roles_with_auth(True, True, 'http') is True
        assert ParameterValidator.validate_roles_with_auth(False, True, 'http') is True
    
    def test_validate_roles_with_auth_http_no_token(self):
        """Test validating roles with HTTP without token."""
        assert ParameterValidator.validate_roles_with_auth(False, False, 'http') is True
        
        with pytest.raises(ValidationError, match="Roles require token authentication for http protocol"):
            ParameterValidator.validate_roles_with_auth(True, False, 'http')
    
    def test_validate_roles_with_auth_mtls(self):
        """Test validating roles with mTLS."""
        assert ParameterValidator.validate_roles_with_auth(True, False, 'mtls') is True
        assert ParameterValidator.validate_roles_with_auth(False, False, 'mtls') is True
    
    def test_validate_port_valid(self):
        """Test validating valid ports."""
        assert ParameterValidator.validate_port(1) is True
        assert ParameterValidator.validate_port(8080) is True
        assert ParameterValidator.validate_port(65535) is True
    
    def test_validate_port_invalid(self):
        """Test validating invalid ports."""
        with pytest.raises(ValidationError, match="Invalid port '0'"):
            ParameterValidator.validate_port(0)
        
        with pytest.raises(ValidationError, match="Invalid port '65536'"):
            ParameterValidator.validate_port(65536)
        
        with pytest.raises(ValidationError, match="Invalid port 'invalid'"):
            ParameterValidator.validate_port('invalid')
    
    def test_validate_host_valid(self):
        """Test validating valid hosts."""
        assert ParameterValidator.validate_host('127.0.0.1') is True
        assert ParameterValidator.validate_host('localhost') is True
        assert ParameterValidator.validate_host('0.0.0.0') is True
    
    def test_validate_host_invalid(self):
        """Test validating invalid hosts."""
        with pytest.raises(ValidationError, match="Host must be a non-empty string"):
            ParameterValidator.validate_host('')
        
        with pytest.raises(ValidationError, match="Host must be a non-empty string"):
            ParameterValidator.validate_host(None)
    
    def test_validate_url_valid(self):
        """Test validating valid URLs."""
        assert ParameterValidator.validate_url('http://localhost:3005') is True
        assert ParameterValidator.validate_url('https://example.com') is True
    
    def test_validate_url_invalid(self):
        """Test validating invalid URLs."""
        with pytest.raises(ValidationError, match="URL must be a non-empty string"):
            ParameterValidator.validate_url('')
        
        with pytest.raises(ValidationError, match="URL must start with 'http://' or 'https://'"):
            ParameterValidator.validate_url('ftp://example.com')
    
    def test_validate_server_id_valid(self):
        """Test validating valid server IDs."""
        assert ParameterValidator.validate_server_id('server-001') is True
        assert ParameterValidator.validate_server_id('my_server') is True
        assert ParameterValidator.validate_server_id('test-123') is True
    
    def test_validate_server_id_invalid(self):
        """Test validating invalid server IDs."""
        with pytest.raises(ValidationError, match="Server ID must be a non-empty string"):
            ParameterValidator.validate_server_id('')
        
        with pytest.raises(ValidationError, match="Server ID must contain only alphanumeric characters"):
            ParameterValidator.validate_server_id('server@001')


class TestConfigurationValidator:
    """Test cases for ConfigurationValidator."""
    
    def test_validate_generate_parameters_valid(self):
        """Test validating valid generate parameters."""
        args = {
            'protocol': 'http',
            'token': True,
            'roles': True,
            'host': '127.0.0.1',
            'port': 8080,
            'cert_dir': './certs',
            'key_dir': './keys',
            'output_dir': './configs'
        }
        
        errors = ConfigurationValidator.validate_generate_parameters(args)
        assert errors == []
    
    def test_validate_generate_parameters_invalid_protocol(self):
        """Test validating generate parameters with invalid protocol."""
        args = {
            'protocol': 'invalid',
            'token': True,
            'roles': True,
            'host': '127.0.0.1',
            'port': 8080
        }
        
        errors = ConfigurationValidator.validate_generate_parameters(args)
        assert len(errors) > 0
        assert any('Invalid protocol' in error for error in errors)
    
    def test_validate_generate_parameters_mtls_with_token(self):
        """Test validating generate parameters with mTLS and token."""
        args = {
            'protocol': 'mtls',
            'token': True,
            'roles': True,
            'host': '127.0.0.1',
            'port': 8080
        }
        
        errors = ConfigurationValidator.validate_generate_parameters(args)
        assert len(errors) > 0
        assert any('Token authentication is not supported with mTLS protocol' in error for error in errors)
    
    def test_validate_generate_parameters_roles_without_token(self):
        """Test validating generate parameters with roles but no token."""
        args = {
            'protocol': 'http',
            'token': False,
            'roles': True,
            'host': '127.0.0.1',
            'port': 8080
        }
        
        errors = ConfigurationValidator.validate_generate_parameters(args)
        assert len(errors) > 0
        assert any('Roles require token authentication for http protocol' in error for error in errors)
    
    def test_validate_sets_parameters_http_valid(self):
        """Test validating valid HTTP set parameters."""
        args = {
            'token': True,
            'roles': True,
            'host': '127.0.0.1',
            'port': 8080
        }
        
        errors = ConfigurationValidator.validate_sets_parameters('http', args)
        assert errors == []
    
    def test_validate_sets_parameters_http_roles_without_token(self):
        """Test validating HTTP set parameters with roles but no token."""
        args = {
            'token': False,
            'roles': True,
            'host': '127.0.0.1',
            'port': 8080
        }
        
        errors = ConfigurationValidator.validate_sets_parameters('http', args)
        assert len(errors) > 0
        assert any('Roles require token authentication for HTTP set' in error for error in errors)
    
    def test_validate_sets_parameters_mtls_with_token(self):
        """Test validating mTLS set parameters with token."""
        args = {
            'token': True,
            'roles': True,
            'host': '127.0.0.1',
            'port': 8080
        }
        
        errors = ConfigurationValidator.validate_sets_parameters('mtls', args)
        assert len(errors) > 0
        assert any('Token authentication is not supported with mTLS set' in error for error in errors)
    
    def test_validate_testconfig_parameters_valid(self):
        """Test validating valid testconfig parameters."""
        args = {
            'config': 'config.json'
        }
        
        errors = ConfigurationValidator.validate_testconfig_parameters(args)
        assert errors == []
    
    def test_validate_testconfig_parameters_missing_config(self):
        """Test validating testconfig parameters without config file."""
        args = {}
        
        errors = ConfigurationValidator.validate_testconfig_parameters(args)
        assert len(errors) > 0
        assert any('Configuration file is required' in error for error in errors)
    
    def test_validate_server_parameters_valid(self):
        """Test validating valid server parameters."""
        args = {
            'config': 'config.json',
            'port': 8080,
            'host': '127.0.0.1'
        }
        
        errors = ConfigurationValidator.validate_server_parameters(args)
        assert errors == []
    
    def test_validate_server_parameters_missing_config(self):
        """Test validating server parameters without config file."""
        args = {
            'port': 8080
        }
        
        errors = ConfigurationValidator.validate_server_parameters(args)
        assert len(errors) > 0
        assert any('Configuration file is required' in error for error in errors)
