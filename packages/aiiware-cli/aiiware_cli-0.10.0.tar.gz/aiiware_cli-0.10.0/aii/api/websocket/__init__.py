# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""WebSocket streaming support for Aii API server."""


from .handler import handle_websocket_connection

__all__ = ["handle_websocket_connection"]
