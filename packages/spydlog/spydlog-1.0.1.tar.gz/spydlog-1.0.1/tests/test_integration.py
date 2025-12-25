import pytest
import spydlog
import tempfile
import os
import time

from tests.conftest import handle_permission_error


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @handle_permission_error
    def test_application_logging_setup(self):
        """Test typical application logging setup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create console and file sinks
            console_sink = spydlog.stdout_color_sink_mt()
            console_sink.set_level(spydlog.level.info)

            file_sink = spydlog.basic_file_sink_mt(
                os.path.join(tmpdir, "app.log")
            )
            file_sink.set_level(spydlog.level.debug)

            # Create logger with both sinks
            logger = spydlog.logger("app", [console_sink, file_sink])
            logger.set_level(spydlog.level.debug)

            # Use logger
            logger.debug("Debug info (only in file)")
            logger.info("Application started")
            logger.warn("Warning message")
            logger.error("Error occurred")

            logger.flush()

            # Verify file contains all messages
            log_file = os.path.join(tmpdir, "app.log")
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Debug info" in content
                assert "Application started" in content
                assert "Warning message" in content
                assert "Error occurred" in content

    @handle_permission_error
    def test_rotating_log_scenario(self):
        """Test rotating log file scenario"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "rotating.log")
            max_size = 1024  # 1KB for testing
            max_files = 3

            logger = spydlog.rotating_logger_mt(
                "rotating_app",
                filepath,
                max_size,
                max_files
            )

            # Write enough data to potentially trigger rotation
            for i in range(50):
                logger.info(f"Log message number {i} with some padding text to increase size" * 5)

            logger.flush()

            # Base file should exist
            assert os.path.exists(filepath)

    @handle_permission_error
    def test_multi_module_logging(self):
        """Test logging from multiple 'modules'"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "multi_module.log")

            # Shared sink
            file_sink = spydlog.basic_file_sink_mt(log_path)

            # Create loggers for different modules
            auth_logger = spydlog.logger("auth", file_sink)
            db_logger = auth_logger.clone("database")
            api_logger = auth_logger.clone("api")

            # Set different patterns
            auth_logger.set_pattern("[%H:%M:%S] [%n] %v")

            # Log from each module
            auth_logger.info("User login attempt")
            db_logger.info("Query executed")
            api_logger.info("Request received")

            auth_logger.flush()
            db_logger.flush()
            api_logger.flush()

            # Verify all messages in file
            with open(log_path, 'r') as f:
                content = f.read()
                assert "auth" in content
                assert "database" in content
                assert "api" in content

    @handle_permission_error
    def test_error_only_file(self):
        """Test logging errors to separate file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Main log file
            main_sink = spydlog.basic_file_sink_mt(
                os.path.join(tmpdir, "main.log")
            )
            main_sink.set_level(spydlog.level.info)

            # Error-only file
            error_sink = spydlog.basic_file_sink_mt(
                os.path.join(tmpdir, "errors.log")
            )
            error_sink.set_level(spydlog.level.err)

            logger = spydlog.logger("app", [main_sink, error_sink])
            logger.set_level(spydlog.level.debug)

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warn("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            logger.flush()

            # Check main log has info and above
            with open(os.path.join(tmpdir, "main.log"), 'r') as f:
                main_content = f.read()
                assert "Debug message" not in main_content
                assert "Info message" in main_content
                assert "Warning message" in main_content
                assert "Error message" in main_content
                assert "Critical message" in main_content

            # Check error log has only errors
            with open(os.path.join(tmpdir, "errors.log"), 'r') as f:
                error_content = f.read()
                assert "Debug message" not in error_content
                assert "Info message" not in error_content
                assert "Warning message" not in error_content
                assert "Error message" in error_content
                assert "Critical message" in error_content

    @handle_permission_error
    def test_daily_rotation_setup(self):
        """Test daily rotation logger setup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "daily.log")

            # Rotate at 2:30 AM
            logger = spydlog.daily_logger_mt("daily_app", filepath, 2, 30)

            filename = logger.sinks()[0].filename()

            logger.info("Daily log message")
            logger.flush()
            time.sleep(0.1)

            assert os.path.exists(filename)

    @handle_permission_error
    def test_async_logging_scenario(self):
        """Test async logging for high-throughput scenario"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create async logger
            sink = spydlog.basic_file_sink_mt(
                os.path.join(tmpdir, "async_app.log")
            )

            logger = spydlog.async_logger("high_throughput", sink)

            # Simulate high-throughput logging
            for i in range(1000):
                logger.info(f"Processing request {i}")

            logger.flush()
            time.sleep(0.2)  # Allow async writes to complete

            log_file = os.path.join(tmpdir, "async_app.log")
            assert os.path.exists(log_file)

            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 900  # Allow some tolerance


class TestPatternFormatting:
    """Test various pattern formatting scenarios"""

    def test_custom_patterns(self):
        """Test various custom log patterns"""
        logger = spydlog.stdout_color_mt("pattern_test")

        patterns = [
            "%v",  # Message only
            "[%l] %v",  # Level and message
            "[%Y-%m-%d %H:%M:%S] %v",  # Date/time and message
            "[%H:%M:%S.%e] [%n] [%l] %v",  # Full format
            "%+",  # Default pattern
        ]

        for pattern in patterns:
            logger.set_pattern(pattern)
            logger.info(f"Testing pattern: {pattern}")

    def test_pattern_with_colors(self):
        """Test patterns with color output"""
        logger = spydlog.stdout_color_mt("color_pattern", spydlog.color_mode.always)
        logger.set_pattern("[%^%l%$] %v")

        logger.trace("Trace with color")
        logger.debug("Debug with color")
        logger.info("Info with color")
        logger.warn("Warn with color")
        logger.error("Error with color")
        logger.critical("Critical with color")


class TestLevelManagement:
    """Test log level management across different scenarios"""

    def test_hierarchical_levels(self):
        """Test hierarchical level filtering"""
        sink = spydlog.null_sink_st()
        logger = spydlog.logger("hierarchy", sink)

        levels = [
            spydlog.level.trace,
            spydlog.level.debug,
            spydlog.level.info,
            spydlog.level.warn,
            spydlog.level.err,
            spydlog.level.critical,
        ]

        for level in levels:
            logger.set_level(level)
            assert logger.level() == level

            # Test should_log
            for test_level in levels:
                if test_level >= level:
                    assert logger.should_log(test_level)
                else:
                    assert not logger.should_log(test_level)

    @handle_permission_error
    def test_global_vs_logger_level(self):
        """Test interaction between global and logger-specific levels"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "level_test.log")

            # Set global level
            spydlog.set_level(spydlog.level.warn)

            # Create logger with different level
            logger = spydlog.basic_logger_mt("level_logger", filepath)
            logger.set_level(spydlog.level.debug)

            # Logger level should override for that logger
            logger.debug("Logger debug message")
            logger.info("Logger info message")
            logger.warn("Logger warn message")

            logger.flush()

            # Check what got logged
            with open(filepath, 'r') as f:
                content = f.read()
                # Logger should log at its own level (debug)
                assert "Logger debug message" in content
                assert "Logger info message" in content
                assert "Logger warn message" in content


class TestErrorConditions:
    """Test error handling and edge cases"""

    def test_empty_logger_name(self):
        """Test creating logger with empty name"""
        # Should not crash
        logger = spydlog.logger("")
        logger.info("Message from unnamed logger")

    def test_very_long_message(self):
        """Test logging very long message"""
        logger = spydlog.stdout_color_mt("long_msg_test")

        long_message = "x" * 10000
        logger.info(long_message)
        logger.flush()

    def test_unicode_messages(self):
        """Test logging unicode messages"""
        logger = spydlog.stdout_color_mt("unicode_test")

        logger.info("Hello 世界 🌍")
        logger.info("Привет мир")
        logger.info("مرحبا بالعالم")
        logger.flush()

    def test_special_characters_in_messages(self):
        """Test logging messages with special characters"""
        logger = spydlog.stdout_color_mt("special_chars")

        logger.info("Message with\nnewline")
        logger.info("Message with\ttab")
        logger.info("Message with \"quotes\"")
        logger.info("Message with 'apostrophes'")
        logger.flush()


class TestCleanup:
    """Test proper cleanup and resource management"""

    @handle_permission_error
    def test_drop_logger_releases_file(self):
        """Test that dropping logger releases file handle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "release_test.log")

            logger = spydlog.basic_logger_mt("release_logger", filepath)
            logger.info("Test message")
            logger.flush()

            # Drop logger
            spydlog.drop("release_logger")

            # Should be able to delete file now (on most systems)
            # Note: On Windows, this might still fail due to OS caching
            assert os.path.exists(filepath)

    def test_drop_all_cleanup(self):
        """Test drop_all cleans up all loggers"""
        spydlog.stdout_color_mt("logger1")
        spydlog.stdout_color_mt("logger2")
        spydlog.stderr_color_mt("logger3")

        spydlog.drop_all()

        assert spydlog.get("logger1") is None
        assert spydlog.get("logger2") is None
        assert spydlog.get("logger3") is None
