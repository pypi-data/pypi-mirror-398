"""
f40_toolkit: shared low-level tooling for the 40F Python stack.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("f40-toolkit")
except PackageNotFoundError:
    # Package not installed, e.g. running from source without build metadata
    __version__ = "0.0.0"

from . import common, config, logging, cache

__all__ = ["common", "config", "logging", "cache"]
