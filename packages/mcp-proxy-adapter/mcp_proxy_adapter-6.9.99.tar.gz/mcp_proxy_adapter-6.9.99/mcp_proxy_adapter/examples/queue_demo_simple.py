#!/usr/bin/env python3
"""
Simple Queue Demo for MCP Proxy Adapter.

This example demonstrates the queue integration concepts
without requiring the queuemgr dependency.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import json
import time
from typing import Dict, Any, List

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
    QueueJobStatus,
    QueueJobResult,
    QueueJobError,
)


class MockQueueManager:
    """Mock queue manager for demonstration purposes."""
    
    def __init__(self):
        """Initialize mock queue storage."""
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.running = True
    
    async def add_job(self, job_class, job_id: str, params: Dict[str, Any]) -> QueueJobResult:
        """Add a job to the mock queue."""
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": QueueJobStatus.PENDING,
            "params": params,
            "result": None,
            "error": None,
            "progress": 0,
            "description": "Job added to queue"
        }
        return QueueJobResult(
            job_id=job_id,
            status=QueueJobStatus.PENDING,
            description="Job added to queue"
        )
    
    async def start_job(self, job_id: str) -> QueueJobResult:
        """Start a job in the mock queue."""
        if job_id not in self.jobs:
            raise QueueJobError(job_id, "Job not found")
        
        self.jobs[job_id]["status"] = QueueJobStatus.RUNNING
        self.jobs[job_id]["description"] = "Job started"
        
        # Simulate job execution in background
        asyncio.create_task(self._simulate_job_execution(job_id))
        
        return QueueJobResult(
            job_id=job_id,
            status=QueueJobStatus.RUNNING,
            description="Job started"
        )
    
    async def stop_job(self, job_id: str) -> QueueJobResult:
        """Stop a job in the mock queue."""
        if job_id not in self.jobs:
            raise QueueJobError(job_id, "Job not found")
        
        self.jobs[job_id]["status"] = QueueJobStatus.STOPPED
        self.jobs[job_id]["description"] = "Job stopped"
        
        return QueueJobResult(
            job_id=job_id,
            status=QueueJobStatus.STOPPED,
            description="Job stopped"
        )
    
    async def delete_job(self, job_id: str) -> QueueJobResult:
        """Delete a job from the mock queue."""
        if job_id not in self.jobs:
            raise QueueJobError(job_id, "Job not found")
        
        del self.jobs[job_id]
        
        return QueueJobResult(
            job_id=job_id,
            status=QueueJobStatus.DELETED,
            description="Job deleted"
        )
    
    async def get_job_status(self, job_id: str) -> QueueJobResult:
        """Get job status from the mock queue."""
        if job_id not in self.jobs:
            raise QueueJobError(job_id, "Job not found")
        
        job = self.jobs[job_id]
        return QueueJobResult(
            job_id=job_id,
            status=job["status"],
            result=job["result"],
            error=job["error"],
            progress=job["progress"],
            description=job["description"]
        )
    
    async def list_jobs(self) -> List[QueueJobResult]:
        """List all jobs in the mock queue."""
        results = []
        for job_id, job in self.jobs.items():
            results.append(QueueJobResult(
                job_id=job_id,
                status=job["status"],
                result=job["result"],
                error=job["error"],
                progress=job["progress"],
                description=job["description"]
            ))
        return results
    
    async def get_queue_health(self) -> Dict[str, Any]:
        """Get queue health information."""
        running_jobs = sum(1 for job in self.jobs.values() if job["status"] == QueueJobStatus.RUNNING)
        completed_jobs = sum(1 for job in self.jobs.values() if job["status"] == QueueJobStatus.COMPLETED)
        failed_jobs = sum(1 for job in self.jobs.values() if job["status"] == QueueJobStatus.FAILED)
        
        return {
            "status": "healthy" if self.running else "unhealthy",
            "running": self.running,
            "total_jobs": len(self.jobs),
            "running_jobs": running_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "registry_path": "mock_registry.jsonl",
            "max_concurrent_jobs": 10,
        }
    
    async def _simulate_job_execution(self, job_id: str):
        """Simulate job execution with progress updates."""
        job = self.jobs[job_id]
        params = job["params"]
        job_type = params.get("job_type", "custom")
        
        try:
            # Simulate different job types
            if job_type == "long_running":
                duration = params.get("duration", 10)
                await self._simulate_long_running_job(job_id, duration)
            elif job_type == "batch_processing":
                items = params.get("items", [])
                await self._simulate_batch_processing_job(job_id, items)
            elif job_type == "file_download":
                file_size = params.get("file_size", 1024 * 1024)
                await self._simulate_file_download_job(job_id, file_size)
            else:
                await self._simulate_simple_job(job_id)
                
        except Exception as e:
            self.jobs[job_id]["status"] = QueueJobStatus.FAILED
            self.jobs[job_id]["error"] = str(e)
            self.jobs[job_id]["description"] = f"Job failed: {str(e)}"
    
    async def _simulate_simple_job(self, job_id: str):
        """Simulate a simple job."""
        job = self.jobs[job_id]
        
        # Update progress
        for i in range(5):
            progress = (i + 1) * 20
            job["progress"] = progress
            job["description"] = f"Processing... {progress}% complete"
            await asyncio.sleep(0.5)
        
        # Complete job
        job["status"] = QueueJobStatus.COMPLETED
        job["progress"] = 100
        job["description"] = "Job completed successfully"
        job["result"] = {
            "job_id": job_id,
            "completed_at": time.time(),
            "status": "completed"
        }
    
    async def _simulate_long_running_job(self, job_id: str, duration: int):
        """Simulate a long-running job."""
        job = self.jobs[job_id]
        task_type = job["params"].get("task_type", "data_processing")
        
        for i in range(duration):
            progress = int((i + 1) / duration * 100)
            job["progress"] = progress
            job["description"] = f"Processing {task_type} task... {progress}% complete"
            await asyncio.sleep(1)
        
        # Complete job
        job["status"] = QueueJobStatus.COMPLETED
        job["progress"] = 100
        job["description"] = f"{task_type} task completed"
        job["result"] = {
            "job_id": job_id,
            "task_type": task_type,
            "duration": duration,
            "completed_at": time.time(),
            "status": "completed"
        }
    
    async def _simulate_batch_processing_job(self, job_id: str, items: List[str]):
        """Simulate a batch processing job."""
        job = self.jobs[job_id]
        processed_items = []
        
        for i, item in enumerate(items):
            progress = int((i + 1) / len(items) * 100)
            job["progress"] = progress
            job["description"] = f"Processing item {i+1}/{len(items)}... {progress}% complete"
            
            # Simulate processing
            await asyncio.sleep(0.1)
            
            processed_items.append({
                "original": item,
                "processed": f"processed_{item}",
                "timestamp": time.time()
            })
        
        # Complete job
        job["status"] = QueueJobStatus.COMPLETED
        job["progress"] = 100
        job["description"] = f"Batch processing completed ({len(processed_items)} items)"
        job["result"] = {
            "job_id": job_id,
            "processed_count": len(processed_items),
            "processed_items": processed_items,
            "completed_at": time.time(),
            "status": "completed"
        }
    
    async def _simulate_file_download_job(self, job_id: str, file_size: int):
        """Simulate a file download job."""
        job = self.jobs[job_id]
        url = job["params"].get("url", "https://example.com/file.zip")
        
        downloaded = 0
        chunk_size = 64 * 1024  # 64KB chunks
        
        while downloaded < file_size:
            chunk = min(chunk_size, file_size - downloaded)
            await asyncio.sleep(0.1)  # Simulate network delay
            
            downloaded += chunk
            progress = int(downloaded / file_size * 100)
            
            job["progress"] = progress
            job["description"] = f"Downloading {url}... {progress}% complete ({downloaded}/{file_size} bytes)"
        
        # Complete job
        job["status"] = QueueJobStatus.COMPLETED
        job["progress"] = 100
        job["description"] = f"Download completed ({file_size} bytes)"
        job["result"] = {
            "job_id": job_id,
            "url": url,
            "file_size": file_size,
            "downloaded_bytes": downloaded,
            "completed_at": time.time(),
            "status": "completed"
        }


# Global mock queue manager
mock_queue_manager = MockQueueManager()


class MockQueueCommands:
    """Mock queue commands that use the mock queue manager."""
    
    @staticmethod
    async def add_job(params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a job to the mock queue."""
        job_type = params.get("job_type")
        job_id = params.get("job_id")
        job_params = params.get("params", {})
        
        if not job_type or not job_id:
            return {
                "success": False,
                "error": "job_type and job_id are required"
            }
        
        # Add job_type to params for simulation
        job_params["job_type"] = job_type
        
        result = await mock_queue_manager.add_job(None, job_id, job_params)
        
        return {
            "success": True,
            "data": {
                "message": f"Job {job_id} added successfully",
                "job_id": job_id,
                "job_type": job_type,
                "status": result.status,
                "description": result.description
            }
        }
    
    @staticmethod
    async def start_job(params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a job in the mock queue."""
        job_id = params.get("job_id")
        
        if not job_id:
            return {
                "success": False,
                "error": "job_id is required"
            }
        
        result = await mock_queue_manager.start_job(job_id)
        
        return {
            "success": True,
            "data": {
                "message": f"Job {job_id} started successfully",
                "job_id": job_id,
                "status": result.status,
                "description": result.description
            }
        }
    
    @staticmethod
    async def stop_job(params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a job in the mock queue."""
        job_id = params.get("job_id")
        
        if not job_id:
            return {
                "success": False,
                "error": "job_id is required"
            }
        
        result = await mock_queue_manager.stop_job(job_id)
        
        return {
            "success": True,
            "data": {
                "message": f"Job {job_id} stopped successfully",
                "job_id": job_id,
                "status": result.status,
                "description": result.description
            }
        }
    
    @staticmethod
    async def delete_job(params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a job from the mock queue."""
        job_id = params.get("job_id")
        
        if not job_id:
            return {
                "success": False,
                "error": "job_id is required"
            }
        
        result = await mock_queue_manager.delete_job(job_id)
        
        return {
            "success": True,
            "data": {
                "message": f"Job {job_id} deleted successfully",
                "job_id": job_id,
                "status": result.status,
                "description": result.description
            }
        }
    
    @staticmethod
    async def get_job_status(params: Dict[str, Any]) -> Dict[str, Any]:
        """Get job status from the mock queue."""
        job_id = params.get("job_id")
        
        if not job_id:
            return {
                "success": False,
                "error": "job_id is required"
            }
        
        result = await mock_queue_manager.get_job_status(job_id)
        
        return {
            "success": True,
            "data": {
                "job_id": result.job_id,
                "status": result.status,
                "progress": result.progress,
                "description": result.description,
                "result": result.result,
                "error": result.error
            }
        }
    
    @staticmethod
    async def list_jobs(params: Dict[str, Any]) -> Dict[str, Any]:
        """List all jobs in the mock queue."""
        jobs = await mock_queue_manager.list_jobs()
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                "job_id": job.job_id,
                "status": job.status,
                "progress": job.progress,
                "description": job.description,
                "has_result": bool(job.result),
                "has_error": bool(job.error)
            })
        
        return {
            "success": True,
            "data": {
                "jobs": jobs_data,
                "total_count": len(jobs_data)
            }
        }
    
    @staticmethod
    async def health(params: Dict[str, Any]) -> Dict[str, Any]:
        """Get queue health information."""
        health = await mock_queue_manager.get_queue_health()
        
        return {
            "success": True,
            "data": health
        }


async def demo_queue_operations():
    """Demonstrate queue operations with mock queue manager."""
    print("\n🚀 Demonstrating queue operations with mock queue manager...")
    
    try:
        # 1. Add various types of jobs
        print("\n1️⃣ Adding jobs to queue...")
        
        # Long-running job (10 seconds)
        result1 = await MockQueueCommands.add_job({
            "job_type": "long_running",
            "job_id": "long_job_1",
            "params": {
                "duration": 10,
                "task_type": "data_analysis"
            }
        })
        print(f"✅ Added long-running job: {result1['data']['job_id']}")
        
        # Batch processing job
        result2 = await MockQueueCommands.add_job({
            "job_type": "batch_processing",
            "job_id": "batch_job_1",
            "params": {
                "items": [f"item_{i}" for i in range(20)]
            }
        })
        print(f"✅ Added batch processing job: {result2['data']['job_id']}")
        
        # File download job
        result3 = await MockQueueCommands.add_job({
            "job_type": "file_download",
            "job_id": "download_job_1",
            "params": {
                "url": "https://example.com/large_file.zip",
                "file_size": 2 * 1024 * 1024  # 2MB
            }
        })
        print(f"✅ Added file download job: {result3['data']['job_id']}")
        
        # 2. Start jobs
        print("\n2️⃣ Starting jobs...")
        
        await MockQueueCommands.start_job({"job_id": "long_job_1"})
        print("✅ Started long-running job")
        
        await MockQueueCommands.start_job({"job_id": "batch_job_1"})
        print("✅ Started batch processing job")
        
        await MockQueueCommands.start_job({"job_id": "download_job_1"})
        print("✅ Started file download job")
        
        # 3. Monitor job status with detailed progress
        print("\n3️⃣ Monitoring job status with progress...")
        
        for i in range(15):  # Monitor for 15 iterations
            print(f"\n--- Status check {i+1} ---")
            
            # Check individual job status
            jobs_to_check = ["long_job_1", "batch_job_1", "download_job_1"]
            
            for job_id in jobs_to_check:
                try:
                    status_result = await MockQueueCommands.get_job_status({"job_id": job_id})
                    if status_result["success"]:
                        data = status_result["data"]
                        print(f"{job_id}: {data['status']} (progress: {data['progress']}%) - {data['description']}")
                        
                        if data["error"]:
                            print(f"  ❌ Error: {data['error']}")
                    else:
                        print(f"{job_id}: Error - {status_result['error']}")
                except Exception as e:
                    print(f"{job_id}: Exception - {e}")
            
            # List all jobs summary
            list_result = await MockQueueCommands.list_jobs({})
            if list_result["success"]:
                jobs = list_result["data"]["jobs"]
                running_jobs = [job for job in jobs if job["status"] == "running"]
                completed_jobs = [job for job in jobs if job["status"] == "completed"]
                failed_jobs = [job for job in jobs if job["status"] == "failed"]
                
                print(f"📊 Summary: {len(running_jobs)} running, {len(completed_jobs)} completed, {len(failed_jobs)} failed")
                
                # Check if all jobs are done
                if len(running_jobs) == 0:
                    print("✅ All jobs completed!")
                    break
            
            await asyncio.sleep(1)  # Check every second
        
        # 4. Get detailed job results
        print("\n4️⃣ Getting detailed job results...")
        
        for job_id in ["long_job_1", "batch_job_1", "download_job_1"]:
            try:
                status_result = await MockQueueCommands.get_job_status({"job_id": job_id})
                if status_result["success"]:
                    data = status_result["data"]
                    print(f"\n📋 {job_id} Results:")
                    print(f"  Status: {data['status']}")
                    print(f"  Progress: {data['progress']}%")
                    print(f"  Description: {data['description']}")
                    
                    if data["result"]:
                        print(f"  Result: {json.dumps(data['result'], indent=4)}")
                    
                    if data["error"]:
                        print(f"  Error: {data['error']}")
                else:
                    print(f"❌ Error getting results for {job_id}: {status_result['error']}")
                    
            except Exception as e:
                print(f"❌ Exception getting results for {job_id}: {e}")
        
        # 5. Check queue health
        print("\n5️⃣ Checking queue health...")
        
        health_result = await MockQueueCommands.health({})
        if health_result["success"]:
            health = health_result["data"]
            print(f"Queue health: {json.dumps(health, indent=2)}")
        else:
            print(f"❌ Error getting health: {health_result['error']}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function to run the queue demo."""
    print("🚀 MCP Proxy Adapter Queue Integration Demo")
    print("=" * 50)
    
    # Demo queue operations
    await demo_queue_operations()
    
    print("\n🎉 Queue integration demo completed!")
    print("\n📋 Available queue commands:")
    print("  - queue_add_job: Add a job to the queue")
    print("  - queue_start_job: Start a job")
    print("  - queue_stop_job: Stop a job")
    print("  - queue_delete_job: Delete a job")
    print("  - queue_get_job_status: Get job status")
    print("  - queue_list_jobs: List all jobs")
    print("  - queue_health: Check queue health")
    
    print("\n📝 Example JSON-RPC calls:")
    print("1. Add a long-running job:")
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "queue_add_job",
        "params": {
            "job_type": "long_running",
            "job_id": "my_long_job",
            "params": {
                "duration": 15,
                "task_type": "data_analysis"
            }
        },
        "id": 1
    }, indent=2))
    
    print("\n2. Start the job:")
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "queue_start_job",
        "params": {
            "job_id": "my_long_job"
        },
        "id": 2
    }, indent=2))
    
    print("\n3. Check job status:")
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "queue_get_job_status",
        "params": {
            "job_id": "my_long_job"
        },
        "id": 3
    }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
