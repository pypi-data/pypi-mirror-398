# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Main WebSocket handler for Aii API server."""


from typing import Any
from pathlib import Path
import yaml
import uuid

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from pydantic import ValidationError

from aii.api.formatters import format_completion_metadata
from aii.api.websocket.streaming import create_streaming_callback
from aii.api.websocket.patterns import (
    handle_llm_first_pattern,
    handle_direct_execution_pattern,
    handle_direct_llm_pattern
)
from aii.api.errors import (
    ErrorCode,
    ErrorDetail,
    format_error_response,
    format_validation_error,
)
from aii.api.models import WebSocketExecuteRequest


async def handle_websocket_connection(websocket: WebSocket, server: Any):
    """
    Handle WebSocket connection for real-time streaming.

    Supports three execution patterns:
    1. LLM-First: User provides natural language, server recognizes intent
    2. Direct Execution: Client specifies exact function + parameters
    3. Direct LLM Call: Client provides custom system_prompt, server calls LLM directly

    Protocol:
    ```
    Client → Server: {"api_key": "...", "function": "translate", "params": {...}}
    Server → Client: {"type": "token", "data": "h"}
    Server → Client: {"type": "token", "data": "o"}
    Server → Client: {"type": "token", "data": "l"}
    Server → Client: {"type": "token", "data": "a"}
    Server → Client: {"type": "complete", "metadata": {...}}
    ```

    Error handling:
    ```
    Server → Client: {"type": "error", "message": "..."}
    ```

    Args:
        websocket: FastAPI WebSocket connection
        server: APIServer instance
    """
    await websocket.accept()

    # v0.6.0: Create WebSocket handler for bidirectional communication (MCP delegation)
    from aii.api.websocket_handler import WebSocketHandler
    ws_handler = None  # Will be initialized after authentication
    # NOTE: Don't start listener yet - start AFTER reading initial request to avoid recv() conflict

    try:
        # Receive request
        data = await websocket.receive_json()

        # Generate request ID for this WebSocket connection
        request_id = f"ws_{uuid.uuid4().hex[:16]}"

        # v0.8.1: Validate request with Pydantic
        try:
            request = WebSocketExecuteRequest(**data)
        except ValidationError as e:
            # Send clear error message to client
            await websocket.send_json({
                "type": "error",
                "code": ErrorCode.VALIDATION_ERROR.value,
                "message": format_validation_error(e),
                "details": e.errors(),
                "request_id": request_id
            })
            await websocket.close()
            return

        # Verify API key FIRST (before starting background listener)
        api_key = data.get("api_key")
        if not api_key or not server or not server.auth.verify_key(api_key):
            await websocket.send_json({
                "type": "error",
                "code": ErrorCode.AUTH_INVALID_API_KEY.value if api_key else ErrorCode.AUTH_MISSING_API_KEY.value,
                "message": "Invalid or missing API key",
                "request_id": request_id
            })
            await websocket.close()
            return

        # Check rate limit
        if not server.rate_limiter.allow(api_key):
            await websocket.send_json({
                "type": "error",
                "code": ErrorCode.RATE_LIMIT_EXCEEDED.value,
                "message": "Rate limit exceeded",
                "request_id": request_id
            })
            await websocket.close()
            return

        # NOW initialize and start background listener (after authentication succeeds)
        ws_handler = WebSocketHandler(websocket)
        ws_handler.start_listening()

        # v0.10.0: Extract attachments for multimodal processing
        attachments = data.get("attachments", [])
        has_attachments = len(attachments) > 0 if attachments else False

        if has_attachments:
            import os
            if os.getenv("AII_DEBUG"):
                print(f"🔍 DEBUG [WebSocket]: Received {len(attachments)} attachment(s)")
                for i, att in enumerate(attachments):
                    print(f"  [{i+1}] Type: {att.get('type')}, Filename: {att.get('filename')}, Size: {att.get('size')} bytes")

        # v0.8.0: Handle model/provider override (per-request model selection)
        override_model = data.get("model")
        override_provider = data.get("provider")
        llm_provider = None

        if override_model:
            # User specified a model override
            try:
                # Auto-detect provider if not specified
                if not override_provider:
                    from aii.data.providers.model_registry import detect_provider_from_model
                    override_provider = detect_provider_from_model(override_model)

                # Create temporary provider for this request
                from aii.data.providers.llm_provider import create_temporary_provider
                llm_provider = await create_temporary_provider(
                    provider_name=override_provider,
                    model=override_model,
                    config_manager=server.config  # Use server.config, not server.config_manager
                )

                # Debug logging for model override
                import os
                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG [WebSocket]: Using model override: {override_provider}:{override_model}")

            except ValueError as e:
                # Invalid model name
                from aii.data.providers.model_registry import get_available_models
                available = get_available_models()
                all_models = [model for models in available.values() for model in models]

                await websocket.send_json({
                    "type": "error",
                    "code": "MODEL_NOT_FOUND",
                    "message": str(e),
                    "available_models": sorted(all_models),
                    "request_id": request_id
                })
                await websocket.close()
                return

            except RuntimeError as e:
                # API key not configured for provider
                await websocket.send_json({
                    "type": "error",
                    "code": "PROVIDER_NOT_CONFIGURED",
                    "message": str(e),
                    "request_id": request_id
                })
                await websocket.close()
                return
        else:
            # No override - use server's default provider
            llm_provider = server.engine.llm_provider

        # v0.6.0 UNIFIED ENDPOINT: Support both command patterns via system_prompt parameter
        # Pattern 1 (LLM-First): system_prompt=null → Server performs intent recognition
        # Pattern 2 (Domain Ops): system_prompt="..." → Server executes with provided prompts

        system_prompt = data.get("system_prompt")  # Can be None or string
        user_prompt = data.get("user_prompt")      # Always required for LLM-first

        # Legacy support: Handle old request formats
        # Old format 1: action="recognize" → Map to system_prompt=null
        # Old format 2: function="auto" → Map to system_prompt=null
        # Old format 3: function="translate", params={} → Direct execution (backward compat)

        action = data.get("action", "execute")

        # Determine execution pattern (v0.6.1 adds Pattern 3 for prompt library)
        is_llm_first = False
        is_direct_llm_call = False

        if system_prompt is not None and isinstance(system_prompt, str) and user_prompt:
            # Pattern 3: Direct LLM Call (v0.6.1 Prompt Library natural_language mode)
            # system_prompt provided → bypass intent recognition, call LLM directly
            is_direct_llm_call = True
        elif system_prompt is None and user_prompt:
            # Pattern 1: LLM-First (new unified format)
            is_llm_first = True
        elif action == "recognize":
            # Legacy: Old recognize action
            is_llm_first = True
        elif data.get("function") == "auto":
            # Legacy: Old auto mode
            is_llm_first = True
        else:
            # Pattern 2: Direct execution (old format or domain ops)
            is_llm_first = False

        # Create streaming callback
        streaming_callback = create_streaming_callback(websocket)

        # Handle Direct LLM Call pattern (v0.6.1 Prompt Library natural_language mode)
        if is_direct_llm_call:
            result = await handle_direct_llm_pattern(
                websocket=websocket,
                data=data,
                server=server,
                streaming_callback=streaming_callback,
                llm_provider=llm_provider,  # v0.8.0: Pass provider override
                attachments=attachments  # v0.10.0: Pass attachments for multimodal
            )

            # Send completion immediately
            # NOTE: Don't include "result" field - tokens already streamed via streaming_callback
            display_function_name = result.function_name
            await websocket.send_json({
                "type": "complete",
                "success": result.success,
                "function_name": display_function_name,
                # "result": result.message,  # Omit - already streamed token-by-token
                "data": result.data,
                "metadata": format_completion_metadata(result)
            })
            return  # Exit early - don't continue to standard execution flow

        # Handle LLM-First pattern (intent recognition)
        elif is_llm_first:
            try:
                recognition_result = await handle_llm_first_pattern(
                    websocket=websocket,
                    data=data,
                    server=server,
                    action=action,
                    llm_provider=llm_provider  # v0.8.0: Pass provider override
                )
            except StopIteration:
                # Recognition-only mode completed successfully
                return

        # Handle Direct Execution pattern
        else:
            recognition_result = await handle_direct_execution_pattern(
                websocket=websocket,
                data=data,
                server=server,
                llm_provider=llm_provider  # v0.8.0: Pass provider override
            )

        # At this point, both LLM-first and direct execution have recognition_result
        function_name = recognition_result.function_name

        # Validate function exists (for LLM-first flow)
        if function_name not in server.engine.function_registry.plugins:
            await websocket.send_json({
                "type": "error",
                "code": ErrorCode.FUNCTION_NOT_FOUND.value,
                "message": f"Function '{function_name}' not found",
                "request_id": request_id
            })
            return

        # Check if LLM provider is required but not initialized
        if not server.initialization_status.get("llm_provider"):
            # Check if this function requires LLM
            function_plugin = server.engine.function_registry.plugins.get(function_name)
            requires_llm = hasattr(function_plugin, 'requires_llm') and function_plugin.requires_llm

            # Most functions require LLM, so assume yes unless explicitly stated
            if requires_llm or not hasattr(function_plugin, 'requires_llm'):
                llm_error = server.initialization_status.get("llm_error", "Unknown error")

                # Check if user has actually configured LLM (not just auto-created config)
                config_file = Path.home() / ".aii" / "config.yaml"
                secrets_file = Path.home() / ".aii" / "secrets.yaml"

                llm_configured = False
                if config_file.exists() and secrets_file.exists():
                    try:
                        with open(config_file) as f:
                            config_data = yaml.safe_load(f) or {}
                        # Check if provider and model are set (not null)
                        llm_provider = config_data.get("llm", {}).get("provider")
                        llm_model = config_data.get("llm", {}).get("model")
                        llm_configured = bool(llm_provider and llm_model)
                    except Exception:
                        pass

                if llm_configured:
                    # Config exists with valid LLM settings but server hasn't picked it up
                    # This happens when user runs `aii config init` while server is running
                    guidance_msg = (
                        "Configuration detected but not loaded yet.\n\n"
                        "Restart the server to apply changes:\n"
                        "  aii serve restart"
                    )
                else:
                    # No valid config - needs initial setup
                    guidance_msg = "To set up AII, run: aii config init\n(Takes ~2 minutes)"

                await websocket.send_json({
                    "type": "error",
                    "code": ErrorCode.FUNCTION_PREREQUISITES_NOT_MET.value,
                    "message": "Prerequisites not met: LLM provider required",
                    "request_id": request_id,
                    "details": {
                        "reason": "LLM provider not initialized",
                        "error": llm_error,
                        "guidance": guidance_msg
                    }
                })
                await websocket.close()
                return

        # Pass streaming callback to execution engine
        # The engine will use it for LLM streaming if available
        # v0.8.0: Use llm_provider override if specified
        result = await server.engine.execution_engine.execute_function(
            recognition_result=recognition_result,
            user_input=f"{function_name} {recognition_result.parameters}",
            chat_context=None,
            config=server.engine.config,
            llm_provider=llm_provider,  # v0.8.0: Use override or default
            web_client=server.engine.web_client,
            mcp_client=server.engine.mcp_client,
            offline_mode=False,
            streaming_callback=streaming_callback,  # Enable real streaming
            websocket_handler=ws_handler  # v0.6.0: For MCP client-side execution
        )

        # Send completion with full metadata (v0.5.1 fix for Aii-CLI-WS-001)
        # v0.6.0: Include data field for client-side domain operations
        # v0.6.2: Use display name from recognition_result (shows prompt name instead of internal function)
        display_function_name = recognition_result.function_name if recognition_result else function_name
        await websocket.send_json({
            "type": "complete",
            "success": result.success,
            "function_name": display_function_name,  # v0.6.2: Use display name (prompt name if applicable)
            "result": result.message,  # Include the actual result text
            "data": result.data,  # v0.6.0: Include data field for git_commit and other functions
            "metadata": format_completion_metadata(result)
        })

    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Generate request ID for error tracking
        request_id = f"ws_{uuid.uuid4().hex[:16]}"

        # Determine error code based on exception type/message
        error_message = str(e)

        # Check for specific error patterns
        if "Content filtered" in error_message:
            # Content filter error (OpenAI, Moonshot, etc.)
            error_code = ErrorCode.LLM_PROVIDER_ERROR
            user_message = error_message  # Already user-friendly from llm_provider.py
        elif "Connection error" in error_message or "connection" in error_message.lower():
            error_code = ErrorCode.LLM_PROVIDER_UNAVAILABLE
            user_message = "LLM provider connection failed. Please check your network connection and API key configuration."
        elif "Pydantic AI completion failed" in error_message:
            error_code = ErrorCode.LLM_PROVIDER_ERROR
            user_message = "LLM provider error occurred. Please try again."
        elif "Rate limit" in error_message.lower():
            error_code = ErrorCode.LLM_RATE_LIMIT_EXCEEDED
            user_message = "LLM provider rate limit exceeded. Please wait and try again."
        elif "Intent recognition failed" in error_message:
            error_code = ErrorCode.LLM_PROVIDER_ERROR
            user_message = f"Intent recognition failed: {error_message.split('Intent recognition failed:')[-1].strip()}"
        elif "Function" in error_message and "not found" in error_message:
            error_code = ErrorCode.FUNCTION_NOT_FOUND
            user_message = error_message
        else:
            error_code = ErrorCode.INTERNAL_ERROR
            user_message = error_message

        # Format structured error
        error_detail = format_error_response(e, request_id=request_id)

        # Send structured error to client
        try:
            await websocket.send_json({
                "type": "error",
                "code": error_code.value,
                "message": user_message,
                "request_id": request_id,
                "details": error_detail.dict() if hasattr(error_detail, 'dict') else None
            })
        except:
            # If sending fails, connection is already closed
            pass

    finally:
        # v0.6.0: Stop WebSocket handler background listener
        if ws_handler:
            await ws_handler.stop_listening()

        # Close connection
        try:
            await websocket.close()
        except:
            pass
