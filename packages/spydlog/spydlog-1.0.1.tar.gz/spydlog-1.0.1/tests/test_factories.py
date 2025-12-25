import spydlog
import tempfile
import os

from tests.conftest import handle_permission_error


class TestConsoleLoggerFactories:
    """Test console logger factory functions"""

    def test_stdout_color_mt(self):
        """Test stdout color multi-threaded logger factory"""
        logger = spydlog.stdout_color_mt("stdout_color_mt_logger")
        assert logger.name() == "stdout_color_mt_logger"
        logger.info("Test message from stdout_color_mt")

    def test_stdout_color_st(self):
        """Test stdout color single-threaded logger factory"""
        logger = spydlog.stdout_color_st("stdout_color_st_logger")
        assert logger.name() == "stdout_color_st_logger"
        logger.info("Test message from stdout_color_st")

    def test_stderr_color_mt(self):
        """Test stderr color multi-threaded logger factory"""
        logger = spydlog.stderr_color_mt("stderr_color_mt_logger")
        assert logger.name() == "stderr_color_mt_logger"
        logger.warn("Test message from stderr_color_mt")

    def test_stderr_color_st(self):
        """Test stderr color single-threaded logger factory"""
        logger = spydlog.stderr_color_st("stderr_color_st_logger")
        assert logger.name() == "stderr_color_st_logger"
        logger.warn("Test message from stderr_color_st")

    def test_stdout_logger_mt(self):
        """Test stdout multi-threaded logger factory (no color)"""
        logger = spydlog.stdout_logger_mt("stdout_mt_logger")
        assert logger.name() == "stdout_mt_logger"
        logger.info("Test message from stdout_logger_mt")

    def test_stdout_logger_st(self):
        """Test stdout single-threaded logger factory (no color)"""
        logger = spydlog.stdout_logger_st("stdout_st_logger")
        assert logger.name() == "stdout_st_logger"
        logger.info("Test message from stdout_logger_st")

    def test_stderr_logger_mt(self):
        """Test stderr multi-threaded logger factory (no color)"""
        logger = spydlog.stderr_logger_mt("stderr_mt_logger")
        assert logger.name() == "stderr_mt_logger"
        logger.warn("Test message from stderr_logger_mt")

    def test_stderr_logger_st(self):
        """Test stderr single-threaded logger factory (no color)"""
        logger = spydlog.stderr_logger_st("stderr_st_logger")
        assert logger.name() == "stderr_st_logger"
        logger.warn("Test message from stderr_logger_st")

    def test_color_logger_with_mode(self):
        """Test color logger factory with color mode"""
        logger_always = spydlog.stdout_color_mt("color_always", spydlog.color_mode.always)
        assert logger_always.name() == "color_always"

        logger_never = spydlog.stdout_color_mt("color_never", spydlog.color_mode.never)
        assert logger_never.name() == "color_never"

        logger_auto = spydlog.stdout_color_mt("color_auto", spydlog.color_mode.automatic)
        assert logger_auto.name() == "color_auto"


class TestFileLoggerFactories:
    """Test file logger factory functions"""

    @handle_permission_error
    def test_basic_logger_mt(self):
        """Test basic multi-threaded file logger factory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "basic_mt.log")
            logger = spydlog.basic_logger_mt("basic_mt_logger", filepath)

            assert logger.name() == "basic_mt_logger"
            logger.info("Test message")
            logger.flush()

            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                assert "Test message" in f.read()

    @handle_permission_error
    def test_basic_logger_st(self):
        """Test basic single-threaded file logger factory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "basic_st.log")
            logger = spydlog.basic_logger_st("basic_st_logger", filepath)

            assert logger.name() == "basic_st_logger"
            logger.info("Test message")
            logger.flush()

            assert os.path.exists(filepath)

    @handle_permission_error
    def test_basic_logger_truncate(self):
        """Test basic file logger with truncate option"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "truncate.log")

            # Create file with content
            with open(filepath, 'w') as f:
                f.write("old content\n")

            logger = spydlog.basic_logger_mt("truncate_logger", filepath, True)
            logger.info("new content")
            logger.flush()

            with open(filepath, 'r') as f:
                content = f.read()
                assert "old content" not in content
                assert "new content" in content

    @handle_permission_error
    def test_rotating_logger_mt(self):
        """Test rotating multi-threaded file logger factory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "rotating_mt.log")
            max_size = 1024 * 1024  # 1MB
            max_files = 3

            logger = spydlog.rotating_logger_mt("rotating_mt_logger", filepath, max_size, max_files)
            assert logger.name() == "rotating_mt_logger"

            logger.info("Test rotating logger")
            logger.flush()
            assert os.path.exists(filepath)

    @handle_permission_error
    def test_rotating_logger_st(self):
        """Test rotating single-threaded file logger factory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "rotating_st.log")
            max_size = 1024 * 512  # 512KB
            max_files = 5

            logger = spydlog.rotating_logger_st("rotating_st_logger", filepath, max_size, max_files)
            assert logger.name() == "rotating_st_logger"

            logger.info("Test rotating logger")
            logger.flush()
            assert os.path.exists(filepath)

    @handle_permission_error
    def test_daily_logger_mt(self):
        """Test daily multi-threaded file logger factory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "daily_mt.log")

            logger = spydlog.daily_logger_mt("daily_mt_logger", filepath, 0, 0)
            assert logger.name() == "daily_mt_logger"

            logger.info("Test daily logger")
            logger.flush()

    @handle_permission_error
    def test_daily_logger_st(self):
        """Test daily single-threaded file logger factory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "daily_st.log")

            logger = spydlog.daily_logger_st("daily_st_logger", filepath, 23, 59)
            assert logger.name() == "daily_st_logger"

            logger.info("Test daily logger")
            logger.flush()

    @handle_permission_error
    def test_daily_logger_default_time(self):
        """Test daily logger with default rotation time"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "daily_default.log")

            # Should default to midnight (0, 0)
            logger = spydlog.daily_logger_mt("daily_default_logger", filepath)
            assert logger.name() == "daily_default_logger"

            logger.info("Test daily logger with default time")
            logger.flush()


class TestLoggerRegistry:
    """Test logger registry functions"""

    def test_get_logger(self):
        """Test retrieving logger from registry"""
        _ = spydlog.stdout_color_mt("registry_test_logger")
        retrieved = spydlog.get("registry_test_logger")

        assert retrieved is not None
        assert retrieved.name() == "registry_test_logger"

        spydlog.drop("registry_test_logger")

    def test_get_non_existent_logger(self):
        """Test getting non-existent logger returns None"""
        result = spydlog.get("non_existent_logger_xyz")
        assert result is None

    def test_register_logger(self):
        """Test registering a custom logger"""
        sink = spydlog.stdout_color_sink_mt()
        logger = spydlog.logger("custom_registered_logger", sink)

        spydlog.register_logger(logger)

        retrieved = spydlog.get("custom_registered_logger")
        assert retrieved is not None
        assert retrieved.name() == "custom_registered_logger"

        spydlog.drop("custom_registered_logger")

    def test_drop_logger(self):
        """Test dropping logger from registry"""
        _ = spydlog.stdout_color_mt("drop_test_logger")
        assert spydlog.get("drop_test_logger") is not None

        spydlog.drop("drop_test_logger")
        assert spydlog.get("drop_test_logger") is None

    def test_drop_all_loggers(self):
        """Test dropping all loggers"""
        spydlog.stdout_color_mt("logger1")
        spydlog.stdout_color_mt("logger2")
        spydlog.stdout_color_mt("logger3")

        spydlog.drop_all()

        assert spydlog.get("logger1") is None
        assert spydlog.get("logger2") is None
        assert spydlog.get("logger3") is None

    def test_apply_all(self):
        """Test applying function to all loggers"""
        spydlog.drop_all()

        spydlog.stdout_color_mt("apply_logger1")
        spydlog.stdout_color_mt("apply_logger2")

        # Set all loggers to debug level
        def set_debug(logger):
            logger.set_level(spydlog.level.debug)

        spydlog.apply_all(set_debug)

        logger1 = spydlog.get("apply_logger1")
        logger2 = spydlog.get("apply_logger2")

        assert logger1.level() == spydlog.level.debug
        assert logger2.level() == spydlog.level.debug

        spydlog.drop_all()


class TestFactoryUniqueness:
    """Test that factory functions create unique loggers"""

    def test_duplicate_logger_name_error(self):
        """Test that creating logger with duplicate name may cause issues"""
        # First logger
        logger1 = spydlog.stdout_color_mt("duplicate_name")
        assert logger1.name() == "duplicate_name"

        # Attempting to create another with same name might fail or return existing
        # This behavior depends on spdlog implementation
        # Just verify we can drop and recreate
        spydlog.drop("duplicate_name")
        logger2 = spydlog.stdout_color_mt("duplicate_name")
        assert logger2.name() == "duplicate_name"

        spydlog.drop("duplicate_name")
