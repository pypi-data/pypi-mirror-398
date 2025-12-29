"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Simple configuration generator for MCP Proxy Adapter.
"""

from __future__ import annotations

from typing import Optional
import uuid

from .simple_config import (
    SimpleConfig,
    SimpleConfigModel,
    ServerConfig,
    ClientConfig,
    RegistrationConfig,
    HeartbeatConfig,
    AuthConfig,
    SSLConfig,
    QueueManagerConfig,
)


class SimpleConfigGenerator:
    """Generate minimal configuration according to the plan."""

    def generate(
        self,
        protocol: str,
        with_proxy: bool = False,
        out_path: str = "config.json",
        # Server parameters
        server_host: Optional[str] = None,
        server_port: Optional[int] = None,
        server_cert_file: Optional[str] = None,
        server_key_file: Optional[str] = None,
        server_ca_cert_file: Optional[str] = None,
        server_crl_file: Optional[str] = None,
        server_debug: Optional[bool] = None,
        server_log_level: Optional[str] = None,
        server_log_dir: Optional[str] = None,
        # Registration parameters
        registration_host: Optional[str] = None,
        registration_port: Optional[int] = None,
        registration_protocol: Optional[str] = None,
        registration_cert_file: Optional[str] = None,
        registration_key_file: Optional[str] = None,
        registration_ca_cert_file: Optional[str] = None,
        registration_crl_file: Optional[str] = None,
        registration_server_id: Optional[str] = None,
        registration_server_name: Optional[str] = None,
        instance_uuid: Optional[str] = None,
    ) -> str:
        """
        Generate configuration with optional custom parameters.

        Args:
            protocol: Server protocol (http, https, mtls)
            with_proxy: Enable proxy registration (always True when generating config)
            out_path: Output file path
            # Server parameters
            server_host: Server host (default: 0.0.0.0)
            server_port: Server port (default: 8080)
            server_cert_file: Server certificate file path
            server_key_file: Server key file path
            server_ca_cert_file: Server CA certificate file path
            server_crl_file: Server CRL file path
            server_debug: Enable debug mode (default: False)
            server_log_level: Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
            server_log_dir: Log directory path (default: ./logs)
            # Registration parameters
            registration_host: Registration proxy host (default: localhost)
            registration_port: Registration proxy port (default: 3005)
            registration_protocol: Registration protocol (http, https, mtls)
            registration_cert_file: Registration certificate file path
            registration_key_file: Registration key file path
            registration_ca_cert_file: Registration CA certificate file path
            registration_crl_file: Registration CRL file path
            registration_server_id: Server ID for registration
            registration_server_name: Server name for registration
            instance_uuid: Server instance UUID (UUID4 format, auto-generated if not provided)
        """
        # Server configuration with new structure
        server_host_val = server_host or "0.0.0.0"
        server_servername = (
            server_host_val if server_host_val != "0.0.0.0" else "localhost"
        )

        # Create SSL config if needed
        server_ssl = None
        if protocol in ("https", "mtls"):
            # For mTLS, CA certificate is required
            if protocol == "mtls":
                if not server_ca_cert_file:
                    raise ValueError(
                        "CA certificate is required for mTLS protocol. Provide --server-ca-cert-file parameter."
                    )
                server_ca = server_ca_cert_file
            else:
                # For HTTPS, CA is optional
                server_ca = server_ca_cert_file

            server_ssl = SSLConfig(
                cert=server_cert_file or "./certs/server.crt",
                key=server_key_file or "./certs/server.key",
                ca=server_ca,
                crl=server_crl_file,
                dnscheck=False,  # Default false for server
            )

        server = ServerConfig(
            host=server_host_val,
            port=server_port or 8080,
            protocol=protocol,
            servername=server_servername,
            ssl=server_ssl,
            debug=(
                server_debug if server_debug is not None else False
            ),  # Default: production mode
            log_level=server_log_level or "INFO",  # Default: INFO level
            log_dir=server_log_dir or "./logs",  # Default: ./logs
        )

        # Client configuration (always disabled - not used)
        client = ClientConfig(enabled=False)

        # Registration configuration
        if with_proxy:
            reg_host = registration_host or "localhost"
            reg_port = registration_port or 3005
            reg_protocol = registration_protocol or "http"

            # Generate instance_uuid if not provided (must be UUID4)
            if instance_uuid is None:
                instance_uuid = str(uuid.uuid4())
            else:
                # Validate provided UUID
                try:
                    uuid_obj = uuid.UUID(instance_uuid)
                    if uuid_obj.version != 4:
                        raise ValueError(
                            f"instance_uuid must be UUID4, got UUID version {uuid_obj.version}"
                        )
                except ValueError as e:
                    raise ValueError(f"Invalid instance_uuid format: {str(e)}")

            # Determine URL scheme based on protocol
            scheme = "https" if reg_protocol in ("https", "mtls") else "http"

            # Create full URLs for registration and heartbeat
            register_url = f"{scheme}://{reg_host}:{reg_port}/register"
            unregister_url = f"{scheme}://{reg_host}:{reg_port}/unregister"
            heartbeat_url = f"{scheme}://{reg_host}:{reg_port}/proxy/heartbeat"

            # Create heartbeat config
            heartbeat_interval = 30
            heartbeat = HeartbeatConfig(url=heartbeat_url, interval=heartbeat_interval)

            # Create SSL config for registration if needed
            registration_ssl = None
            if reg_protocol in ("https", "mtls"):
                registration_ssl = SSLConfig(
                    cert=registration_cert_file or "./certs/registration.crt",
                    key=registration_key_file or "./certs/registration.key",
                    ca=registration_ca_cert_file
                    or ("./certs/ca.crt" if reg_protocol == "mtls" else None),
                    crl=registration_crl_file,
                    dnscheck=(
                        False if reg_protocol == "mtls" else True
                    ),  # Disable DNS check for mTLS by default
                )

            # Create registration config with new format
            registration = RegistrationConfig(
                enabled=True,
                protocol=reg_protocol,
                register_url=register_url,
                unregister_url=unregister_url,
                heartbeat_interval=heartbeat_interval,
                ssl=registration_ssl,
                heartbeat=heartbeat,
                auto_on_startup=True,
                server_id=registration_server_id,
                server_name=registration_server_name,
                instance_uuid=instance_uuid,
            )
        else:
            # Registration disabled - create minimal config with default URLs (not used when disabled)
            registration = RegistrationConfig(
                enabled=False,
                protocol="http",
                register_url="http://localhost:3005/register",  # Default value, not used when disabled
                unregister_url="http://localhost:3005/unregister",  # Default value, not used when disabled
                heartbeat_interval=30,  # Required field even when disabled
                heartbeat=HeartbeatConfig(
                    url="http://localhost:3005/proxy/heartbeat", interval=30
                ),
            )

        auth = AuthConfig(use_token=False, use_roles=False, tokens={}, roles={})

        # Queue manager configuration with defaults
        queue_manager = QueueManagerConfig(
            enabled=True,
            in_memory=True,
            registry_path=None,
            shutdown_timeout=30.0,
            max_concurrent_jobs=10,
            max_queue_size=None,  # No global limit by default
            per_job_type_limits=None,  # No per-type limits by default
        )

        cfg = SimpleConfig()
        cfg.model = SimpleConfigModel(
            server=server,
            client=client,
            registration=registration,
            auth=auth,
            queue_manager=queue_manager,
        )
        cfg.save(out_path)
        return out_path
