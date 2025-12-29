"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Registration management package for MCP Proxy Adapter API.
"""

from .manager import RegistrationManager
from .status import (
    get_registration_status,
    set_registration_status,
    get_stop_flag,
    set_stop_flag,
    set_stop_flag_sync,
)

__all__ = [
    "RegistrationManager",
    "get_registration_status",
    "set_registration_status",
    "get_stop_flag",
    "set_stop_flag",
    "set_stop_flag_sync",
]

