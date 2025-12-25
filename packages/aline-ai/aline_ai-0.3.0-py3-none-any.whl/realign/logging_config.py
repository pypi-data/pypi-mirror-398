"""
ReAlign Logging Configuration

Provides centralized logging setup for the ReAlign project.
Supports file rotation, environment variable configuration, and structured logging.
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def get_log_level() -> int:
    """
    Get log level from environment variable or default to INFO.

    Environment variable: REALIGN_LOG_LEVEL
    Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL

    Returns:
        int: Logging level constant from logging module
    """
    level_name = os.getenv('REALIGN_LOG_LEVEL', 'INFO').upper()

    # Map string to logging constant
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    return level_map.get(level_name, logging.INFO)


def get_log_directory() -> Path:
    """
    Get the log directory path.

    Default: ~/.aline/.logs/
    Can be overridden with REALIGN_LOG_DIR environment variable.

    Returns:
        Path: Log directory path
    """
    log_dir_str = os.getenv('REALIGN_LOG_DIR')

    if log_dir_str:
        log_dir = Path(log_dir_str).expanduser()
    else:
        log_dir = Path.home() / '.aline' / '.logs'

    # Create directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    return log_dir


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = False
) -> logging.Logger:
    """
    Set up a logger with file rotation and optional console output.

    Args:
        name: Logger name (e.g., 'realign.hooks', 'realign.redactor')
        log_file: Log filename (e.g., 'hooks.log'). If None, no file handler is added.
        max_bytes: Maximum size of each log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        console_output: Whether to also output to console/stderr (default: False)

    Returns:
        logging.Logger: Configured logger instance

    Example:
        >>> logger = setup_logger('realign.hooks', 'hooks.log')
        >>> logger.info("Hook started")
        >>> logger.debug("Processing file: %s", file_path)
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    logger.setLevel(get_log_level())
    logger.propagate = False  # Don't propagate to root logger

    # Standard formatter with timestamp, level, name, and message
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation
    if log_file:
        try:
            log_dir = get_log_directory()
            log_path = log_dir / log_file

            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # Capture all levels to file
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        except Exception as e:
            # If file logging fails, fall back to stderr only
            # Don't let logging setup break the application
            import sys
            print(f"Warning: Failed to set up file logging: {e}", file=sys.stderr)

    # Optional console handler (stderr)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(get_log_level())
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name.

    This is a convenience function for getting a logger that was already
    set up with setup_logger().

    Args:
        name: Logger name

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


# Context manager for temporary log level changes
class temporary_log_level:
    """
    Context manager to temporarily change log level.

    Example:
        >>> with temporary_log_level('realign.hooks', logging.DEBUG):
        ...     # Code that needs debug logging
        ...     process_session()
    """

    def __init__(self, logger_name: str, level: int):
        self.logger = logging.getLogger(logger_name)
        self.original_level = self.logger.level
        self.new_level = level

    def __enter__(self):
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)
        return False
