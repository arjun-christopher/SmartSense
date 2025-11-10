"""
Logging system for SmartSense AI Assistant.

This module provides structured logging with configuration-based setup,
rotation, and component-specific loggers.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

from models.config import SmartSenseConfig


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured log output"""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                    'filename', 'module', 'lineno', 'funcName', 'created',
                    'msecs', 'relativeCreated', 'thread', 'threadName',
                    'processName', 'process', 'getMessage', 'exc_info',
                    'exc_text', 'stack_info'
                }:
                    log_data['extra'] = log_data.get('extra', {})
                    log_data['extra'][key] = value

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        logger_name = record.name
        message = record.getMessage()

        if self.use_colors:
            color = self.COLORS.get(level, '')
            reset = self.COLORS['RESET']
            colored_level = f"{color}{level}{reset}"
        else:
            colored_level = level

        formatted = f"[{timestamp}] {colored_level} {logger_name}: {message}"

        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


class SmartSenseLogger:
    """Enhanced logger with SmartSense-specific features"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._component_context: Dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        """Set component context for all subsequent log messages"""
        self._component_context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all component context"""
        self._component_context.clear()

    def _log_with_context(self, level: int, message: str, *args, **kwargs) -> None:
        """Log with additional context"""
        if self._component_context:
            # Add context as extra field
            extra = kwargs.get('extra', {})
            extra['context'] = self._component_context.copy()
            kwargs['extra'] = extra

        self.logger.log(level, message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message with context"""
        self._log_with_context(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message with context"""
        self._log_with_context(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message with context"""
        self._log_with_context(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message with context"""
        self._log_with_context(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message with context"""
        self._log_with_context(logging.CRITICAL, message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with context"""
        kwargs.setdefault('exc_info', True)
        self._log_with_context(logging.ERROR, message, *args, **kwargs)


class LoggerManager:
    """Manager for setting up and configuring loggers"""

    def __init__(self):
        self._configured: bool = False
        self._handlers: Dict[str, logging.Handler] = {}

    def setup_logging(self, config: SmartSenseConfig) -> None:
        """
        Set up logging based on configuration

        Args:
            config: SmartSense configuration
        """
        if self._configured:
            return

        # Get configuration
        log_level = getattr(logging, config.app.log_level.upper())
        is_debug = config.app.debug
        system_config = config.system

        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = self._create_console_handler(is_debug)
        root_logger.addHandler(console_handler)
        self._handlers['console'] = console_handler

        # File handler
        file_handler = self._create_file_handler(logs_dir, system_config.log_rotation)
        root_logger.addHandler(file_handler)
        self._handlers['file'] = file_handler

        # Error file handler
        error_handler = self._create_error_file_handler(logs_dir)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        self._handlers['error'] = error_handler

        # Set up third-party library logging levels
        self._configure_third_party_loggers(is_debug)

        self._configured = True

    def _create_console_handler(self, is_debug: bool) -> logging.StreamHandler:
        """Create console handler with appropriate formatter"""
        console_handler = logging.StreamHandler(sys.stdout)

        if is_debug:
            formatter = ColoredFormatter(use_colors=True)
        else:
            # Simple formatter for production
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        console_handler.setFormatter(formatter)
        return console_handler

    def _create_file_handler(self, logs_dir: Path, rotation: str) -> logging.Handler:
        """Create rotating file handler"""
        log_file = logs_dir / "smartsense.log"

        if rotation == "daily":
            handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
        elif rotation == "weekly":
            handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when='W0',  # Monday
                interval=1,
                backupCount=12,
                encoding='utf-8'
            )
        elif rotation == "monthly":
            handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=30,
                backupCount=12,
                encoding='utf-8'
            )
        else:  # size-based
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10,
                encoding='utf-8'
            )

        formatter = StructuredFormatter(include_extra=True)
        handler.setFormatter(formatter)
        return handler

    def _create_error_file_handler(self, logs_dir: Path) -> logging.Handler:
        """Create error-only file handler"""
        error_log_file = logs_dir / "errors.log"
        handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )

        formatter = StructuredFormatter(include_extra=True)
        handler.setFormatter(formatter)
        return handler

    def _configure_third_party_loggers(self, is_debug: bool) -> None:
        """Configure log levels for third-party libraries"""
        if is_debug:
            # Show debug messages for development
            third_party_level = logging.DEBUG
        else:
            # Suppress verbose third-party logging in production
            third_party_level = logging.WARNING

        # Configure common third-party loggers
        third_party_loggers = [
            'transformers',
            'torch',
            'cv2',
            'PIL',
            'langchain',
            'pyautogui',
            'pywinauto',
            'asyncio',
            'urllib3',
            'requests',
        ]

        for logger_name in third_party_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(third_party_level)

    def get_logger(self, name: str) -> SmartSenseLogger:
        """
        Get a SmartSense logger for a component

        Args:
            name: Logger name (usually __name__)

        Returns:
            SmartSenseLogger instance
        """
        return SmartSenseLogger(name)

    def add_custom_handler(self, name: str, handler: logging.Handler) -> None:
        """Add a custom logging handler"""
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        self._handlers[name] = handler

    def remove_handler(self, name: str) -> None:
        """Remove a logging handler"""
        if name in self._handlers:
            handler = self._handlers[name]
            root_logger = logging.getLogger()
            root_logger.removeHandler(handler)
            del self._handlers[name]

    def get_handler(self, name: str) -> Optional[logging.Handler]:
        """Get a specific handler"""
        return self._handlers.get(name)

    def set_log_level(self, level: str) -> None:
        """Dynamically change log level"""
        log_level = getattr(logging, level.upper())
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Update all handlers
        for handler in root_logger.handlers:
            handler.setLevel(log_level)


# Global logger manager instance
_logger_manager: Optional[LoggerManager] = None


def get_logger_manager() -> LoggerManager:
    """Get the global logger manager instance"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager


def get_logger(name: str) -> SmartSenseLogger:
    """
    Get a SmartSense logger (shortcut for common usage)

    Args:
        name: Logger name (usually __name__)

    Returns:
        SmartSenseLogger instance
    """
    return get_logger_manager().get_logger(name)


def setup_logging(config: SmartSenseConfig) -> None:
    """
    Setup logging system (shortcut for common usage)

    Args:
        config: SmartSense configuration
    """
    get_logger_manager().setup_logging(config)


def set_log_level(level: str) -> None:
    """
    Change log level dynamically (shortcut for common usage)

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    get_logger_manager().set_log_level(level)