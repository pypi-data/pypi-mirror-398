"""
Built-in Command Hooks
This module demonstrates hooks for built-in commands in the full application example.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BuiltinCommandHooks:
    """Hooks for built-in commands."""

    @staticmethod
    def before_health(command, **kwargs):
        """Hook before health command execution."""
        logger.info(f"Before health command at {datetime.now()}")

    @staticmethod
    def after_health(command, result, **kwargs):
        """Hook after health command execution."""
        logger.info(f"After health command at {datetime.now()}")

    @staticmethod
    def before_echo(command, **kwargs):
        """Hook before echo command execution."""
        logger.info(f"Before echo command at {datetime.now()}")

    @staticmethod
    def after_echo(command, result, **kwargs):
        """Hook after echo command execution."""
        logger.info(f"After echo command at {datetime.now()}")

    @staticmethod
    def before_help(command, **kwargs):
        """Hook before help command execution."""
        logger.info(f"Before help command at {datetime.now()}")

    @staticmethod
    def after_help(command, result, **kwargs):
        """Hook after help command execution."""
        logger.info(f"After help command at {datetime.now()}")
