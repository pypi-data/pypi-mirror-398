# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Streaming utilities for WebSocket token delivery."""


from typing import Callable
from fastapi import WebSocket


def create_streaming_callback(websocket: WebSocket) -> Callable[[str], None]:
    """
    Create streaming callback for real-time token delivery.

    Args:
        websocket: FastAPI WebSocket connection

    Returns:
        Async callback function that sends tokens to client
    """
    # Track WebSocket state to stop streaming when disconnected
    disconnected = False

    async def streaming_callback(token: str):
        """Send each token immediately to the client"""
        nonlocal disconnected

        # Skip if already disconnected (prevents error spam)
        if disconnected:
            return

        try:
            await websocket.send_json({
                "type": "token",
                "data": token
            })
        except Exception as e:
            # WebSocket disconnected - mark and stop trying
            if not disconnected:
                disconnected = True
                print(f"WebSocket disconnected, stopping token stream: {e}")

    return streaming_callback
