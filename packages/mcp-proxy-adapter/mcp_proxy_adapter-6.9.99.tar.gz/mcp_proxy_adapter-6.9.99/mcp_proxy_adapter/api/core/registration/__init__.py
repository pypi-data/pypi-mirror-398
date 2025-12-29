"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Registration context package for proxy interactions.
"""

from .models import ProxyCredentials, RegistrationContext, HeartbeatSettings
from .context_builder import prepare_registration_context
from .resolvers import (
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


