"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Queue manager configuration validator.
"""

from __future__ import annotations

from typing import List

from .base_validator import BaseValidator, ValidationError
from ..simple_config import SimpleConfigModel


class QueueManagerValidator(BaseValidator):
    """Validator for queue manager configuration."""

    def validate(self, model: SimpleConfigModel) -> List[ValidationError]:
        """
        Validate queue manager configuration.
        
        Args:
            model: Configuration model
            
        Returns:
            List of validation errors for queue_manager section
        """
        errors: List[ValidationError] = []
        qm = model.queue_manager
        
        # Validate shutdown_timeout
        if qm.shutdown_timeout < 0:
            errors.append(
                ValidationError(
                    "queue_manager.shutdown_timeout must be non-negative"
                )
            )
        
        # Validate max_concurrent_jobs
        if qm.max_concurrent_jobs < 1:
            errors.append(
                ValidationError(
                    "queue_manager.max_concurrent_jobs must be at least 1"
                )
            )
        
        # Validate max_queue_size
        if qm.max_queue_size is not None and qm.max_queue_size < 1:
            errors.append(
                ValidationError(
                    "queue_manager.max_queue_size must be at least 1 if specified"
                )
            )
        
        # Validate per_job_type_limits
        if qm.per_job_type_limits is not None:
            if not isinstance(qm.per_job_type_limits, dict):
                errors.append(
                    ValidationError(
                        "queue_manager.per_job_type_limits must be a dictionary"
                    )
                )
            else:
                valid_job_types = [
                    "data_processing",
                    "file_operation",
                    "api_call",
                    "custom",
                    "long_running",
                    "batch_processing",
                    "file_download",
                    "command_execution",
                ]
                for job_type, limit in qm.per_job_type_limits.items():
                    if not isinstance(job_type, str):
                        errors.append(
                            ValidationError(
                                f"queue_manager.per_job_type_limits keys must be strings, got {type(job_type).__name__}"
                            )
                        )
                        continue
                    
                    if not isinstance(limit, int):
                        errors.append(
                            ValidationError(
                                f"queue_manager.per_job_type_limits['{job_type}'] must be an integer, got {type(limit).__name__}"
                            )
                        )
                        continue
                    
                    if limit < 1:
                        errors.append(
                            ValidationError(
                                f"queue_manager.per_job_type_limits['{job_type}'] must be at least 1"
                            )
                        )
                    
                    # Warn about unknown job types (not an error, just a warning)
                    if job_type not in valid_job_types:
                        # This is just informational, not an error
                        pass
        
        # Validate registry_path if not in_memory
        if not qm.in_memory and not qm.registry_path:
            errors.append(
                ValidationError(
                    "queue_manager.registry_path must be specified when queue_manager.in_memory is false"
                )
            )
        
        return errors

