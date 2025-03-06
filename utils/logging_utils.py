"""
Logging utilities for the SAP Azure Automation tool.
Provides a consistent logging interface throughout the application.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Dict, Any


def setup_logger(
    name: str = "sap_azure_automator",
    log_level: int = logging.INFO,
    log_dir: Optional[Union[str, Path]] = None,
    console: bool = True,
    file_logging: bool = True,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Logger name
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_dir: Directory for log files, defaults to ~/.sap_azure_automator/logs
        console: Whether to log to console
        file_logging: Whether to log to file
        log_format: Custom log format string

    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicate logs
    if logger.handlers:
        logger.handlers.clear()

    # Define log format
    if log_format is None:
        log_format = (
            "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
        )
    formatter = logging.Formatter(log_format)

    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if requested
    if file_logging:
        # Determine log directory
        if log_dir is None:
            log_dir = Path.home() / ".sap_azure_automator" / "logs"
        elif isinstance(log_dir, str):
            log_dir = Path(log_dir)

        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"{name}_{timestamp}.log"

        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class AppLogger:
    """Application logger with context information"""

    def __init__(
        self,
        name: str = "sap_azure_automator",
        log_level: int = logging.INFO,
        log_dir: Optional[Union[str, Path]] = None,
        console: bool = True,
        file_logging: bool = True,
    ):
        """
        Initialize application logger.

        Args:
            name: Logger name
            log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
            log_dir: Directory for log files
            console: Whether to log to console
            file_logging: Whether to log to file
        """
        self.logger = setup_logger(
            name=name,
            log_level=log_level,
            log_dir=log_dir,
            console=console,
            file_logging=file_logging,
        )
        self.context: Dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        """
        Set context information to include in log messages.

        Args:
            **kwargs: Context key-value pairs
        """
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context information"""
        self.context.clear()

    def _format_with_context(self, message: str) -> str:
        """
        Format message with context information.

        Args:
            message: Original log message

        Returns:
            Message with context information
        """
        if not self.context:
            return message

        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        return f"{message} [Context: {context_str}]"

    def debug(self, message: str, **kwargs) -> None:
        """
        Log debug message.

        Args:
            message: Log message
            **kwargs: Additional context for this log only
        """
        temp_context = self.context.copy()
        temp_context.update(kwargs)

        if temp_context:
            context_str = ", ".join(f"{k}={v}" for k, v in temp_context.items())
            formatted_message = f"{message} [Context: {context_str}]"
        else:
            formatted_message = message

        self.logger.debug(formatted_message)

    def info(self, message: str, **kwargs) -> None:
        """
        Log info message.

        Args:
            message: Log message
            **kwargs: Additional context for this log only
        """
        temp_context = self.context.copy()
        temp_context.update(kwargs)

        if temp_context:
            context_str = ", ".join(f"{k}={v}" for k, v in temp_context.items())
            formatted_message = f"{message} [Context: {context_str}]"
        else:
            formatted_message = message

        self.logger.info(formatted_message)

    def warning(self, message: str, **kwargs) -> None:
        """
        Log warning message.

        Args:
            message: Log message
            **kwargs: Additional context for this log only
        """
        temp_context = self.context.copy()
        temp_context.update(kwargs)

        if temp_context:
            context_str = ", ".join(f"{k}={v}" for k, v in temp_context.items())
            formatted_message = f"{message} [Context: {context_str}]"
        else:
            formatted_message = message

        self.logger.warning(formatted_message)

    def error(self, message: str, **kwargs) -> None:
        """
        Log error message.

        Args:
            message: Log message
            **kwargs: Additional context for this log only
        """
        temp_context = self.context.copy()
        temp_context.update(kwargs)

        if temp_context:
            context_str = ", ".join(f"{k}={v}" for k, v in temp_context.items())
            formatted_message = f"{message} [Context: {context_str}]"
        else:
            formatted_message = message

        self.logger.error(formatted_message)

    def critical(self, message: str, **kwargs) -> None:
        """
        Log critical message.

        Args:
            message: Log message
            **kwargs: Additional context for this log only
        """
        temp_context = self.context.copy()
        temp_context.update(kwargs)

        if temp_context:
            context_str = ", ".join(f"{k}={v}" for k, v in temp_context.items())
            formatted_message = f"{message} [Context: {context_str}]"
        else:
            formatted_message = message

        self.logger.critical(formatted_message)

    def exception(self, message: str, exc_info=True, **kwargs) -> None:
        """
        Log exception message with traceback.

        Args:
            message: Log message
            exc_info: Whether to include exception info
            **kwargs: Additional context for this log only
        """
        temp_context = self.context.copy()
        temp_context.update(kwargs)

        if temp_context:
            context_str = ", ".join(f"{k}={v}" for k, v in temp_context.items())
            formatted_message = f"{message} [Context: {context_str}]"
        else:
            formatted_message = message

        self.logger.exception(formatted_message, exc_info=exc_info)


# Create default application logger
app_logger = AppLogger()

# Export common log levels for convenience
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
