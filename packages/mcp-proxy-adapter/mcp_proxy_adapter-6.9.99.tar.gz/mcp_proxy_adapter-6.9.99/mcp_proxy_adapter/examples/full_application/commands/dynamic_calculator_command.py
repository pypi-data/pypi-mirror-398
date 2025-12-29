"""
Dynamic Calculator Command
This module demonstrates a dynamically loaded command implementation for the full application example.
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class CalculatorResult(SuccessResult):
    """Result class for calculator command."""

    def __init__(self, operation: str, result: float, expression: str):
        """
        Initialize calculator result.

        Args:
            operation: Operation type (add, subtract, multiply, divide)
            result: Calculation result
            expression: Mathematical expression string
        """
        data = {
            "operation": operation,
            "result": result,
            "expression": expression,
        }
        super().__init__(data=data)


class DynamicCalculatorCommand(Command):
    """Dynamic calculator command implementation."""

    name = "calculator"
    descr = "Dynamic calculator command for basic arithmetic operations"

    async def execute(
        self, operation: str = None, a: float = None, b: float = None, **kwargs
    ) -> CalculatorResult:
        """Execute the calculator command."""
        if operation is None or a is None or b is None:
            return ErrorResult(
                message="operation, a, and b parameters are required",
                code=-32602,
            )

        try:
            a = float(a)
            b = float(b)
        except (ValueError, TypeError):
            return ErrorResult(
                message="a and b must be numbers",
                code=-32602,
            )

        if operation == "add":
            result = a + b
            expression = f"{a} + {b}"
        elif operation == "subtract":
            result = a - b
            expression = f"{a} - {b}"
        elif operation == "multiply":
            result = a * b
            expression = f"{a} * {b}"
        elif operation == "divide":
            if b == 0:
                return ErrorResult(
                    message="Division by zero is not allowed",
                    code=-32603,
                )
            result = a / b
            expression = f"{a} / {b}"
        else:
            return ErrorResult(
                message=f"Unknown operation: {operation}. Supported: add, subtract, multiply, divide",
                code=-32602,
            )
        return CalculatorResult(
            operation=operation, result=result, expression=expression
        )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "Arithmetic operation to perform",
                },
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["operation", "a", "b"],
            "additionalProperties": False,
        }
