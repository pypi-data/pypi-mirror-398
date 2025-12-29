"""
Module for microservice configuration management.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Optional

from .core.config import Config

# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Configuration instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config




# For backward compatibility
config = get_config()
