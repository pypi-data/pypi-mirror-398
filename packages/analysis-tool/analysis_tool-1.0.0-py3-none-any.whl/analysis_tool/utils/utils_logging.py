'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-07-07 06:52:02 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-10-09 11:39:42 +0200
FilePath     : utils_logging.py
Description  :

Copyright (c) 2025 by everyone, All Rights Reserved.
'''

"""Logging utilities for the analysis framework."""

import logging
import logging.handlers
import sys

from pathlib import Path
from typing import Optional, Union, Callable, Any, Generator
from rich.logging import RichHandler
from rich.console import Console


class LoggerConfig:
    """
    Configuration class for logger setup.

    This class centralizes all logging configuration constants to ensure
    consistency across the logging system.

    Attributes:
        VALID_LEVELS (Dict[str, int]): Mapping of valid log level names to values
        RICH_FORMAT (str): Default format string for rich console output
        FILE_FORMAT (str): Default format string for file logging

    Example:
        >>> # Access valid log levels
        >>> print(LoggerConfig.VALID_LEVELS)
        {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}

        >>> # Use default formats
        >>> handler.setFormatter(logging.Formatter(LoggerConfig.FILE_FORMAT))
    """

    # Valid log levels mapping from string names to integer values
    VALID_LEVELS = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}

    # Default format strings for different output types
    RICH_FORMAT = "%(message)s"  # Simple format for rich console (rich adds formatting)
    FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Detailed format for files


def validate_log_level(log_level: Union[str, int]) -> int:
    """
    Validate and convert log level to integer value.

    This function ensures that log levels are valid and converts string
    representations to their corresponding integer values for use with
    the logging module.

    Args:
        log_level (Union[str, int]): Log level as string name or integer value.
            Valid strings: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
            Valid integers: 10, 20, 30, 40, 50

    Returns:
        int: Integer log level value compatible with logging module

    Raises:
        ValueError: If log_level is not a valid string or integer level

    Example:
        >>> # Convert string to integer
        >>> level = validate_log_level("INFO")
        >>> print(level)  # Output: 20

        >>> # Validate integer level
        >>> level = validate_log_level(logging.DEBUG)
        >>> print(level)  # Output: 10

        >>> # Invalid level raises error
        >>> validate_log_level("INVALID")  # Raises ValueError
    """

    if isinstance(log_level, str):
        # Convert string to uppercase for case-insensitive matching
        normalized_level = log_level.upper()

        if normalized_level not in LoggerConfig.VALID_LEVELS:
            valid_level_names = list(LoggerConfig.VALID_LEVELS.keys())
            raise ValueError(f"Invalid log level string: '{log_level}'. " f"Valid levels: {valid_level_names}")

        return LoggerConfig.VALID_LEVELS[normalized_level]

    elif isinstance(log_level, int):
        # Validate integer level is in valid range
        valid_level_values = list(LoggerConfig.VALID_LEVELS.values())

        if log_level not in valid_level_values:
            raise ValueError(f"Invalid log level integer: {log_level}. " f"Valid levels: {valid_level_values}")

        return log_level

    else:
        raise ValueError(f"Log level must be string or int, got {type(log_level).__name__}")


def setup_rich_logging(
    console_log_level: Union[str, int] = "INFO",
    message_format: str = LoggerConfig.RICH_FORMAT,
    datetime_format: str = "[%x %X]",
    show_rich_tracebacks: bool = True,
    show_timestamps: bool = True,
    show_file_paths: bool = True,
    rich_console: Optional[Console] = None,
) -> logging.Logger:
    """
    Set up rich logging with comprehensive console output options.

    This function configures the root logger with a RichHandler for beautiful
    console output with colors, formatting, and enhanced tracebacks.

    Args:
        console_log_level (Union[str, int], optional):
            Logging level for console output. Defaults to "INFO".
        message_format (str, optional):
            Log message format string. Defaults to LoggerConfig.RICH_FORMAT.
        datetime_format (str, optional):
            Date/time format string. Defaults to "[%x %X]".
        show_rich_tracebacks (bool, optional):
            Whether to show enhanced rich tracebacks. Defaults to True.
        show_timestamps (bool, optional):
            Whether to show timestamps in console output. Defaults to True.
        show_file_paths (bool, optional):
            Whether to show file paths in console output. Defaults to True.
        rich_console (Optional[Console], optional):
            Custom rich Console instance. Defaults to None (creates new one).

    Returns:
        logging.Logger: Configured root logger with rich handler

    Raises:
        ValueError: If console_log_level is invalid

    Example:
        >>> # Basic setup with default options
        >>> logger = setup_rich_logging()
        >>> logger.info("This will appear in color!")

        >>> # Custom setup with specific options
        >>> logger = setup_rich_logging(
        ...     console_log_level="DEBUG",
        ...     show_timestamps=False,
        ...     show_file_paths=False
        ... )

        >>> # Setup with custom console
        >>> from rich.console import Console
        >>> custom_console = Console(width=120)
        >>> logger = setup_rich_logging(rich_console=custom_console)
    """

    # ========================================
    # Validate and convert log level
    # ========================================

    validated_log_level = validate_log_level(console_log_level)

    # ========================================
    # Create and configure rich handler
    # ========================================

    rich_handler = RichHandler(console=rich_console, rich_tracebacks=show_rich_tracebacks, show_time=show_timestamps, show_path=show_file_paths, markup=True)  # Enable rich markup in log messages

    # Set formatter for the handler
    rich_handler.setFormatter(logging.Formatter(message_format, datetime_format))

    # ========================================
    # Configure root logger
    # ========================================

    root_logger = logging.getLogger()
    root_logger.setLevel(validated_log_level)

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add the rich handler
    root_logger.addHandler(rich_handler)

    return root_logger


def setup_file_logging(
    log_file_path: Union[str, Path],
    file_log_level: Union[str, int] = "DEBUG",
    file_message_format: str = LoggerConfig.FILE_FORMAT,
    max_file_size_bytes: int = 100 * 1024 * 1024,  # 100MB
    backup_file_count: int = 5,
    file_encoding: str = "utf-8",
) -> logging.Handler:
    """
    Set up rotating file logging with comprehensive options.

    This function creates a rotating file handler that automatically manages
    log file size and creates backups when files become too large.

    Args:
        log_file_path (Union[str, Path]):
            Path to the log file. Parent directories will be created if needed.
        file_log_level (Union[str, int], optional):
            Logging level for file output. Defaults to "DEBUG".
        file_message_format (str, optional):
            Log message format for file output. Defaults to LoggerConfig.FILE_FORMAT.
        max_file_size_bytes (int, optional):
            Maximum file size in bytes before rotation. Defaults to 100MB.
        backup_file_count (int, optional):
            Number of backup files to keep. Defaults to 5.
        file_encoding (str, optional):
            File encoding for log files. Defaults to "utf-8".

    Returns:
        logging.Handler: Configured rotating file handler

    Raises:
        ValueError: If file_log_level is invalid
        OSError: If log file cannot be created or accessed

    Example:
        >>> # Basic file logging setup
        >>> file_handler = setup_file_logging("logs/analysis.log")
        >>>
        >>> # Add to existing logger
        >>> logger = logging.getLogger("my_module")
        >>> logger.addHandler(file_handler)

        >>> # Custom file logging with specific options
        >>> file_handler = setup_file_logging(
        ...     log_file_path="logs/debug.log",
        ...     file_log_level="DEBUG",
        ...     max_file_size_bytes=50 * 1024 * 1024,  # 50MB
        ...     backup_file_count=10
        ... )
    """

    # ========================================
    # Validate inputs and prepare file path
    # ========================================

    validated_log_level = validate_log_level(file_log_level)
    resolved_log_path = Path(log_file_path).resolve()

    # Create parent directories if they don't exist
    resolved_log_path.parent.mkdir(parents=True, exist_ok=True)

    # ========================================
    # Create and configure rotating file handler
    # ========================================

    try:
        rotating_file_handler = logging.handlers.RotatingFileHandler(filename=resolved_log_path, maxBytes=max_file_size_bytes, backupCount=backup_file_count, encoding=file_encoding)

        # Set log level and formatter
        rotating_file_handler.setLevel(validated_log_level)
        rotating_file_handler.setFormatter(logging.Formatter(file_message_format))

        return rotating_file_handler

    except OSError as e:
        raise OSError(f"Failed to create log file handler for '{resolved_log_path}': {str(e)}")


def get_logger(
    logger_name: Optional[str] = None,
    logger_level: Optional[Union[str, int]] = None,
    add_file_handler: Optional[Union[str, Path]] = None,
    file_handler_level: Optional[Union[str, int]] = "DEBUG",
    auto_setup_rich_logging: bool = False,
    # skip_snakemake: bool = True,
) -> logging.Logger:
    """
    Get a logger with optional configuration and handlers.

    This function provides a convenient way to get a logger with optional
    rich console logging setup and file logging. It ensures proper logging
    configuration and validates that logging is set up before use.

    Args:
        logger_name (Optional[str], optional):
            Name for the logger. If None, returns root logger. Defaults to None.
        logger_level (Optional[Union[str, int]], optional):
            Log level override for this specific logger. Defaults to None.
        add_file_handler (Optional[Union[str, Path]], optional):
            Path to add file logging. If provided, adds rotating file handler. Defaults to None.
        file_handler_level (Optional[Union[str, int]], optional):
            Log level for file handler. Only used if add_file_handler is provided. Defaults to "DEBUG".
        auto_setup_rich_logging (bool, optional):
            Whether to automatically setup rich console logging if not already configured. Defaults to False.
        skip_snakemake (bool, optional):
            Whether to suppress snakemake logger output to avoid duplicates. Defaults to True.

    Returns:
        logging.Logger: Configured logger instance

    Raises:
        ValueError: If auto_setup_rich_logging is False and no logging handlers are configured
        ValueError: If logger_level or file_handler_level is invalid
        OSError: If file handler cannot be created

    Example:
        >>> # Get logger with auto-setup rich logging
        >>> logger = get_logger("my_module", auto_setup_rich_logging=True)
        >>> logger.info("This will appear in rich format!")

        >>> # Get logger with file logging
        >>> logger = get_logger(
        ...     logger_name="data_processor",
        ...     logger_level="INFO",
        ...     add_file_handler="logs/processor.log",
        ...     file_handler_level="DEBUG"
        ... )

        >>> # Get logger when rich logging is already setup
        >>> setup_rich_logging()  # Setup first
        >>> logger = get_logger("analysis")  # This will work

        >>> # This will raise ValueError if no logging is setup
        >>> logger = get_logger("test", auto_setup_rich_logging=False)

        >>> # Get logger without suppressing snakemake
        >>> logger = get_logger("my_module", skip_snakemake=False)
    """

    # ========================================
    # Handle rich logging setup
    # ========================================

    root_logger = logging.getLogger()

    if auto_setup_rich_logging:
        # Auto-setup rich logging if requested
        if root_logger.handlers:
            # Rich logging already configured, just warn
            root_logger.warning("Rich logging already configured, skipping auto-setup. " "Use setup_rich_logging() directly for reconfiguration.")
        else:
            # Setup rich logging with provided level or default
            setup_rich_logging(console_log_level=logger_level or "INFO")

    else:
        # Check if logging has been properly configured
        if not root_logger.handlers:
            raise ValueError(
                "No logging handlers configured. Either:\n"
                "1. Call setup_rich_logging() first, or\n"
                "2. Set auto_setup_rich_logging=True, or\n"
                "3. Configure logging manually with logging.basicConfig()"
            )

    # # ========================================
    # # Suppress snakemake loggers if requested
    # # ========================================

    # if skip_snakemake:
    #     # Suppress snakemake's verbose logging to avoid duplicates
    #     snakemake_loggers = [
    #         'snakemake',
    #         'snakemake.logging',
    #         'snakemake.dag',
    #         'snakemake.jobs',
    #         'snakemake.workflow',
    #     ]

    #     for logger_name_to_suppress in snakemake_loggers:
    #         snakemake_logger = logging.getLogger(logger_name_to_suppress)
    #         snakemake_logger.setLevel(logging.WARNING)
    #         # Prevent propagation to root logger
    #         snakemake_logger.propagate = False

    # ========================================
    # Get or create logger with specified name
    # ========================================

    target_logger = logging.getLogger(logger_name)

    # ========================================
    # Set logger-specific level if provided
    # ========================================

    if logger_level is not None:
        validated_logger_level = validate_log_level(logger_level)
        target_logger.setLevel(validated_logger_level)

    # ========================================
    # Add file handler if requested
    # ========================================

    if add_file_handler is not None:
        try:
            file_handler = setup_file_logging(log_file_path=add_file_handler, file_log_level=file_handler_level)
            target_logger.addHandler(file_handler)

            target_logger.info(f"Added file logging to: {Path(add_file_handler).resolve()}")

        except Exception as e:
            target_logger.error(f"Failed to add file handler: {str(e)}")
            raise

    return target_logger
