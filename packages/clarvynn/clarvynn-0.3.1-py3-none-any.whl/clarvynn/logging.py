"""
Clarvynn Logging System

This file provides a simple, consistent logging system for Clarvynn that supports:
1. Simple [clarvynn] prefix format for infrastructure tool consistency
2. Configurable log levels (debug, info, warning, error, silent)
3. Cross-language consistency (works with Python, Go, Ruby, etc.)
4. Clean output suitable for infrastructure tooling
5. Thread-safe logging for multi-threaded applications

LOGGING ARCHITECTURE:
- Uses Python's standard logging module as the foundation
- Simple [clarvynn] prefix for all messages
- Minimal formatting to maintain consistency across languages
- Supports both console and file logging (extensible)

INFRASTRUCTURE TOOL DESIGN:
Clarvynn is an infrastructure tool, not a development tool, so logging needs to be:
- Consistent across multiple programming languages (Python, Go, Ruby, etc.)
- Simple and clean for operations teams
- Easy to parse and filter in log aggregation systems
- Minimal overhead for production use

LOG LEVELS:
- debug: Detailed information for debugging
- info: General information about system operation
- warning: Warning messages for potential issues
- error: Error messages for failures
- silent: No logging output (useful for production)

CROSS-LANGUAGE CONSISTENCY:
The [clarvynn] format is designed to be consistent whether Clarvynn is:
- Running Python applications (current)
- Running Go applications (future)
- Running Ruby applications (future)
- Running other language applications (future)

THREAD SAFETY:
Python's logging module is thread-safe by default, making this
suitable for multi-threaded web applications.

ARCHITECTURE ROLE:
This logging system provides observability into Clarvynn's operations,
which is crucial for:
- Operations teams monitoring instrumentation
- Debugging configuration issues
- Tracking export operations
- Understanding system health
"""

import logging
import os
import sys
from typing import Optional

# LOGGING CONFIGURATION
# Global configuration for the logging system
_configured = False  # Flag to prevent duplicate configuration
_current_level = "warning"  # Current log level setting (quiet by default)
_loggers = {}  # Cache of created loggers for reuse

# LOG LEVEL MAPPING
# Maps string log levels to Python logging constants
LOG_LEVELS = {
    "debug": logging.DEBUG,  # Detailed debugging information
    "info": logging.INFO,  # General information messages
    "warning": logging.WARNING,  # Warning messages
    "error": logging.ERROR,  # Error messages
    "silent": logging.CRITICAL + 1,  # No output (higher than CRITICAL)
}


class ClarvynnFormatter(logging.Formatter):
    """
    SIMPLE FORMATTER FOR CLARVYNN INFRASTRUCTURE LOGS

    PURPOSE: Provide simple, consistent formatting for all Clarvynn log messages.
    This formatter ensures all log messages have the simple [clarvynn] prefix that
    works consistently across multiple programming languages.

    FORMAT STRUCTURE:
    [clarvynn] MESSAGE

    EXAMPLE OUTPUT:
    [clarvynn] Configuration loaded for profile: production
    [clarvynn] Exemplar created value=0.123 trace_id=abc123
    [clarvynn] Failed to start server: Connection refused

    FEATURES:
    - Simple [clarvynn] prefix for all messages
    - No timestamps (handled by log aggregation systems)
    - No component separation (keeps it simple)
    - Cross-language consistency
    - Infrastructure tool appropriate formatting
    """

    def __init__(self):
        """Initialize the formatter with simple format string."""
        # FORMAT TEMPLATE
        # Simple [clarvynn] prefix format for infrastructure consistency
        format_string = "[clarvynn] %(message)s"

        super().__init__(fmt=format_string)

    def format(self, record):
        """
        FORMAT LOG RECORD

        PURPOSE: Format a log record with simple [clarvynn] prefix.
        This method maintains the simple format needed for infrastructure tools.

        Args:
            record: LogRecord object to format

        Returns:
            str: Formatted log message with [clarvynn] prefix
        """
        # Apply base formatting
        formatted = super().format(record)

        return formatted


class SafeStreamHandler(logging.StreamHandler):
    """
    A StreamHandler that silently ignores I/O errors.

    This is needed because during process shutdown or test teardown,
    the underlying stream (stderr) may be closed before the logger
    finishes writing. Without this, you get:
    'ValueError: I/O operation on closed file'
    """

    def emit(self, record):
        try:
            super().emit(record)
        except (ValueError, OSError):
            # Stream is closed, ignore silently
            pass

    def handleError(self, record):
        # Suppress the default error handling which prints to stderr
        # This is called by the base class when emit() raises an exception
        pass


def configure_logging(level: str = "warning", log_file: Optional[str] = None):
    """
    LOGGING SYSTEM CONFIGURATION

    PURPOSE: Configure the Clarvynn logging system with specified level and output options.
    This is the main function used to set up logging for Clarvynn components only.

    IMPORTANT: This only configures the 'clarvynn' logger, NOT the root logger.
    This ensures we don't interfere with the application's own logging.

    LOG LEVEL BEHAVIOR:
    - debug: Shows all messages (very verbose)
    - info: Shows info, warning, and error messages
    - warning: Shows only warning and error messages
    - error: Shows only error messages
    - silent: Shows no messages (production mode)

    Args:
        level (str): Log level ("debug", "info", "warning", "error", "silent")
        log_file (str, optional): Path to log file for file output
    """
    global _configured, _current_level

    # LEVEL VALIDATION
    if level not in LOG_LEVELS:
        raise ValueError(f"Invalid log level: {level}. Must be one of {list(LOG_LEVELS.keys())}")

    # PREVENT DUPLICATE CONFIGURATION
    if _configured and _current_level == level:
        return

    _current_level = level

    # CLARVYNN LOGGER CONFIGURATION
    # Use Clarvynn's own logger, NOT the root logger
    # This prevents [clarvynn] prefix from appearing on all app logs
    clarvynn_logger = logging.getLogger("clarvynn")
    clarvynn_logger.setLevel(LOG_LEVELS[level])

    # PREVENT PROPAGATION TO ROOT LOGGER
    # This is critical - without this, logs would still go to root
    clarvynn_logger.propagate = False

    # CLEAR EXISTING HANDLERS ON CLARVYNN LOGGER ONLY
    for handler in clarvynn_logger.handlers[:]:
        clarvynn_logger.removeHandler(handler)

    # SILENT MODE HANDLING
    if level == "silent":
        _configured = True
        return

    # CONSOLE HANDLER SETUP
    console_handler = SafeStreamHandler(sys.stderr)
    console_handler.setLevel(LOG_LEVELS[level])
    console_handler.setFormatter(ClarvynnFormatter())
    clarvynn_logger.addHandler(console_handler)

    # FILE HANDLER SETUP (OPTIONAL)
    if log_file:
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(LOG_LEVELS[level])
            file_handler.setFormatter(ClarvynnFormatter())
            clarvynn_logger.addHandler(file_handler)
        except Exception as e:
            print(f"[clarvynn] Warning: Could not create log file {log_file}: {e}", file=sys.stderr)

    # CACHE THE CONFIGURED LOGGER
    _loggers["clarvynn"] = clarvynn_logger

    _configured = True


def get_logger(component: str = "") -> logging.Logger:
    """
    COMPONENT LOGGER FACTORY

    PURPOSE: Get or create a logger for Clarvynn.
    This ensures consistent logger naming and configuration across the system.

    SIMPLE APPROACH:
    Since Clarvynn is an infrastructure tool, we use a simple approach:
    - All loggers use the same [clarvynn] prefix
    - Component parameter is accepted but not used in formatting
    - This maintains consistency across multiple programming languages

    LOGGER CACHING:
    Loggers are cached to avoid creating duplicate loggers.
    This improves performance and ensures consistent behavior.

    AUTOMATIC CONFIGURATION:
    If logging hasn't been configured yet, automatically configures with default settings.

    Args:
        component (str, optional): Component name (for internal organization only)

    Returns:
        logging.Logger: Configured logger with [clarvynn] formatting
    """
    # AUTOMATIC CONFIGURATION
    # Ensure logging is configured before creating loggers
    if not _configured:
        configure_logging()

    # SIMPLE LOGGER NAME
    # Use simple "clarvynn" name for all loggers to maintain consistency
    logger_name = "clarvynn"

    # LOGGER CACHING
    # Return cached logger if it exists
    if logger_name in _loggers:
        return _loggers[logger_name]

    # LOGGER CREATION
    # Create new logger with simple name
    logger = logging.getLogger(logger_name)
    logger.setLevel(LOG_LEVELS[_current_level])

    # CACHE THE LOGGER
    # Store for future use
    _loggers[logger_name] = logger

    return logger


def log_startup_block(component: str, message: str, details: Optional[dict] = None):
    """
    STARTUP BLOCK LOGGING

    PURPOSE: Log startup information in a visually distinct block format.
    This makes system initialization information clearly visible and well-organized.

    WHAT IT DOES:
    1. Creates a visually distinct block around startup messages
    2. Uses simple [clarvynn] prefix for consistency
    3. Optionally includes structured details
    4. Uses consistent formatting for all startup blocks

    VISUAL FORMAT:
    [clarvynn] ───────────────────────────────────────────
    [clarvynn] MESSAGE
    [clarvynn] Key: Value
    [clarvynn] Key: Value
    [clarvynn] ───────────────────────────────────────────

    USAGE:
    This is typically used during system initialization to log:
    - Configuration loading
    - OpenTelemetry initialization
    - Server startup
    - Adapter registration

    Args:
        component (str): Component name for the startup message (not used in output)
        message (str): Main startup message
        details (dict, optional): Additional key-value details to display
    """
    logger = get_logger()

    # BLOCK HEADER
    # Create visually distinct header with simple format
    logger.info("───────────────────────────────────────────")

    # MAIN MESSAGE
    # Log the primary startup message
    logger.info(message)

    # DETAILS SECTION
    # Log additional details if provided
    if details:
        for key, value in details.items():
            logger.info(f"{key}: {value}")

    # BLOCK FOOTER
    # Create visually distinct footer
    logger.info("───────────────────────────────────────────")


def set_log_level(level: str):
    """
    DYNAMIC LOG LEVEL CHANGE

    PURPOSE: Change the log level for all Clarvynn loggers at runtime.
    This allows dynamic control of logging verbosity without restarting the application.

    Args:
        level (str): New log level to set
    """
    global _current_level

    # LEVEL VALIDATION
    if level not in LOG_LEVELS:
        raise ValueError(f"Invalid log level: {level}. Must be one of {list(LOG_LEVELS.keys())}")

    # UPDATE GLOBAL SETTING
    _current_level = level

    # UPDATE CLARVYNN LOGGER ONLY (not root!)
    clarvynn_logger = logging.getLogger("clarvynn")
    clarvynn_logger.setLevel(LOG_LEVELS[level])

    # UPDATE HANDLERS ON CLARVYNN LOGGER
    for handler in clarvynn_logger.handlers:
        handler.setLevel(LOG_LEVELS[level])


def get_current_log_level() -> str:
    """
    GET CURRENT LOG LEVEL

    PURPOSE: Get the current log level setting.
    This is useful for components that need to know the current logging configuration.

    Returns:
        str: Current log level string
    """
    return _current_level


# NOTE: We do NOT auto-configure on import!
# This prevents [clarvynn] prefix from appearing on all app logs
# when clarvynn is installed but not actively used.
# Logging is configured when get_logger() is first called.
