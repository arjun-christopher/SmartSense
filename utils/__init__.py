"""
Utility modules for SmartSense AI Assistant.

This package contains utility modules that provide common functionality
used throughout the SmartSense system.
"""

from .config import ConfigManager, get_config_manager, get_config, get_config_value
from .logger import SmartSenseLogger, LoggerManager, get_logger, setup_logging, set_log_level
from .service_locator import ServiceLocator, ServiceContainer, get_service_locator, register_service, get_service, get_optional_service, clear_services
from .lifecycle import LifecycleManager, SystemPhase, ComponentPhase

__all__ = [
    # Configuration
    "ConfigManager",
    "get_config_manager",
    "get_config",
    "get_config_value",

    # Logging
    "SmartSenseLogger",
    "LoggerManager",
    "get_logger",
    "setup_logging",
    "set_log_level",

    # Service Locator
    "ServiceLocator",
    "ServiceContainer",
    "get_service_locator",
    "register_service",
    "get_service",
    "get_optional_service",
    "clear_services",

    # Lifecycle Management
    "LifecycleManager",
    "SystemPhase",
    "ComponentPhase",
]