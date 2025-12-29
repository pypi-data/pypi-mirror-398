"""
Example: Using Queue-Backed Commands with Fire-and-Forget Execution

This example demonstrates the new fire-and-forget execution mode for queue-backed
commands introduced in mcp-proxy-adapter 6.9.96+ with queuemgr 1.0.13+.

Key improvements:
- HTTP/JSON-RPC layer returns job_id immediately (no blocking on heavy work)
- All heavy processing happens inside queue worker processes
- Client can poll job status independently without HTTP timeout constraints
- Support for long-running operations (NLP pipelines, ML inference, etc.)

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
from typing import Dict, Any, Optional

from mcp_proxy_adapter.client.jsonrpc_client.client import JsonRpcClient


async def example_basic_queue_command():
    """
    Basic example: Execute a queue-backed command with automatic polling.

    The client submits the command once, receives job_id immediately,
    and then polls queue status until completion.
    """
    # Initialize client
    client = JsonRpcClient(
        protocol="http",
        host="127.0.0.1",
        port=8080,
    )

    try:
        # Execute command with auto_poll=True (default)
        # This will:
        #   1. Submit command via JSON-RPC
        #   2. Server enqueues job and returns job_id immediately
        #   3. Client automatically polls queue_get_job_status(job_id)
        #   4. Returns final result when job completes
        result = await client.execute_command_unified(
            command="chunk",  # Example: long-running NLP chunking command
            params={
                "text": "Your long text here...",
                "window": 3,
            },
            auto_poll=True,  # Automatically poll until completion
            poll_interval=1.0,  # Check status every 1 second
            timeout=600.0,  # Overall timeout: 10 minutes
        )

        # Result structure:
        # {
        #     "mode": "queued",
        #     "command": "chunk",
        #     "job_id": "abc-123-def-456",
        #     "status": "completed",
        #     "result": {...},  # Actual command result
        #     "queued": True
        # }
        print(f"Command completed: {result['status']}")
        print(f"Job ID: {result['job_id']}")
        print(f"Result: {result['result']}")

    except TimeoutError:
        print("Command timed out after 10 minutes")
    except RuntimeError as e:
        print(f"Command failed: {e}")
    finally:
        await client.close()


async def example_manual_polling():
    """
    Example: Manual polling for fine-grained control.

    Get job_id immediately, then poll status manually with custom logic.
    """
    client = JsonRpcClient(
        protocol="http",
        host="127.0.0.1",
        port=8080,
    )

    try:
        # Submit command without auto-polling
        result = await client.execute_command_unified(
            command="chunk",
            params={"text": "Long text...", "window": 3},
            auto_poll=False,  # Don't poll automatically
        )

        job_id = result["job_id"]
        print(f"Job submitted: {job_id}")

        # Manual polling loop with custom logic
        max_attempts = 100
        for attempt in range(max_attempts):
            status = await client.queue_get_job_status(job_id)

            current_status = status.get("status", "unknown")
            progress = status.get("progress", 0)
            description = status.get("description", "")

            print(
                f"Attempt {attempt + 1}: status={current_status}, progress={progress}%, {description}"
            )

            if current_status in ("completed", "failed", "stopped"):
                if current_status == "completed":
                    print(f"Job completed! Result: {status.get('result')}")
                else:
                    print(f"Job ended with status: {current_status}")
                break

            await asyncio.sleep(2.0)  # Poll every 2 seconds
        else:
            print("Max polling attempts reached")

    finally:
        await client.close()


async def example_with_progress_hook():
    """
    Example: Using status_hook for progress reporting.

    The status_hook callback is invoked after each poll, allowing
    you to implement custom progress reporting (e.g., progress bars).
    """
    client = JsonRpcClient(
        protocol="http",
        host="127.0.0.1",
        port=8080,
    )

    async def progress_callback(status: Dict[str, Any]) -> None:
        """Custom progress callback called after each status poll."""
        current_status = status.get("status", "unknown")
        progress = status.get("progress", 0)
        description = status.get("description", "")

        # Example: Update progress bar
        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = "=" * filled + "-" * (bar_length - filled)

        print(f"\r[{bar}] {progress}% - {description}", end="", flush=True)

        if current_status in ("completed", "failed", "stopped"):
            print()  # New line when done

    try:
        result = await client.execute_command_unified(
            command="chunk",
            params={"text": "Very long text...", "window": 3},
            auto_poll=True,
            poll_interval=0.5,  # Poll more frequently for smoother progress
            timeout=600.0,
            status_hook=progress_callback,  # Custom progress callback
        )

        print(f"\nFinal result: {result['result']}")

    finally:
        await client.close()


async def example_multiple_commands():
    """
    Example: Submitting multiple long-running commands in parallel.

    Since HTTP layer returns job_id immediately, you can submit
    many commands quickly and poll them all in parallel.
    """
    client = JsonRpcClient(
        protocol="http",
        host="127.0.0.1",
        port=8080,
    )

    try:
        # Submit multiple commands (all return job_id immediately)
        jobs = []
        texts = ["Text 1...", "Text 2...", "Text 3..."]

        for i, text in enumerate(texts):
            result = await client.execute_command_unified(
                command="chunk",
                params={"text": text, "window": 3},
                auto_poll=False,  # Get job_id only
            )
            jobs.append((i, result["job_id"]))
            print(f"Submitted job {i}: {result['job_id']}")

        # Poll all jobs in parallel
        async def poll_job(job_index: int, job_id: str) -> Dict[str, Any]:
            """Poll a single job until completion."""
            while True:
                status = await client.queue_get_job_status(job_id)
                current_status = status.get("status", "unknown")

                if current_status in ("completed", "failed", "stopped"):
                    return {"index": job_index, "job_id": job_id, "status": status}

                await asyncio.sleep(1.0)

        # Wait for all jobs to complete
        results = await asyncio.gather(*[poll_job(idx, jid) for idx, jid in jobs])

        for result in results:
            print(
                f"Job {result['index']} ({result['job_id']}): {result['status']['status']}"
            )

    finally:
        await client.close()


async def example_error_handling():
    """
    Example: Proper error handling for queue-backed commands.

    Demonstrates handling of:
    - Job submission failures
    - Job execution failures
    - Timeout errors
    - Network errors
    """
    client = JsonRpcClient(
        protocol="http",
        host="127.0.0.1",
        port=8080,
    )

    try:
        result = await client.execute_command_unified(
            command="chunk",
            params={"text": "Some text...", "window": 3},
            auto_poll=True,
            timeout=60.0,  # 1 minute timeout
        )

        # Check final status
        if result["status"] == "completed":
            print(f"Success: {result['result']}")
        elif result["status"] == "failed":
            # Job failed - check error details
            raw_status = result.get("raw_status", {})
            error = raw_status.get("error", "Unknown error")
            print(f"Job failed: {error}")
        else:
            print(f"Job ended with unexpected status: {result['status']}")

    except TimeoutError:
        # Polling exceeded timeout
        print("Job did not complete within timeout period")
        # You can still check job status manually if needed
        # status = await client.queue_get_job_status(job_id)

    except RuntimeError as e:
        # Job submission or execution error
        print(f"Error: {e}")

    except Exception as e:
        # Network errors, connection issues, etc.
        print(f"Unexpected error: {e}")

    finally:
        await client.close()


async def example_server_side_command():
    """
    Example: Creating a server-side command that uses queue.

    This shows how to define a command that will be executed via queue.
    """
    from mcp_proxy_adapter.commands.base import Command
    from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

    class ChunkCommand(Command):
        """Example command that processes long text in chunks."""

        name = "chunk"
        descr = "Chunk long text into smaller pieces"
        use_queue = True  # CRITICAL: Enable queue execution

        @classmethod
        def get_schema(cls) -> Dict[str, Any]:
            """Define command schema."""
            return {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to chunk",
                    },
                    "window": {
                        "type": "integer",
                        "description": "Window size for chunking",
                        "default": 3,
                    },
                },
                "required": ["text"],
            }

        async def execute(self, text: str, window: int = 3, **kwargs) -> Dict[str, Any]:
            """
            Execute chunking operation.

            This method runs inside a queue worker process, so it can
            take as long as needed without blocking HTTP requests.
            """
            # Heavy processing happens here
            # This runs in a separate process, not in the HTTP handler
            chunks = []
            words = text.split()

            for i in range(0, len(words), window):
                chunk = " ".join(words[i:i + window])
                chunks.append(chunk)

            return SuccessResult(
                data={
                    "chunks": chunks,
                    "total_chunks": len(chunks),
                    "text_length": len(text),
                }
            )

    # Register command (usually done via hooks or module imports)
    # from mcp_proxy_adapter.commands.command_registry import registry
    # registry.register(ChunkCommand, "custom")


async def main():
    """Run all examples."""
    print("=" * 80)
    print("Queue Fire-and-Forget Execution Examples")
    print("=" * 80)

    examples = [
        ("Basic Queue Command", example_basic_queue_command),
        ("Manual Polling", example_manual_polling),
        ("Progress Hook", example_with_progress_hook),
        ("Multiple Commands", example_multiple_commands),
        ("Error Handling", example_error_handling),
    ]

    for name, example_func in examples:
        print(f"\n{'=' * 80}")
        print(f"Example: {name}")
        print("=" * 80)
        try:
            await example_func()
        except Exception as e:
            print(f"Example failed: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
