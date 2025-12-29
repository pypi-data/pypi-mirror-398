"""
Settings management for the MCP Proxy Adapter framework.
Provides utilities for reading and managing framework settings from configuration.
"""

from typing import Dict, Any

from mcp_proxy_adapter.config import config


class Settings:
    """
    Settings management class for the framework.
    Provides easy access to configuration values with type conversion and validation.
    """

    # Store custom settings as a class variable
    _custom_settings: Dict[str, Any] = {}

    @classmethod
    def add_custom_settings(cls, settings: Dict[str, Any]) -> None:
        """
        Add custom settings to the settings manager.

        Args:
            settings: Dictionary with custom settings
        """
        cls._custom_settings.update(settings)

    @classmethod
    def get_custom_settings(cls) -> Dict[str, Any]:
        """
        Get all custom settings.

        Returns:
            Dictionary with all custom settings
        """
        return cls._custom_settings.copy()

    @classmethod
    def get_custom_setting_value(cls, key: str, default: Any = None) -> Any:
        """
        Get custom setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value
        """
        return cls._custom_settings.get(key, default)

    @classmethod
    def set_custom_setting_value(cls, key: str, value: Any) -> None:
        """
        Set custom setting value.

        Args:
            key: Setting key
            value: Value to set
        """
        cls._custom_settings[key] = value

    @classmethod
    def clear_custom_settings(cls) -> None:
        """
        Clear all custom settings.
        """
        cls._custom_settings.clear()

    @staticmethod
    def get_all_settings() -> Dict[str, Any]:
        """
        Get all settings from configuration and custom settings.

        Returns:
            Dictionary with all settings (custom + config)
        """
        all_settings = {}
        
        # Get custom settings
        all_settings.update(Settings.get_custom_settings())
        
        # Get config settings (if config is available)
        try:
            # Try to get main config sections
            if hasattr(config, 'config_data') and config.config_data:
                all_settings.update(config.config_data)
            elif hasattr(config, 'get'):
                # Get common settings from config
                common_keys = [
                    "server.host", "server.port", "server.debug",
                    "logging.level", "logging.log_dir",
                    "commands.auto_discovery", "commands.discovery_path",
                ]
                for key in common_keys:
                    value = config.get(key)
                    if value is not None:
                        all_settings[key] = value
        except Exception:
            # If config access fails, just return custom settings
            pass
        
        return all_settings

    @staticmethod
    def get_custom_setting(key: str, default: Any = None) -> Any:
        """
        Get custom setting from configuration.

        Args:
            key: Configuration key in dot notation (e.g., "custom.feature_enabled")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return config.get(key, default)

    @staticmethod

    @staticmethod
    def set_custom_setting(key: str, value: Any) -> None:
        """
        Set custom setting in configuration.

        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        config.set(key, value)

    @staticmethod
    def reload_config() -> None:
        """
        Reload configuration from file and environment variables.
        """
        config.load_config()


class ServerSettings:
    """
    Server-specific settings helper.
    """

    @staticmethod
    def get_host() -> str:
        """Get server host."""
        return config.get("server.host", "0.0.0.0")

    @staticmethod
    def get_port() -> int:
        """Get server port."""
        return config.get("server.port", 8000)

    @staticmethod
    def get_debug() -> bool:
        """Get debug mode."""
        return config.get("server.debug", False)


class LoggingSettings:
    """
    Logging-specific settings helper.
    """

    @staticmethod
    def get_level() -> str:
        """Get logging level."""
        return config.get("logging.level", "INFO")

    @staticmethod
    def get_log_dir() -> str:
        """Get log directory."""
        return config.get("logging.log_dir", "./logs")

    @staticmethod

    @staticmethod

    @staticmethod

    @staticmethod

    @staticmethod

    @staticmethod
    def _empty_stub():
        """Empty stub method."""
        pass

    @staticmethod
    def _empty_stub2():
        """Empty stub method."""
        pass

    @staticmethod
    def _empty_stub3():
        """Empty stub method."""
        pass


class CommandsSettings:
    """
    Commands-specific settings helper.
    """

    @staticmethod
    def get_auto_discovery() -> bool:
        """Get auto discovery setting."""
        return config.get("commands.auto_discovery", True)

    @staticmethod
    def get_discovery_path() -> str:
        """Get discovery path."""
        return config.get("commands.discovery_path", "mcp_proxy_adapter.commands")


# Convenience functions for easy access










def get_auto_discovery() -> bool:
    """Get auto discovery setting."""
    return CommandsSettings.get_auto_discovery()


def get_discovery_path() -> str:
    """Get discovery path."""
    return CommandsSettings.get_discovery_path()








def add_custom_settings(settings: Dict[str, Any]) -> None:
    """
    Add custom settings to the settings manager.

    Args:
        settings: Dictionary with custom settings
    """
    Settings.add_custom_settings(settings)


def get_custom_settings() -> Dict[str, Any]:
    """
    Get all custom settings.

    Returns:
        Dictionary with all custom settings
    """
    return Settings.get_custom_settings()


def get_custom_setting_value(key: str, default: Any = None) -> Any:
    """
    Get custom setting value.

    Args:
        key: Setting key
        default: Default value if key not found

    Returns:
        Setting value
    """
    return Settings.get_custom_setting_value(key, default)


def set_custom_setting_value(key: str, value: Any) -> None:
    """
    Set custom setting value.

    Args:
        key: Setting key
        value: Value to set
    """
    Settings.set_custom_setting_value(key, value)


def clear_custom_settings() -> None:
    """
    Clear all custom settings.
    """
    Settings.clear_custom_settings()


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get setting value by key.

    Args:
        key: Setting key
        default: Default value if key not found

    Returns:
        Setting value
    """
    return Settings.get_custom_setting_value(key, default)


def set_setting(key: str, value: Any) -> None:
    """
    Set setting value by key.

    Args:
        key: Setting key
        value: Value to set
    """
    Settings.set_custom_setting_value(key, value)


def reload_settings() -> None:
    """
    Reload settings from configuration.
    """
    Settings.reload_config()
