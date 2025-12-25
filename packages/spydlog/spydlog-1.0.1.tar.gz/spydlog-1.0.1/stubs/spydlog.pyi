# spydlog stubs

from __future__ import annotations
from typing import Any, List, Optional, Union, Callable, overload
import sys

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

class level:
    """Log level enumeration."""

    trace: int
    debug: int
    info: int
    warn: int
    err: int
    critical: int
    off: int

    def __lt__(self, other: level) -> bool: ...
    def __le__(self, other: level) -> bool: ...
    def __gt__(self, other: level) -> bool: ...
    def __ge__(self, other: level) -> bool: ...

class color_mode:
    """Color mode enumeration."""

    always: int
    automatic: int
    never: int

class pattern_time_type:
    """Pattern time type enumeration."""

    local: int
    utc: int

class async_overflow_policy:
    """Async overflow policy enumeration."""

    block: int
    overrun_oldest: int

class sink:
    """Base class for all sinks."""

    def log(self, lvl: level, msg: str) -> None:
        """Log a message with the given level."""
        ...

    def set_level(self, lvl: level) -> None:
        """Set the log level for this sink."""
        ...

    def level(self) -> level:
        """Get the current log level of this sink."""
        ...

    def set_pattern(self, pattern: str) -> None:
        """Set the formatting pattern for this sink."""
        ...

class stdout_color_sink_mt(sink):
    """Multi-threaded stdout color sink."""

    def __init__(self, mode: color_mode = ...) -> None:
        """
        Initialize the sink.

        Args:
            mode: Color mode (default: automatic)
        """
        ...

class stdout_color_sink_st(sink):
    """Single-threaded stdout color sink."""

    def __init__(self, mode: color_mode = ...) -> None:
        """
        Initialize the sink.

        Args:
            mode: Color mode (default: automatic)
        """
        ...

class stderr_color_sink_mt(sink):
    """Multi-threaded stderr color sink."""

    def __init__(self, mode: color_mode = ...) -> None:
        """
        Initialize the sink.

        Args:
            mode: Color mode (default: automatic)
        """
        ...

class stderr_color_sink_st(sink):
    """Single-threaded stderr color sink."""

    def __init__(self, mode: color_mode = ...) -> None:
        """
        Initialize the sink.

        Args:
            mode: Color mode (default: automatic)
        """
        ...

class stdout_sink_mt(sink):
    """Multi-threaded stdout sink."""

    def __init__(self) -> None:
        """Initialize the sink."""
        ...

class stdout_sink_st(sink):
    """Single-threaded stdout sink."""

    def __init__(self) -> None:
        """Initialize the sink."""
        ...

class stderr_sink_mt(sink):
    """Multi-threaded stderr sink."""

    def __init__(self) -> None:
        """Initialize the sink."""
        ...

class stderr_sink_st(sink):
    """Single-threaded stderr sink."""

    def __init__(self) -> None:
        """Initialize the sink."""
        ...

class basic_file_sink_mt(sink):
    """Multi-threaded basic file sink."""

    def __init__(self, filename: str, truncate: bool = False) -> None:
        """
        Initialize the sink.

        Args:
            filename: Path to the log file
            truncate: Whether to truncate the file (default: False)
        """
        ...

class basic_file_sink_st(sink):
    """Single-threaded basic file sink."""

    def __init__(self, filename: str, truncate: bool = False) -> None:
        """
        Initialize the sink.

        Args:
            filename: Path to the log file
            truncate: Whether to truncate the file (default: False)
        """
        ...

class rotating_file_sink_mt(sink):
    """Multi-threaded rotating file sink."""

    def __init__(self, filename: str, max_size: int, max_files: int) -> None:
        """
        Initialize the sink.

        Args:
            filename: Path to the log file
            max_size: Maximum file size in bytes
            max_files: Maximum number of rotated files to keep
        """
        ...

class rotating_file_sink_st(sink):
    """Single-threaded rotating file sink."""

    def __init__(self, filename: str, max_size: int, max_files: int) -> None:
        """
        Initialize the sink.

        Args:
            filename: Path to the log file
            max_size: Maximum file size in bytes
            max_files: Maximum number of rotated files to keep
        """
        ...

class daily_file_sink_mt(sink):
    """Multi-threaded daily file sink."""

    def __init__(self, filename: str, hour: int = 0, minute: int = 0) -> None:
        """
        Initialize the sink.

        Args:
            filename: Path to the log file
            hour: Hour at which to rotate (0-23, default: 0)
            minute: Minute at which to rotate (0-59, default: 0)
        """
        ...

    def filename(self) -> str:
        """Get the current log file name"""
        ...

class daily_file_sink_st(sink):
    """Single-threaded daily file sink."""

    def __init__(self, filename: str, hour: int = 0, minute: int = 0) -> None:
        """
        Initialize the sink.

        Args:
            filename: Path to the log file
            hour: Hour at which to rotate (0-23, default: 0)
            minute: Minute at which to rotate (0-59, default: 0)
        """
        ...

    def filename(self) -> str:
        """Get the current log file name"""
        ...

class null_sink_st(sink):
    """Single-threaded null sink (discards all messages)."""

    def __init__(self) -> None:
        """Initialize the sink."""
        ...

class logger:
    """Logger class for logging messages."""

    def __init__(self, name: str, sink: Optional[SinkPtr] = None, sinks: Optional[List[SinkPtr]] = None) -> None:
        """
        Initialize a logger.

        Args:
            name: Logger name
            sink: Single sink (mutually exclusive with sinks)
            sinks: List of sinks (mutually exclusive with sink)
        """
        ...

    def trace(self, msg: str) -> None:
        """Log a trace message."""
        ...

    def debug(self, msg: str) -> None:
        """Log a debug message."""
        ...

    def info(self, msg: str) -> None:
        """Log an info message."""
        ...

    def warn(self, msg: str) -> None:
        """Log a warning message."""
        ...

    def error(self, msg: str) -> None:
        """Log an error message."""
        ...

    def critical(self, msg: str) -> None:
        """Log a critical message."""
        ...

    def log(self, lvl: level, msg: str) -> None:
        """
        Log a message with the specified level.

        Args:
            lvl: Log level
            msg: Message to log
        """
        ...

    def set_level(self, lvl: level) -> None:
        """Set the log level for this logger."""
        ...

    def level(self) -> level:
        """Get the current log level of this logger."""
        ...

    def name(self) -> str:
        """Get the logger name."""
        ...

    def set_pattern(self, pattern: str, time_type: pattern_time_type = ...) -> None:
        """
        Set the formatting pattern.

        Args:
            pattern: Format pattern string
            time_type: Time type (local or UTC, default: local)
        """
        ...

    def flush(self) -> None:
        """Flush any buffered messages."""
        ...

    def flush_on(self, lvl: level) -> None:
        """
        Set the level at which to automatically flush.

        Args:
            lvl: Log level to trigger flush
        """
        ...

    def sinks(self) -> List[SinkPtr]:
        """Get the list of sinks attached to this logger."""
        ...

    def should_log(self, lvl: level) -> bool:
        """
        Check if the logger would log at the given level.

        Args:
            lvl: Log level to check

        Returns:
            True if the logger would log at this level
        """
        ...

    def clone(self) -> logger:
        """Returns a clone of the logger"""
        ...

# Type aliases for clarity
SinkPtr: TypeAlias = sink # spdlog::sink_ptr is a shared_ptr<sink>
LoggerPtr: TypeAlias = logger # spdlog::logger_ptr is a shared_ptr<logger>

class _async_logger(logger):
    """Asynchronous logger (internal use)."""
    ...

# Async logger factory functions
@overload
def async_logger(name: str, sink: SinkPtr) -> _async_logger:
    """Create an async logger with a single sink."""
    ...

@overload
def async_logger(name: str, sinks: List[SinkPtr]) -> _async_logger:
    """Create an async logger with multiple sinks."""
    ...

def async_logger(name: str, sink_or_sinks: Union[SinkPtr, List[SinkPtr]]) -> _async_logger:
    """Create an async logger."""
    ...

# Global logger functions
def set_level(lvl: level) -> None:
    """Set the global log level."""
    ...

def get_level() -> level:
    """Get the global log level."""
    ...

def flush_on(lvl: level) -> None:
    """Set the global flush level."""
    ...

def flush_every(milliseconds: int) -> None:
    """
    Set periodic flushing interval.

    Args:
        milliseconds: Flush interval in milliseconds
    """
    ...

def set_pattern(pattern: str, time_type: pattern_time_type = ...) -> None:
    """
    Set the global formatting pattern.

    Args:
        pattern: Format pattern string
        time_type: Time type (local or UTC, default: local)
    """
    ...

# Global logging functions
def trace(msg: str) -> None:
    """Log a global trace message."""
    ...

def debug(msg: str) -> None:
    """Log a global debug message."""
    ...

def info(msg: str) -> None:
    """Log a global info message."""
    ...

def warn(msg: str) -> None:
    """Log a global warning message."""
    ...

def error(msg: str) -> None:
    """Log a global error message."""
    ...

def critical(msg: str) -> None:
    """Log a global critical message."""
    ...

# Logger registry functions
def set_default_logger(logger: LoggerPtr) -> None:
    """Set the default logger."""
    ...

def default_logger() -> LoggerPtr:
    """Get the default logger."""
    ...

def get(name: str) -> Optional[LoggerPtr]:
    """
    Get a logger by name.

    Args:
        name: Logger name

    Returns:
        Logger if found, None otherwise
    """
    ...

def drop(name: str) -> None:
    """
    Drop a logger from the registry.

    Args:
        name: Logger name to drop
    """
    ...

def drop_all() -> None:
    """Drop all loggers from the registry."""
    ...

def register_logger(logger: LoggerPtr) -> None:
    """
    Register a logger in the registry.

    Args:
        logger: Logger to register
    """
    ...

def apply_all(fun: Callable[[LoggerPtr], None]) -> None:
    """
    Apply a function to all registered loggers.

    Args:
        fun: Function to apply to each logger
    """
    ...

# Factory functions for common logger types
def stdout_color_mt(logger_name: str, mode: color_mode = ...) -> LoggerPtr:
    """
    Create a multi-threaded stdout color logger.

    Args:
        logger_name: Name of the logger
        mode: Color mode (default: automatic)

    Returns:
        Logger instance
    """
    ...

def stdout_color_st(logger_name: str, mode: color_mode = ...) -> LoggerPtr:
    """
    Create a single-threaded stdout color logger.

    Args:
        logger_name: Name of the logger
        mode: Color mode (default: automatic)

    Returns:
        Logger instance
    """
    ...

def stderr_color_mt(logger_name: str, mode: color_mode = ...) -> LoggerPtr:
    """
    Create a multi-threaded stderr color logger.

    Args:
        logger_name: Name of the logger
        mode: Color mode (default: automatic)

    Returns:
        Logger instance
    """
    ...

def stderr_color_st(logger_name: str, mode: color_mode = ...) -> LoggerPtr:
    """
    Create a single-threaded stderr color logger.

    Args:
        logger_name: Name of the logger
        mode: Color mode (default: automatic)

    Returns:
        Logger instance
    """
    ...

def stdout_logger_mt(logger_name: str) -> LoggerPtr:
    """
    Create a multi-threaded stdout logger.

    Args:
        logger_name: Name of the logger

    Returns:
        Logger instance
    """
    ...

def stdout_logger_st(logger_name: str) -> LoggerPtr:
    """
    Create a single-threaded stdout logger.

    Args:
        logger_name: Name of the logger

    Returns:
        Logger instance
    """
    ...

def stderr_logger_mt(logger_name: str) -> LoggerPtr:
    """
    Create a multi-threaded stderr logger.

    Args:
        logger_name: Name of the logger

    Returns:
        Logger instance
    """
    ...

def stderr_logger_st(logger_name: str) -> LoggerPtr:
    """
    Create a single-threaded stderr logger.

    Args:
        logger_name: Name of the logger

    Returns:
        Logger instance
    """
    ...

def basic_logger_mt(logger_name: str, filename: str, truncate: bool = False) -> LoggerPtr:
    """
    Create a multi-threaded basic file logger.

    Args:
        logger_name: Name of the logger
        filename: Path to the log file
        truncate: Whether to truncate the file (default: False)

    Returns:
        Logger instance
    """
    ...

def basic_logger_st(logger_name: str, filename: str, truncate: bool = False) -> LoggerPtr:
    """
    Create a single-threaded basic file logger.

    Args:
        logger_name: Name of the logger
        filename: Path to the log file
        truncate: Whether to truncate the file (default: False)

    Returns:
        Logger instance
    """
    ...

def rotating_logger_mt(logger_name: str, filename: str, max_size: int, max_files: int) -> LoggerPtr:
    """
    Create a multi-threaded rotating file logger.

    Args:
        logger_name: Name of the logger
        filename: Path to the log file
        max_size: Maximum file size in bytes
        max_files: Maximum number of rotated files to keep

    Returns:
        Logger instance
    """
    ...

def rotating_logger_st(logger_name: str, filename: str, max_size: int, max_files: int) -> LoggerPtr:
    """
    Create a single-threaded rotating file logger.

    Args:
        logger_name: Name of the logger
        filename: Path to the log file
        max_size: Maximum file size in bytes
        max_files: Maximum number of rotated files to keep

    Returns:
        Logger instance
    """
    ...

def daily_logger_mt(logger_name: str, filename: str, hour: int = 0, minute: int = 0) -> LoggerPtr:
    """
    Create a multi-threaded daily file logger.

    Args:
        logger_name: Name of the logger
        filename: Path to the log file
        hour: Hour at which to rotate (0-23, default: 0)
        minute: Minute at which to rotate (0-59, default: 0)

    Returns:
        Logger instance
    """
    ...

def daily_logger_st(logger_name: str, filename: str, hour: int = 0, minute: int = 0) -> LoggerPtr:
    """
    Create a single-threaded daily file logger.

    Args:
        logger_name: Name of the logger
        filename: Path to the log file
        hour: Hour at which to rotate (0-23, default: 0)
        minute: Minute at which to rotate (0-59, default: 0)

    Returns:
        Logger instance
    """
    ...
