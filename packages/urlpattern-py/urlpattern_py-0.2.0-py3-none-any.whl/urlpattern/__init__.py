"""
urlpattern: Pure Python WHATWG URL Pattern implementation.

This library provides URL pattern matching following the WHATWG URL Pattern Standard,
enabling isomorphic routing between Python backends and JavaScript frontends.

Package name: urlpattern
PyPI name: urlpattern-py
"""

from importlib.metadata import PackageNotFoundError, version

from .core import URLPattern

try:
    __version__ = version("urlpattern-py")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["URLPattern"]
