"""
Tests for error handling utilities.
"""

import pytest

from mcp_proxy_adapter.core.error_handling import (
    handle_command_errors,
    handle_sync_command_errors,
)
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class TestHandleCommandErrors:
    """Tests for handle_command_errors decorator."""

    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test decorator with successful operation."""
        @handle_command_errors("Test operation")
        async def test_func():
            return SuccessResult(data={"result": "success"})

        result = await test_func()
        assert isinstance(result, SuccessResult)
        assert result.data == {"result": "success"}

    @pytest.mark.asyncio
    async def test_failed_operation(self):
        """Test decorator with failed operation."""
        @handle_command_errors("Test operation")
        async def test_func():
            raise ValueError("Test error")

        result = await test_func()
        assert isinstance(result, ErrorResult)
        assert "Test operation failed" in result.message

    @pytest.mark.asyncio
    async def test_no_success_logging(self):
        """Test decorator without success logging."""
        @handle_command_errors("Test operation", log_success=False)
        async def test_func():
            return SuccessResult(data={"result": "success"})

        result = await test_func()
        assert isinstance(result, SuccessResult)


class TestHandleSyncCommandErrors:
    """Tests for handle_sync_command_errors decorator."""

    def test_successful_operation(self):
        """Test decorator with successful operation."""
        @handle_sync_command_errors("Test operation")
        def test_func():
            return SuccessResult(data={"result": "success"})

        result = test_func()
        assert isinstance(result, SuccessResult)
        assert result.data == {"result": "success"}

    def test_failed_operation(self):
        """Test decorator with failed operation."""
        @handle_sync_command_errors("Test operation")
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert isinstance(result, ErrorResult)
        assert "Test operation failed" in result.message

    def test_no_success_logging(self):
        """Test decorator without success logging."""
        @handle_sync_command_errors("Test operation", log_success=False)
        def test_func():
            return SuccessResult(data={"result": "success"})

        result = test_func()
        assert isinstance(result, SuccessResult)

