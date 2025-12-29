"""Certificate Management Command

This module is kept for backward compatibility.
New code should import from mcp_proxy_adapter.commands.certificate instead.

Author: MCP Proxy Adapter Team
Version: 1.0.0
"""

from __future__ import annotations

# Re-export from new module structure for backward compatibility
from .certificate import CertificateManagementCommand, CertificateResult

__all__ = [
    "CertificateManagementCommand",
    "CertificateResult",
]
