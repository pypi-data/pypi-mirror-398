"""Shared logging configuration for TestIO MCP.

Provides structured logging utilities used by both the server and CLI commands.
"""

import asyncio
import json
import logging
from pathlib import Path

from testio_mcp.config import settings


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging.

    Useful for log aggregation systems and machine parsing.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log message
        """
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ShutdownErrorFilter(logging.Filter):
    """Filter out expected errors during graceful shutdown.

    Suppresses log records for:
    - asyncio.CancelledError exceptions
    - KeyboardInterrupt exceptions during shutdown
    - Uvicorn shutdown timeout messages
    - Task cancellation messages during shutdown
    - Event loop closed errors from aiosqlite
    - ASGI application exceptions during forced shutdown
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out shutdown-related error messages.

        Args:
            record: Log record to filter

        Returns:
            False to suppress the log record, True to keep it
        """
        message = record.getMessage().lower()

        # Suppress CancelledError and KeyboardInterrupt stack traces
        if record.exc_info:
            exc_type = record.exc_info[0]
            if exc_type in (asyncio.CancelledError, KeyboardInterrupt):
                return False

        # Suppress uvicorn shutdown messages
        if "timeout graceful shutdown exceeded" in message:
            return False
        if "cancel" in message and "running task" in message:
            return False

        # Suppress event loop closed errors
        if "event loop is closed" in message:
            return False

        # Suppress task cancellation error messages
        if "cancel" in message and "task" in message:
            if record.levelname in ("ERROR", "WARNING"):
                return False

        # Suppress ASGI/uvicorn shutdown stack traces
        if record.levelname == "ERROR":
            # "Exception in ASGI application" during shutdown
            if "exception in asgi application" in message:
                return False
            # Traceback messages from uvicorn error handler
            if "traceback" in message and "keyboardinterrupt" in message:
                return False

        # Suppress uvicorn connection closing messages during shutdown
        if "shutting down" in message or "finished server process" in message:
            # Keep our own clean shutdown messages, suppress uvicorn's verbose ones
            if record.name.startswith("uvicorn"):
                # Allow "Shutting down" and "Finished server process" through
                # but suppress everything else
                if not any(x in message for x in ["shutting down", "finished server process"]):
                    return False

        return True


def configure_logging(
    enable_file_logging: bool = True, enable_console_logging: bool = True
) -> None:
    """Configure structured logging based on settings.

    Sets up logging with:
    - JSON or text format based on LOG_FORMAT setting
    - Log level from LOG_LEVEL setting
    - Token sanitization via client event hooks
    - File-based logging for debugging during MCP operation (optional)
    - Console logging to stderr (optional, disable for Rich UI compatibility)
    - Shutdown error filtering to suppress expected cancellation errors

    Args:
        enable_file_logging: Whether to enable file logging (default: True).
                            CLI commands may disable this to reduce file I/O.
        enable_console_logging: Whether to enable console (stderr) logging (default: True).
                               Set to False for CLI commands with Rich progress bars.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if settings.LOG_FORMAT.lower() == "json":
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Handler 1: stderr (optional, for console output)
    if enable_console_logging:
        stderr_handler = logging.StreamHandler()
        stderr_handler.setFormatter(formatter)
        stderr_handler.addFilter(ShutdownErrorFilter())  # Suppress shutdown errors in console
        root_logger.addHandler(stderr_handler)

    # Handler 2: file (optional, for debugging)
    if enable_file_logging:
        log_file = Path(settings.LOG_FILE).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        # Don't filter file logs - keep full debugging info in file
        root_logger.addHandler(file_handler)

    # Configure package logger
    logger = logging.getLogger("testio_mcp")
    logger.setLevel(log_level)

    # Apply shutdown filter to uvicorn's error logger to suppress stack traces
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addFilter(ShutdownErrorFilter())
