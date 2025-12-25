"""
AiXtools - Tools for AI exploration and debugging
"""

try:
    from ._version import version as __version__
except ImportError:
    # Fallback for development installations
    from importlib.metadata import version

    __version__ = version("aixtools")
