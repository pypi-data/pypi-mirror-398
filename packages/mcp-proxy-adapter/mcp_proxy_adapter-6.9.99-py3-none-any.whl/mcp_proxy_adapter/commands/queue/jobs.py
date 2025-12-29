"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Example job classes for queue management.
"""

import copyreg
import json
import os
import random
import time

import requests

from mcp_proxy_adapter.integrations.queuemgr_integration import QueueJobBase

# Note: registry is imported inside run() method to avoid pickle issues with module references


class DataProcessingJob(QueueJobBase):
    """Example data processing job."""

    def run(self) -> None:
        """Execute data processing job."""
        self.logger.info(f"DataProcessingJob {self.job_id}: Starting data processing")

        # Simulate processing
        data = self.mcp_params.get("data", {})
        operation = self.mcp_params.get("operation", "process")

        time.sleep(2)  # Simulate work

        result = {
            "job_id": self.job_id,
            "operation": operation,
            "processed_at": time.time(),
            "data_size": len(json.dumps(data)),
            "status": "completed",
        }

        self.set_mcp_result(result)


class FileOperationJob(QueueJobBase):
    """Example file operation job."""

    def run(self) -> None:
        """Execute file operation job."""
        self.logger.info(f"FileOperationJob {self.job_id}: Starting file operation")

        file_path = self.mcp_params.get("file_path", "")
        operation = self.mcp_params.get("operation", "read")

        try:
            if operation == "read" and os.path.exists(file_path):
                with open(file_path, "r") as f:
                    content = f.read()

                result = {
                    "job_id": self.job_id,
                    "operation": operation,
                    "file_path": file_path,
                    "file_size": len(content),
                    "status": "completed",
                }
            else:
                result = {
                    "job_id": self.job_id,
                    "operation": operation,
                    "file_path": file_path,
                    "error": f"File not found or invalid operation: {operation}",
                    "status": "failed",
                }

            self.set_mcp_result(result, result["status"])

        except Exception as e:
            self.set_mcp_error(f"File operation failed: {str(e)}")


class ApiCallJob(QueueJobBase):
    """Example API call job."""

    def run(self) -> None:
        """Execute API call job."""
        self.logger.info(f"ApiCallJob {self.job_id}: Starting API call")

        url = self.mcp_params.get("url", "")
        method = self.mcp_params.get("method", "GET")
        headers = self.mcp_params.get("headers", {})
        timeout = self.mcp_params.get("timeout", 30)
        verify_ssl = self.mcp_params.get("verify_ssl", True)
        cert_path = self.mcp_params.get("cert")
        key_path = self.mcp_params.get("key")
        cert_tuple = None
        if cert_path and key_path:
            cert_tuple = (cert_path, key_path)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
                verify=verify_ssl,
                cert=cert_tuple,
            )

            result = {
                "job_id": self.job_id,
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "response_size": len(response.content),
                "status": "completed",
            }

            self.set_mcp_result(result)

        except Exception as e:
            self.set_mcp_error(f"API call failed: {str(e)}")


class CustomJob(QueueJobBase):
    """Example custom job."""

    def run(self) -> None:
        """Execute custom job."""
        self.logger.info(f"CustomJob {self.job_id}: Starting custom job")

        # Custom job logic here
        time.sleep(1)  # Simulate work

        result = {
            "job_id": self.job_id,
            "custom_data": self.mcp_params.get("custom_data", {}),
            "status": "completed",
        }

        self.set_mcp_result(result)


class LongRunningJob(QueueJobBase):
    """Example long-running job with progress updates."""

    def run(self) -> None:
        """Execute long-running job with progress updates."""
        self.logger.info(f"LongRunningJob {self.job_id}: Starting long-running job")

        duration = self.mcp_params.get("duration", 10)  # Default 10 seconds
        task_type = self.mcp_params.get("task_type", "data_processing")

        self.set_status("running")
        self.set_description(f"Processing {task_type} task...")

        # Simulate long-running work with progress updates
        for i in range(duration):
            # Update progress
            progress = int((i + 1) / duration * 100)
            self.set_progress(progress)
            self.set_description(f"Processing {task_type} task... {progress}% complete")

            # Simulate work
            time.sleep(1)

            # Simulate occasional errors (5% chance)
            if random.random() < 0.05:
                self.set_mcp_error(f"Simulated error at {progress}%", "failed")
                return

        # Complete successfully
        result = {
            "job_id": self.job_id,
            "task_type": task_type,
            "duration": duration,
            "completed_at": time.time(),
            "status": "completed",
        }

        self.set_mcp_result(result)


class BatchProcessingJob(QueueJobBase):
    """Example batch processing job."""

    def run(self) -> None:
        """Execute batch processing job."""
        self.logger.info(f"BatchProcessingJob {self.job_id}: Starting batch processing")

        batch_size = self.mcp_params.get("batch_size", 100)
        items = self.mcp_params.get("items", [])

        self.set_status("running")
        self.set_description(f"Processing batch of {len(items)} items...")

        processed_items = []

        for i, item in enumerate(items):
            # Update progress
            progress = int((i + 1) / len(items) * 100)
            self.set_progress(progress)
            self.set_description(
                f"Processing item {i + 1}/{len(items)}... {progress}% complete"
            )

            # Simulate processing each item
            time.sleep(0.1)  # 100ms per item

            # Simulate processing result
            processed_item = {
                "original": item,
                "processed": f"processed_{item}",
                "timestamp": time.time(),
            }
            processed_items.append(processed_item)

            # Simulate occasional processing errors (2% chance)
            if random.random() < 0.02:
                self.set_mcp_error(
                    f"Processing failed at item {i + 1}: {item}", "failed"
                )
                return

        # Complete successfully
        result = {
            "job_id": self.job_id,
            "batch_size": batch_size,
            "processed_count": len(processed_items),
            "processed_items": processed_items,
            "completed_at": time.time(),
            "status": "completed",
        }

        self.set_mcp_result(result)


class PeriodicLoggingJob(QueueJobBase):
    """Job that writes messages to stdout every minute for testing log retrieval."""

    def run(self) -> None:
        """Execute periodic logging job."""
        import sys
        from datetime import datetime

        self.logger.info(f"PeriodicLoggingJob {self.job_id}: Starting periodic logging")

        # Get parameters
        duration_minutes = self.mcp_params.get("duration_minutes", 5)
        message_prefix = self.mcp_params.get("message_prefix", "Log message")
        interval_seconds = self.mcp_params.get("interval_seconds", 60)

        # Write initial message
        start_time = datetime.now()
        print(
            f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] {message_prefix} - Job started",
            file=sys.stdout,
            flush=True,
        )
        print(
            f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Job ID: {self.job_id}",
            file=sys.stdout,
            flush=True,
        )
        print(
            f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')}] Duration: {duration_minutes} minutes, Interval: {interval_seconds} seconds",
            file=sys.stdout,
            flush=True,
        )

        # Write periodic messages
        message_count = 0
        end_time = start_time.timestamp() + (duration_minutes * 60)

        while time.time() < end_time:
            current_time = datetime.now()
            message_count += 1
            message = f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] {message_prefix} #{message_count} - Job {self.job_id} is running"
            print(message, file=sys.stdout, flush=True)

            # Also write to stderr occasionally (every 3rd message)
            if message_count % 3 == 0:
                error_message = f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] DEBUG: Message #{message_count} (stderr output)"
                print(error_message, file=sys.stderr, flush=True)

            # Update progress
            elapsed = time.time() - start_time.timestamp()
            progress = int((elapsed / (duration_minutes * 60)) * 100)
            self.set_progress(min(progress, 99))
            self.set_description(f"Logging messages... {message_count} messages sent")

            # Wait for next interval
            time.sleep(interval_seconds)

        # Write final message
        end_time_obj = datetime.now()
        print(
            f"[{end_time_obj.strftime('%Y-%m-%d %H:%M:%S')}] {message_prefix} - Job completed",
            file=sys.stdout,
            flush=True,
        )
        print(
            f"[{end_time_obj.strftime('%Y-%m-%d %H:%M:%S')}] Total messages: {message_count}",
            file=sys.stdout,
            flush=True,
        )

        result = {
            "job_id": self.job_id,
            "started_at": start_time.isoformat(),
            "completed_at": end_time_obj.isoformat(),
            "duration_minutes": duration_minutes,
            "interval_seconds": interval_seconds,
            "total_messages": message_count,
            "status": "completed",
        }

        self.set_progress(100)
        self.set_description(f"Completed: {message_count} messages logged")
        self.set_mcp_result(result)


class CommandExecutionJob(QueueJobBase):
    """Job that executes any MCP command in the queue.

    This job is designed to work with multiprocessing spawn mode (required for CUDA).
    It only stores command name and parameters (not command class/instance) to avoid
    pickle errors with module references. Command is looked up by name in child process.
    """

    def __reduce_ex__(self, protocol):
        """
        Custom pickle reduction for spawn mode compatibility.

        This method ensures that only serializable data is pickled,
        avoiding module reference issues when using spawn mode with CUDA.

        Args:
            protocol: Pickle protocol version

        Returns:
            Tuple of (callable, args, state, listitems, dictitems) for pickle
        """
        # Get minimal state without non-serializable objects
        state = self.__dict__.copy()
        # Remove logger and registry references to avoid module serialization issues
        state.pop("logger", None)
        state.pop("_registry", None)
        # Process handle is recreated on start
        state.pop("_process", None)

        # Return reduction tuple: (callable, args, state, listitems, dictitems)
        # Use _rebuild_from_state as the callable to reconstruct the object
        return (
            CommandExecutionJob._rebuild_from_state,
            (self.job_id, self.mcp_params),
            state,
            None,
            None,
        )

    @staticmethod
    def _rebuild_from_state(job_id: str, params: dict, state: dict):
        """
        Rebuild CommandExecutionJob instance from pickled state.

        This is called in the child process after unpickling to restore
        the object state, including recreating the logger.

        Args:
            job_id: Job identifier
            params: Job parameters
            state: Additional state dictionary

        Returns:
            Reconstructed CommandExecutionJob instance
        """
        # Create new instance
        instance = object.__new__(CommandExecutionJob)
        instance.job_id = job_id
        instance.mcp_params = params

        # Restore state
        instance.__dict__.update(state)

        # Recreate logger in child process to avoid module reference issues
        from mcp_proxy_adapter.core.logging import get_global_logger

        instance.logger = get_global_logger()

        return instance

    def __getstate__(self):
        """Prepare minimal pickle state without non-serializable objects."""
        state = self.__dict__.copy()
        # Remove logger and registry references to avoid module serialization issues
        state.pop("logger", None)
        state.pop("_registry", None)
        # Process handle is recreated on start
        state.pop("_process", None)
        return state

    def __setstate__(self, state):
        """Restore state after unpickling - recreate logger in child process."""
        self.__dict__.update(state)
        # Recreate logger in child process to avoid module reference issues
        from mcp_proxy_adapter.core.logging import get_global_logger

        self.logger = get_global_logger()

    def run(self) -> None:
        """Execute command in queue with progress tracking.

        Command is looked up by name from registry in child process to avoid
        pickle errors with module references (e.g., CUDA modules).
        """
        import asyncio

        self.logger.info(
            f"CommandExecutionJob {self.job_id}: Starting command execution"
        )

        command_name = self.mcp_params.get("command")
        command_params = self.mcp_params.get("params", {}) or {}
        context = self.mcp_params.get("context", {})

        if not command_name:
            self.set_mcp_error("Command name is required")
            return

        try:
            # Import registry in child process to avoid pickle issues
            # This allows CUDA and other modules to be initialized fresh in child process
            from mcp_proxy_adapter.commands.command_registry import registry

            # CRITICAL FIX: Register custom commands in child process (spawn mode)
            # In spawn mode, child processes start with a fresh Python interpreter
            # and do not inherit the parent process's CommandRegistry state.
            # Custom commands registered via register_custom_commands_hook() in the
            # main process are not available in child processes because hook functions
            # cannot be pickled and transferred to child processes.
            #
            # Strategy:
            # 1. Use modules list passed from parent process via job parameters
            # 2. Import modules that were registered for auto-import (stored as strings)
            # 3. Modules should auto-register commands at import time (module-level registration)
            # 4. Also try to execute hooks if they're available (for backward compatibility)
            # 5. Support environment variable as fallback mechanism
            try:
                import importlib
                from mcp_proxy_adapter.commands.hooks import hooks

                # Get list of modules from job parameters (passed from parent process)
                # This is the primary source - modules are extracted from hooks in parent process
                auto_import_modules = self.mcp_params.get("auto_import_modules", [])

                if auto_import_modules:
                    self.logger.debug(
                        f"CommandExecutionJob {self.job_id}: Using {len(auto_import_modules)} modules "
                        f"from job parameters: {auto_import_modules[:3]}..."
                    )
                else:
                    # Fallback: try to get from hooks (for backward compatibility)
                    try:
                        auto_import_modules = hooks.get_auto_import_modules()
                        if auto_import_modules:
                            self.logger.debug(
                                f"CommandExecutionJob {self.job_id}: Using {len(auto_import_modules)} modules "
                                f"from hooks (fallback): {auto_import_modules[:3]}..."
                            )
                    except Exception:
                        pass

                # Also check environment variable as fallback
                env_modules = os.environ.get("MCP_AUTO_REGISTER_MODULES", "")
                if env_modules:
                    env_module_list = [
                        m.strip() for m in env_modules.split(",") if m.strip()
                    ]
                    for module_path in env_module_list:
                        if module_path not in auto_import_modules:
                            auto_import_modules.append(module_path)

                # Import all registered modules to trigger auto-registration
                imported_count = 0
                failed_imports = []
                for module_path in auto_import_modules:
                    try:
                        importlib.import_module(module_path)
                        imported_count += 1
                        self.logger.debug(
                            f"CommandExecutionJob {self.job_id}: Imported module for auto-registration: {module_path}"
                        )
                    except (ImportError, ModuleNotFoundError) as e:
                        # Enhanced logging for import failures
                        pythonpath = os.environ.get("PYTHONPATH", "not set")
                        sys_path_preview = sys.path[:5]  # First 5 entries
                        failed_imports.append(module_path)
                        self.logger.warning(
                            f"CommandExecutionJob {self.job_id}: Could not import module {module_path}: {e}\n"
                            f"  PYTHONPATH={pythonpath}\n"
                            f"  sys.path (first 5)={sys_path_preview}\n"
                            f"  This may cause 'Command not found' errors. "
                            f"Ensure the module's directory is in PYTHONPATH or use ensure_application_path()."
                        )
                        # Try to add module path to sys.path if we can find it
                        try:
                            from mcp_proxy_adapter.core.path_utils import (
                                ensure_module_path_in_syspath,
                            )

                            if ensure_module_path_in_syspath(module_path):
                                # Retry import
                                try:
                                    importlib.import_module(module_path)
                                    imported_count += 1
                                    self.logger.info(
                                        f"CommandExecutionJob {self.job_id}: Successfully imported {module_path} after adding to sys.path"
                                    )
                                    failed_imports.remove(module_path)
                                except Exception:
                                    pass  # Still failed
                        except Exception:
                            pass  # Path utils not available
                    except Exception as e:
                        self.logger.warning(
                            f"CommandExecutionJob {self.job_id}: Error importing module {module_path}: {e}"
                        )
                        failed_imports.append(module_path)

                if failed_imports:
                    self.logger.error(
                        f"CommandExecutionJob {self.job_id}: Failed to import {len(failed_imports)} modules: {failed_imports}. "
                        f"Commands from these modules may not be available in child process."
                    )

                # Also try to execute hooks if they're available (for backward compatibility)
                # Note: In spawn mode, hooks list is usually empty, but we try anyway
                hooks_count = hooks.execute_custom_commands_hooks(registry)

                # Option B: Try to reconstruct hooks from stored module paths and function names
                # This provides an additional mechanism if module-level auto-registration is not used
                reconstructed_count = 0
                try:
                    reconstructed_count = hooks.reconstruct_hooks(registry)
                    if reconstructed_count > 0:
                        self.logger.debug(
                            f"CommandExecutionJob {self.job_id}: Reconstructed {reconstructed_count} hooks in child process"
                        )
                except Exception as recon_error:
                    self.logger.debug(
                        f"CommandExecutionJob {self.job_id}: Hook reconstruction failed (this is OK if using module-level registration): {recon_error}"
                    )

                if imported_count > 0 or hooks_count > 0 or reconstructed_count > 0:
                    self.logger.debug(
                        f"CommandExecutionJob {self.job_id}: Registered commands in child process "
                        f"(imported {imported_count} modules, executed {hooks_count} hooks, reconstructed {reconstructed_count} hooks)"
                    )
            except Exception as hook_error:
                # Log but don't fail - commands may have been registered via module imports
                self.logger.warning(
                    f"CommandExecutionJob {self.job_id}: Failed to register commands in child process: {hook_error}"
                )

            # Get command class by name (not passed via pickle)
            command_class = registry.get_command(command_name)

            if command_class is None:
                self.set_mcp_error(f"Command '{command_name}' not found in registry")
                return

            # Set initial status
            self.set_status("running")
            self.set_description(f"Executing command: {command_name}")
            self.set_progress(0)

            # Execute command asynchronously with context and progress tracking
            async def _execute_with_progress():
                # Check if command has duration parameter for progress tracking
                duration = command_params.get("duration", 0)
                steps = command_params.get("steps", 10)

                if duration > 0 and steps > 0:
                    # Long-running command with progress updates
                    # Execute command in background and update progress in parallel
                    self.set_progress(5)
                    self.set_description(f"Starting {command_name}...")

                    # Create task for command execution
                    command_task = asyncio.create_task(
                        command_class.run(**command_params, context=context)
                    )

                    # Update progress while command is running
                    step_duration = max(0.1, duration / steps)
                    start_time = asyncio.get_event_loop().time()

                    for i in range(steps):
                        # Wait a bit
                        await asyncio.sleep(step_duration)

                        # Calculate progress based on time elapsed
                        elapsed = asyncio.get_event_loop().time() - start_time
                        progress = min(
                            90, int((elapsed / duration) * 90)
                        )  # Leave 10% for completion

                        self.set_progress(progress)
                        self.set_description(
                            f"Executing {command_name}: step {i + 1}/{steps} ({progress}%)"
                        )

                        # Check if command is done
                        if command_task.done():
                            break

                    # Wait for command to complete
                    self.set_progress(95)
                    self.set_description(f"Finalizing {command_name}...")
                    result = await command_task
                    self.set_progress(100)
                    self.set_description(f"Command {command_name} completed")
                    return result
                else:
                    # Regular command execution
                    self.set_progress(50)
                    self.set_description(f"Executing command: {command_name}")
                    result = await command_class.run(**command_params, context=context)
                    self.set_progress(100)
                    self.set_description(f"Command {command_name} completed")
                    return result

            # Run in event loop - handle both cases
            try:
                # Try to get existing event loop
                asyncio.get_running_loop()
                # If we're in an async context, we need to use a different approach
                # Create a new task in the existing loop
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(_execute_with_progress())
                    )
                    result_obj = future.result(timeout=300)  # 5 minute timeout
            except RuntimeError:
                # No event loop running, create new one
                result_obj = asyncio.run(_execute_with_progress())

            result_dict = (
                result_obj.to_dict()
                if hasattr(result_obj, "to_dict")
                else {"result": str(result_obj)}
            )

            self.set_mcp_result(
                {
                    "job_id": self.job_id,
                    "command": command_name,
                    "result": result_dict,
                    "status": "completed",
                }
            )
        except Exception as e:
            self.logger.exception(f"Command execution failed: {e}")
            self.set_mcp_error(f"Command execution failed: {str(e)}")


class FileDownloadJob(QueueJobBase):
    """Example file download job with progress tracking."""

    def run(self) -> None:
        """Execute file download job."""
        self.logger.info(f"FileDownloadJob {self.job_id}: Starting file download")

        url = self.mcp_params.get("url", "https://example.com/file.zip")
        file_size = self.mcp_params.get("file_size", 1024 * 1024)  # Default 1MB

        self.set_status("running")
        self.set_description(f"Downloading {url}...")

        # Simulate download with progress updates
        downloaded = 0
        chunk_size = 64 * 1024  # 64KB chunks

        while downloaded < file_size:
            # Simulate download chunk
            chunk = min(chunk_size, file_size - downloaded)
            time.sleep(0.1)  # Simulate network delay

            downloaded += chunk
            progress = int(downloaded / file_size * 100)

            self.set_progress(progress)
            self.set_description(
                f"Downloading {url}... {progress}% complete "
                f"({downloaded}/{file_size} bytes)"
            )

            # Simulate occasional network errors (3% chance)
            if random.random() < 0.03:
                self.set_mcp_error(
                    f"Network error during download at {progress}%", "failed"
                )
                return

        # Complete successfully
        result = {
            "job_id": self.job_id,
            "url": url,
            "file_size": file_size,
            "downloaded_bytes": downloaded,
            "completed_at": time.time(),
            "status": "completed",
        }

        self.set_mcp_result(result)


def _rebuild_command_execution_job_class(module_name: str, class_name: str):
    """
    Rebuild CommandExecutionJob class reference in child process.

    This function is called in the child process to get the class reference
    without trying to serialize the class definition, MRO, or base classes.

    Args:
        module_name: Module name where CommandExecutionJob is defined
        class_name: Class name (should be "CommandExecutionJob")

    Returns:
        CommandExecutionJob class
    """
    # Import the class in the child process
    # This ensures the class is available without serializing module references
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)


def _reduce_command_execution_job_class(obj):
    """
    Reduction function for CommandExecutionJob class serialization.

    This function is used by copyreg to control how the class is pickled.
    It returns a tuple that tells pickle how to reconstruct the class reference
    in the child process without trying to serialize module references.

    The key insight is that we use the module path and class name to reconstruct
    the class in the child process, avoiding serialization of the class definition
    and its MRO (Method Resolution Order) which may contain module references.

    Args:
        obj: CommandExecutionJob class or instance

    Returns:
        Tuple of (callable, args) for pickle to reconstruct class reference
    """
    # Get the class from object (handles both class and instance)
    cls = obj if isinstance(obj, type) else obj.__class__

    # Use named function (not lambda) to reconstruct the class in child process
    # This avoids serializing the class definition, MRO, and base classes
    # which may contain module references that cannot be pickled
    return (
        _rebuild_command_execution_job_class,
        (cls.__module__, cls.__name__),
    )


# Register the reduction function for CommandExecutionJob class
# This ensures pickle can serialize the class reference without module errors
# when using spawn mode (required for CUDA)
copyreg.pickle(CommandExecutionJob, _reduce_command_execution_job_class)
