# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""WebSocket handler wrapper for server-side MCP delegation.

This module provides a WebSocket handler that can send requests to the client
and wait for responses (bidirectional communication for cloud-compatible MCP).
"""


import asyncio
import logging
from typing import Any, Dict, Optional
from fastapi import WebSocket
from starlette.websockets import WebSocketState, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    WebSocket handler wrapper for bidirectional communication (v0.6.0).

    Supports server→client requests with response waiting (for MCP delegation).
    """

    def __init__(self, websocket: WebSocket):
        """
        Initialize WebSocket handler.

        Args:
            websocket: FastAPI WebSocket connection
        """
        self.websocket = websocket
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False

    async def send_and_wait(
        self,
        message: Dict[str, Any],
        timeout: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to the client and wait for response.

        This enables server→client requests for MCP tool queries and execution.

        Args:
            message: Message to send (must have request_id field)
            timeout: Timeout in seconds (default: 10s)

        Returns:
            Response message from client, or None if timeout

        Raises:
            ValueError: If message doesn't have request_id
            asyncio.TimeoutError: If response not received within timeout
        """
        request_id = message.get("request_id")
        if not request_id:
            raise ValueError("Message must have request_id for send_and_wait")

        # Create future for this request
        future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            # Send message to client
            await self.websocket.send_json(message)
            logger.debug(f"WebSocket: Sent request {request_id} (type={message.get('type')})")

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            logger.debug(f"WebSocket: Received response for {request_id}")

            return response

        except asyncio.TimeoutError:
            logger.warning(f"WebSocket: Request {request_id} timed out after {timeout}s")
            raise
        finally:
            # Clean up pending request
            self._pending_requests.pop(request_id, None)

    def handle_response(self, response: Dict[str, Any]):
        """
        Handle response from client (completes pending send_and_wait).

        Called by WebSocket message loop when client sends a response.

        Args:
            response: Response message from client (must have request_id)
        """
        request_id = response.get("request_id")
        if not request_id:
            logger.warning("Received response without request_id, ignoring")
            return

        future = self._pending_requests.get(request_id)
        if future and not future.done():
            future.set_result(response)
            logger.debug(f"WebSocket: Completed future for {request_id}")
        else:
            logger.warning(f"WebSocket: No pending request for {request_id}")

    def cancel_pending_requests(self):
        """Cancel all pending requests (for cleanup on disconnect)."""
        for request_id, future in list(self._pending_requests.items()):
            if not future.done():
                future.cancel()
                logger.debug(f"WebSocket: Cancelled pending request {request_id}")

        self._pending_requests.clear()

    async def _background_listener(self):
        """
        Background task to listen for incoming messages from client.

        This handles MCP response messages (mcp_query_tools_response, mcp_tool_response)
        that complete pending send_and_wait requests.
        """
        logger.debug(f"WebSocket: Starting background message listener (state={self.websocket.client_state})")
        self._running = True

        try:
            while self._running:
                try:
                    # Check if WebSocket is still connected before attempting to receive
                    # This prevents "WebSocket is not connected. Need to call 'accept' first." errors
                    if self.websocket.client_state != WebSocketState.CONNECTED:
                        logger.debug(f"WebSocket: Connection closed (state={self.websocket.client_state}), stopping listener")
                        break

                    # Wait for incoming message with short timeout
                    message = await asyncio.wait_for(
                        self.websocket.receive_json(),
                        timeout=0.1  # 100ms poll
                    )

                    # Check if this is a response to a pending request
                    msg_type = message.get("type", "")
                    if msg_type in ["mcp_query_tools_response", "mcp_tool_response"]:
                        # This is a response to our request
                        self.handle_response(message)
                        logger.debug(f"WebSocket: Handled {msg_type}")
                    else:
                        # Not an MCP response, ignore (might be handled elsewhere)
                        logger.debug(f"WebSocket: Ignoring message type: {msg_type}")

                except asyncio.TimeoutError:
                    # No message received, continue polling
                    continue
                except WebSocketDisconnect:
                    # Client disconnected gracefully
                    logger.debug("WebSocket: Client disconnected")
                    break
                except Exception as e:
                    logger.error(f"WebSocket: Error in background listener: {e} (state={self.websocket.client_state})")
                    break

        finally:
            self._running = False
            # Cancel all pending requests when listener stops
            self.cancel_pending_requests()
            logger.debug("WebSocket: Background listener stopped")

    def start_listening(self):
        """Start background message listener task."""
        if not self._listener_task or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._background_listener())
            logger.debug("WebSocket: Background listener started")

    async def stop_listening(self):
        """Stop background message listener task."""
        self._running = False
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            logger.debug("WebSocket: Background listener stopped")
