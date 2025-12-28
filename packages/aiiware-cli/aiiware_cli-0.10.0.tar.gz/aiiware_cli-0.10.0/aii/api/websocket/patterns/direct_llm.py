# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Direct LLM call pattern - Prompt library natural language mode."""


from typing import Dict, Any
from fastapi import WebSocket
import time

from aii.core.models import ExecutionResult
from aii.api.utils import is_debug_enabled


async def handle_direct_llm_pattern(
    websocket: WebSocket,
    data: Dict[str, Any],
    server: Any,
    streaming_callback,
    llm_provider = None,  # v0.8.0: Optional provider override
    attachments = None  # v0.10.0: Optional file attachments for vision
) -> ExecutionResult:
    """
    Handle direct LLM call pattern (v0.6.1 Prompt Library natural_language mode).

    Pattern 3: Client provides custom system_prompt + user_prompt, server calls LLM directly.
    Bypasses intent recognition and uses ONLY the custom system prompt.

    Args:
        websocket: FastAPI WebSocket connection
        data: Request data containing system_prompt, user_prompt, prompt_name
        server: APIServer instance
        streaming_callback: Async callback for token streaming
        llm_provider: Optional LLM provider override (v0.8.0)
        attachments: Optional file attachments for vision models (v0.10.0)

    Returns:
        ExecutionResult with LLM response

    Raises:
        Exception: If LLM call fails
    """
    system_prompt = data.get("system_prompt")
    user_prompt = data.get("user_prompt")
    prompt_name = data.get("prompt_name")

    # v0.10.0: Log multimodal requests
    has_attachments = attachments and len(attachments) > 0
    if has_attachments and is_debug_enabled():
        print(f"🔍 DEBUG [Direct LLM]: Multimodal request with {len(attachments)} attachment(s)")

    # v0.6.2: Call LLM directly with ONLY the custom system_prompt + user_input
    # Do NOT use universal_generate (which adds orchestrator prompts)
    try:
        # v0.8.0: Use override or default provider
        provider = llm_provider or server.engine.llm_provider

        # Check if LLM provider is initialized
        if provider is None:
            error_msg = "LLM provider not initialized. "
            if hasattr(server, 'initialization_status') and server.initialization_status.get('llm_error'):
                error_msg += server.initialization_status['llm_error']
            else:
                error_msg += "Please configure your LLM provider with 'aii config provider <provider_name>'."

            # Raise exception - let existing exception handler send error to client
            raise RuntimeError(error_msg)

        # Assemble full prompt (system_prompt + user_input in triple quotes)
        # v0.6.2: Wrap user input in triple quotes for better prompt adherence
        assembled_prompt = f"{system_prompt}\n\n\"\"\"{user_prompt}\"\"\""

        # Get display name
        display_name = prompt_name if prompt_name else "direct_llm_call"

        # Call LLM provider directly (bypass universal_generate orchestrator)
        start_time = time.time()

        # v0.10.0: Pass attachments for multimodal processing
        llm_response = await provider.complete_with_usage(
            prompt=assembled_prompt,
            on_token=streaming_callback,  # Fixed: use on_token parameter
            attachments=attachments  # v0.10.0: Multimodal support
        )

        execution_time = time.time() - start_time

        # Build ExecutionResult from LLM response
        result = ExecutionResult(
            success=True,
            message=llm_response.content,
            function_name=display_name,
            data={
                "content": llm_response.content,
                "clean_output": llm_response.content,
                "input_tokens": llm_response.usage.get("input_tokens", 0) if llm_response.usage else 0,
                "output_tokens": llm_response.usage.get("output_tokens", 0) if llm_response.usage else 0,
                "cost": llm_response.usage.get("cost", 0) if llm_response.usage else 0,
                "model": llm_response.model,
                "reasoning": f"Direct LLM call with custom prompt: {display_name}",
                "generation_method": "direct_llm_call",
                "original_request": user_prompt,
                "prompt_name": prompt_name,
            },
            execution_time=execution_time
        )

        # v0.6.2: Calculate cost using CostCalculator (direct LLM call bypasses ExecutionEngine)
        if server.engine.execution_engine.cost_calculator:
            try:
                # v0.8.0: Use actual provider (may be override)
                provider_name = getattr(provider, 'provider_name', 'unknown')
                model_name = getattr(provider, 'model_name', 'unknown')

                cost_breakdown = server.engine.execution_engine.cost_calculator.calculate_cost(
                    provider=provider_name,
                    model=model_name,
                    input_tokens=result.data.get('input_tokens', 0),
                    output_tokens=result.data.get('output_tokens', 0),
                    reasoning_tokens=0
                )
                result.data['cost'] = cost_breakdown.total_cost
            except Exception as e:
                # Silently fail on cost calculation (non-critical feature)
                result.data['cost'] = 0.0

        return result

    except Exception as e:
        if is_debug_enabled():
            import traceback
            traceback.print_exc()
        await websocket.send_json({
            "type": "error",
            "message": f"Direct LLM call failed: {str(e)}"
        })
        # Don't close here - let main handler clean up
        raise
