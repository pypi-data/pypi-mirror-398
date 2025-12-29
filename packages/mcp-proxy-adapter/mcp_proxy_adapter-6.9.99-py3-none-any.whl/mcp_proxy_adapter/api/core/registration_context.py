"""Registration helper context builders for proxy interactions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Re-exports from mcp_proxy_adapter.api.core.registration.
"""

from __future__ import annotations

# Re-export from new module structure for backward compatibility
from .registration import (
    ProxyCredentials,
    RegistrationContext,
    HeartbeatSettings,
    prepare_registration_context,
    resolve_runtime_credentials,
    resolve_heartbeat_settings,
    resolve_unregister_endpoint,
)

__all__ = [
    "ProxyCredentials",
    "RegistrationContext",
    "HeartbeatSettings",
    "prepare_registration_context",
    "resolve_runtime_credentials",
    "resolve_heartbeat_settings",
    "resolve_unregister_endpoint",
]
