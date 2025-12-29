"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Simple configuration validator ensuring required fields and files exist.
"""

from __future__ import annotations

from typing import List, Optional

from .simple_config import SimpleConfigModel
from .validators import (
    ValidationError,
    ServerValidator,
    ClientValidator,
    RegistrationValidator,
    ServerValidationValidator,
    AuthValidator,
    QueueManagerValidator,
)


class SimpleConfigValidator:
    """
    Validate SimpleConfigModel instances.
    
    This is a facade class that delegates validation to specialized validators
    for each configuration section.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize validator with optional config file path for resolving relative paths.
        
        Args:
            config_path: Path to configuration file (used to resolve relative file paths)
        """
        self.config_path = config_path
        self.server_validator = ServerValidator(config_path)
        self.client_validator = ClientValidator(config_path)
        self.registration_validator = RegistrationValidator(config_path)
        self.server_validation_validator = ServerValidationValidator(config_path)
        self.auth_validator = AuthValidator(config_path)
        self.queue_manager_validator = QueueManagerValidator(config_path)

    def validate(self, model: SimpleConfigModel) -> List[ValidationError]:
        """
        Validate SimpleConfigModel instance.
        
        Args:
            model: Configuration model to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors: List[ValidationError] = []
        errors.extend(self.server_validator.validate(model))
        errors.extend(self.client_validator.validate(model))
        errors.extend(self.registration_validator.validate(model))
        errors.extend(self.server_validation_validator.validate(model))
        errors.extend(self.auth_validator.validate(model))
        errors.extend(self.queue_manager_validator.validate(model))
        return errors
