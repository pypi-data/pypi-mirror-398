"""
CLI Parameter Validators

This module provides validation functions for CLI parameters and their combinations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
from pathlib import Path


class ValidationError(Exception):
    """Exception raised when parameter validation fails."""
    pass


class ParameterValidator:
    """Validates CLI parameters and their combinations."""
    
    @staticmethod
    def validate_protocol(protocol: str) -> bool:
        """
        Validate protocol parameter.
        
        Args:
            protocol: Protocol string to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If protocol is invalid
        """
        valid_protocols = ['http', 'https', 'mtls']
        if protocol not in valid_protocols:
            raise ValidationError(
                f"Invalid protocol '{protocol}'. Must be one of: {', '.join(valid_protocols)}"
            )
        return True
    
    @staticmethod
    def validate_token_with_protocol(token: bool, protocol: str) -> bool:
        """
        Validate token parameter with protocol.
        
        Args:
            token: Whether token authentication is enabled
            protocol: Protocol being used
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If token is not compatible with protocol
        """
        if token and protocol == 'mtls':
            raise ValidationError(
                "Token authentication is not supported with mTLS protocol. "
                "mTLS uses client certificates for authentication."
            )
        return True
    
    @staticmethod
    def validate_roles_with_auth(roles: bool, token: bool, protocol: str) -> bool:
        """
        Validate roles parameter with authentication method.
        
        Args:
            roles: Whether roles are enabled
            token: Whether token authentication is enabled
            protocol: Protocol being used
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If roles are not compatible with authentication method
        """
        if roles and protocol in ['http', 'https'] and not token:
            raise ValidationError(
                f"Roles require token authentication for {protocol} protocol. "
                "Use --token flag when enabling --roles."
            )
        return True
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """
        Validate port number.
        
        Args:
            port: Port number to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If port is invalid
        """
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValidationError(f"Invalid port '{port}'. Must be an integer between 1 and 65535.")
        return True
    
    @staticmethod
    def validate_host(host: str) -> bool:
        """
        Validate host address.
        
        Args:
            host: Host address to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If host is invalid
        """
        if not host or not isinstance(host, str):
            raise ValidationError("Host must be a non-empty string.")
        return True
    
    @staticmethod
    def validate_file_path(file_path: str, must_exist: bool = False) -> bool:
        """
        Validate file path.
        
        Args:
            file_path: File path to validate
            must_exist: Whether file must exist
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If file path is invalid
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path must be a non-empty string.")
        
        if must_exist and not Path(file_path).exists():
            raise ValidationError(f"File does not exist: {file_path}")
        
        return True
    
    @staticmethod
    def validate_directory_path(dir_path: str, must_exist: bool = False) -> bool:
        """
        Validate directory path.
        
        Args:
            dir_path: Directory path to validate
            must_exist: Whether directory must exist
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If directory path is invalid
        """
        if not dir_path or not isinstance(dir_path, str):
            raise ValidationError("Directory path must be a non-empty string.")
        
        if must_exist and not Path(dir_path).exists():
            raise ValidationError(f"Directory does not exist: {dir_path}")
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL must be a non-empty string.")
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            raise ValidationError("URL must start with 'http://' or 'https://'")
        
        return True
    
    @staticmethod
    def validate_server_id(server_id: str) -> bool:
        """
        Validate server ID.
        
        Args:
            server_id: Server ID to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If server ID is invalid
        """
        if not server_id or not isinstance(server_id, str):
            raise ValidationError("Server ID must be a non-empty string.")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', server_id):
            raise ValidationError(
                "Server ID must contain only alphanumeric characters, hyphens, and underscores."
            )
        
        return True


class ConfigurationValidator:
    """Validates configuration combinations and dependencies."""
    
    @staticmethod
    def validate_generate_parameters(args: dict) -> list[str]:
        """
        Validate parameters for config generate command.
        
        Args:
            args: Dictionary of command arguments
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate protocol
        protocol = args.get('protocol', 'http')
        try:
            ParameterValidator.validate_protocol(protocol)
        except ValidationError as e:
            errors.append(str(e))
        
        # Validate token with protocol
        token = args.get('token', False)
        try:
            ParameterValidator.validate_token_with_protocol(token, protocol)
        except ValidationError as e:
            errors.append(str(e))
        
        # Validate roles with auth
        roles = args.get('roles', False)
        try:
            ParameterValidator.validate_roles_with_auth(roles, token, protocol)
        except ValidationError as e:
            errors.append(str(e))
        
        # Validate host if provided
        if 'host' in args:
            try:
                ParameterValidator.validate_host(args['host'])
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate port if provided
        if 'port' in args:
            try:
                ParameterValidator.validate_port(args['port'])
            except ValidationError as e:
                errors.append(str(e))
        
        return errors
    
    @staticmethod
    def validate_sets_parameters(protocol: str, args: dict) -> list[str]:
        """
        Validate parameters for config sets command.
        
        Args:
            protocol: Protocol being used
            args: Dictionary of command arguments
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate protocol
        try:
            ParameterValidator.validate_protocol(protocol)
        except ValidationError as e:
            errors.append(str(e))
        
        # Validate token with protocol
        token = args.get('token', False)
        try:
            ParameterValidator.validate_token_with_protocol(token, protocol)
        except ValidationError as e:
            error_msg = str(e).replace('mTLS protocol', f'mTLS set')
            errors.append(error_msg)
        
        # Validate roles with auth
        roles = args.get('roles', False)
        try:
            ParameterValidator.validate_roles_with_auth(roles, token, protocol)
        except ValidationError as e:
            error_msg = str(e).replace(f'{protocol} protocol', f'{protocol.upper()} set')
            errors.append(error_msg)
        
        # Validate host if provided
        if 'host' in args:
            try:
                ParameterValidator.validate_host(args['host'])
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate port if provided
        if 'port' in args:
            try:
                ParameterValidator.validate_port(args['port'])
            except ValidationError as e:
                errors.append(str(e))
        
        return errors
    
    @staticmethod
    def validate_testconfig_parameters(args: dict) -> list[str]:
        """
        Validate parameters for config testconfig command.
        
        Args:
            args: Dictionary of command arguments
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Config file is required
        if 'config' not in args or not args.get('config'):
            errors.append('Configuration file is required')
        else:
            # Validate config file path format (but don't require existence)
            try:
                ParameterValidator.validate_file_path(args['config'], must_exist=False)
            except ValidationError as e:
                errors.append(str(e))
        
        return errors
    
    @staticmethod
    def validate_server_parameters(args: dict) -> list[str]:
        """
        Validate parameters for server command.
        
        Args:
            args: Dictionary of command arguments
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Config file is required
        if 'config' not in args or not args.get('config'):
            errors.append('Configuration file is required')
        else:
            # Validate config file path format (but don't require existence)
            try:
                ParameterValidator.validate_file_path(args['config'], must_exist=False)
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate host if provided
        if 'host' in args:
            try:
                ParameterValidator.validate_host(args['host'])
            except ValidationError as e:
                errors.append(str(e))
        
        # Validate port if provided
        if 'port' in args:
            try:
                ParameterValidator.validate_port(args['port'])
            except ValidationError as e:
                errors.append(str(e))
        
        return errors

