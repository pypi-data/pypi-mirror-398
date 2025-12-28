# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Response formatters for API completion metadata."""


from aii.core.models import ExecutionResult


def format_completion_metadata(result: ExecutionResult) -> dict:
    """
    Extract token metadata from ExecutionResult for API completion responses.

    Ensures parity between REST and WebSocket API metadata structure.
    Resolves Aii-CLI-WS-001: WebSocket token metadata bug.

    Args:
        result: ExecutionResult from function execution

    Returns:
        dict: Formatted metadata with tokens, cost, model, execution_time

    Example:
        >>> result = ExecutionResult(...)
        >>> metadata = format_completion_metadata(result)
        >>> metadata
        {
            "tokens": {"input": 245, "output": 182},
            "cost": 0.0042,
            "model": "gemini-2.0-flash-exp",
            "execution_time": 3.94
        }
    """
    # Initialize metadata dict
    metadata = {
        "execution_time": getattr(result, "execution_time", None)
    }

    # Extract result data (functions store token info in result.data dict)
    result_data = result.data if result.data else {}

    # Extract token usage from result.data
    # Functions store tokens as 'input_tokens' and 'output_tokens'
    input_tokens = result_data.get("input_tokens")
    output_tokens = result_data.get("output_tokens")

    # Add tokens if available (both must be present)
    if input_tokens is not None and output_tokens is not None:
        metadata["tokens"] = {
            "input": int(input_tokens) if input_tokens is not None else 0,
            "output": int(output_tokens) if output_tokens is not None else 0
        }
    else:
        metadata["tokens"] = None

    # Extract cost (may be in result.data or calculated separately)
    cost = result_data.get("cost") or result_data.get("estimated_cost")
    metadata["cost"] = float(cost) if cost is not None else None

    # Extract model name
    model = result_data.get("model") or result_data.get("provider")
    if model:
        metadata["model"] = str(model)

    # Extract confidence (optional, if available)
    confidence = result_data.get("confidence")
    if confidence is not None:
        metadata["confidence"] = float(confidence)

    # Extract reasoning (for THINKING and VERBOSE modes)
    reasoning = result_data.get("reasoning")
    if reasoning:
        metadata["reasoning"] = str(reasoning)

    # Extract session ID from SessionManager (for VERBOSE mode)
    from ..core.session.manager import SessionManager
    session = SessionManager.get_current_session()
    if session:
        metadata["session_id"] = session.session_id
        # Add success rate for quality assessment
        metadata["success_rate"] = session.success_rate if hasattr(session, 'success_rate') else None
        metadata["total_functions"] = session.total_functions if hasattr(session, 'total_functions') else None

    # Special handling for git_commit - include commit preview data
    if result_data.get("requires_commit_confirmation"):
        metadata["requires_commit_confirmation"] = True
        metadata["git_diff"] = result_data.get("git_diff")
        metadata["commit_message"] = result_data.get("commit_message")

    # Special handling for shell commands - include explanation and risks (v0.6.0)
    if result_data.get("requires_execution_confirmation"):
        metadata["requires_execution_confirmation"] = True
        metadata["command"] = result_data.get("command")
        metadata["explanation"] = result_data.get("explanation")
        metadata["risks"] = result_data.get("safety_notes") or result_data.get("risks", [])

    return metadata
