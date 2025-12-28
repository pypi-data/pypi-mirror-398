"""Internal logger for SDK operations."""

import json
import os
import traceback
from datetime import datetime
from enum import IntEnum
from typing import Any, Optional, Union


class LogLevel(IntEnum):
    """Log levels for the SDK logger."""

    ERROR = 0
    WARN = 1
    INFO = 2
    DEBUG = 3
    TRACE = 4


class LoggerOptions:
    """Options for configuring the logger."""

    def __init__(self, context: Optional[str] = None, level: Optional[LogLevel] = None):
        """
        Initialize logger options.

        Args:
            context: Context string for categorizing logs
            level: Log level for the logger
        """
        self.context = context
        self.level = level


class Logger:
    """Internal logger for SDK operations."""

    PREFIX = "[enebular-sdk]"
    _default_log_level: Optional[LogLevel] = None

    def __init__(self, context_or_options: Optional[Union[str, LoggerOptions]] = None):
        """
        Initialize the logger.

        Args:
            context_or_options: Either a context string or LoggerOptions object
        """
        self._context: Optional[str]
        self._log_level: LogLevel

        if isinstance(context_or_options, str):
            self._context = context_or_options
            self._log_level = self._get_default_log_level()
        elif isinstance(context_or_options, LoggerOptions):
            self._context = context_or_options.context
            self._log_level = (
                context_or_options.level
                if context_or_options.level is not None
                else self._get_default_log_level()
            )
        else:
            self._context = None
            self._log_level = self._get_default_log_level()

    @classmethod
    def _get_default_log_level(cls) -> LogLevel:
        """Get the default log level from environment or cache."""
        if cls._default_log_level is not None:
            return cls._default_log_level

        log_level_str = os.environ.get("LOG_LEVEL", "TRACE").upper()
        try:
            cls._default_log_level = LogLevel[log_level_str]
        except KeyError:
            cls._default_log_level = LogLevel.TRACE

        return cls._default_log_level

    def set_log_level(self, level: LogLevel) -> None:
        """
        Set the log level for this logger instance.

        Args:
            level: The log level to set
        """
        self._log_level = level

    def get_log_level(self) -> LogLevel:
        """
        Get the current log level.

        Returns:
            The current log level
        """
        return self._log_level

    def _should_log(self, level: LogLevel) -> bool:
        """Check if a message at the given level should be logged."""
        return level <= self._log_level

    def _format_message(self, level: str, message: str) -> str:
        """Format a log message with timestamp and context."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        parts = [timestamp, self.PREFIX, f"[{level}]"]
        if self._context:
            parts.append(f"[{self._context}]")
        parts.append(message)
        return " ".join(parts)

    def error(self, message: str, error: Optional[Union[Exception, Any]] = None) -> None:
        """
        Log an error message.

        Args:
            message: The error message
            error: Optional exception or error object
        """
        if not self._should_log(LogLevel.ERROR):
            return

        formatted_msg = self._format_message("ERROR", message)
        if error is not None:
            if isinstance(error, Exception):
                error_details = "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )
                print(f"{formatted_msg}\n{error_details}", flush=True)
            else:
                print(f"{formatted_msg}\n{str(error)}", flush=True)
        else:
            print(formatted_msg, flush=True)

    def warn(self, message: str, data: Optional[Any] = None) -> None:
        """
        Log a warning message.

        Args:
            message: The warning message
            data: Optional data to include in the log
        """
        if not self._should_log(LogLevel.WARN):
            return

        formatted_msg = self._format_message("WARN", message)
        if data is not None:
            formatted_data = json.dumps(data, indent=2, default=str)
            print(f"{formatted_msg}\n{formatted_data}", flush=True)
        else:
            print(formatted_msg, flush=True)

    def info(self, message: str, data: Optional[Any] = None) -> None:
        """
        Log an info message.

        Args:
            message: The info message
            data: Optional data to include in the log
        """
        if not self._should_log(LogLevel.INFO):
            return

        formatted_msg = self._format_message("INFO", message)
        if data is not None:
            formatted_data = json.dumps(data, indent=2, default=str)
            print(f"{formatted_msg}\n{formatted_data}", flush=True)
        else:
            print(formatted_msg, flush=True)

    def debug(self, message: str, data: Optional[Any] = None) -> None:
        """
        Log a debug message.

        Args:
            message: The debug message
            data: Optional data to include in the log
        """
        if not self._should_log(LogLevel.DEBUG):
            return

        formatted_msg = self._format_message("DEBUG", message)
        if data is not None:
            formatted_data = json.dumps(data, indent=2, default=str)
            print(f"{formatted_msg}\n{formatted_data}", flush=True)
        else:
            print(formatted_msg, flush=True)

    def trace(self, method_name: str, params: Optional[Any] = None) -> None:
        """
        Log method entry with an arrow.

        Args:
            method_name: Name of the method being entered
            params: Optional parameters to log
        """
        if not self._should_log(LogLevel.TRACE):
            return

        message = f"→ {method_name}"
        if params is not None:
            formatted_params = json.dumps(params, indent=2, default=str)
            message = f"{message}\n{formatted_params}"

        formatted_msg = self._format_message("TRACE", message)
        print(formatted_msg, flush=True)

    def trace_end(self, method_name: str, result: Optional[Any] = None) -> None:
        """
        Log method exit with an arrow.

        Args:
            method_name: Name of the method being exited
            result: Optional result to log
        """
        if not self._should_log(LogLevel.TRACE):
            return

        message = f"← {method_name}"
        if result is not None:
            formatted_result = json.dumps(result, indent=2, default=str)
            message = f"{message}\n{formatted_result}"

        formatted_msg = self._format_message("TRACE", message)
        print(formatted_msg, flush=True)
