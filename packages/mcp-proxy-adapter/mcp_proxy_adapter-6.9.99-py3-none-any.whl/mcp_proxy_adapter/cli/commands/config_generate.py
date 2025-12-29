"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

CLI command: config generate (Simple configuration generator)
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from argparse import Namespace
from pathlib import Path
from typing import Optional, Dict

from mcp_proxy_adapter.core.config.simple_config_generator import SimpleConfigGenerator
from mcp_proxy_adapter.core.config.simple_config import SimpleConfig
from mcp_proxy_adapter.core.role_utils import RoleUtils


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
            raise ValueError(
                f"Invalid format for per_job_type_limits item: {item}. Expected 'job_type:limit'"
            )
        job_type, limit_str = item.split(":", 1)
        try:
            limit = int(limit_str.strip())
            if limit < 1:
                raise ValueError(f"Limit must be at least 1, got {limit}")
            limits[job_type.strip()] = limit
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(
                    f"Invalid limit value '{limit_str}': must be an integer"
                )
            raise
    return limits if limits else None


def config_generate_command(args: Namespace) -> int:
    """
    Generate a simple MCP configuration based on CLI arguments.

    Args:
        args: Parsed argparse namespace with generator options.

    Returns:
        Exit status code (0 on success).
    """
    # Validate mTLS requirements
    if args.protocol == "mtls":
        server_ca_cert_file = getattr(args, "server_ca_cert_file", None)
        if not server_ca_cert_file:
            print(
                "❌ Error: --server-ca-cert-file is required for mTLS protocol",
                file=sys.stderr,
            )
            print("   Example: --server-ca-cert-file ./certs/ca.crt", file=sys.stderr)
            return 1
        # Validate that CA certificate file exists
        ca_path = Path(server_ca_cert_file)
        if not ca_path.exists():
            print(
                f"❌ Error: CA certificate file not found: {server_ca_cert_file}",
                file=sys.stderr,
            )
            return 1

    # Validate instance_uuid if provided
    instance_uuid = getattr(args, "instance_uuid", None)
    if instance_uuid is not None:
        try:
            uuid_obj = uuid.UUID(instance_uuid)
            if uuid_obj.version != 4:
                print(
                    f"❌ Error: --instance-uuid must be a valid UUID4, got UUID version {uuid_obj.version}",
                    file=sys.stderr,
                )
                return 1
        except ValueError as e:
            print(
                f"❌ Error: Invalid --instance-uuid format: {str(e)}", file=sys.stderr
            )
            print(
                "   Example: --instance-uuid 550e8400-e29b-41d4-a716-446655440000",
                file=sys.stderr,
            )
            return 1

    generator = SimpleConfigGenerator()
    out = generator.generate(
        protocol=args.protocol,
        with_proxy=True,  # Always enable registration when generating config
        out_path=args.out,
        # Server parameters
        server_host=getattr(args, "server_host", None),
        server_port=getattr(args, "server_port", None),
        server_cert_file=getattr(args, "server_cert_file", None),
        server_key_file=getattr(args, "server_key_file", None),
        server_ca_cert_file=getattr(args, "server_ca_cert_file", None),
        server_crl_file=getattr(args, "server_crl_file", None),
        server_debug=getattr(args, "server_debug", None),
        server_log_level=getattr(args, "server_log_level", None),
        server_log_dir=getattr(args, "server_log_dir", None),
        # Registration parameters
        registration_host=getattr(args, "registration_host", None),
        registration_port=getattr(args, "registration_port", None),
        registration_protocol=getattr(args, "registration_protocol", None),
        registration_cert_file=getattr(args, "registration_cert_file", None),
        registration_key_file=getattr(args, "registration_key_file", None),
        registration_ca_cert_file=getattr(args, "registration_ca_cert_file", None),
        registration_crl_file=getattr(args, "registration_crl_file", None),
        registration_server_id=getattr(args, "registration_server_id", None),
        registration_server_name=getattr(args, "registration_server_name", None),
        instance_uuid=instance_uuid,
    )

    # Load and modify config for auth and queue_manager
    cfg = SimpleConfig()
    cfg.config_path = Path(args.out)
    cfg.load()

    # Set authentication
    if getattr(args, "use_token", False):
        cfg.model.auth.use_token = True
        tokens_str = getattr(args, "tokens", None)
        if tokens_str:
            # Try to parse as JSON string or file path
            if Path(tokens_str).exists():
                tokens_str = Path(tokens_str).read_text(encoding="utf-8")
            cfg.model.auth.tokens = json.loads(tokens_str)
        else:
            # Default token with valid role from CertificateRole enum
            # Use MCPPROXY as default role (most permissive for proxy services)
            valid_roles = RoleUtils.get_valid_roles()
            default_role = "mcpproxy"  # Default fallback
            if "mcpproxy" in valid_roles:
                default_role = "mcpproxy"
            elif valid_roles:
                default_role = valid_roles[0]  # Use first available role
            cfg.model.auth.tokens = {"admin-secret-key": [default_role]}

    if getattr(args, "use_roles", False):
        if not getattr(args, "use_token", False):
            print("❌ Error: --use-roles requires --use-token", file=sys.stderr)
            return 1
        cfg.model.auth.use_roles = True
        roles_str = getattr(args, "roles", None)
        if roles_str:
            # Try to parse as JSON string or file path
            if Path(roles_str).exists():
                roles_str = Path(roles_str).read_text(encoding="utf-8")
            roles_dict = json.loads(roles_str)

            # Validate roles using RoleUtils
            validated_roles_dict = {}
            valid_roles = RoleUtils.get_valid_roles()
            for role_name, permissions in roles_dict.items():
                if RoleUtils.validate_single_role(role_name):
                    validated_roles_dict[role_name] = permissions
                else:
                    print(f"⚠️  Warning: Invalid role '{role_name}'", file=sys.stderr)
                    if valid_roles:
                        print(
                            f"   Valid roles: {', '.join(valid_roles)}", file=sys.stderr
                        )
                    # Use the role anyway, but warn user (validation will catch it later)
                    validated_roles_dict[role_name] = permissions
            cfg.model.auth.roles = validated_roles_dict
        else:
            # Default roles (mcpproxy is a valid role with all permissions)
            valid_roles = RoleUtils.get_valid_roles()
            default_role = "mcpproxy"  # Default fallback
            if "mcpproxy" in valid_roles:
                default_role = "mcpproxy"
            elif valid_roles:
                default_role = valid_roles[0]  # Use first available role
            cfg.model.auth.roles = {default_role: ["*"]}

    # Set queue manager configuration
    queue_enabled = getattr(args, "queue_enabled", True) and not getattr(
        args, "queue_disabled", False
    )
    queue_in_memory = getattr(args, "queue_in_memory", True) and not getattr(
        args, "queue_persistent", False
    )

    cfg.model.queue_manager.enabled = queue_enabled
    cfg.model.queue_manager.in_memory = queue_in_memory
    if hasattr(args, "queue_registry_path") and args.queue_registry_path:
        cfg.model.queue_manager.registry_path = args.queue_registry_path
    if hasattr(args, "queue_shutdown_timeout"):
        cfg.model.queue_manager.shutdown_timeout = args.queue_shutdown_timeout
    if hasattr(args, "queue_max_concurrent"):
        cfg.model.queue_manager.max_concurrent_jobs = args.queue_max_concurrent
    if hasattr(args, "max_queue_size") and args.max_queue_size is not None:
        cfg.model.queue_manager.max_queue_size = args.max_queue_size
    if hasattr(args, "per_job_type_limits") and args.per_job_type_limits:
        try:
            cfg.model.queue_manager.per_job_type_limits = parse_per_job_type_limits(
                args.per_job_type_limits
            )
        except ValueError as e:
            print(f"❌ Error parsing --per-job-type-limits: {e}", file=sys.stderr)
            return 1

    # Save modified config
    cfg.save()

    print(f"✅ Configuration generated: {out}")
    return 0


def main() -> int:
    """Main entry point for adapter-cfg-gen CLI command."""
    parser = argparse.ArgumentParser(
        prog="adapter-cfg-gen",
        description="Generate simple configuration file for MCP Proxy Adapter",
    )
    parser.add_argument(
        "--protocol",
        required=True,
        choices=["http", "https", "mtls"],
        help="Server/proxy protocol",
    )
    parser.add_argument(
        "--out", default="config.json", help="Output config path (default: config.json)"
    )

    # Server parameters
    parser.add_argument("--server-host", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--server-port", type=int, help="Server port (default: 8080)")
    parser.add_argument("--server-cert-file", help="Server certificate file path")
    parser.add_argument("--server-key-file", help="Server key file path")
    parser.add_argument(
        "--server-ca-cert-file",
        help="Server CA certificate file path (required for mTLS protocol)",
    )
    parser.add_argument("--server-crl-file", help="Server CRL file path")
    parser.add_argument(
        "--server-debug", action="store_true", help="Enable debug mode (default: False)"
    )
    parser.add_argument(
        "--server-log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: INFO)",
    )
    parser.add_argument("--server-log-dir", help="Log directory path (default: ./logs)")

    # Registration parameters
    parser.add_argument(
        "--registration-host", help="Registration proxy host (default: localhost)"
    )
    parser.add_argument(
        "--registration-port", type=int, help="Registration proxy port (default: 3005)"
    )
    parser.add_argument(
        "--registration-protocol",
        choices=["http", "https", "mtls"],
        help="Registration protocol",
    )
    parser.add_argument(
        "--registration-cert-file", help="Registration certificate file path"
    )
    parser.add_argument("--registration-key-file", help="Registration key file path")
    parser.add_argument(
        "--registration-ca-cert-file", help="Registration CA certificate file path"
    )
    parser.add_argument("--registration-crl-file", help="Registration CRL file path")
    parser.add_argument("--registration-server-id", help="Server ID for registration")
    parser.add_argument(
        "--registration-server-name", help="Server name for registration"
    )
    parser.add_argument(
        "--instance-uuid",
        help="Server instance UUID (UUID4 format, auto-generated if not provided). If provided but invalid, command will exit with error.",
    )

    # Authentication parameters
    parser.add_argument(
        "--use-token", action="store_true", help="Enable token-based authentication"
    )
    parser.add_argument(
        "--use-roles",
        action="store_true",
        help="Enable role-based authorization (requires --use-token)",
    )
    parser.add_argument(
        "--tokens",
        type=str,
        help='Tokens JSON string or file path. Format: \'{"token1": ["role1"], "token2": ["role2"]}\' or path to JSON file',
    )
    parser.add_argument(
        "--roles",
        type=str,
        help='Roles JSON string or file path. Format: \'{"role1": ["perm1"], "role2": ["perm2"]}\' or path to JSON file',
    )

    # Queue manager parameters
    parser.add_argument(
        "--queue-enabled",
        action="store_true",
        default=True,
        help="Enable queue manager (default: True)",
    )
    parser.add_argument(
        "--queue-disabled", action="store_true", help="Disable queue manager"
    )
    parser.add_argument(
        "--queue-in-memory",
        action="store_true",
        default=True,
        help="Use in-memory queue (default: True)",
    )
    parser.add_argument(
        "--queue-persistent",
        action="store_true",
        help="Use persistent queue (not in-memory)",
    )
    parser.add_argument(
        "--queue-registry-path",
        type=str,
        help="Queue registry file path (ignored if in-memory)",
    )
    parser.add_argument(
        "--queue-shutdown-timeout",
        type=float,
        default=30.0,
        help="Queue shutdown timeout in seconds (default: 30.0)",
    )
    parser.add_argument(
        "--queue-max-concurrent",
        type=int,
        default=10,
        help="Maximum concurrent jobs (default: 10)",
    )
    parser.add_argument(
        "--max-queue-size",
        type=int,
        help="Global maximum number of jobs in queue. If reached, oldest job is deleted before adding new one",
    )
    parser.add_argument(
        "--per-job-type-limits",
        type=str,
        help="Per-job-type limits. Format: 'job_type1:limit1,job_type2:limit2,...' Example: 'command_execution:100,data_processing:50'",
    )

    args = parser.parse_args()
    return config_generate_command(args)


if __name__ == "__main__":
    sys.exit(main())
