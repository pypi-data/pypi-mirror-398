"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Helper functions for RegistrationManager.
"""

from typing import Any, Dict, List

from mcp_proxy_adapter.api.core.registration_context import (
    ProxyCredentials,
    RegistrationContext,
)


def apply_context(
    context: RegistrationContext,
    config: Dict[str, Any],
    manager_state: Dict[str, Any],
) -> None:
    """
    Apply registration context to manager state.
    
    Args:
        context: Registration context with server and proxy information
        config: Configuration dictionary
        manager_state: Dictionary to update with context values
    """
    manager_state["server_name"] = context.server_name
    manager_state["server_url"] = context.advertised_url
    manager_state["proxy_url"] = context.proxy_url
    manager_state["capabilities"] = list(context.capabilities)
    manager_state["metadata"] = dict(context.metadata)
    manager_state["config"] = config
    manager_state["_proxy_registration_config"] = context.proxy_registration_config
    manager_state["_registration_credentials"] = context.credentials
    # Use registration credentials for runtime as well (they're the same)
    manager_state["_runtime_credentials"] = context.credentials
    manager_state["_register_endpoint"] = context.register_endpoint


def log_credentials(logger: Any, prefix: str, credentials: ProxyCredentials) -> None:
    """
    Log proxy credentials information (without sensitive data).
    
    Args:
        logger: Logger instance
        prefix: Log message prefix
        credentials: Proxy credentials to log
    """
    logger.info(
        "%s: cert=%s, verify=%s",
        prefix,
        credentials.cert is not None,
        credentials.verify,
    )
    if credentials.cert:
        logger.debug("   Client cert: %s, key: %s", *credentials.cert)
    if isinstance(credentials.verify, str):
        logger.debug("   CA cert: %s", credentials.verify)


def format_httpx_error(exc: Exception) -> str:
    """
    Format httpx exception for logging.
    
    Args:
        exc: Exception to format
        
    Returns:
        Formatted error message string
    """
    import httpx

    error_msg = str(exc) or type(exc).__name__
    details: List[str] = [f"type={type(exc).__name__}"]

    if isinstance(exc, httpx.HTTPStatusError):
        details.append(f"status={exc.response.status_code}")
        try:
            details.append(f"response={exc.response.text[:200]}")
        except Exception:  # noqa: BLE001
            pass
    elif isinstance(exc, httpx.ConnectError):
        details.append("connection_failed")
        if hasattr(exc, "request"):
            details.append(f"url={exc.request.url}")
    elif isinstance(exc, httpx.TimeoutException):
        details.append("timeout")

    return f"{error_msg} ({', '.join(details)})" if details else error_msg


def can_start_tasks(manager_state: Dict[str, Any]) -> bool:
    """
    Check if registration tasks can be started.
    
    Args:
        manager_state: Manager state dictionary
        
    Returns:
        True if all required fields are set for task execution
    """
    return bool(
        manager_state.get("proxy_url")
        and manager_state.get("server_name")
        and manager_state.get("server_url")
    )

