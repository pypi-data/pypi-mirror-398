# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
CLI client that communicates with Aii Server via WebSocket.

Features:
- Ensure server is running (auto-start if needed)
- Establish WebSocket connection
- Send requests and stream responses
- Handle errors with retry and fail-fast strategy
- Format output for terminal display
"""


import asyncio
import logging
from typing import Optional, Dict, Any
from aii.cli.server_manager import ServerManager
from aii.cli.websocket_client import (
    AiiWebSocketClient,
    create_websocket_client,
    WebSocketConnectionError,
    WebSocketTimeout
)
from aii.cli.debug import debug_print

logger = logging.getLogger(__name__)


class AiiCLIClient:
    """
    CLI client that communicates with Aii Server via WebSocket.

    Responsibilities:
    - Ensure server is running (auto-start if needed)
    - Establish WebSocket connection
    - Send requests and stream responses
    - Handle errors with retry and fail-fast strategy
    """

    def __init__(self, config_manager):
        """
        Initialize CLI client.

        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.server_manager = ServerManager(config_manager)
        self.ws_client: Optional[AiiWebSocketClient] = None
        self.max_retries = config_manager.get("cli.max_retries", 3)
        self.api_url = config_manager.get("api.url", "http://localhost:16169")
        self.api_key = self._get_or_create_api_key()
        debug_print(f"CLIENT: API URL: {self.api_url}, API Key: {self.api_key[:20]}...")

        # v0.6.0: Initialize MCP client for client-side execution
        self.mcp_client = self._initialize_mcp_client()

    def _get_or_create_api_key(self) -> str:
        """Get or create API key from config"""
        # Check if get_or_create_api_key method exists
        if hasattr(self.config, 'get_or_create_api_key'):
            return self.config.get_or_create_api_key()

        # Fallback: get from config
        api_keys = self.config.get("api.keys", [])
        if api_keys:
            return api_keys[0]

        # Use default development API key if none exists
        default_key = "aii_sk_7WyvfQ0PRzufJ1G66Qn8Sm4gW9Tealpo6vOWDDUeiv4"
        self.config.set("api.keys", [default_key])
        return default_key

    def _initialize_mcp_client(self):
        """
        Initialize MCP client for client-side execution (v0.6.0).

        Returns:
            MCPClientManager if MCP servers are configured, None otherwise
        """
        try:
            from aii.data.integrations.mcp.client_manager import MCPClientManager
            from aii.data.integrations.mcp.config_loader import MCPConfigLoader

            # Create config loader and load MCP servers from config
            config_loader = MCPConfigLoader()
            config_loader.load_configurations()

            # Check if any servers are configured
            if not config_loader.servers:
                debug_print("CLIENT: No MCP servers configured")
                return None

            # Create MCP client manager
            mcp_client = MCPClientManager(config_loader=config_loader, enable_health_monitoring=False)
            debug_print(f"CLIENT: MCP client initialized with {len(config_loader.servers)} servers")
            return mcp_client

        except ImportError:
            logger.warning("MCP integration not available (missing dependencies)")
            return None
        except Exception as e:
            logger.warning(f"Failed to initialize MCP client: {e}")
            return None

    async def execute_command(
        self,
        user_input: str,
        output_mode: Optional[str] = None,
        offline: bool = False,
        model: Optional[str] = None,  # v0.8.0: Model override
        spinner = None,  # Optional spinner to stop when streaming starts
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute command via WebSocket API with retry logic.

        Flow:
        1. Ensure server is running (auto-start if needed)
        2. Connect WebSocket (or reuse existing connection)
        3. Send request with streaming
        4. Receive and format response
        5. On error, retry with exponential backoff (fail fast if exhausted)

        Args:
            user_input: User's natural language prompt
            output_mode: Output mode (clean, standard, thinking)
            offline: Whether to run in offline mode
            model: Optional model override (e.g., 'kimi-k2-thinking', 'gpt-4.1-mini')
            spinner: Optional spinner instance to stop when streaming starts
            **kwargs: Additional parameters

        Returns:
            dict: Execution result with metadata

        Raises:
            RuntimeError: If server fails to start or request fails after retries
        """

        # Step 1: Ensure server is running
        server_ready = await self._ensure_server_ready()
        if not server_ready:
            # Build helpful error message based on configuration
            host = self.server_manager.host
            port = self.server_manager.port
            is_default = (host in ["127.0.0.1", "localhost"] and port == 16169)

            if is_default:
                # Default config - auto-start failed
                error_msg = (
                    "❌ Failed to start Aii server.\n\n"
                    "Try:\n"
                    "  1. Check if port 16169 is available: lsof -i :16169\n"
                    "  2. Start server manually: aii serve\n"
                    "  3. Check logs: ~/.aii/logs/server.log"
                )
            else:
                # Custom host/port - user must start manually
                # Extract just the command part from user_input (remove "translate hello to french" → "translate hello")
                short_example = " ".join(user_input.split()[:2]) if len(user_input.split()) > 1 else user_input
                error_msg = (
                    f"❌ Could not connect to Aii server at {host}:{port}\n\n"
                    f"Server may not be running. To start:\n"
                    f"  aii serve --host {host} --port {port}\n\n"
                    f"Or use default server (auto-starts):\n"
                    f"  aii {short_example}"
                )

            raise RuntimeError(error_msg)

        # Step 2-4: Execute with retry
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Connect WebSocket (or reuse)
                if not self.ws_client or not self.ws_client.is_connected():
                    debug_print("CLIENT: Creating WebSocket client...")
                    self.ws_client = create_websocket_client(self.api_url, self.api_key, self.mcp_client)
                    await self.ws_client.connect()
                    debug_print("CLIENT: WebSocket connected!")

                # Send request (v0.6.0 unified format)
                # Pattern 1 (LLM-First): system_prompt=null triggers intent recognition
                request = {
                    "system_prompt": None,  # null = Server performs intent recognition
                    "user_prompt": user_input,  # User's natural language input
                    "output_mode": output_mode,
                    "offline": offline,
                    **kwargs
                }

                # v0.8.0: Add model override if provided
                if model:
                    request["model"] = model

                debug_print(f"CLIENT: Sending unified request (LLM-first): user_prompt={user_input[:50]}...")

                # Track if we've cleared the loading indicator
                loading_cleared = [False]  # Use list to allow modification in lambda

                def on_token_callback(token: str):
                    """Print token and clear loading indicator on first token"""
                    if not loading_cleared[0]:
                        import sys
                        # Stop spinner and CLEAR the line immediately
                        if spinner:
                            # Use stop_sync with clear=True to clear the spinner line
                            spinner.stop_sync(clear=True)

                        loading_cleared[0] = True
                    print(token, end="", flush=True)

                # Stream response tokens
                result = await self.ws_client.execute_request(
                    request,
                    on_token=on_token_callback
                )

                # Add flag to indicate if streaming occurred (tokens were printed)
                result["_streaming_occurred"] = loading_cleared[0]

                return result

            except WebSocketTimeout as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Request timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                continue

            except WebSocketConnectionError as e:
                last_error = e
                error_msg = str(e)

                # Check if this is a prerequisite error (config issue) - don't retry
                if "Prerequisites not met" in error_msg or "aii config init" in error_msg:
                    # This is a configuration issue, not a transient error
                    # Extract just the first line for logging (without guidance)
                    log_msg = error_msg.split('\n')[0]
                    logger.error(f"WebSocket execution error: {log_msg}")

                    # Fail immediately with the full guidance
                    raise RuntimeError(f"❌ {error_msg}")

                # For other connection errors, log full message
                logger.error(f"WebSocket connection lost: {error_msg}")

                # Try to reconnect for other connection errors
                self.ws_client = None
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Reconnecting in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                continue

            except Exception as e:
                last_error = e
                logger.error(f"Command execution failed: {e}")
                raise

        # All retries exhausted - fail fast
        raise RuntimeError(
            f"❌ Server timeout after {self.max_retries} attempts.\n\n"
            f"Last error: {last_error}\n\n"
            f"Possible causes:\n"
            f"  • LLM provider is slow or unavailable\n"
            f"  • Server is overloaded\n"
            f"  • Network issues\n\n"
            f"Try:\n"
            f"  1. Retry your command: aii \"{user_input}\"\n"
            f"  2. Check server status: aii serve status\n"
            f"  3. Restart server: aii serve restart\n"
            f"  4. Use faster model: aii config model"
        )

    async def execute_function(
        self,
        function_name: str,
        parameters: Dict[str, Any],
        output_mode: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a specific function directly (bypass intent recognition).

        This method is used by client-side domain operations (v0.6.0) to call
        server functions without going through intent recognition. This ensures
        prompts like "Generate a commit message..." don't get misinterpreted.

        Args:
            function_name: Exact function name (e.g., "universal_generate")
            parameters: Function parameters as dict
            output_mode: Output mode (CLEAN/STANDARD/THINKING)
            **kwargs: Additional parameters

        Returns:
            dict: Execution result with success, result, data, metadata

        Raises:
            RuntimeError: If server fails or request fails
        """
        debug_print(f"CLIENT: execute_function - {function_name}, params: {list(parameters.keys())}")

        # Step 1: Ensure server is running
        server_ready = await self._ensure_server_ready()
        if not server_ready:
            raise RuntimeError("❌ Failed to start Aii server")

        # Step 2: Initialize and connect WebSocket client if needed
        if not self.ws_client or not self.ws_client.is_connected():
            debug_print("CLIENT: Creating WebSocket client for execute_function...")
            self.ws_client = create_websocket_client(self.api_url, self.api_key, self.mcp_client)
            await self.ws_client.connect()
            debug_print("CLIENT: WebSocket connected!")

        # Step 3: Call server's execute endpoint with explicit function name
        # This bypasses intent recognition and calls the function directly
        try:
            request = {
                "function": function_name,
                "params": parameters,
                "output_mode": output_mode or "STANDARD"
            }
            result = await self.ws_client.execute_request(request)
            debug_print(f"CLIENT: execute_function result - success: {result.get('success')}")
            return result

        except Exception as e:
            debug_print(f"CLIENT: execute_function failed - {e}")
            raise RuntimeError(f"Failed to execute {function_name}: {e}")

    async def execute_with_system_prompt(
        self,
        system_prompt: str,
        user_input: str,
        output_mode: Optional[str] = None,
        spinner = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute natural language prompt with system prompt (bypass intent recognition).

        This method is used for natural_language mode prompts (v0.6.1 Prompt Library Refactor).
        Instead of using intent recognition, it sends the system prompt + user input directly
        to the LLM for processing.

        Flow:
        1. Ensure server is running
        2. Connect WebSocket
        3. Send direct_llm_call request with system_prompt + user_prompt
        4. Stream response tokens
        5. Return result

        Args:
            system_prompt: System prompt that defines LLM behavior
            user_input: User's natural language input to be processed
            output_mode: Output mode (CLEAN/STANDARD/THINKING)
            spinner: Optional spinner instance to stop when streaming starts
            **kwargs: Additional parameters (e.g., prompt_name for metadata)

        Returns:
            dict: Execution result with success, result, data, metadata

        Raises:
            RuntimeError: If server fails or request fails

        Example:
            # For word-explanation prompt
            system_prompt = "You are a language expert. Explain the word with pronunciation..."
            result = await client.execute_with_system_prompt(
                system_prompt=system_prompt,
                user_input="prompt",
                output_mode="CLEAN"
            )
        """
        debug_print(f"CLIENT: execute_with_system_prompt - user_input: {user_input[:50]}...")

        # Step 1: Ensure server is running
        server_ready = await self._ensure_server_ready()
        if not server_ready:
            raise RuntimeError("❌ Failed to start Aii server")

        # Step 2: Connect WebSocket (or reuse)
        if not self.ws_client or not self.ws_client.is_connected():
            debug_print("CLIENT: Creating WebSocket client for execute_with_system_prompt...")
            self.ws_client = create_websocket_client(self.api_url, self.api_key, self.mcp_client)
            await self.ws_client.connect()
            debug_print("CLIENT: WebSocket connected!")

        # Step 3: Send direct_llm_call request (v0.6.1 unified format)
        # Pattern 2 (Direct LLM Call): system_prompt=string bypasses intent recognition
        request = {
            "system_prompt": system_prompt,  # Non-null = Direct LLM call
            "user_prompt": user_input,       # User's natural language input
            "output_mode": output_mode or "CLEAN",
            **kwargs
        }
        debug_print(f"CLIENT: Sending direct_llm_call request (bypass intent recognition)")

        # Track if we've cleared the loading indicator
        loading_cleared = [False]

        def on_token_callback(token: str):
            """Print token and clear loading indicator on first token"""
            if not loading_cleared[0]:
                # Stop spinner and clear the line immediately
                if spinner:
                    spinner.stop_sync(clear=True)
                loading_cleared[0] = True
            print(token, end="", flush=True)

        try:
            # Stream response tokens
            result = await self.ws_client.execute_request(
                request,
                on_token=on_token_callback
            )

            # Add flag to indicate if streaming occurred
            result["_streaming_occurred"] = loading_cleared[0]

            return result

        except (WebSocketConnectionError, WebSocketTimeout) as e:
            debug_print(f"CLIENT: execute_with_system_prompt failed - {e}")
            raise RuntimeError(f"❌ Direct LLM call failed: {e}")

    async def recognize_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Recognize intent WITHOUT executing (Phase 1 of two-phase confirmation flow).

        This method analyzes the user's input to determine which function would be called,
        what parameters would be used, and whether confirmation is required, but does NOT
        execute the function.

        Args:
            user_input: Natural language input

        Returns:
            dict: Recognition result with:
                - function: Function name that would be called
                - parameters: Parameters that would be passed
                - safety: Safety level (SAFE, RISKY, DESTRUCTIVE)
                - description: Human-readable description
                - requires_confirmation: Whether confirmation is needed

        Raises:
            RuntimeError: If server fails to start or recognition fails
        """

        # Step 1: Ensure server is running
        server_ready = await self._ensure_server_ready()
        if not server_ready:
            raise RuntimeError(
                "❌ Failed to start Aii server.\n\n"
                "Try:\n"
                "  1. Check if port 16169 is available: lsof -i :16169\n"
                "  2. Start server manually: aii serve\n"
                "  3. Check logs: ~/.aii/logs/server.log"
            )

        # Step 2: Connect WebSocket (or reuse)
        if not self.ws_client or not self.ws_client.is_connected():
            debug_print("CLIENT: Creating WebSocket client...")
            self.ws_client = create_websocket_client(self.api_url, self.api_key, self.mcp_client)
            await self.ws_client.connect()
            debug_print("CLIENT: WebSocket connected!")

        # Step 3: Call recognize_intent on WebSocket client
        try:
            result = await self.ws_client.recognize_intent(user_input)
            debug_print(f"CLIENT: Recognition result - {result.get('function')} (requires_confirmation: {result.get('requires_confirmation')})")
            return result
        except (WebSocketConnectionError, WebSocketTimeout) as e:
            raise RuntimeError(f"❌ Intent recognition failed: {e}")

    async def _ensure_server_ready(self) -> bool:
        """
        Ensure server is running, start if needed.

        Auto-start ONLY happens for default localhost:16169.
        For custom hosts/ports, user must start server manually.

        Returns:
            True if server is ready
        """

        # Check if server is already running
        if self.server_manager.is_server_running():
            logger.debug("Server already running")
            return True

        # v0.6.0: Only auto-start if using default localhost:16169
        # If user specified custom --host, they must start server manually
        is_default_config = (
            self.server_manager.host in ["127.0.0.1", "localhost"] and
            self.server_manager.port == 16169
        )

        if not is_default_config:
            # Custom host/port - don't auto-start
            logger.error(f"Server not running on {self.server_manager.host}:{self.server_manager.port}")
            return False

        # Auto-start server (only for default localhost:16169)
        logger.info("Server not running, auto-starting...")
        started = await self.server_manager.start_server(background=True)

        if not started:
            logger.error("Failed to auto-start server")
            return False

        # Wait for server to be ready (max 5 seconds)
        for i in range(50):  # 50 × 100ms = 5s
            await asyncio.sleep(0.1)
            if self.server_manager.is_server_running():
                logger.info(f"Server ready after {(i+1)*100}ms")
                return True

        logger.error("Server started but not responding")
        return False

    async def close(self):
        """Close WebSocket connection"""
        if self.ws_client:
            await self.ws_client.close()
            self.ws_client = None
            logger.debug("CLI client closed")
