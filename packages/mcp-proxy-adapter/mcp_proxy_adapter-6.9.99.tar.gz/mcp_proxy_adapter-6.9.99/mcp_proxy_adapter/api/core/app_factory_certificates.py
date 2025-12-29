"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Certificate validation helpers for API AppFactory.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from mcp_proxy_adapter.core.config.simple_config import ServerConfig

RegistrationConfigData = Dict[str, Any]


def validate_certificates(
    current_config: Dict[str, Any],
    config_path: Optional[str],
    logger,
) -> None:
    """
    Validate certificates at startup.

    Args:
        current_config: Configuration dictionary.
        config_path: Optional path to config file for SimpleConfig loader.
        logger: Logger instance.

    Raises:
        SystemExit: When certificate validation fails.
    """
    try:
        certificate_errors: List[str] = []
        is_simple_config = _is_simple_config_format(current_config)

        if is_simple_config:
            validation_errors = _validate_simple_config(current_config, config_path, logger)
            certificate_errors.extend(validation_errors)

        if certificate_errors:
            logger.critical(
                "CRITICAL CERTIFICATE ERROR: Certificate validation failed at startup:"
            )
            for error in certificate_errors:
                logger.critical(f"  - {error}")
            logger.critical(
                "Server startup aborted due to certificate validation errors"
            )
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as ex:
        logger.error(f"Failed to run certificate validation: {ex}")
        logger.warning(
            "Certificate validation could not be completed, but server will continue to start"
        )


def _is_simple_config_format(current_config: Dict[str, Any]) -> bool:
    """Return True if configuration resembles SimpleConfig structure."""
    return "server" in current_config and any(
        key in current_config for key in ("proxy_client", "client", "registration")
    )


def _validate_simple_config(
    current_config: Dict[str, Any],
    config_path: Optional[str],
    logger,
) -> List[str]:
    """Validate configuration using SimpleConfig validator."""
    from mcp_proxy_adapter.core.config.simple_config import (  # type: ignore
        SimpleConfig,
        SimpleConfigModel,
        ServerConfig,
        ClientConfig,
        RegistrationConfig,
        AuthConfig,
        HeartbeatConfig,
    )
    from mcp_proxy_adapter.core.config.simple_config_validator import (  # type: ignore
        SimpleConfigValidator,
    )

    errors: List[str] = []

    try:
        if config_path:
            cfg = SimpleConfig(config_path)
            model = cfg.load()
        else:
            server = _build_server_config(current_config)
            client = ClientConfig(**current_config.get("client", {}))  # type: ignore[arg-type]
            registration, heartbeat_override = _build_registration_config(current_config)
            auth = AuthConfig(**current_config.get("auth", {}))  # type: ignore[arg-type]

            registration_model = RegistrationConfig(**registration)  # type: ignore[arg-type]
            if heartbeat_override is not None:
                registration_model.heartbeat = HeartbeatConfig(**heartbeat_override)  # type: ignore[arg-type]

            model = SimpleConfigModel(
                server=server,
                client=client,
                registration=registration_model,
                auth=auth,
            )

        validator = SimpleConfigValidator()
        validation_errors = validator.validate(model)
        for error in validation_errors:
            errors.append(error.message)

    except Exception as exc:
        logger.error(f"Failed to validate as SimpleConfig format: {exc}")
        errors.append(
            f"Configuration validation failed: {exc}. Only SimpleConfig format is supported."
        )

    return errors


def _build_server_config(current_config: Dict[str, Any]) -> "ServerConfig":
    """Build ServerConfig instance from raw dictionary."""
    from mcp_proxy_adapter.core.config.simple_config import ServerConfig

    server_config = current_config.get("server", {})
    known_fields = {
        "host",
        "port",
        "protocol",
        "cert_file",
        "key_file",
        "ca_cert_file",
        "crl_file",
        "use_system_ca",
        "log_dir",
    }
    server_data = {k: v for k, v in server_config.items() if k in known_fields}
    return ServerConfig(**server_data)  # type: ignore[arg-type]


def _build_registration_config(
    current_config: Dict[str, Any],
) -> (RegistrationConfigData, Optional[Dict[str, Any]]):
    """Build registration configuration and heartbeat overrides."""
    from mcp_proxy_adapter.core.config.simple_config import RegistrationConfig  # type: ignore

    registration_config = current_config.get("registration", {}) or {}
    if not registration_config and current_config.get("proxy_client"):
        pc = current_config["proxy_client"]
        registration_config = {
            "enabled": pc.get("enabled", False),
            "host": pc.get("host", "localhost"),
            "port": pc.get("port", 3005),
            "protocol": pc.get("protocol", "http"),
            "server_id": pc.get("server_id"),
            "server_name": pc.get("server_name"),
            "cert_file": pc.get("cert_file"),
            "key_file": pc.get("key_file"),
            "ca_cert_file": pc.get("ca_cert_file"),
            "crl_file": pc.get("crl_file"),
            "use_system_ca": pc.get("use_system_ca", False),
            "register_endpoint": pc.get("registration", {}).get("register_endpoint", "/register")
            if isinstance(pc.get("registration"), dict)
            else "/register",
            "unregister_endpoint": pc.get("registration", {}).get("unregister_endpoint", "/unregister")
            if isinstance(pc.get("registration"), dict)
            else "/unregister",
            "auto_on_startup": pc.get("registration", {}).get("auto_on_startup", True)
            if isinstance(pc.get("registration"), dict)
            else True,
            "auto_on_shutdown": pc.get("registration", {}).get("auto_on_shutdown", True)
            if isinstance(pc.get("registration"), dict)
            else True,
            "heartbeat": pc.get("heartbeat", {}),
        }

    heartbeat_override = None
    heartbeat = registration_config.get("heartbeat")
    if isinstance(heartbeat, dict):
        heartbeat_override = heartbeat.copy()
        if "endpoint" in heartbeat_override and "url" not in heartbeat_override:
            heartbeat_override.pop("endpoint")

    return registration_config, heartbeat_override


