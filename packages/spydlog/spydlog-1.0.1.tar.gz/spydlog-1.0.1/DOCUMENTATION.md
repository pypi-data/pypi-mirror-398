# spydlog Documentation

## Overview

**spydlog** is a Python binding for the high-performance C++ logging library [spdlog](https://github.com/gabime/spdlog). It provides fast, thread-safe logging with multiple output targets (sinks), flexible formatting, and both synchronous and asynchronous logging capabilities.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Log Levels](#log-levels)
- [Loggers](#loggers)
- [Sinks](#sinks)
- [Patterns and Formatting](#patterns-and-formatting)
- [Async Logging](#async-logging)
- [Global Logging Functions](#global-logging-functions)
- [Logger Registry](#logger-registry)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)

## Installation

spydlog is supported on Python 3.9 up to the latest version (3.14). It is available on Windows, Linux and MacOS.

```bash
pip install spydlog
```

## Quick Start

```python
import spydlog as spd

# Use global logging functions
spd.info("Hello, World!")
spd.warn("This is a warning")
spd.error("An error occurred")

# Create a custom logger
logger = spd.stdout_color_mt("my_logger")
logger.info("Custom logger message")
logger.set_level(spd.level.debug)
logger.debug("Debug message")
```

## Core Concepts

### Loggers

A **logger** is the main interface for writing log messages. Each logger has:
- A unique name
- One or more sinks (output destinations)
- A log level that filters messages
- An optional message format pattern

### Sinks

A **sink** is an output destination for log messages. Common sinks include:
- Console output (stdout/stderr)
- Files (basic, rotating, daily)
- Null sink (discards messages)

### Thread Safety

spydlog provides both multi-threaded (`_mt`) and single-threaded (`_st`) variants:
- **Multi-threaded (`_mt`)**: Thread-safe, suitable for concurrent logging
- **Single-threaded (`_st`)**: Faster but not thread-safe, use only in single-threaded contexts

## Log Levels

spydlog supports six log levels, in order of increasing severity:

```python
import spydlog as spd

# Log levels
spd.level.trace      # Most verbose
spd.level.debug      # Debug information
spd.level.info       # Informational messages
spd.level.warn       # Warnings
spd.level.err        # Errors
spd.level.critical   # Critical errors
spd.level.off        # Disable logging
```

### Setting Log Levels

```python
# Set global log level
spd.set_level(spd.level.debug)

# Set level for specific logger
logger = spd.stdout_color_mt("my_logger")
logger.set_level(spd.level.warn)

# Check current level
current_level = spd.get_level()
logger_level = logger.level()
```

### Conditional Logging

```python
logger = spd.stdout_color_mt("my_logger")

# Check if a level would be logged
if logger.should_log(spd.level.debug):
    # Expensive operation only if debug is enabled
    debug_info = compute_expensive_debug_info()
    logger.debug(debug_info)
```

## Loggers

### Creating Loggers

#### Factory Functions (Recommended)

```python
import spydlog as spd

# Console loggers with color
logger1 = spd.stdout_color_mt("console_logger")
logger2 = spd.stderr_color_mt("error_logger")

# Console loggers without color
logger3 = spd.stdout_logger_mt("plain_console")
logger4 = spd.stderr_logger_mt("plain_error")

# File loggers
logger5 = spd.basic_logger_mt("file_logger", "logs/app.log")
logger6 = spd.rotating_logger_mt("rotating", "logs/rotating.log",
                                  max_size=1048576, max_files=3)
logger7 = spd.daily_logger_mt("daily", "logs/daily.log", hour=0, minute=0)
```

#### Manual Construction

```python
import spydlog as spd

# Create a sink
sink = spd.stdout_color_sink_mt()

# Create logger with single sink
logger = spd.logger("my_logger", sink=sink)

# Create logger with multiple sinks
sinks = [
    spd.stdout_color_sink_mt(),
    spd.basic_file_sink_mt("logs/app.log")
]
logger = spd.logger("multi_sink_logger", sinks=sinks)
```

### Logging Messages

```python
logger = spd.stdout_color_mt("my_logger")

# Basic logging
logger.trace("Trace message")
logger.debug("Debug message")
logger.info("Info message")
logger.warn("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# Generic log method
logger.log(spd.level.info, "Generic log message")
```

### Logger Configuration

```python
logger = spd.stdout_color_mt("my_logger")

# Set log level
logger.set_level(spd.level.debug)

# Set pattern
logger.set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%n] [%l] %v")

# Set pattern with UTC time
logger.set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%n] [%l] %v",
                   spd.pattern_time_type.utc)

# Configure automatic flushing
logger.flush_on(spd.level.error)  # Flush on error and above

# Manual flush
logger.flush()
```

### Logger Properties

```python
logger = spd.stdout_color_mt("my_logger")

# Get logger name
name = logger.name()

# Get attached sinks
sinks = logger.sinks()

# Get current level
level = logger.level()
```

## Sinks

### Console Sinks

#### Color Sinks

```python
import spydlog as spd

# Multi-threaded color sinks
stdout_sink = spd.stdout_color_sink_mt()
stderr_sink = spd.stderr_color_sink_mt()

# Single-threaded color sinks
stdout_sink_st = spd.stdout_color_sink_st()
stderr_sink_st = spd.stderr_color_sink_st()

# Control color mode
sink = spd.stdout_color_sink_mt(spd.color_mode.always)
sink = spd.stdout_color_sink_mt(spd.color_mode.automatic)
sink = spd.stdout_color_sink_mt(spd.color_mode.never)
```

#### Plain Sinks

```python
# Multi-threaded plain sinks
stdout_sink = spd.stdout_sink_mt()
stderr_sink = spd.stderr_sink_mt()

# Single-threaded plain sinks
stdout_sink_st = spd.stdout_sink_st()
stderr_sink_st = spd.stderr_sink_st()
```

### File Sinks

#### Basic File Sink

```python
# Create or append to file
sink = spd.basic_file_sink_mt("logs/app.log")

# Truncate file on open
sink = spd.basic_file_sink_mt("logs/app.log", truncate=True)

# Single-threaded variant
sink_st = spd.basic_file_sink_st("logs/app.log")
```

#### Rotating File Sink

```python
# Rotate when file reaches max_size
# Keep max_files rotated files
sink = spd.rotating_file_sink_mt(
    filename="logs/rotating.log",
    max_size=1048576,      # 1 MB
    max_files=3            # Keep 3 backup files
)

# Single-threaded variant
sink_st = spd.rotating_file_sink_st("logs/rotating.log", 1048576, 3)
```

#### Daily File Sink

```python
# Rotate daily at specified time
sink = spd.daily_file_sink_mt(
    filename="logs/daily.log",
    hour=0,      # Rotate at midnight
    minute=0
)

# Rotate at 3:30 AM
sink = spd.daily_file_sink_mt("logs/daily.log", hour=3, minute=30)

# Single-threaded variant
sink_st = spd.daily_file_sink_st("logs/daily.log", 0, 0)
```

#### Null Sink

```python
# Discard all messages (useful for testing)
sink = spd.null_sink_st()
```

### Sink Configuration

```python
sink = spd.stdout_color_sink_mt()

# Set sink level (independent of logger level)
sink.set_level(spd.level.warn)

# Get sink level
level = sink.level()

# Set sink pattern
sink.set_pattern("[%H:%M:%S] %v")

# Log directly to sink (uncommon)
sink.log(spd.level.info, "Direct message to sink")
```

### Multiple Sinks Example

```python
import spydlog as spd

# Create multiple sinks
console_sink = spd.stdout_color_sink_mt()
console_sink.set_level(spd.level.info)

file_sink = spd.basic_file_sink_mt("logs/all.log")
file_sink.set_level(spd.level.trace)

error_sink = spd.basic_file_sink_mt("logs/errors.log")
error_sink.set_level(spd.level.err)

# Create logger with all sinks
logger = spd.logger("multi_sink", sinks=[console_sink, file_sink, error_sink])

# Info goes to console and all.log
logger.info("Info message")

# Error goes to all three sinks
logger.error("Error message")
```

## Patterns and Formatting

### Pattern Syntax

spydlog uses a pattern string to format log messages. Common pattern flags:

| Flag | Description | Example |
|------|-------------|---------|
| `%v` | The actual message | "Log message" |
| `%t` | Thread ID | "1234" |
| `%P` | Process ID | "5678" |
| `%n` | Logger name | "my_logger" |
| `%l` | Log level (short) | "I", "W", "E" |
| `%L` | Log level (full) | "info", "warning" |
| `%Y` | Year (4 digits) | "2025" |
| `%m` | Month (01-12) | "03" |
| `%d` | Day (01-31) | "15" |
| `%H` | Hour (00-23) | "14" |
| `%M` | Minute (00-59) | "30" |
| `%S` | Second (00-59) | "45" |
| `%e` | Milliseconds (000-999) | "123" |
| `%f` | Microseconds (000000-999999) | "123456" |
| `%F` | Nanoseconds (000000000-999999999) | "123456789" |
| `%a` | Weekday (short) | "Mon" |
| `%A` | Weekday (full) | "Monday" |
| `%b` | Month (short) | "Mar" |
| `%B` | Month (full) | "March" |
| `%c` | Date and time | "Mon Mar 15 14:30:45 2025" |
| `%+` | ISO 8601 format | "2025-03-15T14:30:45.123" |

### Setting Patterns

```python
import spydlog as spd

# Global pattern
spd.set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%n] [%^%l%$] %v")

# Logger-specific pattern
logger = spd.stdout_color_mt("my_logger")
logger.set_pattern("[%H:%M:%S] %v")

# UTC time instead of local time
logger.set_pattern("[%Y-%m-%d %H:%M:%S] %v", spd.pattern_time_type.utc)

# Sink-specific pattern
sink = spd.stdout_color_sink_mt()
sink.set_pattern("%v")  # Only message, no metadata
```

### Common Pattern Examples

```python
# Compact format
logger.set_pattern("[%H:%M:%S] %v")
# Output: [14:30:45] Log message

# Detailed format
logger.set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%n] [%l] %v")
# Output: [2025-12-21 14:30:45.123] [my_logger] [info] Log message

# With thread ID
logger.set_pattern("[%H:%M:%S.%e] [thread %t] %v")
# Output: [14:30:45.123] [thread 1234] Log message

# ISO 8601 format
logger.set_pattern("%+")
# Output: 2025-12-21T14:30:45.123

# Color emphasis for level
logger.set_pattern("[%H:%M:%S] [%^%l%$] %v")
# Color codes are applied to the level
```

## Async Logging

Asynchronous logging improves performance by offloading log writes to a background thread.

### Creating Async Loggers

```python
import spydlog as spd

# Create async logger with single sink
sink = spd.basic_file_sink_mt("logs/async.log")
async_logger = spd.async_logger("async_logger", sink)

# Create async logger with multiple sinks
sinks = [
    spd.stdout_color_sink_mt(),
    spd.basic_file_sink_mt("logs/async.log")
]
async_logger = spd.async_logger("multi_async", sinks)
```

### Async Overflow Policy

```python
# Control what happens when async queue is full
# (Note: Configuration typically done at library initialization)

# Block until space is available (default)
spd.async_overflow_policy.block

# Drop oldest messages
spd.async_overflow_policy.overrun_oldest
```

### Async Logging Example

```python
import spydlog as spd

# Create async logger
sink = spd.basic_file_sink_mt("logs/async.log")
logger = spd.async_logger("async_logger", sink)

# Use exactly like synchronous logger
logger.info("Async log message")
logger.warn("Warning message")

# Ensure all messages are written before exit
logger.flush()
```

## Global Logging Functions

spydlog provides convenient global logging functions that use the default logger.

### Basic Logging

```python
import spydlog as spd

spd.trace("Trace message")
spd.debug("Debug message")
spd.info("Info message")
spd.warn("Warning message")
spd.error("Error message")
spd.critical("Critical message")
```

### Global Configuration

```python
import spydlog as spd

# Set global log level
spd.set_level(spd.level.debug)

# Get global log level
level = spd.get_level()

# Set global pattern
spd.set_pattern("[%H:%M:%S] %v")

# Set global flush level
spd.flush_on(spd.level.error)

# Periodic flushing (every N milliseconds)
spd.flush_every(5000)  # Flush every 5 seconds
```

## Logger Registry

The logger registry manages all created loggers, allowing retrieval by name.

### Working with the Registry

```python
import spydlog as spd

# Create and register a logger
logger = spd.stdout_color_mt("my_logger")

# Retrieve logger by name
logger = spd.get("my_logger")
if logger is None:
    print("Logger not found")

# Get default logger
default = spd.default_logger()

# Set default logger
custom_default = spd.stdout_color_mt("custom_default")
spd.set_default_logger(custom_default)

# Register a manually created logger
sink = spd.stdout_color_sink_mt()
logger = spd.logger("manual_logger", sink=sink)
spd.register_logger(logger)

# Remove logger from registry
spd.drop("my_logger")

# Remove all loggers
spd.drop_all()
```

### Apply Function to All Loggers

```python
import spydlog as spd

# Create multiple loggers
spd.stdout_color_mt("logger1")
spd.stdout_color_mt("logger2")
spd.stdout_color_mt("logger3")

# Apply function to all registered loggers
def set_debug_level(logger):
    logger.set_level(spd.level.debug)

spd.apply_all(set_debug_level)

# Or with lambda
spd.apply_all(lambda l: l.set_pattern("[%H:%M:%S] %v"))
```

## Advanced Usage

### Conditional Compilation

Use `should_log()` to avoid expensive computations when a log level is disabled:

```python
import spydlog as spd

logger = spd.stdout_color_mt("my_logger")
logger.set_level(spd.level.info)

# Expensive operation only runs if debug is enabled
if logger.should_log(spd.level.debug):
    expensive_data = compute_expensive_debug_info()
    logger.debug(expensive_data)
```

### Custom Sink Combinations

```python
import spydlog as spd

# Console with minimal info
console_sink = spd.stdout_color_sink_mt()
console_sink.set_level(spd.level.info)
console_sink.set_pattern("[%H:%M:%S] [%^%l%$] %v")

# File with everything
file_sink = spd.basic_file_sink_mt("logs/debug.log")
file_sink.set_level(spd.level.trace)
file_sink.set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%n] [%l] [thread %t] %v")

# Error file
error_sink = spd.basic_file_sink_mt("logs/errors.log")
error_sink.set_level(spd.level.err)

# Combine all
logger = spd.logger("app", sinks=[console_sink, file_sink, error_sink])
```

### Rotating Logs Best Practices

```python
import spydlog as spd

# Keep logs under 10 MB total (5 files × 2 MB each)
logger = spd.rotating_logger_mt(
    "app",
    "logs/app.log",
    max_size=2 * 1024 * 1024,  # 2 MB
    max_files=5
)

# Daily logs, keep 7 days
logger = spd.daily_logger_mt(
    "daily",
    "logs/app-%Y-%m-%d.log",
    hour=0,
    minute=0
)
```

### Multi-threaded Logging

```python
import spydlog as spd
import threading

# Create thread-safe logger
logger = spd.stdout_color_mt("threaded_logger")

def worker(thread_id):
    for i in range(10):
        logger.info(f"Thread {thread_id}: Message {i}")

# Start multiple threads
threads = []
for i in range(5):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Ensure all messages are written
logger.flush()
```

## API Reference

### Enumerations

#### `level`

Log level constants:
- `trace`: Most verbose
- `debug`: Debug information
- `info`: Informational messages
- `warn`: Warning messages
- `err`: Error messages
- `critical`: Critical errors
- `off`: Disable logging

Supports comparison operators: `<`, `<=`, `>`, `>=`

#### `color_mode`

Color output modes:
- `always`: Always use colors
- `automatic`: Use colors if terminal supports them
- `never`: Never use colors

#### `pattern_time_type`

Time format for patterns:
- `local`: Local time (default)
- `utc`: UTC time

#### `async_overflow_policy`

Behavior when async queue is full:
- `block`: Block until space is available
- `overrun_oldest`: Drop oldest messages

### Classes

#### `logger`

**Constructor:**
```python
logger(name: str, sink: Optional[sink] = None, sinks: Optional[List[sink]] = None)
```

**Methods:**
- `trace(msg: str)`: Log trace message
- `debug(msg: str)`: Log debug message
- `info(msg: str)`: Log info message
- `warn(msg: str)`: Log warning message
- `error(msg: str)`: Log error message
- `critical(msg: str)`: Log critical message
- `log(lvl: level, msg: str)`: Log with specific level
- `set_level(lvl: level)`: Set minimum log level
- `level() -> level`: Get current log level
- `name() -> str`: Get logger name
- `set_pattern(pattern: str, time_type: pattern_time_type = local)`: Set format pattern
- `flush()`: Flush buffered messages
- `flush_on(lvl: level)`: Auto-flush at level
- `sinks() -> List[sink]`: Get attached sinks
- `should_log(lvl: level) -> bool`: Check if level would be logged
- `clone() -> logger`: Returns a clone of the logger

#### `sink`

Base class for all sinks.

**Methods:**
- `log(lvl: level, msg: str)`: Log message
- `set_level(lvl: level)`: Set sink log level
- `level() -> level`: Get sink log level
- `set_pattern(pattern: str)`: Set sink pattern

### Factory Functions

#### Console Loggers

```python
stdout_color_mt(logger_name: str, mode: color_mode = automatic) -> logger
stdout_color_st(logger_name: str, mode: color_mode = automatic) -> logger
stderr_color_mt(logger_name: str, mode: color_mode = automatic) -> logger
stderr_color_st(logger_name: str, mode: color_mode = automatic) -> logger
stdout_logger_mt(logger_name: str) -> logger
stdout_logger_st(logger_name: str) -> logger
stderr_logger_mt(logger_name: str) -> logger
stderr_logger_st(logger_name: str) -> logger
```

#### File Loggers

```python
basic_logger_mt(logger_name: str, filename: str, truncate: bool = False) -> logger
basic_logger_st(logger_name: str, filename: str, truncate: bool = False) -> logger
rotating_logger_mt(logger_name: str, filename: str, max_size: int, max_files: int) -> logger
rotating_logger_st(logger_name: str, filename: str, max_size: int, max_files: int) -> logger
daily_logger_mt(logger_name: str, filename: str, hour: int = 0, minute: int = 0) -> logger
daily_logger_st(logger_name: str, filename: str, hour: int = 0, minute: int = 0) -> logger
```

#### Async Loggers

```python
async_logger(name: str, sink: sink) -> logger
async_logger(name: str, sinks: List[sink]) -> logger
```

### Global Functions

#### Logging

```python
trace(msg: str)
debug(msg: str)
info(msg: str)
warn(msg: str)
error(msg: str)
critical(msg: str)
```

#### Configuration

```python
set_level(lvl: level)
get_level() -> level
flush_on(lvl: level)
flush_every(milliseconds: int)
set_pattern(pattern: str, time_type: pattern_time_type = local)
```

#### Registry

```python
set_default_logger(logger: logger)
default_logger() -> logger
get(name: str) -> Optional[logger]
drop(name: str)
drop_all()
register_logger(logger: logger)
apply_all(fun: Callable[[logger], None])
```

## Best Practices

1. **Choose the right threading model**: Use `_mt` variants in multi-threaded applications, `_st` for single-threaded performance
2. **Use appropriate log levels**: Reserve `trace` and `debug` for development, use `info` for production
3. **Configure flush behavior**: Use `flush_on(level.error)` to ensure errors are immediately written
4. **Leverage multiple sinks**: Send different log levels to different destinations
5. **Use async logging for performance**: When logging performance matters, use async loggers
6. **Manage log rotation**: Use rotating or daily sinks to prevent unbounded log growth
7. **Optimize patterns**: Simpler patterns are faster to format
8. **Use `should_log()` for expensive operations**: Avoid computing debug info when debug is disabled

---

**Note**: This documentation covers the Python binding interface. For more information about the underlying spdlog library, visit the [spdlog GitHub repository](https://github.com/gabime/spdlog).
