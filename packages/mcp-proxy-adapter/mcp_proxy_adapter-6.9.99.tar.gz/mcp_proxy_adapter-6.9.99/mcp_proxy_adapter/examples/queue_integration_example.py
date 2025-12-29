"""
Queue Integration Example for MCP Proxy Adapter.

This example demonstrates how to use the queuemgr integration
with mcp_proxy_adapter for managing background jobs.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import time

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.queue_commands import (
    QueueAddJobCommand,
    QueueStartJobCommand,
    QueueStopJobCommand,
    QueueDeleteJobCommand,
    QueueGetJobStatusCommand,
    QueueListJobsCommand,
    QueueHealthCommand,
)
from mcp_proxy_adapter.integrations.queuemgr_integration import (
    init_global_queue_manager,
    shutdown_global_queue_manager,
    QueueManagerIntegration,
    queue_manager_context,
    QueueJobBase,
)


async def setup_queue_commands():
    """Setup queue management commands."""
    print("🔧 Setting up queue management commands...")
    
    # Register queue commands
    registry.register(QueueAddJobCommand())
    registry.register(QueueStartJobCommand())
    registry.register(QueueStopJobCommand())
    registry.register(QueueDeleteJobCommand())
    registry.register(QueueGetJobStatusCommand())
    registry.register(QueueListJobsCommand())
    registry.register(QueueHealthCommand())
    
    print("✅ Queue commands registered")


async def demo_queue_operations():
    """Demonstrate queue operations with long-running jobs."""
    print("\n🚀 Demonstrating queue operations with long-running jobs...")
    
    # Initialize queue manager
    queue_manager = await init_global_queue_manager(
        registry_path="demo_queue_registry.jsonl",
        shutdown_timeout=30.0,
        max_concurrent_jobs=5
    )
    
    try:
        # 1. Add various types of jobs
        print("\n1️⃣ Adding jobs to queue...")
        
        # Quick data processing job
        data_job_result = await queue_manager.add_job(
            DataProcessingJob,
            "data_job_1",
            {
                "data": {"key1": "value1", "key2": "value2"},
                "operation": "process"
            }
        )
        print(f"✅ Added data processing job: {data_job_result.job_id}")
        
        # Long-running job (15 seconds)
        long_job_result = await queue_manager.add_job(
            LongRunningJob,
            "long_job_1",
            {
                "duration": 15,
                "task_type": "data_analysis"
            }
        )
        print(f"✅ Added long-running job: {long_job_result.job_id}")
        
        # Batch processing job
        batch_job_result = await queue_manager.add_job(
            BatchProcessingJob,
            "batch_job_1",
            {
                "batch_size": 50,
                "items": [f"item_{i}" for i in range(50)]
            }
        )
        print(f"✅ Added batch processing job: {batch_job_result.job_id}")
        
        # File download job
        download_job_result = await queue_manager.add_job(
            FileDownloadJob,
            "download_job_1",
            {
                "url": "https://example.com/large_file.zip",
                "file_size": 5 * 1024 * 1024  # 5MB
            }
        )
        print(f"✅ Added file download job: {download_job_result.job_id}")
        
        # 2. Start jobs
        print("\n2️⃣ Starting jobs...")
        
        await queue_manager.start_job("data_job_1")
        print("✅ Started data processing job")
        
        await queue_manager.start_job("long_job_1")
        print("✅ Started long-running job")
        
        await queue_manager.start_job("batch_job_1")
        print("✅ Started batch processing job")
        
        await queue_manager.start_job("download_job_1")
        print("✅ Started file download job")
        
        # 3. Monitor job status with detailed progress
        print("\n3️⃣ Monitoring job status with progress...")
        
        for i in range(20):  # Monitor for 20 iterations
            print(f"\n--- Status check {i+1} ---")
            
            # Check individual job status
            jobs_to_check = ["data_job_1", "long_job_1", "batch_job_1", "download_job_1"]
            
            for job_id in jobs_to_check:
                try:
                    status = await queue_manager.get_job_status(job_id)
                    print(f"{job_id}: {status.status} (progress: {status.progress}%) - {status.description}")
                    
                    if status.error:
                        print(f"  ❌ Error: {status.error}")
                except Exception as e:
                    print(f"{job_id}: Error getting status - {e}")
            
            # List all jobs summary
            all_jobs = await queue_manager.list_jobs()
            running_jobs = [job for job in all_jobs if job.status == "running"]
            completed_jobs = [job for job in all_jobs if job.status == "completed"]
            failed_jobs = [job for job in all_jobs if job.status == "failed"]
            
            print(f"📊 Summary: {len(running_jobs)} running, {len(completed_jobs)} completed, {len(failed_jobs)} failed")
            
            # Check if all jobs are done
            if len(running_jobs) == 0:
                print("✅ All jobs completed!")
                break
            
            await asyncio.sleep(1)  # Check every second
        
        # 4. Get detailed job results
        print("\n4️⃣ Getting detailed job results...")
        
        for job_id in ["data_job_1", "long_job_1", "batch_job_1", "download_job_1"]:
            try:
                status = await queue_manager.get_job_status(job_id)
                print(f"\n📋 {job_id} Results:")
                print(f"  Status: {status.status}")
                print(f"  Progress: {status.progress}%")
                print(f"  Description: {status.description}")
                
                if status.result:
                    print(f"  Result: {json.dumps(status.result, indent=4)}")
                
                if status.error:
                    print(f"  Error: {status.error}")
                    
            except Exception as e:
                print(f"❌ Error getting results for {job_id}: {e}")
        
        # 5. Check queue health
        print("\n5️⃣ Checking queue health...")
        
        health = await queue_manager.get_queue_health()
        print(f"Queue health: {json.dumps(health, indent=2)}")
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await shutdown_global_queue_manager()
        print("✅ Queue manager stopped")


async def demo_with_context_manager():
    """Demonstrate using queue manager with context manager."""
    print("\n🔄 Demonstrating context manager usage...")
    
    async with queue_manager_context(
        registry_path="demo_context_registry.jsonl",
        shutdown_timeout=30.0,
        max_concurrent_jobs=3
    ) as queue_manager:
        
        # Add and start a job
        result = await queue_manager.add_job(
            CustomJob,
            "context_job_1",
            {"custom_data": {"test": "value"}}
        )
        print(f"✅ Added job: {result.job_id}")
        
        await queue_manager.start_job("context_job_1")
        print("✅ Started job")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check status
        status = await queue_manager.get_job_status("context_job_1")
        print(f"Job status: {status.status}")
        
        if status.result:
            print(f"Job result: {json.dumps(status.result, indent=2)}")
    
    print("✅ Context manager cleanup completed")


def create_mcp_app_with_queue():
    """Create MCP application with queue integration."""
    app = create_app()
    
    # Setup startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        await setup_queue_commands()
        await init_global_queue_manager()
        print("✅ MCP application with queue integration started")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await shutdown_global_queue_manager()
        print("✅ MCP application with queue integration stopped")
    
    return app


async def main():
    """Main function to run the queue integration example."""
    print("🚀 MCP Proxy Adapter Queue Integration Example")
    print("=" * 50)
    
    # Demo 1: Basic queue operations
    await demo_queue_operations()
    
    # Demo 2: Context manager usage
    await demo_with_context_manager()
    
    print("\n🎉 Queue integration example completed!")
    print("\n📋 Available queue commands:")
    print("  - queue_add_job: Add a job to the queue")
    print("  - queue_start_job: Start a job")
    print("  - queue_stop_job: Stop a job")
    print("  - queue_delete_job: Delete a job")
    print("  - queue_get_job_status: Get job status")
    print("  - queue_list_jobs: List all jobs")
    print("  - queue_health: Check queue health")
    
    print("\n📝 Example JSON-RPC calls:")
    print("1. Add a data processing job:")
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "queue_add_job",
        "params": {
            "job_type": "data_processing",
            "job_id": "my_data_job",
            "params": {
                "data": {"key": "value"},
                "operation": "process"
            }
        },
        "id": 1
    }, indent=2))
    
    print("\n2. Start the job:")
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "queue_start_job",
        "params": {
            "job_id": "my_data_job"
        },
        "id": 2
    }, indent=2))
    
    print("\n3. Check job status:")
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "queue_get_job_status",
        "params": {
            "job_id": "my_data_job"
        },
        "id": 3
    }, indent=2))


# Example job classes
class DataProcessingJob(QueueJobBase):
    """Example data processing job."""
    
    def run(self) -> None:
        """Execute data processing job."""
        import time
        import json
        
        self.logger.info(f"DataProcessingJob {self.job_id}: Starting data processing")
        
        data = self.mcp_params.get("data", {})
        operation = self.mcp_params.get("operation", "process")
        
        # Simulate processing
        time.sleep(2)
        
        result = {
            "job_id": self.job_id,
            "operation": operation,
            "processed_at": time.time(),
            "data_size": len(json.dumps(data)),
            "status": "completed"
        }
        
        self.set_mcp_result(result)


class FileOperationJob(QueueJobBase):
    """Example file operation job."""
    
    def run(self) -> None:
        """Execute file operation job."""
        import os
        import time
        
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
                    "status": "completed"
                }
            else:
                result = {
                    "job_id": self.job_id,
                    "operation": operation,
                    "file_path": file_path,
                    "error": f"File not found or invalid operation: {operation}",
                    "status": "failed"
                }
            
            self.set_mcp_result(result, result["status"])
            
        except Exception as e:
            self.set_mcp_error(f"File operation failed: {str(e)}")


class ApiCallJob(QueueJobBase):
    """Example API call job."""
    
    def run(self) -> None:
        """Execute API call job."""
        import requests
        import time
        
        self.logger.info(f"ApiCallJob {self.job_id}: Starting API call")
        
        url = self.mcp_params.get("url", "")
        method = self.mcp_params.get("method", "GET")
        headers = self.mcp_params.get("headers", {})
        timeout = self.mcp_params.get("timeout", 30)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout
            )
            
            result = {
                "job_id": self.job_id,
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "response_size": len(response.content),
                "status": "completed"
            }
            
            self.set_mcp_result(result)
            
        except Exception as e:
            self.set_mcp_error(f"API call failed: {str(e)}")


class CustomJob(QueueJobBase):
    """Example custom job."""
    
    def run(self) -> None:
        """Execute custom job."""
        import time
        
        self.logger.info(f"CustomJob {self.job_id}: Starting custom job")
        
        custom_data = self.mcp_params.get("custom_data", {})
        
        # Simulate work
        time.sleep(1)
        
        result = {
            "job_id": self.job_id,
            "custom_data": custom_data,
            "processed_at": time.time(),
            "status": "completed"
        }
        
        self.set_mcp_result(result)


class LongRunningJob(QueueJobBase):
    """Example long-running job with progress updates."""
    
    def run(self) -> None:
        """Execute long-running job with progress updates."""
        import time
        import random
        
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
            "status": "completed"
        }
        
        self.set_mcp_result(result)


class BatchProcessingJob(QueueJobBase):
    """Example batch processing job."""
    
    def run(self) -> None:
        """Execute batch processing job."""
        import time
        import random
        
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
            self.set_description(f"Processing item {i+1}/{len(items)}... {progress}% complete")
            
            # Simulate processing each item
            time.sleep(0.1)  # 100ms per item
            
            # Simulate processing result
            processed_item = {
                "original": item,
                "processed": f"processed_{item}",
                "timestamp": time.time()
            }
            processed_items.append(processed_item)
            
            # Simulate occasional processing errors (2% chance)
            if random.random() < 0.02:
                self.set_mcp_error(f"Processing failed at item {i+1}: {item}", "failed")
                return
        
        # Complete successfully
        result = {
            "job_id": self.job_id,
            "batch_size": batch_size,
            "processed_count": len(processed_items),
            "processed_items": processed_items,
            "completed_at": time.time(),
            "status": "completed"
        }
        
        self.set_mcp_result(result)


class FileDownloadJob(QueueJobBase):
    """Example file download job with progress tracking."""
    
    def run(self) -> None:
        """Execute file download job."""
        import time
        import random
        
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
            self.set_description(f"Downloading {url}... {progress}% complete ({downloaded}/{file_size} bytes)")
            
            # Simulate occasional network errors (3% chance)
            if random.random() < 0.03:
                self.set_mcp_error(f"Network error during download at {progress}%", "failed")
                return
        
        # Complete successfully
        result = {
            "job_id": self.job_id,
            "url": url,
            "file_size": file_size,
            "downloaded_bytes": downloaded,
            "completed_at": time.time(),
            "status": "completed"
        }
        
        self.set_mcp_result(result)


if __name__ == "__main__":
    asyncio.run(main())
