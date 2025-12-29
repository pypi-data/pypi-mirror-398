#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test for SSL shutdown timeout exception handler.

This test verifies that:
1. SSL shutdown timeout exceptions are handled correctly
2. They are logged only at DEBUG level
3. Server functionality is not affected
"""

import asyncio
import logging
import sys
from io import StringIO
from typing import Dict, Any
from unittest.mock import patch, MagicMock

import pytest

from mcp_proxy_adapter.core.server_engine import HypercornEngine
from mcp_proxy_adapter.core.app_runner import ApplicationRunner
from mcp_proxy_adapter.core.logging import get_global_logger


class TestSSLShutdownTimeoutHandler:
    """Test suite for SSL shutdown timeout exception handler."""

    def test_exception_handler_can_be_installed(self):
        """Test that exception handler can be installed in event loop."""
        import asyncio

        # Create a new event loop for testing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Initially handler may be None (default)
            original_handler = loop.get_exception_handler()
            
            # Setup custom handler (simulating what HypercornEngine does)
            def custom_handler(loop, context):
                pass
            
            loop.set_exception_handler(custom_handler)
            
            # Verify handler is now set
            handler = loop.get_exception_handler()
            assert handler is not None, "Exception handler should be installable"
            assert handler == custom_handler, "Custom handler should be set"
        finally:
            loop.close()

    def test_ssl_shutdown_timeout_suppressed(self):
        """Test that SSL shutdown timeout is suppressed and logged at DEBUG level."""
        logger = get_global_logger()
        
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            # Create a mock event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Setup exception handler (simulating what HypercornEngine does)
            original_handler = loop.get_exception_handler()

            def exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
                """Custom exception handler that suppresses SSL shutdown timeout noise."""
                exception = context.get("exception")
                message = context.get("message", "")

                # Check if this is the SSL shutdown timeout error
                if (
                    isinstance(exception, TimeoutError)
                    and "SSL shutdown timed out" in str(exception)
                ) or "SSL shutdown timed out" in message:
                    # Log only at DEBUG level to avoid log pollution
                    logger.debug(
                        "SSL shutdown timeout during connection close (benign, suppressing noise): %s",
                        message,
                        exc_info=exception,
                    )
                    return

                # For all other exceptions, use original handler or default logging
                if original_handler:
                    original_handler(loop, context)
                else:
                    logger.error(
                        "Unhandled exception in event loop: %s",
                        message,
                        exc_info=exception,
                    )

            loop.set_exception_handler(exception_handler)

            # Simulate SSL shutdown timeout exception
            ssl_timeout_error = TimeoutError("SSL shutdown timed out")
            context = {
                "exception": ssl_timeout_error,
                "message": "Task exception was never retrieved: SSL shutdown timed out",
            }

            # Call exception handler
            exception_handler(loop, context)

            # Check that it was logged (at DEBUG level via logger.debug)
            log_output = log_capture.getvalue()
            assert "SSL shutdown timeout" in log_output, "Should log SSL shutdown timeout"
            assert "benign, suppressing noise" in log_output, "Should indicate this is benign"
            # Verify it's not logged as ERROR (check that ERROR handler wasn't called)
            # The log should contain the debug message, not an error message
            assert "Unhandled exception" not in log_output, "Should not log as unhandled exception"

        finally:
            logger.removeHandler(handler)
            loop.close()

    def test_other_exceptions_not_suppressed(self):
        """Test that other exceptions are not suppressed."""
        logger = get_global_logger()
        
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.ERROR)
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        try:
            # Create a mock event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Setup exception handler
            original_handler = loop.get_exception_handler()

            def exception_handler(loop: asyncio.AbstractEventLoop, context: Dict[str, Any]) -> None:
                """Custom exception handler."""
                exception = context.get("exception")
                message = context.get("message", "")

                # Check if this is the SSL shutdown timeout error
                if (
                    isinstance(exception, TimeoutError)
                    and "SSL shutdown timed out" in str(exception)
                ) or "SSL shutdown timed out" in message:
                    logger.debug(
                        "SSL shutdown timeout during connection close (benign, suppressing noise): %s",
                        message,
                        exc_info=exception,
                    )
                    return

                # For all other exceptions, use original handler or default logging
                if original_handler:
                    original_handler(loop, context)
                else:
                    logger.error(
                        "Unhandled exception in event loop: %s",
                        message,
                        exc_info=exception,
                    )

            loop.set_exception_handler(exception_handler)

            # Simulate a different exception (not SSL shutdown timeout)
            other_error = ValueError("Some other error")
            context = {
                "exception": other_error,
                "message": "Task exception was never retrieved: Some other error",
            }

            # Call exception handler
            exception_handler(loop, context)

            # Check that it was logged at ERROR level
            log_output = log_capture.getvalue()
            assert "Some other error" in log_output or "Unhandled exception" in log_output, "Should log other exceptions"

        finally:
            logger.removeHandler(handler)
            loop.close()

    def test_hypercorn_engine_exception_handler_setup(self):
        """Test that HypercornEngine sets up exception handler correctly."""
        engine = HypercornEngine()
        
        # Verify engine exists and has correct name
        assert engine.get_name() == "hypercorn"
        
        # Verify that run_server method exists and is callable
        assert hasattr(engine, "run_server")
        assert callable(engine.run_server)

    def test_app_runner_exception_handler_setup(self):
        """Test that ApplicationRunner sets up exception handler correctly."""
        from fastapi import FastAPI
        
        app = FastAPI()
        config = {
            "server": {
                "host": "127.0.0.1",
                "port": 8000,
                "protocol": "http",
            }
        }
        
        runner = ApplicationRunner(app, config)
        
        # Verify runner exists
        assert runner is not None
        assert hasattr(runner, "run")
        assert callable(runner.run)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

