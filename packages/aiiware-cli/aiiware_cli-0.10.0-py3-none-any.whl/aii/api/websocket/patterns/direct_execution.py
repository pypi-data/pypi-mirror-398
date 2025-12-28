# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Direct execution pattern - Direct function invocation."""


from typing import Dict, Any
from fastapi import WebSocket

from aii.core.models import RecognitionResult, RouteSource


async def handle_direct_execution_pattern(
    websocket: WebSocket,
    data: Dict[str, Any],
    server: Any,
    llm_provider = None  # v0.8.0: Optional provider override (not used in this pattern)
) -> RecognitionResult:
    """
    Handle direct execution pattern (domain operations or legacy format).

    Pattern 2: Client specifies exact function + parameters.

    Args:
        websocket: FastAPI WebSocket connection
        data: Request data containing function and params
        server: APIServer instance
        llm_provider: Optional LLM provider override (v0.8.0, not used in this pattern)

    Returns:
        RecognitionResult for direct invocation

    Raises:
        Exception: If function not found
    """
    function_name = data.get("function", "")
    parameters = data.get("params", {})

    # Validate function exists first
    if function_name not in server.engine.function_registry.plugins:
        await websocket.send_json({
            "type": "error",
            "message": f"Function '{function_name}' not found"
        })
        raise ValueError(f"Function '{function_name}' not found")

    # Create recognition result for direct invocation
    recognition_result = RecognitionResult(
        intent=function_name,
        confidence=1.0,
        parameters=parameters,
        function_name=function_name,
        requires_confirmation=False,
        reasoning="Direct WebSocket invocation",
        source=RouteSource.DIRECT_MATCH
    )

    return recognition_result
