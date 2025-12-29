"""
Test module for spawn mode registration testing.

This module is imported in child processes to test auto-registration.
"""

from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.base import Command, CommandResult


class TestSpawnCommand(Command):
    """Test command for spawn mode registration."""

    name = "test_spawn_command"
    descr = "Test command for spawn mode"
    use_queue = True

    async def execute(self, message: str = "test", **kwargs) -> CommandResult:
        """Execute test command."""
        return CommandResult(
            success=True, data={"message": message, "executed_in": "child_process"}
        )

    @classmethod
    def get_schema(cls):
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "default": "test",
                    "description": "Test message to return",
                }
            },
        }


def _auto_register_test_commands():
    """Auto-register test commands when module is imported."""
    try:
        registry.get_command("test_spawn_command")
    except KeyError:
        registry.register(TestSpawnCommand, "custom")


# Execute on import
_auto_register_test_commands()
