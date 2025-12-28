# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""LLM-First execution pattern - Intent recognition flow."""


from typing import Dict, Any
from fastapi import WebSocket

from aii.core.models import RecognitionResult, FunctionSafety
from aii.api.utils import is_debug_enabled


async def handle_llm_first_pattern(
    websocket: WebSocket,
    data: Dict[str, Any],
    server: Any,
    action: str,
    llm_provider = None  # v0.8.0: Optional provider override
) -> RecognitionResult:
    """
    Handle LLM-first pattern (intent recognition).

    Pattern 1: User provides natural language, server recognizes intent.

    Args:
        websocket: FastAPI WebSocket connection
        data: Request data containing user_input or user_prompt
        server: APIServer instance
        action: Legacy action type (for backward compatibility)
        llm_provider: Optional LLM provider override (v0.8.0)

    Returns:
        RecognitionResult with recognized function and parameters

    Raises:
        Exception: If intent recognition fails or user input is missing
    """
    # Extract user input (support both new and legacy formats)
    user_prompt = data.get("user_prompt")
    function_name = data.get("function", "")
    parameters = data.get("params", {})

    if user_prompt:
        user_input = user_prompt
    elif action == "recognize":
        user_input = data.get("user_input", "")
    elif function_name == "auto":
        user_input = parameters.get("user_input", "")
    else:
        user_input = None

    if not user_input:
        await websocket.send_json({
            "type": "error",
            "message": "Missing user input for LLM-first mode"
        })
        # Don't close here - let main handler clean up
        raise ValueError("Missing user input")

    # Perform intent recognition
    try:
        recognition_result = await server.engine.intent_recognizer.recognize_intent(user_input)
        function_name = recognition_result.function_name
        parameters = recognition_result.parameters

        # Get function plugin to check safety and generate metadata
        function_plugin = server.engine.function_registry.plugins.get(function_name)
        if not function_plugin:
            await websocket.send_json({
                "type": "error",
                "message": f"Function '{function_name}' not found"
            })
            # Don't close here - let main handler clean up
            raise ValueError(f"Function '{function_name}' not found")

        # Get safety level and description
        safety_level = function_plugin.safety_level
        requires_confirmation = safety_level in [FunctionSafety.RISKY, FunctionSafety.DESTRUCTIVE]
        description = function_plugin.description if hasattr(function_plugin, 'description') else f"Execute {function_name}"

        # For backward compatibility with old "recognize" action, send recognition response
        if action == "recognize":
            await websocket.send_json({
                "type": "recognition",
                "function": function_name,
                "parameters": parameters,
                "safety": str(safety_level.value) if hasattr(safety_level, 'value') else str(safety_level),
                "description": description,
                "requires_confirmation": requires_confirmation
            })
            # Don't close here - let main handler clean up
            raise StopIteration("Recognition-only mode completed")

        # New unified flow: Continue to execution with complete metadata
        # Update recognition_result to include confirmation requirement
        recognition_result = RecognitionResult(
            intent=function_name,
            confidence=recognition_result.confidence,
            parameters=parameters,
            function_name=function_name,
            requires_confirmation=requires_confirmation,
            reasoning=recognition_result.reasoning,
            source=recognition_result.source
        )

        return recognition_result

    except StopIteration:
        # Recognition-only mode completed successfully
        raise
    except Exception as e:
        if is_debug_enabled():
            import traceback
            traceback.print_exc()
        # Don't send error here - let main handler send structured error
        # Just re-raise with clear message for main handler to categorize
        raise Exception(f"Intent recognition failed: {str(e)}") from e
