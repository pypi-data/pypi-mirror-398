#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

CLI tool for generating MCP Proxy Adapter configurations.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .simple_config_generator import SimpleConfigGenerator
from .simple_config_validator import SimpleConfigValidator
from .simple_config import SimpleConfig


def parse_per_job_type_limits(value: str) -> Optional[Dict[str, int]]:
    """
    Parse per_job_type_limits from string format.
    
    Format: "job_type1:limit1,job_type2:limit2,..."
    Example: "command_execution:100,data_processing:50"
    
    Args:
        value: String representation of limits
        
    Returns:
        Dictionary mapping job types to limits, or None if empty
    """
    if not value or value.strip() == "":
        return None
    
    limits = {}
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"Invalid format for per_job_type_limits item: {item}. Expected 'job_type:limit'")
        job_type, limit_str = item.split(":", 1)
        try:
            limit = int(limit_str.strip())
            if limit < 1:
                raise ValueError(f"Limit must be at least 1, got {limit}")
            limits[job_type.strip()] = limit
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Invalid limit value '{limit_str}': must be an integer")
            raise
    return limits if limits else None


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate MCP Proxy Adapter configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate basic HTTP config
  %(prog)s --protocol http --output config.json

  # Generate HTTPS config with certificates
  %(prog)s --protocol https --output config.json \\
    --server-cert ./certs/server.crt --server-key ./certs/server.key

  # Generate config with proxy registration
  %(prog)s --protocol http --output config.json \\
    --with-proxy --proxy-host localhost --proxy-port 3005

  # Generate config with authentication
  %(prog)s --protocol http --output config.json \\
    --use-token --use-roles

  # Generate config with queue manager limits
  %(prog)s --protocol http --output config.json \\
    --max-queue-size 1000 \\
    --per-job-type-limits "command_execution:100,data_processing:50"
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--protocol",
        required=True,
        choices=["http", "https", "mtls"],
        help="Server protocol (http, https, or mtls)"
    )
    parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="Output configuration file path"
    )
    
    # Server arguments
    parser.add_argument(
        "--server-host",
        type=str,
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--server-port",
        type=int,
        help="Server port (default: 8080 for http, 8443 for https/mtls)"
    )
    parser.add_argument(
        "--server-cert",
        type=str,
        help="Server certificate file path (required for https/mtls)"
    )
    parser.add_argument(
        "--server-key",
        type=str,
        help="Server key file path (required for https/mtls)"
    )
    parser.add_argument(
        "--server-ca",
        type=str,
        help="Server CA certificate file path (optional for mtls)"
    )
    parser.add_argument(
        "--server-crl",
        type=str,
        help="Server CRL file path (optional)"
    )
    parser.add_argument(
        "--server-debug",
        action="store_true",
        help="Enable server debug mode"
    )
    parser.add_argument(
        "--server-log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Server log level (default: INFO)"
    )
    parser.add_argument(
        "--server-log-dir",
        type=str,
        help="Server log directory (default: ./logs)"
    )
    
    # Client arguments
    parser.add_argument(
        "--client-enabled",
        action="store_true",
        help="Enable client configuration"
    )
    parser.add_argument(
        "--client-protocol",
        type=str,
        choices=["http", "https", "mtls"],
        help="Client protocol (default: same as server)"
    )
    parser.add_argument(
        "--client-cert",
        type=str,
        help="Client certificate file path"
    )
    parser.add_argument(
        "--client-key",
        type=str,
        help="Client key file path"
    )
    parser.add_argument(
        "--client-ca",
        type=str,
        help="Client CA certificate file path"
    )
    parser.add_argument(
        "--client-crl",
        type=str,
        help="Client CRL file path"
    )
    
    # Registration/proxy arguments
    parser.add_argument(
        "--with-proxy",
        action="store_true",
        help="Enable proxy registration"
    )
    parser.add_argument(
        "--proxy-host",
        type=str,
        default="localhost",
        help="Proxy host (default: localhost)"
    )
    parser.add_argument(
        "--proxy-port",
        "--registration-port",  # Alias for compatibility with test pipeline
        type=int,
        default=3005,
        dest="proxy_port",
        help="Proxy/registration port (default: 3005)"
    )
    parser.add_argument(
        "--proxy-protocol",
        type=str,
        choices=["http", "https", "mtls"],
        help="Proxy protocol (default: http)"
    )
    parser.add_argument(
        "--proxy-cert",
        type=str,
        help="Proxy certificate file path (for https/mtls)"
    )
    parser.add_argument(
        "--proxy-key",
        type=str,
        help="Proxy key file path (for https/mtls)"
    )
    parser.add_argument(
        "--proxy-ca",
        type=str,
        help="Proxy CA certificate file path (for mtls)"
    )
    parser.add_argument(
        "--proxy-crl",
        type=str,
        help="Proxy CRL file path"
    )
    parser.add_argument(
        "--server-id",
        type=str,
        help="Server ID for registration"
    )
    parser.add_argument(
        "--server-name",
        type=str,
        help="Server name for registration"
    )
    
    # Authentication arguments
    parser.add_argument(
        "--use-token",
        action="store_true",
        help="Enable token-based authentication"
    )
    parser.add_argument(
        "--use-roles",
        action="store_true",
        help="Enable role-based authorization (requires --use-token)"
    )
    parser.add_argument(
        "--tokens",
        type=str,
        help="Tokens JSON string or file path. Format: '{\"token1\": [\"role1\"], \"token2\": [\"role2\"]}' or path to JSON file"
    )
    parser.add_argument(
        "--roles",
        type=str,
        help="Roles JSON string or file path. Format: '{\"role1\": [\"perm1\"], \"role2\": [\"perm2\"]}' or path to JSON file"
    )
    
    # Queue manager arguments
    parser.add_argument(
        "--queue-enabled",
        action="store_true",
        default=True,
        help="Enable queue manager (default: True)"
    )
    parser.add_argument(
        "--queue-disabled",
        action="store_true",
        help="Disable queue manager"
    )
    parser.add_argument(
        "--queue-in-memory",
        action="store_true",
        default=True,
        help="Use in-memory queue (default: True)"
    )
    parser.add_argument(
        "--queue-persistent",
        action="store_true",
        help="Use persistent queue (not in-memory)"
    )
    parser.add_argument(
        "--queue-registry-path",
        type=str,
        help="Queue registry file path (ignored if in-memory)"
    )
    parser.add_argument(
        "--queue-shutdown-timeout",
        type=float,
        default=30.0,
        help="Queue shutdown timeout in seconds (default: 30.0)"
    )
    parser.add_argument(
        "--queue-max-concurrent",
        type=int,
        default=10,
        help="Maximum concurrent jobs (default: 10)"
    )
    parser.add_argument(
        "--max-queue-size",
        type=int,
        help="Global maximum number of jobs in queue. If reached, oldest job is deleted before adding new one"
    )
    parser.add_argument(
        "--per-job-type-limits",
        type=str,
        help="Per-job-type limits. Format: 'job_type1:limit1,job_type2:limit2,...' Example: 'command_execution:100,data_processing:50'"
    )
    
    # Validation
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate generated configuration (default: True)"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation"
    )
    
    args = parser.parse_args()
    
    # Determine default port
    if args.server_port is None:
        args.server_port = 8443 if args.protocol in ("https", "mtls") else 8080
    
    # Auto-enable proxy registration if registration parameters are explicitly provided
    # Check if --registration-port or --proxy-port was explicitly passed (not just default)
    import sys
    registration_port_explicit = "--registration-port" in sys.argv or (
        "--proxy-port" in sys.argv and args.proxy_port != 3005
    )
    if not args.with_proxy and registration_port_explicit:
        args.with_proxy = True
    
    # Determine queue enabled
    queue_enabled = args.queue_enabled and not args.queue_disabled
    queue_in_memory = args.queue_in_memory and not args.queue_persistent
    
    # Parse per_job_type_limits
    per_job_type_limits = None
    if args.per_job_type_limits:
        try:
            per_job_type_limits = parse_per_job_type_limits(args.per_job_type_limits)
        except ValueError as e:
            print(f"❌ Error parsing --per-job-type-limits: {e}", file=sys.stderr)
            return 1
    
    # Generate configuration
    try:
        generator = SimpleConfigGenerator()
        generator.generate(
            protocol=args.protocol,
            with_proxy=args.with_proxy,
            out_path=args.output,
            server_host=args.server_host,
            server_port=args.server_port,
            server_cert_file=args.server_cert,
            server_key_file=args.server_key,
            server_ca_cert_file=args.server_ca,
            server_crl_file=args.server_crl,
            server_debug=args.server_debug if args.server_debug else None,
            server_log_level=args.server_log_level,
            server_log_dir=args.server_log_dir,
            client_enabled=args.client_enabled,
            client_protocol=args.client_protocol,
            client_cert_file=args.client_cert,
            client_key_file=args.client_key,
            client_ca_cert_file=args.client_ca,
            client_crl_file=args.client_crl,
            registration_host=args.proxy_host,
            registration_port=args.proxy_port,
            registration_protocol=args.proxy_protocol,
            registration_cert_file=args.proxy_cert,
            registration_key_file=args.proxy_key,
            registration_ca_cert_file=args.proxy_ca,
            registration_crl_file=args.proxy_crl,
            registration_server_id=args.server_id,
            registration_server_name=args.server_name,
            instance_uuid=None,  # Will be auto-generated as UUID4 when with_proxy=True
        )
        
        # Load and modify config for auth and queue_manager
        cfg = SimpleConfig()
        cfg.config_path = Path(args.output)
        cfg.load()
        
        # Set authentication
        if args.use_token:
            cfg.model.auth.use_token = True
            if args.tokens:
                # Try to parse as JSON string or file path
                tokens_str = args.tokens
                if Path(tokens_str).exists():
                    tokens_str = Path(tokens_str).read_text(encoding="utf-8")
                cfg.model.auth.tokens = json.loads(tokens_str)
            else:
                # Default token
                cfg.model.auth.tokens = {"admin-secret-key": ["admin"]}
        
        if args.use_roles:
            if not args.use_token:
                print("❌ Error: --use-roles requires --use-token", file=sys.stderr)
                return 1
            cfg.model.auth.use_roles = True
            if args.roles:
                # Try to parse as JSON string or file path
                roles_str = args.roles
                if Path(roles_str).exists():
                    roles_str = Path(roles_str).read_text(encoding="utf-8")
                cfg.model.auth.roles = json.loads(roles_str)
            else:
                # Default roles
                cfg.model.auth.roles = {"admin": ["*"]}
        
        # Set queue manager configuration
        cfg.model.queue_manager.enabled = queue_enabled
        cfg.model.queue_manager.in_memory = queue_in_memory
        if args.queue_registry_path:
            cfg.model.queue_manager.registry_path = args.queue_registry_path
        cfg.model.queue_manager.shutdown_timeout = args.queue_shutdown_timeout
        cfg.model.queue_manager.max_concurrent_jobs = args.queue_max_concurrent
        if args.max_queue_size is not None:
            cfg.model.queue_manager.max_queue_size = args.max_queue_size
        if per_job_type_limits is not None:
            cfg.model.queue_manager.per_job_type_limits = per_job_type_limits
        
        # Save modified config
        cfg.save()
        
        print(f"✅ Configuration generated: {args.output}")
        
        # Validate if requested
        if args.validate and not args.no_validate:
            validator = SimpleConfigValidator()
            errors = validator.validate(cfg.model)
            if errors:
                print(f"❌ Validation errors:")
                for error in errors:
                    print(f"   - {error.message}")
                return 1
            else:
                print(f"✅ Configuration validated successfully")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating configuration: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

