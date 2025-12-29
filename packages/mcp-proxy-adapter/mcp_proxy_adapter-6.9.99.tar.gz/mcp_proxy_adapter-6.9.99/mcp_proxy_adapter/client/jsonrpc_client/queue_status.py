"""Queue job status enumeration.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Set


class QueueJobStatus(str, Enum):
    """
    Queue job status enumeration.

    This enum represents all possible states of a job in the queue system.
    It extends str to ensure JSON serialization compatibility.

    Status Categories:
    - Pending: Job is waiting to be processed
    - Active: Job is currently being processed
    - Terminal Success: Job completed successfully
    - Terminal Failure: Job failed or encountered an error
    - Terminal Cancelled: Job was stopped or cancelled
    """

    # Pending states - job is waiting or queued
    PENDING = "pending"
    QUEUED = "queued"

    # Active states - job is currently running
    RUNNING = "running"
    IN_PROGRESS = "in_progress"

    # Terminal success states
    COMPLETED = "completed"
    SUCCESS = "success"

    # Terminal failure states
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"

    # Terminal cancelled states
    STOPPED = "stopped"
    CANCELLED = "cancelled"

    @classmethod
    def get_pending_states(cls) -> Set[str]:
        """
        Get set of all pending/active state values.

        Returns:
            Set of status strings that indicate job is still processing
        """
        return {
            cls.PENDING.value,
            cls.QUEUED.value,
            cls.RUNNING.value,
            cls.IN_PROGRESS.value,
        }

    @classmethod
    def get_terminal_states(cls) -> Set[str]:
        """
        Get set of all terminal state values.

        Returns:
            Set of status strings that indicate job has finished
        """
        return {
            cls.COMPLETED.value,
            cls.SUCCESS.value,
            cls.FAILED.value,
            cls.ERROR.value,
            cls.TIMEOUT.value,
            cls.STOPPED.value,
            cls.CANCELLED.value,
        }

    @classmethod
    def get_failure_states(cls) -> Set[str]:
        """
        Get set of all failure state values.

        Returns:
            Set of status strings that indicate job failed
        """
        return {
            cls.FAILED.value,
            cls.ERROR.value,
            cls.TIMEOUT.value,
        }

    @classmethod
    def get_success_states(cls) -> Set[str]:
        """
        Get set of all success state values.

        Returns:
            Set of status strings that indicate job succeeded
        """
        return {
            cls.COMPLETED.value,
            cls.SUCCESS.value,
        }

    @classmethod
    def get_cancelled_states(cls) -> Set[str]:
        """
        Get set of all cancelled state values.

        Returns:
            Set of status strings that indicate job was cancelled
        """
        return {
            cls.STOPPED.value,
            cls.CANCELLED.value,
        }

    @classmethod
    def from_string(cls, value: Any) -> QueueJobStatus:
        """
        Convert string value to QueueJobStatus enum.

        Args:
            value: String value to convert (case-insensitive)

        Returns:
            QueueJobStatus enum value

        Raises:
            ValueError: If value is not a valid status
        """
        if not isinstance(value, str):
            raise ValueError(f"Status must be a string, got {type(value)}")

        value_lower = value.lower().strip()

        # Try exact match first
        for status in cls:
            if status.value.lower() == value_lower:
                return status

        # If no exact match, raise error
        valid_values = [s.value for s in cls]
        raise ValueError(
            f"Invalid status value '{value}'. "
            f"Valid values are: {', '.join(valid_values)}"
        )

    def is_pending(self) -> bool:
        """Check if status is a pending/active state."""
        return self.value in self.get_pending_states()

    def is_terminal(self) -> bool:
        """Check if status is a terminal state."""
        return self.value in self.get_terminal_states()

    def is_failure(self) -> bool:
        """Check if status indicates failure."""
        return self.value in self.get_failure_states()

    def is_success(self) -> bool:
        """Check if status indicates success."""
        return self.value in self.get_success_states()

    def is_cancelled(self) -> bool:
        """Check if status indicates cancellation."""
        return self.value in self.get_cancelled_states()

    def to_json(self) -> str:
        """
        Serialize status to JSON string.

        Returns:
            JSON string representation of the status
        """
        return json.dumps(self.value)

    @classmethod
    def from_json(cls, json_str: str) -> QueueJobStatus:
        """
        Deserialize status from JSON string.

        Args:
            json_str: JSON string representation of the status

        Returns:
            QueueJobStatus enum value
        """
        value = json.loads(json_str)
        return cls.from_string(value)


__all__ = ["QueueJobStatus"]
