"""
Sets Command

This module implements the sets command for generating configurations using predefined sets.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import json
from pathlib import Path
from typing import Dict, Any

from mcp_proxy_adapter.core.config.simple_config import (
    SimpleConfig,
    SimpleConfigModel,
    ServerConfig,
    ClientConfig,
    RegistrationConfig,
    AuthConfig,
)


class SetsCommand:
    """Command for generating configurations using predefined sets."""
    
    def __init__(self):
        """Initialize the sets command."""
        pass
    
    def execute(self, args: Dict[str, Any]) -> int:
        """
        Execute the sets command.
        
        Args:
            args: Parsed command arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        set_name = args.get('set_name')
        
        if not set_name:
            print("❌ No set specified. Use: sets {http,https,mtls}")
            return 1
        
        try:
            # Generate configuration based on set
            config_path = self._create_config_from_set(set_name, args)
            
            print(f"✅ {set_name.upper()} configuration saved to: {config_path}")
            return 0
            
        except Exception as e:
            print(f"❌ Error generating {set_name} configuration: {e}")
            return 1
    
    def _create_config_from_set(self, set_name: str, args: Dict[str, Any]) -> Path:
        """
        Create configuration based on the specified set.
        
        Args:
            set_name: Name of the configuration set
            args: Command arguments
            
        Returns:
            Path to saved configuration file
        """
        host = args.get('host', '127.0.0.1')
        port = int(args.get('port', 8000))
        protocol = set_name

        # Build server config compatible with SimpleConfig
        server = ServerConfig(host=host, port=port, protocol=protocol)
        cert_dir = Path(args.get('cert_dir') or './certs')
        key_dir = Path(args.get('key_dir') or './keys')
        if protocol in ('https', 'mtls'):
            # Prefer test-server.* filenames if present, otherwise fallback to server.*
            cert_file = cert_dir / 'test-server.crt'
            key_file = key_dir / 'test-server.key'
            if not cert_file.exists():
                cert_file = cert_dir / 'server.crt'
            if not key_file.exists():
                key_file = key_dir / 'server.key'
            server.cert_file = str(cert_file)
            server.key_file = str(key_file)
        if protocol == 'mtls':
            # CA file path is expected by validator; try ca/ca.crt relative to provided cert_dir
            ca_candidate = cert_dir.parent / 'ca' / 'ca.crt'
            if not ca_candidate.exists():
                ca_candidate = cert_dir / 'ca.crt'
            server.ca_cert_file = str(ca_candidate)

        # Client config (disabled by default)
        client = ClientConfig(enabled=False)
        
        # Registration config (disabled by default)
        registration = RegistrationConfig(enabled=False)

        # Auth config based on modifiers
        use_token = 'token' in (args.get('modifiers') or []) or bool(args.get('token'))
        use_roles = 'roles' in (args.get('modifiers') or []) or bool(args.get('roles'))
        # If roles are requested, token must be enabled to satisfy validator
        if use_roles and not use_token:
            use_token = True
        tokens = {
            'admin': ['read', 'write', 'delete', 'admin'],
        } if use_token else {}
        roles = {
            'admin': ['read', 'write', 'delete', 'admin'],
            'user': ['read', 'write'],
        } if use_roles else {}
        auth = AuthConfig(use_token=use_token, use_roles=use_roles, tokens=tokens, roles=roles)

        # Save using SimpleConfig
        model = SimpleConfigModel(server=server, client=client, registration=registration, auth=auth)
        out_dir = Path(args.get('output_dir', './configs'))
        out_dir.mkdir(parents=True, exist_ok=True)
        name_parts = [set_name]
        if use_token and set_name in ['http', 'https']:
            name_parts.append('token')
        if use_roles:
            name_parts.append('roles')
        filename = args.get('output') or "_".join(name_parts)
        out_path = out_dir / f"{filename}.json"

        cfg = SimpleConfig(str(out_path))
        cfg.model = model
        cfg.save()
        return out_path


