# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
AII API Module - HTTP Server for programmatic access.

Provides:
- RESTful API for function execution
- WebSocket streaming for real-time responses
- API key authentication
- Rate limiting per key
- OpenAPI documentation
"""

from aii.api.server import APIServer
from aii.api.utils import generate_api_key

__all__ = ["APIServer", "generate_api_key"]
