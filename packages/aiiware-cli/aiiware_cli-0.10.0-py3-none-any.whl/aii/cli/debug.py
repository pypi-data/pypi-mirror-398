# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Debug logging utility for AII CLI.

Enable debug output by setting environment variable:
    AII_DEBUG=1 aii "your command"
"""


import os
import sys


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled via AII_DEBUG environment variable."""
    return os.environ.get("AII_DEBUG", "0") == "1"


def debug_print(message: str, flush: bool = True) -> None:
    """
    Print debug message only if AII_DEBUG=1.

    Args:
        message: Debug message to print
        flush: Whether to flush stdout immediately (default: True)
    """
    if is_debug_enabled():
        print(f"[DEBUG] {message}", file=sys.stderr, flush=flush)
