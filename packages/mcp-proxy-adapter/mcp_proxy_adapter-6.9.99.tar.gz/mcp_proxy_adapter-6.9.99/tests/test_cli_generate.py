"""
Tests for CLI Generate Command

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp_proxy_adapter.cli.commands.generate import GenerateCommand


class TestGenerateCommand:
    """Test cases for GenerateCommand."""
    
    def test_create_config_from_args_http(self):
        """Test creating HTTP configuration from arguments."""
        cmd = GenerateCommand()
        args = {
            'protocol': 'http',
            'token': True,
            'roles': True,
            'host': '127.0.0.1',
            'port': 8080
        }
        
        with patch('mcp_proxy_adapter.cli.commands.generate.generate_complete_config') as mock_generate:
            mock_generate.return_value = {
                'server': {'protocol': 'http', 'host': '127.0.0.1', 'port': 8080},
                'security': {'enabled': False, 'tokens': {}, 'roles': {}, 'roles_file': None},
                'roles': {'enabled': False, 'config_file': None},
                'ssl': {'enabled': False, 'cert_file': None, 'key_file': None, 'ca_cert': None},
                'transport': {'verify_client': False}
            }
            
            config = cmd._create_config_from_args(args)
            
            assert config['server']['protocol'] == 'http'
            assert config['security']['enabled'] is True
            assert 'tokens' in config['security']
            assert 'roles' in config['security']
            assert config['roles']['enabled'] is True
    
    def test_create_config_from_args_https(self):
        """Test creating HTTPS configuration from arguments."""
        cmd = GenerateCommand()
        args = {
            'protocol': 'https',
            'token': True,
            'host': '127.0.0.1',
            'port': 8443,
            'cert_dir': './certs',
            'key_dir': './keys'
        }
        
        with patch('mcp_proxy_adapter.cli.commands.generate.generate_complete_config') as mock_generate:
            mock_generate.return_value = {
                'server': {'protocol': 'https', 'host': '127.0.0.1', 'port': 8443},
                'security': {'enabled': False, 'tokens': {}, 'roles': {}, 'roles_file': None},
                'roles': {'enabled': False, 'config_file': None},
                'ssl': {'enabled': False, 'cert_file': None, 'key_file': None, 'ca_cert': None},
                'transport': {'verify_client': False}
            }
            
            config = cmd._create_config_from_args(args)
            
            assert config['server']['protocol'] == 'https'
            assert config['ssl']['enabled'] is True
            assert config['ssl']['cert_file'] == './certs/server.crt'
            assert config['ssl']['key_file'] == './keys/server.key'
            assert config['security']['enabled'] is True
    
    def test_create_config_from_args_mtls(self):
        """Test creating mTLS configuration from arguments."""
        cmd = GenerateCommand()
        args = {
            'protocol': 'mtls',
            'roles': True,
            'host': '127.0.0.1',
            'port': 8443,
            'cert_dir': './certs',
            'key_dir': './keys'
        }
        
        with patch('mcp_proxy_adapter.cli.commands.generate.generate_complete_config') as mock_generate:
            mock_generate.return_value = {
                'server': {'protocol': 'mtls', 'host': '127.0.0.1', 'port': 8443},
                'security': {'enabled': False, 'tokens': {}, 'roles': {}, 'roles_file': None},
                'roles': {'enabled': False, 'config_file': None},
                'ssl': {'enabled': False, 'cert_file': None, 'key_file': None, 'ca_cert': None},
                'transport': {'verify_client': False}
            }
            
            config = cmd._create_config_from_args(args)
            
            assert config['server']['protocol'] == 'mtls'
            assert config['ssl']['enabled'] is True
            assert config['ssl']['cert_file'] == './certs/server.crt'
            assert config['ssl']['key_file'] == './keys/server.key'
            assert config['ssl']['ca_cert'] == './certs/ca.crt'
            assert config['transport']['verify_client'] is True
            assert config['roles']['enabled'] is True
    
    def test_save_config(self):
        """Test saving configuration to file."""
        cmd = GenerateCommand()
        config = {
            'server': {'protocol': 'http', 'host': '127.0.0.1', 'port': 8080},
            'security': {'enabled': True, 'tokens': {'admin': 'test-token'}}
        }
        args = {
            'output_dir': './test_configs',
            'no_validate': True
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            args['output_dir'] = temp_dir
            
            config_file = cmd._save_config(config, args, 'test_config')
            
            assert config_file.exists()
            assert config_file.name == 'test_config.json'
            
            # Verify file content
            with open(config_file, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config == config
    
    def test_generate_all_configs(self):
        """Test generating all standard configurations."""
        cmd = GenerateCommand()
        args = {
            'output_dir': './test_configs',
            'no_validate': True
        }
        
        with patch('mcp_proxy_adapter.cli.commands.generate.generate_complete_config') as mock_generate:
            mock_generate.return_value = {
                'server': {'protocol': 'http', 'host': '127.0.0.1', 'port': 8080},
                'security': {'enabled': False, 'tokens': {}, 'roles': {}, 'roles_file': None},
                'roles': {'enabled': False, 'config_file': None},
                'ssl': {'enabled': False, 'cert_file': None, 'key_file': None, 'ca_cert': None},
                'transport': {'verify_client': False}
            }
            
            with tempfile.TemporaryDirectory() as temp_dir:
                args['output_dir'] = temp_dir
                
                result = cmd._generate_all_configs(args)
                
                assert result == 0
                
                # Check that files were created
                config_dir = Path(temp_dir)
                config_files = list(config_dir.glob("*.json"))
                assert len(config_files) >= 8  # Should have at least 8 config files
                
                # Check for specific files
                expected_files = [
                    'http.json',
                    'http_token.json',
                    'http_token_roles.json',
                    'https.json',
                    'https_token.json',
                    'https_token_roles.json',
                    'mtls.json',
                    'mtls_roles.json'
                ]
                
                for expected_file in expected_files:
                    assert (config_dir / expected_file).exists()
    
    def test_execute_generate_single(self):
        """Test executing generate command for single configuration."""
        cmd = GenerateCommand()
        args = {
            'protocol': 'http',
            'token': True,
            'stdout': True,
            'no_validate': True
        }
        
        with patch('mcp_proxy_adapter.cli.commands.generate.generate_complete_config') as mock_generate:
            mock_generate.return_value = {
                'server': {'protocol': 'http', 'host': '127.0.0.1', 'port': 8080},
                'security': {'enabled': False, 'tokens': {}, 'roles': {}, 'roles_file': None},
                'roles': {'enabled': False, 'config_file': None},
                'ssl': {'enabled': False, 'cert_file': None, 'key_file': None, 'ca_cert': None},
                'transport': {'verify_client': False}
            }
            
            with patch('builtins.print') as mock_print:
                result = cmd.execute(args)
                
                assert result == 0
                mock_print.assert_called_once()
    
    def test_execute_generate_all(self):
        """Test executing generate command for all configurations."""
        cmd = GenerateCommand()
        args = {
            'all': True,
            'output_dir': './test_configs',
            'no_validate': True
        }
        
        with patch('mcp_proxy_adapter.cli.commands.generate.generate_complete_config') as mock_generate:
            mock_generate.return_value = {
                'server': {'protocol': 'http', 'host': '127.0.0.1', 'port': 8080},
                'security': {'enabled': False, 'tokens': {}, 'roles': {}, 'roles_file': None},
                'roles': {'enabled': False, 'config_file': None},
                'ssl': {'enabled': False, 'cert_file': None, 'key_file': None, 'ca_cert': None},
                'transport': {'verify_client': False}
            }
            
            with tempfile.TemporaryDirectory() as temp_dir:
                args['output_dir'] = temp_dir
                
                result = cmd.execute(args)
                
                assert result == 0
