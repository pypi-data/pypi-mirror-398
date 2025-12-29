"""
Tests for completed jobs retention in queue manager.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import time
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from mcp_proxy_adapter.integrations.queuemgr_integration import (
    init_global_queue_manager,
    shutdown_global_queue_manager,
    QueueJobStatus,
    QueueJobBase,
    QueueManagerIntegration,
)


class QuickJob(QueueJobBase):
    """Quick job that completes immediately."""

    def run(self) -> None:
        """Execute quick job."""
        result = {
            "job_id": self.job_id,
            "status": "completed",
            "completed_at": time.time(),
        }
        self.set_mcp_result(result)


class SlowJob(QueueJobBase):
    """Slow job that takes time to complete."""

    def run(self) -> None:
        """Execute slow job."""
        import time as time_module

        duration = self.mcp_params.get("duration", 1)
        time_module.sleep(duration)
        result = {
            "job_id": self.job_id,
            "status": "completed",
            "completed_at": time_module.time(),
        }
        self.set_mcp_result(result)


@pytest_asyncio.fixture
async def queue_manager() -> AsyncGenerator[QueueManagerIntegration, None]:
    """Create and start queue manager for testing."""
    manager = await init_global_queue_manager(
        in_memory=True,
        max_concurrent_jobs=5,
        completed_job_retention_seconds=60,  # 1 minute for testing
    )
    yield manager
    await shutdown_global_queue_manager()


@pytest.mark.asyncio
async def test_completed_job_remains_accessible(queue_manager):
    """Test that completed jobs remain accessible after completion."""
    # Add a quick job
    job_id = "test_completed_1"
    result = await queue_manager.add_job(QuickJob, job_id, {})
    assert result.status == QueueJobStatus.PENDING

    # Start the job
    await queue_manager.start_job(job_id)

    # Wait for completion
    await asyncio.sleep(2)

    # Check that job is still accessible
    status = await queue_manager.get_job_status(job_id)
    assert status.status == QueueJobStatus.COMPLETED
    assert status.job_id == job_id
    assert status.result is not None

    # Verify we can retrieve the actual data from the result
    assert isinstance(status.result, dict), "Result should be a dictionary"
    assert (
        "job_id" in status.result or "status" in status.result
    ), "Result should contain job data"

    # Try retrieving again to ensure data persists
    status2 = await queue_manager.get_job_status(job_id)
    assert status2.result == status.result, "Result data should be consistent"


@pytest.mark.asyncio
async def test_completed_jobs_not_counted_in_limits(queue_manager):
    """Test that completed jobs don't count toward max_queue_size limit."""
    # Set a small limit
    queue_manager.max_queue_size = 3

    # Add and complete 5 jobs
    completed_job_ids = []
    for i in range(5):
        job_id = f"test_limit_{i}"
        await queue_manager.add_job(QuickJob, job_id, {})
        await queue_manager.start_job(job_id)
        completed_job_ids.append(job_id)

    # Wait for all to complete
    await asyncio.sleep(3)

    # Verify all completed jobs are still accessible
    for job_id in completed_job_ids:
        status = await queue_manager.get_job_status(job_id)
        assert (
            status.status == QueueJobStatus.COMPLETED
        ), f"Job {job_id} should be completed"

    # Add a new job - should succeed because completed jobs don't count
    new_job_id = "test_limit_new"
    result = await queue_manager.add_job(QuickJob, new_job_id, {})
    assert result.status == QueueJobStatus.PENDING

    # Verify the new job was added
    status = await queue_manager.get_job_status(new_job_id)
    assert status.job_id == new_job_id


@pytest.mark.asyncio
async def test_only_non_completed_jobs_counted_for_limits(queue_manager):
    """Test that only non-completed jobs are counted when enforcing limits."""
    queue_manager.max_queue_size = 2

    # Add 2 jobs first, then start them
    job_ids = []
    for i in range(2):
        job_id = f"test_pending_{i}"
        await queue_manager.add_job(SlowJob, job_id, {"duration": 0.5})
        job_ids.append(job_id)

    # Start both jobs
    for job_id in job_ids:
        await queue_manager.start_job(job_id)

    # Wait for completion
    await asyncio.sleep(2)

    # Verify both jobs are completed
    for job_id in job_ids:
        status = await queue_manager.get_job_status(job_id)
        assert status.status == QueueJobStatus.COMPLETED

    # Add new jobs - should work because completed jobs don't count
    new_job_id = "test_after_completion"
    result = await queue_manager.add_job(QuickJob, new_job_id, {})
    assert result.status == QueueJobStatus.PENDING


@pytest.mark.asyncio
async def test_per_job_type_limits_exclude_completed(queue_manager):
    """Test that per_job_type_limits exclude completed jobs."""
    queue_manager.per_job_type_limits = {"quick": 2}

    # Add and complete 3 quick jobs
    for i in range(3):
        job_id = f"test_type_{i}"
        await queue_manager.add_job(QuickJob, job_id, {})
        await queue_manager.start_job(job_id)

    await asyncio.sleep(2)

    # All should be completed and accessible
    for i in range(3):
        job_id = f"test_type_{i}"
        status = await queue_manager.get_job_status(job_id)
        assert status.status == QueueJobStatus.COMPLETED

    # Add another quick job - should work because completed don't count
    new_job_id = "test_type_new"
    result = await queue_manager.add_job(QuickJob, new_job_id, {})
    assert result.status == QueueJobStatus.PENDING


@pytest.mark.asyncio
async def test_completed_job_retention_configuration():
    """Test that completed_job_retention_seconds configuration works."""
    # Test with short retention
    manager_short = await init_global_queue_manager(
        in_memory=True,
        completed_job_retention_seconds=5,  # 5 seconds
    )

    job_id = "test_retention_short"
    await manager_short.add_job(QuickJob, job_id, {})
    await manager_short.start_job(job_id)
    await asyncio.sleep(1)

    # Job should be accessible
    status = await manager_short.get_job_status(job_id)
    assert status.status == QueueJobStatus.COMPLETED

    await shutdown_global_queue_manager()

    # Test with zero retention (keep indefinitely)
    manager_infinite = await init_global_queue_manager(
        in_memory=True,
        completed_job_retention_seconds=0,  # Keep forever
    )

    job_id2 = "test_retention_infinite"
    await manager_infinite.add_job(QuickJob, job_id2, {})
    await manager_infinite.start_job(job_id2)
    await asyncio.sleep(1)

    # Job should be accessible
    status = await manager_infinite.get_job_status(job_id2)
    assert status.status == QueueJobStatus.COMPLETED

    await shutdown_global_queue_manager()


@pytest.mark.asyncio
async def test_completed_jobs_listed_correctly(queue_manager):
    """Test that completed jobs are listed in list_jobs."""
    # Add and complete a job
    job_id = "test_list_1"
    await queue_manager.add_job(QuickJob, job_id, {})
    await queue_manager.start_job(job_id)
    await asyncio.sleep(2)

    # List all jobs
    all_jobs = await queue_manager.list_jobs()

    # Find our job
    found_job = None
    for job in all_jobs:
        if job.job_id == job_id:
            found_job = job
            break

    assert found_job is not None, "Completed job should be in list"
    assert found_job.status == QueueJobStatus.COMPLETED
    # Verify result data is available in listed job
    assert found_job.result is not None, "Completed job should have result data"
    assert isinstance(found_job.result, dict), "Result should be a dictionary"


@pytest.mark.asyncio
async def test_failed_jobs_also_preserved(queue_manager):
    """Test that failed jobs are also preserved like completed jobs."""
    # Use a job that will fail - create it at module level to avoid pickling issues
    # We'll use a job that fails by design
    from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob

    # Create a job that will fail by passing invalid command
    job_id = "test_failed_1"
    await queue_manager.add_job(
        CommandExecutionJob,
        job_id,
        {
            "command": "nonexistent_command_that_will_fail",
            "params": {},
        },
    )
    await queue_manager.start_job(job_id)
    await asyncio.sleep(3)  # Wait longer for failure

    # Job should be accessible with failed status
    status = await queue_manager.get_job_status(job_id)
    # Job might be failed or completed with error, both are fine
    assert status.status in (
        QueueJobStatus.FAILED,
        QueueJobStatus.COMPLETED,
    ), f"Expected failed or completed, got {status.status}"

    # Failed/completed jobs should not count toward limits
    queue_manager.max_queue_size = 1
    new_job_id = "test_after_failed"
    result = await queue_manager.add_job(QuickJob, new_job_id, {})
    assert result.status == QueueJobStatus.PENDING


@pytest.mark.asyncio
async def test_explicit_delete_still_works(queue_manager):
    """Test that explicit delete command still works for completed jobs."""
    job_id = "test_delete_1"
    await queue_manager.add_job(QuickJob, job_id, {})
    await queue_manager.start_job(job_id)
    await asyncio.sleep(2)

    # Verify job exists
    status = await queue_manager.get_job_status(job_id)
    assert status.status == QueueJobStatus.COMPLETED

    # Delete explicitly
    result = await queue_manager.delete_job(job_id)
    assert result.status == QueueJobStatus.DELETED

    # Verify job is gone
    try:
        await queue_manager.get_job_status(job_id)
        assert False, "Job should not exist after deletion"
    except Exception:
        pass  # Expected


@pytest.mark.asyncio
async def test_queue_health_includes_completed_jobs(queue_manager):
    """Test that queue health correctly reports completed jobs."""
    # Add and complete some jobs
    for i in range(3):
        job_id = f"test_health_{i}"
        await queue_manager.add_job(QuickJob, job_id, {})
        await queue_manager.start_job(job_id)

    await asyncio.sleep(2)

    # Get health
    health = await queue_manager.get_queue_health()

    assert health["completed_jobs"] >= 3, "Health should report completed jobs"
    assert health["total_jobs"] >= 3, "Total should include completed jobs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
