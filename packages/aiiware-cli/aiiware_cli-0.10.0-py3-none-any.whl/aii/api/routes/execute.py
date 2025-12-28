# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Function execution endpoint."""


from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from aii.api.models import ExecuteRequest, ExecuteResponse, ErrorResponse
from aii.api.middleware import verify_api_key, check_rate_limit, get_server_instance
from aii.api.formatters import format_completion_metadata
from aii.api.errors import (
    format_error_response,
    get_status_code,
    FunctionNotFoundError,
    FunctionExecutionError,
    AiiError,
)
from aii.core.models import RecognitionResult, RouteSource

router = APIRouter()


def detect_client_type(http_request: Request, request: ExecuteRequest) -> str:
    """
    Detect client type from request headers or explicit field.

    Priority:
    1. Explicit client_type in request body
    2. Aii-Client header
    3. User-Agent header detection
    4. Default to "api"
    """
    # Check explicit field first
    if request.client_type:
        return request.client_type

    # Check custom header
    client_header = http_request.headers.get("Aii-Client", "").lower()
    if client_header in ["cli", "vscode", "chrome"]:
        return client_header

    # Check User-Agent
    user_agent = http_request.headers.get("user-agent", "").lower()
    if "vscode" in user_agent or "aii-vscode" in user_agent:
        return "vscode"
    elif "chrome" in user_agent or "aii-chrome" in user_agent:
        return "chrome"

    # Default to generic API client
    return "api"


@router.post("/api/execute", response_model=ExecuteResponse, responses={
    400: {"model": ErrorResponse, "description": "Validation error"},
    401: {"model": ErrorResponse, "description": "Authentication error"},
    404: {"model": ErrorResponse, "description": "Function not found"},
    429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
})
async def execute_function(
    http_request: Request,
    request: ExecuteRequest,
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute AII function with parameters.

    Supports two execution patterns:
    1. Natural Language (LLM-First): Provide 'user_prompt' for natural language input
    2. Direct Execution: Provide 'function' + 'params' for explicit function calls

    **Client Tracking (v0.9.2)**: Optionally include `Aii-Client` header to track which
    client is making the request (cli, vscode, chrome). If not provided, client type is
    auto-detected from User-Agent or defaults to "api".

    Example 1 (Natural Language - v0.8.0):
    ```bash
    curl -X POST http://localhost:16169/api/execute \\
      -H "Content-Type: application/json" \\
      -H "Aii-API-Key: aii_sk_..." \\
      -d '{
        "user_prompt": "translate hello to spanish",
        "model": "gpt-4o"
      }'
    ```

    Example 2 (Direct Execution - backward compatible):
    ```bash
    curl -X POST http://localhost:16169/api/execute \\
      -H "Content-Type: application/json" \\
      -H "Aii-API-Key: aii_sk_..." \\
      -d '{
        "function": "translate",
        "params": {"text": "hello", "target_language": "spanish"}
      }'
    ```

    Example 3 (With Client Tracking - v0.9.2):
    ```bash
    curl -X POST http://localhost:16169/api/execute \\
      -H "Content-Type: application/json" \\
      -H "Aii-API-Key: aii_sk_..." \\
      -H "Aii-Client: vscode" \\
      -d '{
        "user_prompt": "explain this code",
        "model": "claude-3.5-sonnet"
      }'
    ```

    Success Response:
    ```json
    {
      "success": true,
      "result": "hola",
      "metadata": {
        "tokens": {"input": 145, "output": 28},
        "cost": 0.0004,
        "execution_time": 1.23
      }
    }
    ```

    Error Response:
    ```json
    {
      "error": {
        "code": "FUNCTION_NOT_FOUND",
        "message": "Function 'invalid' not found",
        "details": {
          "function": "invalid",
          "available_functions": ["translate", "explain", ...]
        },
        "request_id": "req_abc123"
      }
    }
    ```
    """
    # Get request ID from middleware (RequestIDMiddleware)
    request_id = getattr(http_request.state, "request_id", None)

    server = get_server_instance()

    if not server:
        # Server not initialized - this is an internal error
        error_detail = format_error_response(
            Exception("Server not initialized"),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error=error_detail).dict()
        )

    try:
        # v0.8.0: Handle model/provider override (per-request model selection)
        llm_provider = None
        if request.model:
            try:
                # Auto-detect provider if not specified
                provider_name = request.provider
                if not provider_name:
                    from aii.data.providers.model_registry import detect_provider_from_model
                    provider_name = detect_provider_from_model(request.model)

                # Create temporary provider for this request
                from aii.data.providers.llm_provider import create_temporary_provider
                llm_provider = await create_temporary_provider(
                    provider_name=provider_name,
                    model=request.model,
                    config_manager=server.config  # Use server.config, not server.config_manager
                )

            except ValueError as e:
                # Invalid model name
                from aii.data.providers.model_registry import get_available_models
                available = get_available_models()
                all_models = [model for models in available.values() for model in models]

                error_detail = format_error_response(
                    Exception(str(e)),
                    request_id=request_id,
                    error_code="MODEL_NOT_FOUND",
                    details={"available_models": sorted(all_models)}
                )
                return JSONResponse(
                    status_code=400,
                    content=ErrorResponse(error=error_detail).dict()
                )

            except RuntimeError as e:
                # API key not configured for provider
                error_detail = format_error_response(
                    Exception(str(e)),
                    request_id=request_id,
                    error_code="PROVIDER_NOT_CONFIGURED"
                )
                return JSONResponse(
                    status_code=400,
                    content=ErrorResponse(error=error_detail).dict()
                )
        else:
            # No override - use server's default provider
            llm_provider = server.engine.llm_provider

        # v0.8.0: Support both execution patterns
        if request.user_prompt:
            # Pattern 1: Natural language (LLM-first) - recognize intent from user prompt
            from aii.core.intent.recognizer import IntentRecognizer
            recognizer = IntentRecognizer(llm_provider=llm_provider)
            recognizer.register_function_registry(server.engine.function_registry)
            recognition_result = await recognizer.recognize_intent(request.user_prompt)

            # Check if recognition failed
            if not recognition_result or not recognition_result.function_name:
                raise FunctionExecutionError(
                    "Could not recognize function from natural language input",
                    function_name=None
                )

        else:
            # Pattern 2: Direct execution - use function name directly from request
            function_name = request.function
            parameters = request.params or {}

            # Validate function exists - use structured error
            if function_name not in server.engine.function_registry.plugins:
                available = list(server.engine.function_registry.plugins.keys())
                raise FunctionNotFoundError(function_name, available)

            # Create recognition result for direct API execution
            recognition_result = RecognitionResult(
                intent=function_name,
                confidence=1.0,  # API clients explicitly specify function
                parameters=parameters,
                function_name=function_name,
                requires_confirmation=False,  # API execution doesn't require confirmation
                reasoning="Direct API invocation",
                source=RouteSource.DIRECT_MATCH
            )

        # v0.9.2: Detect client type for analytics
        client_type = detect_client_type(http_request, request)

        # Execute function via execution engine
        # v0.8.0: Use llm_provider override if specified
        result = await server.engine.execution_engine.execute_function(
            recognition_result=recognition_result,
            user_input=request.get_formatted_input(),
            chat_context=None,
            config=server.engine.config,
            llm_provider=llm_provider,  # v0.8.0: Use override or default
            web_client=server.engine.web_client,
            mcp_client=server.engine.mcp_client,
            offline_mode=False,
            client_type=client_type  # v0.9.2: Track client source
        )

        return ExecuteResponse(
            success=result.success,
            result=result.data if result.success else None,
            error=result.message if not result.success else None,
            metadata=format_completion_metadata(result)
        )

    except AiiError as e:
        # Handle Aii-specific errors with structured response
        error_detail = format_error_response(e, request_id=request_id)
        return JSONResponse(
            status_code=e.status_code,
            content=ErrorResponse(error=error_detail).dict()
        )

    except HTTPException as e:
        # Re-raise FastAPI HTTP exceptions (auth, rate limit, etc.)
        raise

    except Exception as e:
        # Handle unexpected errors with structured response
        error_detail = format_error_response(e, request_id=request_id)
        status_code = get_status_code(e)
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(error=error_detail).dict()
        )
