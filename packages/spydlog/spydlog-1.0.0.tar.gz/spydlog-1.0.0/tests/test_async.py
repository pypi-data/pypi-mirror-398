import pytest
import spydlog
import tempfile
import os
import time

from tests.conftest import handle_permission_error


class TestAsyncOverflowPolicy:
    """Test async overflow policy enum"""

    def test_async_overflow_policy_enum(self):
        """Test that async overflow policy enum exists"""
        assert hasattr(spydlog.async_overflow_policy, 'block')
        assert hasattr(spydlog.async_overflow_policy, 'overrun_oldest')

    def test_async_overflow_policy_values(self):
        """Test that policy values are distinct"""
        assert spydlog.async_overflow_policy.block != spydlog.async_overflow_policy.overrun_oldest


class TestAsyncLogger:
    """Test async logger creation and operations"""

    def test_async_logger_with_single_sink(self):
        """Test creating async logger with single sink"""
        sink = spydlog.stdout_color_sink_mt()

        logger = spydlog.async_logger("async_single", sink)
        assert logger.name() == "async_single"
        assert isinstance(logger, spydlog.logger)

    def test_async_logger_with_multiple_sinks(self):
        """Test creating async logger with multiple sinks"""
        sink1 = spydlog.stdout_color_sink_mt()
        sink2 = spydlog.null_sink_st()

        logger = spydlog.async_logger("async_multi", [sink1, sink2])
        assert logger.name() == "async_multi"
        assert len(logger.sinks()) == 2

    @handle_permission_error
    def test_async_logger_logging(self):
        """Test logging with async logger"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "async_test.log")
            sink = spydlog.basic_file_sink_mt(filepath)

            logger = spydlog.async_logger("async_log_test", sink)

            logger.info("Async info message")
            logger.warn("Async warn message")
            logger.error("Async error message")

            # Flush to ensure messages are written
            logger.flush()
            time.sleep(0.1)

            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                content = f.read()
                assert "Async info message" in content
                assert "Async warn message" in content
                assert "Async error message" in content

    def test_async_logger_all_log_levels(self):
        """Test all log levels with async logger"""
        sink = spydlog.null_sink_st()

        logger = spydlog.async_logger("async_levels", sink)
        logger.set_level(spydlog.level.trace)

        # Should not crash
        logger.trace("trace message")
        logger.debug("debug message")
        logger.info("info message")
        logger.warn("warn message")
        logger.error("error message")
        logger.critical("critical message")

        logger.flush()

    @handle_permission_error
    def test_async_logger_level_filtering(self):
        """Test level filtering with async logger"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "async_filter.log")
            sink = spydlog.basic_file_sink_mt(filepath)

            logger = spydlog.async_logger("async_filter", sink)
            logger.set_level(spydlog.level.warn)

            logger.debug("Should not appear")
            logger.info("Should not appear")
            logger.warn("Should appear")
            logger.error("Should appear")

            logger.flush()
            time.sleep(0.1)

            with open(filepath, 'r') as f:
                content = f.read()
                assert "Should not appear" not in content
                assert "Should appear" in content

    def test_async_logger_set_pattern(self):
        """Test setting pattern on async logger"""
        sink = spydlog.stdout_color_sink_mt()

        logger = spydlog.async_logger("async_pattern", sink)
        logger.set_pattern("[%H:%M:%S] [%n] %v")
        logger.info("Custom pattern message")
        logger.flush()

    @handle_permission_error
    def test_async_logger_flush(self):
        """Test explicit flush on async logger"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "async_flush.log")
            sink = spydlog.basic_file_sink_mt(filepath)

            logger = spydlog.async_logger("async_flush", sink)

            logger.info("Message 1")
            logger.info("Message 2")
            logger.flush()
            time.sleep(0.1)

            logger.info("Message 3")
            logger.flush()
            time.sleep(0.1)

            with open(filepath, 'r') as f:
                content = f.read()
                assert "Message 1" in content
                assert "Message 2" in content
                assert "Message 3" in content


class TestAsyncLoggerPerformance:
    """Test async logger performance characteristics"""

    def test_async_logger_high_throughput(self):
        """Test async logger with many messages"""
        sink = spydlog.null_sink_st()

        logger = spydlog.async_logger("async_throughput", sink)

        # Log many messages
        for i in range(1000):
            logger.info(f"Message {i}")

        logger.flush()
        # Should complete without issues

    @handle_permission_error
    def test_async_logger_with_file_sink(self):
        """Test async logger performance with file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "async_perf.log")
            sink = spydlog.basic_file_sink_mt(filepath)

            logger = spydlog.async_logger("async_perf", sink)

            num_messages = 100
            for i in range(num_messages):
                logger.info(f"Performance test message {i}")

            logger.flush()
            time.sleep(0.2)  # Give time for async writes

            assert os.path.exists(filepath)

            with open(filepath, 'r') as f:
                lines = f.readlines()
                # Should have written all messages
                assert len(lines) >= num_messages


class TestAsyncLoggerWithRegistry:
    """Test async logger with logger registry"""

    def test_register_async_logger(self):
        """Test registering async logger"""
        sink = spydlog.stdout_color_sink_mt()

        logger = spydlog.async_logger("registered_async", sink)
        spydlog.register_logger(logger)

        retrieved = spydlog.get("registered_async")
        assert retrieved is not None
        assert retrieved.name() == "registered_async"

    def test_async_logger_as_default(self):
        """Test setting async logger as default"""
        sink = spydlog.stdout_color_sink_mt()

        logger = spydlog.async_logger("default_async", sink)
        spydlog.set_default_logger(logger)

        default = spydlog.default_logger()
        assert default.name() == "default_async"

        # Global logging should use this logger
        spydlog.info("Message via default async logger")


class TestAsyncLoggerConcurrency:
    """Test async logger in concurrent scenarios"""

    def test_multiple_async_loggers(self):
        """Test creating multiple async loggers"""
        logger1 = spydlog.async_logger("async1", spydlog.null_sink_st())
        logger2 = spydlog.async_logger("async2", spydlog.null_sink_st())
        logger3 = spydlog.async_logger("async3", spydlog.null_sink_st())

        logger1.info("From logger1")
        logger2.info("From logger2")
        logger3.info("From logger3")

        logger1.flush()
        logger2.flush()
        logger3.flush()

    def test_mixed_sync_async_loggers(self):
        """Test using both sync and async loggers"""
        sync_logger = spydlog.stdout_color_mt("sync")
        async_logger = spydlog.async_logger("async", spydlog.stdout_color_sink_mt())

        sync_logger.info("From sync logger")
        async_logger.info("From async logger")

        async_logger.flush()
