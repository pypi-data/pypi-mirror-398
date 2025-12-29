"""
CLI Commands Module

This module contains all CLI commands for MCP Proxy Adapter.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from .generate import GenerateCommand
from .testconfig import TestConfigCommand
from .server import ServerCommand
from .sets import SetsCommand

__all__ = ['GenerateCommand', 'TestConfigCommand', 'ServerCommand', 'SetsCommand']
