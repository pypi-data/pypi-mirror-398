import spydlog
import tempfile
import os

from tests.conftest import handle_permission_error


class TestConsoleSinks:
    """Test console sink creation and configuration"""

    def test_stdout_color_sink_mt(self):
        """Test multi-threaded stdout color sink"""
        sink = spydlog.stdout_color_sink_mt()
        assert sink is not None

        sink.set_level(spydlog.level.debug)
        assert sink.level() == spydlog.level.debug

    def test_stdout_color_sink_st(self):
        """Test single-threaded stdout color sink"""
        sink = spydlog.stdout_color_sink_st()
        assert sink is not None

        sink.set_level(spydlog.level.info)
        assert sink.level() == spydlog.level.info

    def test_stderr_color_sink_mt(self):
        """Test multi-threaded stderr color sink"""
        sink = spydlog.stderr_color_sink_mt()
        assert sink is not None

    def test_stderr_color_sink_st(self):
        """Test single-threaded stderr color sink"""
        sink = spydlog.stderr_color_sink_st()
        assert sink is not None

    def test_color_sinks_with_mode(self):
        """Test color sinks with different color modes"""
        sink_always = spydlog.stdout_color_sink_mt(spydlog.color_mode.always)
        assert sink_always is not None

        sink_never = spydlog.stdout_color_sink_mt(spydlog.color_mode.never)
        assert sink_never is not None

        sink_auto = spydlog.stdout_color_sink_mt(spydlog.color_mode.automatic)
        assert sink_auto is not None

    def test_stdout_sink_mt(self):
        """Test multi-threaded stdout sink (no color)"""
        sink = spydlog.stdout_sink_mt()
        assert sink is not None

    def test_stdout_sink_st(self):
        """Test single-threaded stdout sink (no color)"""
        sink = spydlog.stdout_sink_st()
        assert sink is not None

    def test_stderr_sink_mt(self):
        """Test multi-threaded stderr sink (no color)"""
        sink = spydlog.stderr_sink_mt()
        assert sink is not None

    def test_stderr_sink_st(self):
        """Test single-threaded stderr sink (no color)"""
        sink = spydlog.stderr_sink_st()
        assert sink is not None


class TestFileSinks:
    """Test file sink creation and basic operations"""

    @handle_permission_error
    def test_basic_file_sink_mt(self):
        """Test multi-threaded basic file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_mt.log")
            sink = spydlog.basic_file_sink_mt(filepath, False)
            assert sink is not None
            assert os.path.exists(filepath)

    @handle_permission_error
    def test_basic_file_sink_st(self):
        """Test single-threaded basic file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_st.log")
            sink = spydlog.basic_file_sink_st(filepath, False)
            assert sink is not None
            assert os.path.exists(filepath)

    @handle_permission_error
    def test_basic_file_sink_truncate(self):
        """Test basic file sink with truncate option"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_truncate.log")

            # Create file with content
            with open(filepath, 'w') as f:
                f.write("existing content\n")

            # Open with truncate=True
            sink = spydlog.basic_file_sink_mt(filepath, True)
            assert sink is not None

    @handle_permission_error
    def test_rotating_file_sink_mt(self):
        """Test multi-threaded rotating file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "rotating_mt.log")
            max_size = 1024 * 1024  # 1MB
            max_files = 3

            sink = spydlog.rotating_file_sink_mt(filepath, max_size, max_files)
            assert sink is not None

    @handle_permission_error
    def test_rotating_file_sink_st(self):
        """Test single-threaded rotating file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "rotating_st.log")
            max_size = 1024 * 512  # 512KB
            max_files = 5

            sink = spydlog.rotating_file_sink_st(filepath, max_size, max_files)
            assert sink is not None

    @handle_permission_error
    def test_daily_file_sink_mt(self):
        """Test multi-threaded daily file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "daily_mt.log")
            hour = 0
            minute = 0

            sink = spydlog.daily_file_sink_mt(filepath, hour, minute)
            assert sink is not None

    @handle_permission_error
    def test_daily_file_sink_st(self):
        """Test single-threaded daily file sink"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "daily_st.log")
            hour = 23
            minute = 59

            sink = spydlog.daily_file_sink_st(filepath, hour, minute)
            assert sink is not None


class TestNullSink:
    """Test null sink (discards all logs)"""

    def test_null_sink_st(self):
        """Test null sink"""
        sink = spydlog.null_sink_st()
        assert sink is not None

    def test_null_sink_st(self):
        """Test single-threaded null sink"""
        sink = spydlog.null_sink_st()
        assert sink is not None


class TestSinkConfiguration:
    """Test sink configuration methods"""

    def test_sink_set_level(self):
        """Test setting sink log level"""
        sink = spydlog.stdout_color_sink_mt()

        sink.set_level(spydlog.level.trace)
        assert sink.level() == spydlog.level.trace

        sink.set_level(spydlog.level.critical)
        assert sink.level() == spydlog.level.critical

    def test_sink_set_pattern(self):
        """Test setting sink pattern"""
        sink = spydlog.stdout_color_sink_mt()

        # This should not crash
        sink.set_pattern("[%H:%M:%S] %v")
        sink.set_pattern("%+")  # Reset to default

    def test_sink_log(self):
        """Test logging directly to sink"""
        sink = spydlog.stdout_color_sink_mt()

        # Should not crash
        sink.log(spydlog.level.info, "Direct sink logging test")
        sink.log(spydlog.level.warn, "Warning message")
