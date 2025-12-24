"""
EnhancedPolars - Enhanced utilities for Polars DataFrames

This package provides enhanced functionality for Polars DataFrames including:
- EnhancedPolars (epl): Advanced DataFrame operations and type inference
- PolarsSQLExtension: SQL upload functionality
- Series extensions: Additional series-level operations
- And more...

Usage:
    from enhancedpolars import epl
    from enhancedpolars.register import *  # Register namespace extensions
"""

from .epl import EnhancedPolars
from .register import EPL, EPLNamespace, epl

# Version is set dynamically from git tags via hatch-vcs
try:
    from ._version import __version__, __version_tuple__
except ImportError:
    # Fallback for when package is not installed (e.g., during development)
    __version__ = "0.0.0.dev0"
    __version_tuple__ = (0, 0, 0, "dev0")

__all__ = [
    'EnhancedPolars',
    'EPL',
    'EPLNamespace',
    'epl',
    '__version__',
]
