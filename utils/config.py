"""
Configuration management system for SmartSense AI Assistant.

This module provides centralized configuration management with validation,
environment variable overrides, and runtime updates.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
import logging

from pydantic import ValidationError

from models.config import (
    SmartSenseConfig,
    EnvironmentConfig,
    AppConfig,
    MessageBusConfig,
    AIModelsConfig,
    UIConfig,
    SecurityConfig,
    SystemConfig,
)

T = TypeVar('T')


class ConfigManager:
    """Centralized configuration management with validation and hot-reloading"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._config: Optional[SmartSenseConfig] = None
        self._environment_config: Optional[EnvironmentConfig] = None
        self._config_path: Optional[Path] = None
        self._watchers: List[callable] = []

    async def load_config(self, config_path: Union[str, Path]) -> SmartSenseConfig:
        """
        Load configuration from file with environment variable overrides

        Args:
            config_path: Path to the configuration file

        Returns:
            SmartSenseConfig: Loaded and validated configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If configuration is invalid
        """
        self._config_path = Path(config_path)

        # Load environment configuration first
        self._environment_config = self._load_environment_config()

        # Load main configuration file
        config_data = self._load_yaml_config(self._config_path)

        # Apply environment overrides
        config_data = self._apply_environment_overrides(config_data)

        # Validate and create configuration object
        try:
            self._config = SmartSenseConfig(**config_data)
            self.logger.info(f"Configuration loaded successfully from {config_path}")
            return self._config

        except ValidationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise

    def _load_environment_config(self) -> EnvironmentConfig:
        """Load environment variables into configuration"""
        env_vars = {
            'SMARTSENSE_CONFIG_PATH': os.getenv('SMARTSENSE_CONFIG_PATH'),
            'SMARTSENSE_LOG_LEVEL': os.getenv('SMARTSENSE_LOG_LEVEL'),
            'SMARTSENSE_DATA_DIR': os.getenv('SMARTSENSE_DATA_DIR'),
            'SMARTSENSE_MODEL_DIR': os.getenv('SMARTSENSE_MODEL_DIR'),
            'SMARTSENSE_CACHE_SIZE': os.getenv('SMARTSENSE_CACHE_SIZE'),
            'SMARTSENSE_API_KEY': os.getenv('SMARTSENSE_API_KEY'),
            'SMARTSENSE_DEBUG': os.getenv('SMARTSENSE_DEBUG'),
        }

        # Filter out None values
        env_vars = {k: v for k, v in env_vars.items() if v is not None}

        return EnvironmentConfig(**env_vars)

    def _load_yaml_config(self, config_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if not isinstance(config_data, dict):
                raise ValueError("Configuration file must contain a YAML dictionary")

            return config_data

        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML configuration: {e}")
            raise ValueError(f"Invalid YAML configuration: {e}")

    def _apply_environment_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration"""
        if not self._environment_config:
            return config_data

        env_config = self._environment_config

        # Apply log level override
        if env_config.SMARTSENSE_LOG_LEVEL:
            if 'app' not in config_data:
                config_data['app'] = {}
            config_data['app']['log_level'] = env_config.SMARTSENSE_LOG_LEVEL

        # Apply debug override
        if env_config.SMARTSENSE_DEBUG:
            if 'app' not in config_data:
                config_data['app'] = {}
            config_data['app']['debug'] = True

        # Apply data directory override
        if env_config.SMARTSENSE_DATA_DIR:
            if 'system' not in config_data:
                config_data['system'] = {}
            config_data['system']['data_dir'] = env_config.SMARTSENSE_DATA_DIR

        # Apply model directory override
        if env_config.SMARTSENSE_MODEL_DIR:
            if 'system' not in config_data:
                config_data['system'] = {}
            config_data['system']['model_dir'] = env_config.SMARTSENSE_MODEL_DIR

        # Apply cache size override
        if env_config.SMARTSENSE_CACHE_SIZE:
            if 'system' not in config_data:
                config_data['system'] = {}
            config_data['system']['model_cache_size'] = env_config.SMARTSENSE_CACHE_SIZE

        # Apply specific model configuration overrides
        if env_config.SMARTSENSE_API_KEY:
            if 'models' not in config_data:
                config_data['models'] = {}
            if 'nlp' not in config_data['models']:
                config_data['models']['nlp'] = {}
            config_data['models']['nlp']['api_key'] = env_config.SMARTSENSE_API_KEY

        return config_data

    def get_config(self) -> SmartSenseConfig:
        """Get the current configuration"""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation

        Args:
            key: Configuration key in dot notation (e.g., 'app.name', 'models.nlp.primary_model')
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    value = getattr(value, k)
            return value

        except (AttributeError, KeyError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation

        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        keys = key.split('.')
        config_obj = self._config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if isinstance(config_obj, dict):
                config_obj = config_obj.setdefault(k, {})
            else:
                config_obj = getattr(config_obj, k)

        # Set the final value
        if isinstance(config_obj, dict):
            config_obj[keys[-1]] = value
        else:
            setattr(config_obj, keys[-1], value)

    async def reload(self) -> SmartSenseConfig:
        """Reload configuration from file"""
        if self._config_path is None:
            raise RuntimeError("No configuration file path set")

        old_config = self._config
        self._config = None

        try:
            new_config = await self.load_config(self._config_path)

            # Notify watchers of configuration change
            for watcher in self._watchers:
                try:
                    await watcher(old_config, new_config)
                except Exception as e:
                    self.logger.error(f"Error notifying config watcher: {e}")

            return new_config

        except Exception as e:
            # Restore old config on error
            self._config = old_config
            self.logger.error(f"Error reloading configuration: {e}")
            raise

    def validate(self) -> List[str]:
        """
        Validate the current configuration

        Returns:
            List of validation errors (empty if valid)
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        errors = []

        try:
            # Re-validate the configuration
            SmartSenseConfig(**self._config.dict())
        except ValidationError as e:
            for error in e.errors():
                field_path = '.'.join(str(loc) for loc in error['loc'])
                errors.append(f"{field_path}: {error['msg']}")

        return errors

    def add_watcher(self, callback: callable) -> None:
        """
        Add a configuration change watcher

        Args:
            callback: Async callback function that receives (old_config, new_config)
        """
        self._watchers.append(callback)

    def remove_watcher(self, callback: callable) -> None:
        """
        Remove a configuration change watcher

        Args:
            callback: Callback function to remove
        """
        if callback in self._watchers:
            self._watchers.remove(callback)

    def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific AI model type

        Args:
            model_type: Type of model ('nlp', 'vision', 'speech')

        Returns:
            Model configuration dictionary
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        models_config = self._config.models.dict()
        return models_config.get(model_type, {})

    def get_system_paths(self) -> Dict[str, Path]:
        """Get all system paths as Path objects"""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        system_config = self._config.system
        base_path = Path.cwd()

        return {
            'temp_dir': Path(system_config.temp_dir),
            'cache_dir': Path(system_config.cache_dir),
            'data_dir': base_path / 'data',
            'logs_dir': base_path / 'logs',
            'models_dir': base_path / 'data' / 'models',
            'user_data_dir': base_path / 'data' / 'user_data',
        }

    def is_debug_enabled(self) -> bool:
        """Check if debug mode is enabled"""
        if self._config is None:
            return False
        return self._config.app.debug

    def get_log_level(self) -> str:
        """Get the configured log level"""
        if self._config is None:
            return "INFO"
        return self._config.app.log_level

    def get_app_info(self) -> Dict[str, str]:
        """Get application information"""
        if self._config is None:
            return {}

        app_config = self._config.app
        return {
            'name': app_config.name,
            'version': app_config.version,
            'debug': str(app_config.debug),
            'log_level': app_config.log_level,
        }


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> SmartSenseConfig:
    """Get the current configuration (shortcut for common usage)"""
    return get_config_manager().get_config()


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value (shortcut for common usage)"""
    return get_config_manager().get(key, default)