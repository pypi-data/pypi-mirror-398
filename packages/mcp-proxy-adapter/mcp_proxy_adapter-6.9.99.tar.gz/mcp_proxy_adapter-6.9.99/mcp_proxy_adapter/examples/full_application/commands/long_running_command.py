"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Long-running command example with progress updates.

This command demonstrates:
- Queue-based execution (use_queue=True)
- Progress updates during execution
- Status changes during execution
- Final result output

CRITICAL FOR SPAWN MODE (CUDA compatibility):
--------------------------------------------
This command uses use_queue=True, which means it executes in a child process
when using multiprocessing spawn mode (required for CUDA).

IMPORTANT REGISTRATION REQUIREMENTS:
1. The command MUST be registered in the main process via registry.register()
2. The module containing this command SHOULD be registered for auto-import
   using register_auto_import_module() or register_custom_commands_hook()
3. When the module is imported in a child process, it should auto-register
   the command at module level (see example below)

MODULE-LEVEL AUTO-REGISTRATION EXAMPLE:
----------------------------------------
To ensure this command works in spawn mode, add this to your module's __init__.py
or main.py:

```python
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.examples.full_application.commands.long_running_command import LongRunningCommand

def _auto_register_commands():
    \"\"\"Auto-register commands when module is imported.\"\"\"
    try:
        registry.get_command("long_running_task")
    except KeyError:
        registry.register(LongRunningCommand, "custom")

# Execute on import
_auto_register_commands()
```

Alternatively, register the module path:
```python
from mcp_proxy_adapter.commands.hooks import register_auto_import_module
register_auto_import_module("mcp_proxy_adapter.examples.full_application.commands.long_running_command")
```

Or use hooks (module path is automatically extracted):
```python
from mcp_proxy_adapter.commands.hooks import register_custom_commands_hook

def register_commands(registry):
    registry.register(LongRunningCommand, "custom")

register_custom_commands_hook(register_commands)
```

ENVIRONMENT VARIABLE FALLBACK:
------------------------------
You can also set MCP_AUTO_REGISTER_MODULES environment variable:
export MCP_AUTO_REGISTER_MODULES="mcp_proxy_adapter.examples.full_application.commands.long_running_command"
"""

import asyncio
from typing import Any, Dict

from mcp_proxy_adapter.commands.base import Command, CommandResult


class LongRunningCommand(Command):
    """
    Long-running command that executes via queue with progress updates.

    This command:
    - Executes for about 1 minute
    - Updates progress and status during execution
    - Returns final result when completed
    """

    name = "long_running_task"
    version = "1.0.0"
    descr = "Long-running task with progress updates (executes via queue)"
    category = "examples"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"
    result_class = CommandResult
    use_queue = True  # Enable automatic queue execution

    async def execute(
        self,
        task_name: str = "default_task",
        duration: int = 60,
        steps: int = 10,
        **kwargs,
    ) -> CommandResult:
        """
        Execute long-running task with progress updates.

        Args:
            task_name: Name of the task
            duration: Duration in seconds (default: 60)
            steps: Number of steps for progress tracking (default: 10)
            **kwargs: Additional parameters including optional 'context'

        Returns:
            CommandResult with task completion information
        """
        # Note: Progress updates are handled by CommandExecutionJob
        # This command just simulates work - progress is tracked automatically

        step_duration = duration / steps

        # Simulate work with steps
        for i in range(steps):
            # Simulate work for each step
            await asyncio.sleep(step_duration)

            # Log progress (actual progress updates are done by CommandExecutionJob)
            # Progress = (i + 1) / steps * 100

        return CommandResult(
            success=True,
            data={
                "task_name": task_name,
                "duration": duration,
                "steps_completed": steps,
                "status": "completed",
                "message": f"Task '{task_name}' completed successfully after {duration} seconds",
            },
        )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters."""
        return {
            "type": "object",
            "properties": {
                "task_name": {
                    "type": "string",
                    "default": "default_task",
                    "description": "Name of the task",
                },
                "duration": {
                    "type": "integer",
                    "default": 60,
                    "minimum": 1,
                    "maximum": 300,
                    "description": "Task duration in seconds (1-300)",
                },
                "steps": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Number of steps for progress tracking (1-100)",
                },
            },
            "additionalProperties": False,
        }
