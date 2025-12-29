"""
Application Hooks
This module demonstrates application-level hooks in the full application example.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ApplicationHooks:
    """Application-level hooks."""

    @staticmethod
    def on_startup():
        """Hook called on application startup."""
        logger.info(f"Application started at {datetime.now()}")

    @staticmethod
    def on_shutdown():
        """Hook called on application shutdown."""
        logger.info(f"Application shutdown at {datetime.now()}")

    @staticmethod
    def before_request(request):
        """Hook called before processing request."""
        logger.debug(f"Before request: {request}")

    @staticmethod
    def after_request(request, response):
        """Hook called after processing request."""
        logger.debug(f"After request: {request}")

    @staticmethod
    def on_error(error):
        """Hook called on error."""
        logger.error(f"Error occurred: {error}")

    @staticmethod
    def before_command(command_name, **kwargs):
        """Hook called before command execution."""
        logger.info(f"Before command: {command_name}")

    @staticmethod
    def after_command(command_name, result, **kwargs):
        """Hook called after command execution."""
        logger.info(f"After command: {command_name}")
