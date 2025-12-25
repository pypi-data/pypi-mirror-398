import spydlog

class TestBasicLogging:
    """Test basic global logging functions"""

    def test_log_levels_enum(self):
        """Test that all log levels are available"""
        assert hasattr(spydlog.level, "trace")
        assert hasattr(spydlog.level, "debug")
        assert hasattr(spydlog.level, "info")
        assert hasattr(spydlog.level, "warn")
        assert hasattr(spydlog.level, "err")
        assert hasattr(spydlog.level, "critical")
        assert hasattr(spydlog.level, "off")

    def test_global_logging_functions(self):
        """Test global logging functions don't crash"""
        spydlog.trace("trace message")
        spydlog.debug("debug message")
        spydlog.info("info message")
        spydlog.warn("warn message")
        spydlog.error("error message")
        spydlog.critical("critical message")

    def test_set_get_level(self):
        """Test setting and getting global log level"""
        spydlog.set_level(spydlog.level.debug)
        assert spydlog.get_level() == spydlog.level.debug

        spydlog.set_level(spydlog.level.info)
        assert spydlog.get_level() == spydlog.level.info

        spydlog.set_level(spydlog.level.warn)
        assert spydlog.get_level() == spydlog.level.warn

    def test_set_pattern(self):
        """Test setting log pattern"""
        spydlog.set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%l] %v")
        spydlog.info("pattern test message")

        spydlog.set_pattern("%+")  # Reset to default
        spydlog.info("default pattern message")

    def test_flush_on(self):
        """Test flush_on function"""
        spydlog.flush_on(spydlog.level.err)
        spydlog.error("This should trigger flush")

        spydlog.flush_on(spydlog.level.info)
        spydlog.info("This should also trigger flush")

    def test_flush_every(self):
        """Test flush_every function"""
        spydlog.flush_every(5000)  # Flush every 5 seconds
        spydlog.info("Message with periodic flush")


class TestDefaultLogger:
    """Test default logger operations"""

    def test_default_logger_exists(self):
        """Test that default logger can be retrieved"""
        logger = spydlog.default_logger()
        assert logger is not None
        assert logger.name() == ""

    def test_set_default_logger(self):
        """Test setting a custom default logger"""
        original = spydlog.default_logger()

        custom_logger = spydlog.stdout_color_mt("custom_default")
        spydlog.set_default_logger(custom_logger)

        default = spydlog.default_logger()
        assert default.name() == "custom_default"

        # Reset to avoid affecting other tests
        spydlog.set_default_logger(original)


class TestColorMode:
    """Test color mode enum"""

    def test_color_mode_enum(self):
        """Test that all color modes are available"""
        assert hasattr(spydlog.color_mode, "always")
        assert hasattr(spydlog.color_mode, "automatic")
        assert hasattr(spydlog.color_mode, "never")

    def test_color_mode_values(self):
        """Test color mode values are distinct"""
        assert spydlog.color_mode.always != spydlog.color_mode.never
        assert spydlog.color_mode.automatic != spydlog.color_mode.always
        assert spydlog.color_mode.automatic != spydlog.color_mode.never
