try:
    from ._version import version as __version__
except ImportError:
    try:
        from importlib.metadata import version as _get_version
        __version__ = _get_version("spydlog")
    except Exception:
        __version__ = "0.0.0+unknown"

from .spydlog import *
