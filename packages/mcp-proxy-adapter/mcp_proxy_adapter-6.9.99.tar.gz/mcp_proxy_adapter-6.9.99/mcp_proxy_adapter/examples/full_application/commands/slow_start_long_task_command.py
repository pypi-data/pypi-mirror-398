"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Slow-start long-running command for testing fire-and-forget queue execution.

This command demonstrates:
- Slow startup phase (30-60 seconds) to test queuemgr start_job timeout handling
- Long execution phase (2-5 minutes) to test client polling
- Progress updates during both phases
- Proper error handling and status reporting

This command is specifically designed to test the fire-and-forget execution
mode introduced in mcp-proxy-adapter 6.9.96+ with queuemgr 1.0.13+.
"""

import asyncio
import time
from typing import Any, Dict

from mcp_proxy_adapter.commands.base import Command, CommandResult


class SlowStartLongTaskCommand(Command):
    """
    Command with slow startup and long execution for testing queue execution.

    This command:
    - Takes 30-60 seconds to initialize (startup_phase_duration)
    - Runs for 2-5 minutes (execution_phase_duration)
    - Updates progress during both phases
    - Tests fire-and-forget execution mode
    """

    name = "slow_start_long_task"
    version = "1.0.0"
    descr = "Slow-start long-running task for testing queue execution (slow init + long run)"
    category = "testing"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"
    result_class = CommandResult
    use_queue = True  # CRITICAL: Enable queue execution for fire-and-forget mode

    async def execute(
        self,
        task_name: str = "slow_task",
        startup_phase_duration: int = 45,
        execution_phase_duration: int = 180,
        startup_steps: int = 10,
        execution_steps: int = 20,
        **kwargs,
    ) -> CommandResult:
        """
        Execute slow-start long-running task.

        Args:
            task_name: Name of the task
            startup_phase_duration: Duration of startup phase in seconds (default: 45)
            execution_phase_duration: Duration of execution phase in seconds (default: 180 = 3 minutes)
            startup_steps: Number of steps in startup phase (default: 10)
            execution_steps: Number of steps in execution phase (default: 20)
            **kwargs: Additional parameters including optional 'context'

        Returns:
            CommandResult with task completion information
        """
        start_time = time.time()

        # PHASE 1: Slow startup (simulates heavy initialization)
        # This phase tests queuemgr start_job timeout handling
        startup_step_duration = startup_phase_duration / startup_steps

        for i in range(startup_steps):
            # Simulate initialization work (e.g., loading models, connecting to services)
            await asyncio.sleep(startup_step_duration)

            # Progress: 0-40% during startup
            progress = int((i + 1) / startup_steps * 40)

        startup_completed = time.time()
        startup_elapsed = startup_completed - start_time

        # PHASE 2: Long execution (simulates heavy processing)
        # This phase tests client polling and timeout handling
        execution_step_duration = execution_phase_duration / execution_steps

        for i in range(execution_steps):
            # Simulate processing work (e.g., NLP pipeline, ML inference)
            await asyncio.sleep(execution_step_duration)

            # Progress: 40-100% during execution
            progress = int(40 + (i + 1) / execution_steps * 60)

        total_elapsed = time.time() - start_time

        return CommandResult(
            success=True,
            data={
                "task_name": task_name,
                "startup_phase_duration": startup_phase_duration,
                "execution_phase_duration": execution_phase_duration,
                "startup_elapsed": round(startup_elapsed, 2),
                "execution_elapsed": round(total_elapsed - startup_elapsed, 2),
                "total_elapsed": round(total_elapsed, 2),
                "startup_steps": startup_steps,
                "execution_steps": execution_steps,
                "status": "completed",
                "message": (
                    f"Task '{task_name}' completed successfully. "
                    f"Startup: {startup_elapsed:.1f}s, Execution: {total_elapsed - startup_elapsed:.1f}s, "
                    f"Total: {total_elapsed:.1f}s"
                ),
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
                    "default": "slow_task",
                    "description": "Name of the task",
                },
                "startup_phase_duration": {
                    "type": "integer",
                    "default": 45,
                    "minimum": 1,
                    "maximum": 120,
                    "description": "Startup phase duration in seconds (1-120). "
                    "Simulates slow initialization (e.g., model loading).",
                },
                "execution_phase_duration": {
                    "type": "integer",
                    "default": 180,
                    "minimum": 30,
                    "maximum": 600,
                    "description": "Execution phase duration in seconds (30-600). "
                    "Simulates long-running processing (e.g., NLP pipeline).",
                },
                "startup_steps": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Number of steps in startup phase (1-50)",
                },
                "execution_steps": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Number of steps in execution phase (1-100)",
                },
            },
            "additionalProperties": False,
        }
