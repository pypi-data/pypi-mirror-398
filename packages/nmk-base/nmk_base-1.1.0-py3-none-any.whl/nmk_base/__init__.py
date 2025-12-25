"""
Python module for **nmk-base** plugin code.
"""

from importlib.metadata import version

__title__ = "nmk-base"
"""
Module name
"""

try:
    __version__ = version(__title__)
    """
    Module version, dynamically resolved from installed package
    """
except Exception:  # pragma: no cover
    __version__ = "unknown"
