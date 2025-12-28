# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Structured error handling for Aii API.

Provides:
- Error code taxonomy
- Structured error responses
- Environment-aware traceback handling
- Type-safe error models
"""


import os
import traceback
import logging
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """
    Error code taxonomy for Aii API.

    Format: CATEGORY_SPECIFIC_ERROR
    Categories: VALIDATION, AUTH, RATE_LIMIT, FUNCTION, LLM, MCP, INTERNAL
    """

    # Validation Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    VALIDATION_MISSING_PARAMETER = "VALIDATION_MISSING_PARAMETER"
    VALIDATION_INVALID_PARAMETER = "VALIDATION_INVALID_PARAMETER"
    VALIDATION_INVALID_FUNCTION = "VALIDATION_INVALID_FUNCTION"

    # v0.8.1: Pydantic validation error codes
    VALIDATION_INVALID_FIELD = "VALIDATION_INVALID_FIELD"
    VALIDATION_TYPE_ERROR = "VALIDATION_TYPE_ERROR"
    VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"

    # Authentication & Authorization Errors (401, 403)
    AUTH_MISSING_API_KEY = "AUTH_MISSING_API_KEY"
    AUTH_INVALID_API_KEY = "AUTH_INVALID_API_KEY"
    AUTH_DISABLED_API_KEY = "AUTH_DISABLED_API_KEY"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"

    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Function Execution Errors (400, 500)
    FUNCTION_NOT_FOUND = "FUNCTION_NOT_FOUND"
    FUNCTION_EXECUTION_FAILED = "FUNCTION_EXECUTION_FAILED"
    FUNCTION_PREREQUISITES_NOT_MET = "FUNCTION_PREREQUISITES_NOT_MET"
    FUNCTION_TIMEOUT = "FUNCTION_TIMEOUT"

    # LLM Provider Errors (500, 503)
    LLM_PROVIDER_ERROR = "LLM_PROVIDER_ERROR"
    LLM_PROVIDER_UNAVAILABLE = "LLM_PROVIDER_UNAVAILABLE"
    LLM_RATE_LIMIT_EXCEEDED = "LLM_RATE_LIMIT_EXCEEDED"
    LLM_CONTEXT_LENGTH_EXCEEDED = "LLM_CONTEXT_LENGTH_EXCEEDED"

    # MCP Integration Errors (500, 503)
    MCP_SERVER_ERROR = "MCP_SERVER_ERROR"
    MCP_SERVER_UNAVAILABLE = "MCP_SERVER_UNAVAILABLE"
    MCP_TOOL_NOT_FOUND = "MCP_TOOL_NOT_FOUND"
    MCP_TOOL_EXECUTION_FAILED = "MCP_TOOL_EXECUTION_FAILED"

    # Internal Server Errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INTERNAL_DATABASE_ERROR = "INTERNAL_DATABASE_ERROR"
    INTERNAL_CONFIGURATION_ERROR = "INTERNAL_CONFIGURATION_ERROR"

    # Model Override Errors (v0.8.0) (400)
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
    MODEL_PROVIDER_MISMATCH = "MODEL_PROVIDER_MISMATCH"
    MODEL_OVERRIDE_FAILED = "MODEL_OVERRIDE_FAILED"


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context-specific error details"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for debugging"
    )
    traceback: Optional[str] = Field(
        default=None,
        description="Stack trace (only in development mode)"
    )


class ErrorResponse(BaseModel):
    """Structured error response."""

    error: ErrorDetail


class AiiError(Exception):
    """
    Base exception for Aii API errors.

    All Aii-specific errors should inherit from this class.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
        cause: Optional[Exception] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.cause = cause
        super().__init__(message)

    def to_error_detail(
        self,
        request_id: Optional[str] = None,
        include_traceback: bool = False,
    ) -> ErrorDetail:
        """Convert to structured error detail."""
        error_detail = ErrorDetail(
            code=self.code,
            message=self.message,
            details=self.details,
            request_id=request_id,
        )

        if include_traceback and self.cause:
            error_detail.traceback = "".join(
                traceback.format_exception(
                    type(self.cause),
                    self.cause,
                    self.cause.__traceback__
                )
            )

        return error_detail


# Validation Errors (400)

class ValidationError(AiiError):
    """Validation error (missing or invalid parameters)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            status_code=400,
        )


class MissingParameterError(AiiError):
    """Missing required parameter."""

    def __init__(self, parameter: str, function: Optional[str] = None):
        details = {"parameter": parameter}
        if function:
            details["function"] = function

        super().__init__(
            code=ErrorCode.VALIDATION_MISSING_PARAMETER,
            message=f"Missing required parameter: {parameter}",
            details=details,
            status_code=400,
        )


class InvalidParameterError(AiiError):
    """Invalid parameter value."""

    def __init__(
        self,
        parameter: str,
        value: Any,
        expected: str,
        function: Optional[str] = None,
    ):
        details = {
            "parameter": parameter,
            "value": str(value),
            "expected": expected,
        }
        if function:
            details["function"] = function

        super().__init__(
            code=ErrorCode.VALIDATION_INVALID_PARAMETER,
            message=f"Invalid value for parameter '{parameter}': expected {expected}",
            details=details,
            status_code=400,
        )


class FunctionNotFoundError(AiiError):
    """Function not found in registry."""

    def __init__(self, function_name: str, available_functions: Optional[list] = None):
        details = {"function": function_name}
        if available_functions:
            details["available_functions"] = available_functions[:10]  # Limit to 10

        super().__init__(
            code=ErrorCode.FUNCTION_NOT_FOUND,
            message=f"Function '{function_name}' not found",
            details=details,
            status_code=404,
        )


# Authentication Errors (401, 403)

class AuthenticationError(AiiError):
    """Authentication error."""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.AUTH_INVALID_API_KEY):
        super().__init__(
            code=code,
            message=message,
            status_code=401,
        )


class MissingAPIKeyError(AuthenticationError):
    """Missing API key in request."""

    def __init__(self):
        super().__init__(
            message="API key required. Provide 'Aii-API-Key' header.",
            code=ErrorCode.AUTH_MISSING_API_KEY,
        )


class InvalidAPIKeyError(AuthenticationError):
    """Invalid API key."""

    def __init__(self):
        super().__init__(
            message="Invalid API key",
            code=ErrorCode.AUTH_INVALID_API_KEY,
        )


class DisabledAPIKeyError(AiiError):
    """API key is disabled."""

    def __init__(self):
        super().__init__(
            code=ErrorCode.AUTH_DISABLED_API_KEY,
            message="API key has been disabled",
            status_code=403,
        )


# Rate Limiting (429)

class RateLimitError(AiiError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after

        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Rate limit exceeded",
            details=details,
            status_code=429,
        )


# Function Execution Errors (400, 500)

class FunctionExecutionError(AiiError):
    """Function execution failed."""

    def __init__(
        self,
        function_name: str,
        message: str,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            code=ErrorCode.FUNCTION_EXECUTION_FAILED,
            message=f"Function '{function_name}' execution failed: {message}",
            details={"function": function_name},
            status_code=500,
            cause=cause,
        )


class FunctionPrerequisitesError(AiiError):
    """Function prerequisites not met."""

    def __init__(self, function_name: str, missing: list):
        super().__init__(
            code=ErrorCode.FUNCTION_PREREQUISITES_NOT_MET,
            message=f"Function '{function_name}' prerequisites not met",
            details={
                "function": function_name,
                "missing_prerequisites": missing,
            },
            status_code=400,
        )


# LLM Provider Errors (500, 503)

class LLMProviderError(AiiError):
    """LLM provider error."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        details = {}
        if provider:
            details["provider"] = provider

        super().__init__(
            code=ErrorCode.LLM_PROVIDER_ERROR,
            message=f"LLM provider error: {message}",
            details=details,
            status_code=500,
            cause=cause,
        )


class LLMProviderUnavailableError(AiiError):
    """LLM provider unavailable."""

    def __init__(self, provider: Optional[str] = None):
        details = {}
        if provider:
            details["provider"] = provider

        super().__init__(
            code=ErrorCode.LLM_PROVIDER_UNAVAILABLE,
            message="LLM provider is currently unavailable",
            details=details,
            status_code=503,
        )


# MCP Integration Errors (500, 503)

class MCPServerError(AiiError):
    """MCP server error."""

    def __init__(
        self,
        server_name: str,
        message: str,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            code=ErrorCode.MCP_SERVER_ERROR,
            message=f"MCP server '{server_name}' error: {message}",
            details={"server": server_name},
            status_code=500,
            cause=cause,
        )


# Utility Functions

def is_development_mode() -> bool:
    """
    Check if running in development mode.

    Development mode is enabled if:
    - AII_DEBUG environment variable is set to '1' or 'true'
    - AII_ENV environment variable is set to 'development'
    """
    debug = os.getenv("AII_DEBUG", "").lower() in ("1", "true")
    env = os.getenv("AII_ENV", "production").lower()
    return debug or env == "development"


def format_error_response(
    error: Exception,
    request_id: Optional[str] = None,
) -> ErrorDetail:
    """
    Format any exception as structured error response.

    Args:
        error: Exception to format
        request_id: Optional request ID for tracing

    Returns:
        ErrorDetail with appropriate error code and message
    """
    include_traceback = is_development_mode()

    # Handle Aii-specific errors
    if isinstance(error, AiiError):
        error_detail = error.to_error_detail(
            request_id=request_id,
            include_traceback=include_traceback,
        )

        # Log error with context
        logger.error(
            f"Aii error: {error.code.value}",
            extra={
                "error_code": error.code.value,
                "error_message": error.message,  # Use error_message instead of message (reserved by LogRecord)
                "details": error.details,
                "request_id": request_id,
            },
            exc_info=error.cause if include_traceback else None,
        )

        return error_detail

    # Handle generic exceptions
    error_detail = ErrorDetail(
        code=ErrorCode.INTERNAL_ERROR,
        message="Internal server error" if not include_traceback else str(error),
        request_id=request_id,
    )

    if include_traceback:
        error_detail.traceback = traceback.format_exc()

    # Log unexpected errors
    logger.exception(
        "Unexpected error",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "request_id": request_id,
        },
    )

    return error_detail


def get_status_code(error: Exception) -> int:
    """Get HTTP status code for exception."""
    if isinstance(error, AiiError):
        return error.status_code
    return 500  # Default to 500 for unknown errors


# v0.8.1: Pydantic validation error formatting

def format_validation_error(validation_error: Any) -> str:
    """
    Format Pydantic ValidationError into user-friendly message.

    Transforms technical Pydantic validation errors into clear, actionable
    error messages for API clients. Handles common error types like typos,
    type mismatches, missing required fields, and provides helpful suggestions.

    Examples:
        Input: usr_prompt (typo)
        Output: "Invalid field 'usr_prompt'. Did you mean 'user_prompt'?"

        Input: model=123 (wrong type)
        Output: "Field 'model' must be a string, got: int"

        Input: Missing required field 'user_prompt'
        Output: "Missing required field 'user_prompt'"

    Args:
        validation_error: Pydantic ValidationError object

    Returns:
        Human-readable error message with suggestions where applicable

    Note:
        Uses Levenshtein distance for field name suggestions (threshold: 2 edits)
    """
    # Import Pydantic ValidationError locally to avoid circular imports
    from pydantic import ValidationError as PydanticValidationError

    # Handle non-ValidationError inputs gracefully
    if not isinstance(validation_error, PydanticValidationError):
        return str(validation_error)

    errors = validation_error.errors()

    if not errors:
        return "Validation failed"

    # Take first error for main message (most important)
    first_error = errors[0]
    field = ".".join(str(loc) for loc in first_error["loc"])
    error_type = first_error["type"]
    msg = first_error.get("msg", "")

    # Handle different error types with specific formatting
    if error_type == "missing":
        return f"Missing required field '{field}'"

    elif error_type in ("string_type", "int_type", "float_type", "bool_type"):
        expected_type = error_type.replace("_type", "")
        # Try to extract actual type from context
        ctx = first_error.get("ctx", {})
        return f"Field '{field}' must be a {expected_type}"

    elif error_type in ("int_parsing", "float_parsing", "bool_parsing"):
        # Parsing errors (e.g., "not_a_number" -> int)
        expected_type = error_type.replace("_parsing", "")
        return f"Field '{field}' must be a {expected_type}"

    elif error_type == "extra_forbidden":
        return f"Unknown field '{field}' (not allowed in this request)"

    elif error_type == "value_error":
        # Custom validation error from model_validator
        return f"Validation error for '{field}': {msg}"

    elif error_type == "type_error":
        return f"Type error for field '{field}': {msg}"

    # Check for potential typos using Levenshtein distance
    if error_type == "extra_forbidden":
        suggestion = _suggest_field_name(field)
        if suggestion:
            return f"Invalid field '{field}'. Did you mean '{suggestion}'?"

    # Fallback: Use Pydantic's message
    return f"Validation error for '{field}': {msg}"


def _suggest_field_name(invalid_field: str) -> Optional[str]:
    """
    Suggest correct field name based on Levenshtein distance.

    Args:
        invalid_field: The invalid field name provided by user

    Returns:
        Suggested field name if found within threshold, otherwise None

    Note:
        Uses threshold of 2 edits (inserts/deletes/substitutions)
    """
    # Valid fields for WebSocketExecuteRequest and ExecuteRequest
    valid_fields = {
        "user_prompt",
        "function",
        "params",
        "model",
        "provider",
        "streaming",
        "system_prompt",
        "page_context",
    }

    min_distance = float("inf")
    suggestion = None

    for valid_field in valid_fields:
        distance = _levenshtein_distance(invalid_field.lower(), valid_field.lower())
        if distance < min_distance and distance <= 2:  # Threshold: 2 edits
            min_distance = distance
            suggestion = valid_field

    return suggestion


def _levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.

    Uses dynamic programming approach (Wagner-Fischer algorithm).

    Args:
        s1: First string
        s2: Second string

    Returns:
        Minimum number of single-character edits (insertions, deletions, substitutions)
        required to change s1 into s2

    Time Complexity: O(len(s1) * len(s2))
    Space Complexity: O(len(s1) * len(s2))
    """
    len1, len2 = len(s1), len(s2)

    # Create DP table
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    # Initialize base cases
    for i in range(len1 + 1):
        dp[i][0] = i  # Deletions
    for j in range(len2 + 1):
        dp[0][j] = j  # Insertions

    # Fill DP table
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]  # No operation needed
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],  # Deletion
                    dp[i][j - 1],  # Insertion
                    dp[i - 1][j - 1],  # Substitution
                )

    return dp[len1][len2]
