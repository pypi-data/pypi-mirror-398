"""
Commands package for full application example.
"""

# Note: Old commands (EchoCommand, ListCommand, HelpCommand) are not imported
# to avoid import errors. They use BaseCommand which doesn't exist.
# Use built-in commands from the framework instead.

from mcp_proxy_adapter.examples.full_application.commands.custom_echo_command import (
    CustomEchoCommand,
)
from mcp_proxy_adapter.examples.full_application.commands.dynamic_calculator_command import (
    DynamicCalculatorCommand,
)
from mcp_proxy_adapter.examples.full_application.commands.embed_queue_command import (
    EmbedQueueCommand,
)
from mcp_proxy_adapter.examples.full_application.commands.embed_job_status_command import (
    EmbedJobStatusCommand,
)
from mcp_proxy_adapter.examples.full_application.commands.slow_start_long_task_command import (
    SlowStartLongTaskCommand,
)

__all__ = [
    "CustomEchoCommand",
    "DynamicCalculatorCommand",
    "EmbedQueueCommand",
    "EmbedJobStatusCommand",
    "SlowStartLongTaskCommand",
]
