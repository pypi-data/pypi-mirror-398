#!/usr/bin/env python3
"""
UDPScope command-line entry point
Legacy entry point for backward compatibility
"""
import sys
import warnings

warnings.warn(
    "The cmd.udpscope.main entry point is deprecated. Use 'udpscope.cli' directly instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export main function from the new CLI
try:
    from udpscope.cli import main
except ImportError:
    # Fallback for development
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from udpscope.cli import main

if __name__ == "__main__":
    sys.exit(main())