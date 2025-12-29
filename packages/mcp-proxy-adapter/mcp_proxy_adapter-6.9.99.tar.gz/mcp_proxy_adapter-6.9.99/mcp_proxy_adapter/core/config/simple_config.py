"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Simple configuration data container and IO helpers for MCP Proxy Adapter.

This module provides a minimal, explicit configuration model with three
sections: server, client, registration and auth.

- server: Server endpoint configuration (listening for incoming connections)
- client: Client configuration (for connecting to external servers)
- registration: Proxy registration configuration (for registering with proxy server)
- auth: Authentication and authorization configuration
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .simple_config_validator import ValidationError


@dataclass
class SSLConfig:
    """SSL/TLS configuration sub-section."""

    cert: Optional[str] = None
    key: Optional[str] = None
    ca: Optional[str] = None
    crl: Optional[str] = None
    dnscheck: bool = False  # Default: false for server, true for registration
    check_hostname: Optional[bool] = (
        None  # DNS/hostname check (None means use dnscheck value)
    )


@dataclass
class ServerConfig:
    """Server endpoint configuration (listening for incoming connections)."""

    host: str
    port: int
    protocol: str  # http | https | mtls
    servername: str  # DNS name of the server (required)
    ssl: Optional[SSLConfig] = None  # SSL sub-section (required for https/mtls)
    rules: Optional[Dict[str, Any]] = None  # Access control rules (optional)
    log_dir: str = "./logs"
    debug: bool = False  # Debug mode (required by validator)
    log_level: str = (
        "INFO"  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL (required by validator)
    )
    advertised_host: Optional[str] = (
        None  # Hostname advertised to external clients (optional)
    )


@dataclass
class ClientConfig:
    """Client configuration (for connecting to external servers)."""

    enabled: bool = False
    protocol: str = "http"  # http | https | mtls
    ssl: Optional[SSLConfig] = None  # SSL sub-section (required for https/mtls)


@dataclass
class HeartbeatConfig:
    """Heartbeat configuration."""

    url: Optional[str] = (
        None  # Full URL for heartbeat (e.g., "http://localhost:3005/proxy/heartbeat")
    )
    interval: int = 30


@dataclass
class RegistrationConfig:
    """Proxy registration configuration (for registering with proxy server)."""

    enabled: bool = False
    protocol: str = "http"  # http | https | mtls - determines how to connect to proxy
    register_url: Optional[str] = (
        None  # Full URL for registration (e.g., "http://localhost:3005/register") - MUST match protocol, required when enabled=True
    )
    unregister_url: Optional[str] = (
        None  # Full URL for unregistration (e.g., "http://localhost:3005/unregister")
    )
    heartbeat_interval: int = (
        30  # Heartbeat ping interval in seconds (required if enabled)
    )
    ssl: Optional[SSLConfig] = None  # SSL sub-section (required for https/mtls)
    server_id: Optional[str] = None  # Server identifier for registration
    server_name: Optional[str] = None  # Server name for registration
    instance_uuid: Optional[str] = None  # Server instance UUID (UUID4 format, required when enabled=True)
    auto_on_startup: bool = True
    auto_on_shutdown: bool = True
    heartbeat: HeartbeatConfig = field(default_factory=HeartbeatConfig)


@dataclass
class AuthConfig:
    """
    Authentication and authorization configuration.

    Attributes:
        use_token: Whether to use token-based authentication
        use_roles: Whether to use role-based authorization
        tokens: Dictionary mapping token values to lists of roles
        roles: Dictionary mapping role names to lists of permissions
    """

    use_token: bool = False
    use_roles: bool = False
    tokens: Dict[str, List[str]] = field(default_factory=dict)
    roles: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ServerValidationConfig:
    """Server validation configuration (for proxy to validate registered servers)."""

    enabled: bool = False
    protocol: str = "http"  # http | https | mtls
    ssl: Optional[SSLConfig] = None  # SSL sub-section (required for https/mtls)
    timeout: int = 10  # Connection timeout in seconds
    use_token: bool = False
    use_roles: bool = False
    tokens: Dict[str, List[str]] = field(default_factory=dict)
    roles: Dict[str, List[str]] = field(default_factory=dict)
    auth_header: str = "X-API-Key"  # Header name for token authentication
    roles_header: str = "X-Roles"  # Header name for roles
    health_path: str = "/health"  # Health endpoint path
    check_hostname: bool = False  # Verify DNS name on TLS connections


@dataclass
class QueueManagerConfig:
    """Queue manager configuration."""

    enabled: bool = True  # Enable queue manager (default: True)
    in_memory: bool = True  # Use in-memory queue (default: True)
    registry_path: Optional[str] = (
        None  # Path to registry file (ignored if in_memory=True)
    )
    shutdown_timeout: float = 30.0  # Timeout for graceful shutdown in seconds
    max_concurrent_jobs: int = 10  # Maximum number of concurrent jobs
    max_queue_size: Optional[int] = (
        None  # Global maximum number of jobs. If reached, oldest job is deleted before adding new one. If None, no limit (default: None)
    )
    per_job_type_limits: Optional[Dict[str, int]] = (
        None  # Dict mapping job_type to max count. If limit is reached for a job type, oldest job of that type is deleted before adding new one. If None, no per-type limits (default: None)
    )
    completed_job_retention_seconds: int = (
        21600  # How long to keep completed jobs before cleanup (default: 21600 = 6 hours). Set to 0 to keep completed jobs indefinitely.
    )


@dataclass
class SimpleConfigModel:
    """
    Complete simple configuration model.

    Attributes:
        server: Server endpoint configuration
        client: Client configuration for external connections
        registration: Proxy registration configuration
        server_validation: Server validation configuration
        auth: Authentication and authorization configuration
        queue_manager: Queue manager configuration
    """

    server: ServerConfig
    client: ClientConfig = field(default_factory=ClientConfig)
    registration: RegistrationConfig = field(default_factory=RegistrationConfig)
    server_validation: ServerValidationConfig = field(
        default_factory=ServerValidationConfig
    )
    auth: AuthConfig = field(default_factory=AuthConfig)
    queue_manager: QueueManagerConfig = field(default_factory=QueueManagerConfig)


class SimpleConfig:
    """High-level loader/saver for SimpleConfigModel."""

    def __init__(self, config_path: str = "config.json") -> None:
        """
        Initialize SimpleConfig loader/saver.

        Args:
            config_path: Path to configuration file
        """
        self.config_path: Path = Path(config_path)
        self.model: Optional[SimpleConfigModel] = None

    def load(self) -> SimpleConfigModel:
        """
        Load configuration from file.

        Returns:
            Loaded SimpleConfigModel instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        content = json.loads(self.config_path.read_text(encoding="utf-8"))
        server_data = content["server"].copy()

        # Remove legacy fields (they should be in ssl sub-section)
        for legacy_field in [
            "cert_file",
            "key_file",
            "ca_cert_file",
            "crl_file",
            "use_system_ca",
            "check_hostname",
            "debug",
            "log_level",
        ]:
            server_data.pop(legacy_field, None)

        # Set default servername if not provided (use host or localhost)
        if "servername" not in server_data:
            server_data["servername"] = server_data.get("host", "localhost")

        # Convert ssl dict to SSLConfig if present (skip if None/null)
        if (
            "ssl" in server_data
            and server_data["ssl"] is not None
            and isinstance(server_data["ssl"], dict)
        ):
            server_data["ssl"] = SSLConfig(**server_data["ssl"])
        elif "ssl" in server_data and server_data["ssl"] is None:
            # Remove None ssl to avoid passing it to ServerConfig
            server_data.pop("ssl")

        server = ServerConfig(**server_data)

        # Load client config
        client_data = content.get("client", {})
        # Remove legacy fields (they should be in ssl sub-section)
        for legacy_field in [
            "cert_file",
            "key_file",
            "ca_cert_file",
            "crl_file",
            "use_system_ca",
            "check_hostname",
        ]:
            client_data.pop(legacy_field, None)

        # Convert ssl dict to SSLConfig if present (skip if None/null)
        if (
            "ssl" in client_data
            and client_data["ssl"] is not None
            and isinstance(client_data["ssl"], dict)
        ):
            client_data["ssl"] = SSLConfig(**client_data["ssl"])
        elif "ssl" in client_data and client_data["ssl"] is None:
            # Remove None ssl to avoid passing it to ClientConfig
            client_data.pop("ssl")
        client = ClientConfig(**client_data)

        # Load registration config
        registration_data = content.get("registration", {})

        # Remove legacy fields (they should be in ssl sub-section or not used)
        for legacy_field in [
            "cert_file",
            "key_file",
            "ca_cert_file",
            "crl_file",
            "use_system_ca",
            "check_hostname",
            "host",
            "port",
            "register_endpoint",
            "unregister_endpoint",
            "server_name",
            "proxy_url",
            "server_url",
            "auto_register_on_startup",
        ]:
            registration_data.pop(legacy_field, None)

        # Convert ssl dict to SSLConfig if present (skip if None/null)
        if (
            "ssl" in registration_data
            and registration_data["ssl"] is not None
            and isinstance(registration_data["ssl"], dict)
        ):
            ssl_dict = registration_data["ssl"].copy()
            # Support both check_hostname and dnscheck, prefer check_hostname
            if "check_hostname" in ssl_dict:
                ssl_dict["dnscheck"] = ssl_dict["check_hostname"]
            elif "dnscheck" in ssl_dict and "check_hostname" not in ssl_dict:
                ssl_dict["check_hostname"] = ssl_dict["dnscheck"]
            registration_data["ssl"] = SSLConfig(**ssl_dict)
        elif "ssl" in registration_data and registration_data["ssl"] is None:
            # Remove None ssl to avoid passing it to RegistrationConfig
            registration_data.pop("ssl")

        registration = RegistrationConfig(**registration_data)

        # Handle nested heartbeat structure
        if isinstance(registration_data.get("heartbeat"), dict):
            heartbeat_data = registration_data["heartbeat"].copy()
            registration.heartbeat = HeartbeatConfig(**heartbeat_data)

        # Load server_validation config (for proxy to validate registered servers)
        server_validation_data = content.get("server_validation", {})
        # Remove legacy fields (they should be in ssl sub-section)
        for legacy_field in [
            "cert_file",
            "key_file",
            "ca_cert_file",
            "crl_file",
            "use_system_ca",
        ]:
            server_validation_data.pop(legacy_field, None)

        # Convert ssl dict to SSLConfig if present (skip if None/null)
        if (
            "ssl" in server_validation_data
            and server_validation_data["ssl"] is not None
            and isinstance(server_validation_data["ssl"], dict)
        ):
            server_validation_data["ssl"] = SSLConfig(**server_validation_data["ssl"])
        elif "ssl" in server_validation_data and server_validation_data["ssl"] is None:
            # Remove None ssl to avoid passing it to ServerValidationConfig
            server_validation_data.pop("ssl")
        server_validation = ServerValidationConfig(**server_validation_data)

        auth = AuthConfig(**content.get("auth", {}))

        # Load queue_manager config
        queue_manager_data = content.get("queue_manager", {})
        queue_manager = QueueManagerConfig(**queue_manager_data)

        self.model = SimpleConfigModel(
            server=server,
            client=client,
            registration=registration,
            server_validation=server_validation,
            auth=auth,
            queue_manager=queue_manager,
        )
        return self.model

    def save(self, out_path: Optional[str] = None) -> None:
        """
        Persist configuration model to disk.

        Args:
            out_path: Optional override path; defaults to self.config_path.

        Raises:
            ValueError: If configuration model is not loaded.
        """
        if self.model is None:
            raise ValueError("Configuration model is not loaded")
        path = Path(out_path) if out_path else self.config_path

        # Convert dataclasses to dict, handling SSLConfig
        def convert_to_dict(obj: Any) -> Any:
            """Recursively convert dataclasses to dictionaries, including SSLConfig."""
            if hasattr(obj, "__dict__"):
                result = {}
                for k, v in vars(obj).items():
                    if isinstance(v, SSLConfig):
                        ssl_dict = vars(v).copy()
                        # Add check_hostname if dnscheck is present (for compatibility)
                        if "dnscheck" in ssl_dict and "check_hostname" not in ssl_dict:
                            ssl_dict["check_hostname"] = ssl_dict["dnscheck"]
                        result[k] = ssl_dict
                    elif hasattr(v, "__dict__"):
                        result[k] = convert_to_dict(v)
                    else:
                        result[k] = v
                return result
            return obj

        data: Dict[str, Any] = {
            "server": convert_to_dict(self.model.server),
            "client": convert_to_dict(self.model.client),
            "registration": {
                **{
                    k: v
                    for k, v in convert_to_dict(self.model.registration).items()
                    if k != "heartbeat"
                },
                "heartbeat": convert_to_dict(self.model.registration.heartbeat),
            },
            "server_validation": convert_to_dict(self.model.server_validation),
            "auth": vars(self.model.auth),
            "queue_manager": vars(self.model.queue_manager),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration model as dictionary."""
        if self.model is None:
            raise ValueError("Configuration model is not loaded")
        return asdict(self.model)

    def validate(self) -> List["ValidationError"]:
        """
        Validate configuration model.

        Returns:
            List of ValidationError objects (empty if validation passes)
        """
        if self.model is None:
            raise ValueError("Configuration model is not loaded")
        from .simple_config_validator import SimpleConfigValidator

        validator = SimpleConfigValidator(str(self.config_path))
        return validator.validate(self.model)
