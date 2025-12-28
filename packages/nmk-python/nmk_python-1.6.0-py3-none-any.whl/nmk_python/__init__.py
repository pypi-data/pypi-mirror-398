"""
Python support for nmk
"""

from importlib.metadata import version

from nmk_base.version import VersionResolver

__title__ = "nmk-python"
try:
    __version__ = version(__title__)
except Exception:  # pragma: no cover
    __version__ = "unknown"


class NmkPythonVersionResolver(VersionResolver):
    """Plugin version resolver"""

    def get_version(self) -> str:
        """Returns nmk-python plugin version"""
        return __version__
