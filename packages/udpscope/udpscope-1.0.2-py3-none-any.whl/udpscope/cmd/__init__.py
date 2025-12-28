"""
Command module for udpscope
This module provides backward compatibility for command-line interface.
"""

import warnings

warnings.warn(
    "The udpscope.cmd module is deprecated. Use 'udpscope.cli' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
from udpscope.cli import main

__all__ = ['main']