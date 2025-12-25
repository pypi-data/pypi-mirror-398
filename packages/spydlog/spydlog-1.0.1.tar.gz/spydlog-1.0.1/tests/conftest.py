import pytest
import spydlog
import platform


# Windows has issues with file permissions and accesses
def handle_permission_error(f):
    def wrapper(*args, **kwargs):
        if platform.system() == "Windows":
            try:
                return f(*args, **kwargs)
            except PermissionError:
                pass
            except NotADirectoryError:
                pass
        else:
            return f(*args, **kwargs)

    return wrapper

@pytest.fixture(autouse=True)
def cleanup_loggers():
    """Cleanup loggers after each test to avoid conflicts"""
    yield
    # Drop all loggers after each test and reset the default
    spydlog.drop_all()

    if spydlog.default_logger() is None:
        default = spydlog.logger("")
        spydlog.set_default_logger(default)


@pytest.fixture(autouse=True)
def reset_global_settings():
    """Reset global logger settings after each test"""
    yield
    # Reset to default settings
    spydlog.set_level(spydlog.level.info)
    spydlog.set_pattern("%+")  # Default pattern
    spydlog.flush_on(spydlog.level.off)


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "async_test: marks tests that use async logging"
    )
