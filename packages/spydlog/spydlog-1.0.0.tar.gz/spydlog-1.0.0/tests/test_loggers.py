import pytest
import spydlog
import tempfile
import os

from tests.conftest import handle_permission_error


class TestLoggerCreation:
    """Test logger creation with different constructors"""

    def test_logger_name_only(self):
        """Test creating logger with name only"""
        logger = spydlog.logger("test_logger")
        assert logger.name() == "test_logger"

    def test_logger_with_single_sink(self):
        """Test creating logger with single sink"""
        sink = spydlog.stdout_color_sink_mt()
        logger = spydlog.logger("single_sink_logger", sink)
        assert logger.name() == "single_sink_logger"
        assert len(logger.sinks()) == 1

    def test_logger_with_multiple_sinks(self):
        """Test creating logger with multiple sinks"""
        sink1 = spydlog.stdout_color_sink_mt()
        sink2 = spydlog.stderr_color_sink_mt()
        sink3 = spydlog.null_sink_st()

        logger = spydlog.logger("multi_sink_logger", [sink1, sink2, sink3])
        assert logger.name() == "multi_sink_logger"
        assert len(logger.sinks()) == 3

    @handle_permission_error
    def test_logger_with_file_sink(self):
        """Test creating logger with file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "logger_test.log")
            sink = spydlog.basic_file_sink_mt(filepath)
            logger = spydlog.logger("file_logger", sink)

            logger.info("Test message to file")
            logger.flush()

            assert os.path.exists(filepath)


class TestLoggerMethods:
    """Test logger methods"""

    @pytest.fixture
    def logger(self):
        """Create a test logger"""
        sink = spydlog.stdout_color_sink_mt()
        return spydlog.logger("test_logger", sink)

    def test_logger_trace(self, logger):
        """Test trace logging"""
        logger.set_level(spydlog.level.trace)
        logger.trace("trace message")

    def test_logger_debug(self, logger):
        """Test debug logging"""
        logger.set_level(spydlog.level.debug)
        logger.debug("debug message")

    def test_logger_info(self, logger):
        """Test info logging"""
        logger.info("info message")

    def test_logger_warn(self, logger):
        """Test warn logging"""
        logger.warn("warn message")

    def test_logger_error(self, logger):
        """Test error logging"""
        logger.error("error message")

    def test_logger_critical(self, logger):
        """Test critical logging"""
        logger.critical("critical message")

    def test_logger_log_with_level(self, logger):
        """Test generic log method with level"""
        logger.log(spydlog.level.info, "info via log()")
        logger.log(spydlog.level.warn, "warn via log()")
        logger.log(spydlog.level.err, "error via log()")

    def test_logger_set_level(self, logger):
        """Test setting logger level"""
        logger.set_level(spydlog.level.debug)
        assert logger.level() == spydlog.level.debug

        logger.set_level(spydlog.level.warn)
        assert logger.level() == spydlog.level.warn

    def test_logger_should_log(self, logger):
        """Test should_log method"""
        logger.set_level(spydlog.level.info)

        assert logger.should_log(spydlog.level.info)
        assert logger.should_log(spydlog.level.warn)
        assert not logger.should_log(spydlog.level.debug)
        assert not logger.should_log(spydlog.level.trace)

    def test_logger_flush(self, logger):
        """Test flush method"""
        logger.info("Message before flush")
        logger.flush()
        logger.info("Message after flush")

    def test_logger_flush_on(self, logger):
        """Test flush_on method"""
        logger.flush_on(spydlog.level.err)
        logger.error("This should trigger flush")

    def test_logger_set_pattern(self, logger):
        """Test setting logger pattern"""
        logger.set_pattern("[%Y-%m-%d %H:%M:%S] [%n] [%l] %v")
        logger.info("Message with custom pattern")

        logger.set_pattern("%+")  # Reset
        logger.info("Message with default pattern")

    def test_logger_name(self, logger):
        """Test getting logger name"""
        assert logger.name() == "test_logger"

    def test_logger_sinks(self, logger):
        """Test accessing logger sinks"""
        sinks = logger.sinks()
        assert len(sinks) >= 1


class TestLoggerFiltering:
    """Test logger level filtering"""

    @handle_permission_error
    def test_logger_filters_by_level(self):
        """Test that logger respects level filtering"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "filter_test.log")
            sink = spydlog.basic_file_sink_mt(filepath)
            logger = spydlog.logger("filter_logger", sink)

            logger.set_level(spydlog.level.warn)

            logger.debug("This should not appear")
            logger.info("This should not appear")
            logger.warn("This should appear")
            logger.error("This should appear")

            logger.flush()

            with open(filepath, 'r') as f:
                content = f.read()
                assert "should not appear" not in content
                assert "should appear" in content


class TestMultipleSinks:
    """Test logger with multiple sinks"""

    @handle_permission_error
    def test_logger_writes_to_all_sinks(self):
        """Test that messages go to all sinks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "sink1.log")
            file2 = os.path.join(tmpdir, "sink2.log")

            sink1 = spydlog.basic_file_sink_mt(file1)
            sink2 = spydlog.basic_file_sink_mt(file2)

            logger = spydlog.logger("multi_logger", [sink1, sink2])
            logger.info("Message to multiple sinks")
            logger.flush()

            assert os.path.exists(file1)
            assert os.path.exists(file2)

            with open(file1, 'r') as f:
                content1 = f.read()
                assert "multiple sinks" in content1

            with open(file2, 'r') as f:
                content2 = f.read()
                assert "multiple sinks" in content2

    @handle_permission_error
    def test_sinks_with_different_levels(self):
        """Test multiple sinks with different log levels"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_debug = os.path.join(tmpdir, "debug.log")
            file_error = os.path.join(tmpdir, "error.log")

            sink_debug = spydlog.basic_file_sink_mt(file_debug)
            sink_debug.set_level(spydlog.level.debug)

            sink_error = spydlog.basic_file_sink_mt(file_error)
            sink_error.set_level(spydlog.level.err)

            logger = spydlog.logger("level_logger", [sink_debug, sink_error])
            logger.set_level(spydlog.level.debug)

            logger.debug("Debug message")
            logger.info("Info message")
            logger.error("Error message")
            logger.flush()

            with open(file_debug, 'r') as f:
                debug_content = f.read()
                assert "Debug message" in debug_content
                assert "Info message" in debug_content
                assert "Error message" in debug_content

            with open(file_error, 'r') as f:
                error_content = f.read()
                assert "Debug message" not in error_content
                assert "Info message" not in error_content
                assert "Error message" in error_content
