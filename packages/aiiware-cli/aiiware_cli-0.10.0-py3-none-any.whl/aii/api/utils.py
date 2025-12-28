# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Utility functions for API server."""


import os


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled via AII_DEBUG environment variable."""
    return os.environ.get("AII_DEBUG", "0") == "1"


def debug_print(message: str) -> None:
    """Print debug message only if AII_DEBUG=1."""
    if is_debug_enabled():
        import sys
        print(f"[DEBUG] {message}", file=sys.stderr, flush=True)


def generate_api_key() -> str:
    """
    Generate default API key.

    Returns the standard development API key for local testing.
    For production, users should generate their own keys.
    """
    # Default key for local development and testing
    return "aii_sk_7WyvfQ0PRzufJ1G66Qn8Sm4gW9Tealpo6vOWDDUeiv4"
