# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
WebSocket client for CLI-to-Server communication.

Features:
- Token-by-token streaming
- Automatic reconnection (exponential backoff)
- Error handling with retry
- Connection pooling
- Clean disconnection
"""


import asyncio
import json
import logging
from typing import AsyncIterator, Callable, Optional, Dict, Any
from websockets.asyncio.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed, WebSocketException
from aii.cli.debug import debug_print
from aii.cli.mcp_executor import ClientMCPExecutor

logger = logging.getLogger(__name__)


class WebSocketConnectionError(Exception):
    """WebSocket connection error"""
    pass


class WebSocketTimeout(Exception):
    """WebSocket request timeout"""
    pass


class AiiWebSocketClient:
    """
    WebSocket client for real-time streaming from Aii Server.

    Features:
    - Token-by-token streaming display
    - Automatic reconnection with exponential backoff
    - Connection pooling (reuse connection for multiple requests)
    - Intelligent timeout handling (function-specific)
    - Error handling with clear messages
    """

    # Function-specific timeout configuration (v0.8.0)
    # Some functions legitimately need longer timeouts due to large inputs
    FUNCTION_TIMEOUTS = {
        # Extended timeout functions (3 minutes)
        "git_commit": 180,          # Large git diffs can take time to analyze
        "content_generate": 180,    # Long-form content generation
        "code_review": 180,         # Large codebases
        "universal_generate": 180,  # Universal generation (used by client workflows like git commit)

        # Default timeout for all other functions: 60s
    }
    DEFAULT_TIMEOUT = 60  # seconds

    def __init__(self, ws_url: str, api_key: str, mcp_executor: Optional[ClientMCPExecutor] = None):
        self.ws_url = ws_url
        self.api_key = api_key
        self.ws = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.mcp_executor = mcp_executor  # v0.6.0: Client-side MCP execution
        self._message_loop_task = None  # Background task for handling server messages

    async def connect(self) -> None:
        """Establish WebSocket connection with timeout"""
        try:
            # v0.6.0: Add 3-second timeout for connection attempt
            # This prevents hanging when server is not running
            # v0.9.4: Disable proxy for localhost to prevent system proxy interference
            self.ws = await asyncio.wait_for(
                ws_connect(self.ws_url, proxy=None),
                timeout=3.0
            )
            logger.info(f"WebSocket connected to {self.ws_url}")
            self.reconnect_attempts = 0
        except asyncio.TimeoutError:
            logger.error(f"WebSocket connection timeout to {self.ws_url}")
            raise WebSocketConnectionError(f"Connection timeout to {self.ws_url} (server may not be running)")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise WebSocketConnectionError(f"Cannot connect to {self.ws_url}: {e}")

    async def execute_request(
        self,
        request: Dict[str, Any],
        on_token: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute request with streaming.

        Args:
            request: Request payload (function, params, etc.)
            on_token: Optional callback for each streamed token

        Returns:
            dict: Final result with metadata

        Raises:
            WebSocketTimeout: If request times out
            WebSocketConnectionError: If connection fails
        """

        if not self.ws:
            await self.connect()

        try:
            # Add API key to request
            request_with_auth = {**request, "api_key": self.api_key}

            # Send request
            await self.ws.send(json.dumps(request_with_auth))

            # v0.8.0: Determine timeout based on function type
            function_name = request.get('function', 'auto')
            request_timeout = self.FUNCTION_TIMEOUTS.get(function_name, self.DEFAULT_TIMEOUT)
            logger.debug(f"WebSocket request sent: {function_name} (timeout: {request_timeout}s)")

            # Stream response with function-specific timeout
            result_buffer = []
            metadata = None

            start_time = asyncio.get_event_loop().time()

            # Use recv() instead of async iteration (websockets library pattern)
            while True:
                # Check timeout (v0.8.0: function-specific)
                if asyncio.get_event_loop().time() - start_time > request_timeout:
                    raise WebSocketTimeout(f"Request timed out after {request_timeout}s")

                # Receive message with timeout
                try:
                    debug_print("WS: Waiting for message...")
                    message = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                    debug_print(f"WS: Received: {message[:100]}...")
                except asyncio.TimeoutError:
                    debug_print("WS: Recv timeout (5s), retrying...")
                    # Check if we've exceeded total timeout
                    if asyncio.get_event_loop().time() - start_time > request_timeout:
                        raise WebSocketTimeout(f"Request timed out after {request_timeout}s")
                    continue

                msg = json.loads(message)
                debug_print(f"WS: Parsed message type: {msg.get('type')}")

                # v0.6.0: Handle MCP-related messages from server
                if msg["type"] == "mcp_query_tools":
                    # Server asking for available MCP tools
                    if self.mcp_executor:
                        response = await self.mcp_executor.handle_query_tools(msg)
                        await self.ws.send(json.dumps(response))
                        debug_print(f"WS: Sent mcp_query_tools_response with {len(response.get('tools', []))} tools")
                    else:
                        # No MCP executor available
                        error_response = {
                            "type": "mcp_query_tools_response",
                            "request_id": msg.get("request_id", "unknown"),
                            "success": False,
                            "error": "MCP client not configured on this client",
                            "tools": []
                        }
                        await self.ws.send(json.dumps(error_response))
                    continue

                elif msg["type"] == "mcp_tool_request":
                    # Server requesting tool execution
                    if self.mcp_executor:
                        response = await self.mcp_executor.handle_tool_execution(msg)
                        await self.ws.send(json.dumps(response))
                        debug_print(f"WS: Sent mcp_tool_response (success={response.get('success')})")
                    else:
                        # No MCP executor available
                        error_response = {
                            "type": "mcp_tool_response",
                            "request_id": msg.get("request_id", "unknown"),
                            "success": False,
                            "error": "MCP client not configured on this client"
                        }
                        await self.ws.send(json.dumps(error_response))
                    continue

                elif msg["type"] == "token":
                    # Stream token
                    token = msg["data"]  # Match server field name
                    result_buffer.append(token)

                    if on_token:
                        on_token(token)

                elif msg["type"] == "complete":
                    # Execution complete
                    # Use streamed tokens if available, otherwise extract from completion message data
                    if result_buffer:
                        # Streaming occurred - use buffered tokens
                        result = "".join(result_buffer)
                    else:
                        # No streaming - extract from completion message
                        # v0.6.0: Server sends response in data.clean_output for non-streaming responses
                        data = msg.get("data") or {}  # Handle None explicitly
                        result = data.get("clean_output") or data.get("response") or data.get("result") or msg.get("result", "")

                    # Extract metadata from the server response
                    # Server sends metadata as a nested object with execution_time, tokens, cost, model, confidence, session_id, reasoning, etc.
                    server_metadata = msg.get("metadata", {})

                    metadata = {
                        "function_name": msg.get("function_name"),
                        "success": msg.get("success", True),
                        "execution_time": server_metadata.get("execution_time"),
                        "tokens": server_metadata.get("tokens"),
                        "cost": server_metadata.get("cost"),
                        "model": server_metadata.get("model"),
                        "confidence": server_metadata.get("confidence"),
                        "reasoning": server_metadata.get("reasoning"),
                        "session_id": server_metadata.get("session_id"),
                        "success_rate": server_metadata.get("success_rate"),
                        "total_functions": server_metadata.get("total_functions"),
                    }

                    return {
                        "success": msg.get("success", True),
                        "result": result,
                        "data": msg.get("data"),  # v0.6.0: Include data field from server
                        "metadata": metadata
                    }

                elif msg["type"] == "error":
                    # Error occurred - include guidance if provided
                    error_msg = msg.get("message", "Unknown error")
                    details = msg.get("details", {})
                    guidance = details.get("guidance") if details else None

                    # If guidance provided (e.g., "run: aii config init"), include it
                    if guidance:
                        error_msg = f"{error_msg}\n\n{guidance}"

                    raise WebSocketConnectionError(error_msg)

        except ConnectionClosed:
            # WebSocket connection closed - this is normal after each request
            # Don't print warning, just silently reconnect
            logger.debug("WebSocket connection closed, will reconnect for next request")

            # Reset connection so next attempt will reconnect
            self.ws = None

            # Attempt reconnection silently
            if self.reconnect_attempts < self.max_reconnect_attempts:
                self.reconnect_attempts += 1
                wait_time = 2 ** self.reconnect_attempts  # Exponential backoff
                logger.debug(f"Reconnecting in {wait_time}s... (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                await asyncio.sleep(wait_time)

                # Retry request (will call connect() since self.ws is None)
                return await self.execute_request(request, on_token)
            else:
                raise WebSocketConnectionError("WebSocket connection lost after max retries")

        except asyncio.TimeoutError:
            raise WebSocketTimeout(f"Request timed out after {request_timeout}s")

        except Exception as e:
            # For prerequisite errors, only log first line (guidance will show in final error)
            error_msg = str(e)
            if "Prerequisites not met" in error_msg or "aii config init" in error_msg:
                log_msg = error_msg.split('\n')[0]
                logger.error(f"WebSocket execution error: {log_msg}")
            else:
                logger.error(f"WebSocket execution error: {e}")
            raise

    async def recognize_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Recognize intent WITHOUT executing (Phase 1 of two-phase confirmation flow).

        Args:
            user_input: Natural language input

        Returns:
            dict: Recognition result with function, parameters, safety level, requires_confirmation

        Raises:
            WebSocketConnectionError: If connection fails or intent recognition fails
        """
        if not self.ws:
            await self.connect()

        try:
            # Send recognize request
            request = {
                "action": "recognize",
                "user_input": user_input,
                "api_key": self.api_key
            }

            await self.ws.send(json.dumps(request))
            debug_print(f"CLIENT: Sent recognize request for: {user_input}")

            # Wait for recognition result (with timeout)
            start_time = asyncio.get_event_loop().time()

            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > self.DEFAULT_TIMEOUT:
                    raise WebSocketTimeout(f"Intent recognition timed out after {self.DEFAULT_TIMEOUT}s")

                message = await self.ws.recv()
                msg = json.loads(message)
                debug_print(f"CLIENT: Received message type: {msg.get('type')}")

                if msg["type"] == "recognition":
                    # Got recognition result
                    return {
                        "function": msg.get("function"),
                        "parameters": msg.get("parameters", {}),
                        "safety": msg.get("safety"),
                        "description": msg.get("description"),
                        "requires_confirmation": msg.get("requires_confirmation", False)
                    }

                elif msg["type"] == "error":
                    # Error occurred during recognition - include guidance if provided
                    error_msg = msg.get("message", "Unknown error during intent recognition")
                    details = msg.get("details", {})
                    guidance = details.get("guidance") if details else None

                    # If guidance provided (e.g., "run: aii config init"), include it
                    if guidance:
                        error_msg = f"{error_msg}\n\n{guidance}"

                    raise WebSocketConnectionError(error_msg)

        except ConnectionClosed:
            logger.warning("WebSocket connection closed during intent recognition")
            raise WebSocketConnectionError("Connection closed during intent recognition")

        except asyncio.TimeoutError:
            raise WebSocketTimeout(f"Intent recognition timed out after {self.DEFAULT_TIMEOUT}s")

        except Exception as e:
            logger.error(f"Intent recognition error: {e}")
            raise

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        # websockets ClientConnection doesn't have .closed attribute
        # Instead, check if ws exists (it gets set to None on close)
        return self.ws is not None

    async def close(self) -> None:
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.ws = None
            logger.info("WebSocket disconnected")

        # v0.6.0: Shutdown MCP executor if present
        if self.mcp_executor:
            await self.mcp_executor.shutdown()


def create_websocket_client(
    base_url: str,
    api_key: str,
    mcp_client=None
) -> AiiWebSocketClient:
    """
    Create WebSocket client from configuration.

    Args:
        base_url: HTTP API URL (e.g., "http://localhost:16169")
        api_key: API key for authentication
        mcp_client: Optional MCPClientManager for client-side MCP execution (v0.6.0)

    Returns:
        AiiWebSocketClient instance
    """
    # Convert HTTP URL to WebSocket URL
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/execute"

    # v0.6.0: Create MCP executor if MCP client is provided
    mcp_executor = None
    if mcp_client:
        mcp_executor = ClientMCPExecutor(mcp_client)

    return AiiWebSocketClient(ws_url, api_key, mcp_executor)
