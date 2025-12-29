"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Data models for registration context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class ProxyCredentials:
    """Client certificate and verification settings for proxy communication."""

    cert: Optional[Tuple[str, str]]
    verify: Union[bool, str]
    check_hostname: bool = True  # DNS/hostname verification flag


@dataclass
class RegistrationContext:
    """Prepared data required to register the adapter with a proxy."""

    server_name: str
    advertised_url: str
    proxy_url: str
    register_endpoint: str
    capabilities: List[str]
    metadata: Dict[str, Any]
    proxy_registration_config: Dict[str, Any]
    credentials: ProxyCredentials


@dataclass
class HeartbeatSettings:
    """Configuration for heartbeat scheduling."""

    interval: int
    url: str  # Full URL for heartbeat (e.g., "http://localhost:3005/proxy/heartbeat")

