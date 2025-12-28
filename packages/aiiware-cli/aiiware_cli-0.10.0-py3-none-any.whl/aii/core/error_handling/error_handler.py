# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Central error handling and recovery system"""


import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Union
from threading import Lock

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"          # Minor issues, can continue normally
    MEDIUM = "medium"    # Moderate issues, may need user notification
    HIGH = "high"        # Serious issues, require immediate attention
    CRITICAL = "critical" # System-breaking issues, need emergency handling


class ErrorCategory(Enum):
    """Error category classification"""
    NETWORK = "network"              # Network connectivity issues
    LLM_PROVIDER = "llm_provider"    # LLM service failures
    SESSION = "session"              # Session management errors
    STORAGE = "storage"              # File/database storage issues
    PERFORMANCE = "performance"      # Performance degradation
    VALIDATION = "validation"        # Data validation failures
    TIMEOUT = "timeout"              # Operation timeouts
    PERMISSION = "permission"        # Access/permission issues
    MEMORY = "memory"                # Memory-related issues
    UNKNOWN = "unknown"              # Unclassified errors


class ErrorRecoveryStrategy(Enum):
    """Available recovery strategies"""
    RETRY = "retry"                  # Retry the operation
    FALLBACK = "fallback"            # Use alternative approach
    GRACEFUL_DEGRADATION = "graceful_degradation"  # Reduced functionality
    USER_INTERVENTION = "user_intervention"        # Require user action
    ABORT = "abort"                  # Stop operation completely
    IGNORE = "ignore"                # Continue despite error


@dataclass
class RecoveryResult:
    """Result of error recovery attempt"""
    success: bool
    strategy_used: ErrorRecoveryStrategy
    recovery_time: float
    message: str
    data: Optional[Dict[str, Any]] = None
    should_retry: bool = False
    retry_delay: float = 0.0


@dataclass
class ErrorContext:
    """Context information for error handling"""
    error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    operation: str
    timestamp: float
    recovery_attempts: int = 0
    max_retries: int = 3
    context_data: Dict[str, Any] = field(default_factory=dict)
    user_facing_message: Optional[str] = None


class ErrorHandler:
    """Central error handling and recovery coordinator"""

    def __init__(self):
        self._lock = Lock()
        self._error_history: List[ErrorContext] = []
        self._recovery_strategies: Dict[ErrorCategory, List[ErrorRecoveryStrategy]] = {}
        self._error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self._setup_default_strategies()

    def _setup_default_strategies(self):
        """Set up default recovery strategies for each error category"""
        self._recovery_strategies = {
            ErrorCategory.NETWORK: [
                ErrorRecoveryStrategy.RETRY,
                ErrorRecoveryStrategy.FALLBACK,
                ErrorRecoveryStrategy.USER_INTERVENTION
            ],
            ErrorCategory.LLM_PROVIDER: [
                ErrorRecoveryStrategy.RETRY,
                ErrorRecoveryStrategy.FALLBACK,
                ErrorRecoveryStrategy.GRACEFUL_DEGRADATION
            ],
            ErrorCategory.SESSION: [
                ErrorRecoveryStrategy.RETRY,
                ErrorRecoveryStrategy.GRACEFUL_DEGRADATION,
                ErrorRecoveryStrategy.USER_INTERVENTION
            ],
            ErrorCategory.STORAGE: [
                ErrorRecoveryStrategy.RETRY,
                ErrorRecoveryStrategy.FALLBACK,
                ErrorRecoveryStrategy.USER_INTERVENTION
            ],
            ErrorCategory.PERFORMANCE: [
                ErrorRecoveryStrategy.GRACEFUL_DEGRADATION,
                ErrorRecoveryStrategy.FALLBACK
            ],
            ErrorCategory.VALIDATION: [
                ErrorRecoveryStrategy.USER_INTERVENTION,
                ErrorRecoveryStrategy.GRACEFUL_DEGRADATION
            ],
            ErrorCategory.TIMEOUT: [
                ErrorRecoveryStrategy.RETRY,
                ErrorRecoveryStrategy.GRACEFUL_DEGRADATION
            ],
            ErrorCategory.PERMISSION: [
                ErrorRecoveryStrategy.USER_INTERVENTION,
                ErrorRecoveryStrategy.FALLBACK
            ],
            ErrorCategory.MEMORY: [
                ErrorRecoveryStrategy.GRACEFUL_DEGRADATION,
                ErrorRecoveryStrategy.RETRY
            ],
            ErrorCategory.UNKNOWN: [
                ErrorRecoveryStrategy.RETRY,
                ErrorRecoveryStrategy.ABORT
            ]
        }

    def classify_error(self, error: Exception, operation: str = "") -> ErrorContext:
        """Classify an error and determine appropriate handling"""
        category = self._determine_category(error)
        severity = self._determine_severity(error, category)
        user_message = self._generate_user_message(error, category, operation)

        return ErrorContext(
            error=error,
            severity=severity,
            category=category,
            operation=operation,
            timestamp=time.time(),
            user_facing_message=user_message
        )

    def _determine_category(self, error: Exception) -> ErrorCategory:
        """Determine error category based on exception type and message"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network-related errors
        if any(term in error_str or term in error_type for term in [
            'connection', 'network', 'timeout', 'unreachable', 'dns',
            'connectionerror', 'httperror', 'sslerror'
        ]):
            return ErrorCategory.NETWORK

        # LLM provider specific errors
        if any(term in error_str or term in error_type for term in [
            'anthropic', 'openai', 'api_key', 'rate_limit', 'quota',
            'model_not_found', 'invalid_request', 'authentication'
        ]):
            return ErrorCategory.LLM_PROVIDER

        # Session management errors
        if any(term in error_str or term in error_type for term in [
            'session', 'state', 'corruption', 'invalid_session'
        ]):
            return ErrorCategory.SESSION

        # Storage errors
        if any(term in error_str or term in error_type for term in [
            'file', 'disk', 'storage', 'database', 'sqlite', 'permission denied',
            'no space', 'read-only', 'ioerror', 'oserror'
        ]):
            return ErrorCategory.STORAGE

        # Memory errors
        if any(term in error_str or term in error_type for term in [
            'memory', 'out of memory', 'memoryerror'
        ]):
            return ErrorCategory.MEMORY

        # Timeout errors
        if any(term in error_str or term in error_type for term in [
            'timeout', 'asyncio.timeouterror', 'timed out'
        ]):
            return ErrorCategory.TIMEOUT

        # Validation errors
        if any(term in error_str or term in error_type for term in [
            'validation', 'invalid', 'valueerror', 'typeerror', 'schema'
        ]):
            return ErrorCategory.VALIDATION

        # Permission errors
        if any(term in error_str or term in error_type for term in [
            'permission', 'access denied', 'forbidden', 'unauthorized'
        ]):
            return ErrorCategory.PERMISSION

        return ErrorCategory.UNKNOWN

    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on type and category"""
        error_str = str(error).lower()

        # Critical severity indicators
        if any(term in error_str for term in [
            'critical', 'fatal', 'corruption', 'out of memory',
            'disk full', 'system error'
        ]):
            return ErrorSeverity.CRITICAL

        # High severity indicators
        if any(term in error_str for term in [
            'authentication failed', 'permission denied', 'quota exceeded',
            'service unavailable', 'database error'
        ]):
            return ErrorSeverity.HIGH

        # Medium severity for certain categories
        if category in [ErrorCategory.LLM_PROVIDER, ErrorCategory.NETWORK, ErrorCategory.SESSION]:
            return ErrorSeverity.MEDIUM

        return ErrorSeverity.LOW

    def _generate_user_message(self, error: Exception, category: ErrorCategory, operation: str) -> str:
        """Generate user-friendly error message"""
        base_messages = {
            ErrorCategory.NETWORK: "Network connectivity issue detected",
            ErrorCategory.LLM_PROVIDER: "AI service temporarily unavailable",
            ErrorCategory.SESSION: "Session management issue encountered",
            ErrorCategory.STORAGE: "File system or storage issue detected",
            ErrorCategory.PERFORMANCE: "Performance degradation detected",
            ErrorCategory.VALIDATION: "Data validation issue encountered",
            ErrorCategory.TIMEOUT: "Operation timed out",
            ErrorCategory.PERMISSION: "Permission or access issue detected",
            ErrorCategory.MEMORY: "Memory usage issue detected",
            ErrorCategory.UNKNOWN: "Unexpected issue encountered"
        }

        base = base_messages.get(category, "Issue encountered")
        if operation:
            return f"{base} during {operation}"
        return base

    async def handle_error(self, error: Exception, operation: str = "",
                          context_data: Optional[Dict[str, Any]] = None) -> RecoveryResult:
        """Handle an error with appropriate recovery strategy"""
        error_context = self.classify_error(error, operation)
        if context_data:
            error_context.context_data.update(context_data)

        # Record error
        with self._lock:
            self._error_history.append(error_context)
            if len(self._error_history) > 1000:  # Keep only recent errors
                self._error_history = self._error_history[-1000:]

        logger.error(f"Error in {operation}: {error}", exc_info=True)

        # Try recovery strategies
        strategies = self._recovery_strategies.get(error_context.category, [ErrorRecoveryStrategy.ABORT])

        for strategy in strategies:
            try:
                recovery_start = time.time()
                result = await self._attempt_recovery(error_context, strategy)
                recovery_time = time.time() - recovery_start

                if result.success:
                    logger.info(f"Recovered from error using {strategy.value} in {recovery_time:.2f}s")
                    return result

            except Exception as recovery_error:
                logger.error(f"Recovery strategy {strategy.value} failed: {recovery_error}")
                continue

        # All recovery strategies failed
        return RecoveryResult(
            success=False,
            strategy_used=ErrorRecoveryStrategy.ABORT,
            recovery_time=0.0,
            message=f"Unable to recover from {error_context.category.value} error: {error}",
            data={"original_error": str(error), "category": error_context.category.value}
        )

    async def _attempt_recovery(self, error_context: ErrorContext,
                               strategy: ErrorRecoveryStrategy) -> RecoveryResult:
        """Attempt recovery using specific strategy"""
        if strategy == ErrorRecoveryStrategy.RETRY:
            return await self._retry_recovery(error_context)
        elif strategy == ErrorRecoveryStrategy.FALLBACK:
            return await self._fallback_recovery(error_context)
        elif strategy == ErrorRecoveryStrategy.GRACEFUL_DEGRADATION:
            return await self._graceful_degradation_recovery(error_context)
        elif strategy == ErrorRecoveryStrategy.USER_INTERVENTION:
            return await self._user_intervention_recovery(error_context)
        elif strategy == ErrorRecoveryStrategy.IGNORE:
            return RecoveryResult(
                success=True,
                strategy_used=strategy,
                recovery_time=0.0,
                message="Error ignored as per strategy"
            )
        else:  # ABORT
            return RecoveryResult(
                success=False,
                strategy_used=strategy,
                recovery_time=0.0,
                message="Operation aborted due to unrecoverable error"
            )

    async def _retry_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Implement retry recovery strategy"""
        if error_context.recovery_attempts >= error_context.max_retries:
            return RecoveryResult(
                success=False,
                strategy_used=ErrorRecoveryStrategy.RETRY,
                recovery_time=0.0,
                message="Maximum retry attempts exceeded"
            )

        # Calculate retry delay with exponential backoff
        delay = min(2 ** error_context.recovery_attempts, 30)  # Max 30 seconds

        return RecoveryResult(
            success=False,  # Indicates we should retry
            strategy_used=ErrorRecoveryStrategy.RETRY,
            recovery_time=delay,
            message=f"Retrying in {delay} seconds (attempt {error_context.recovery_attempts + 1})",
            should_retry=True,
            retry_delay=delay
        )

    async def _fallback_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Implement fallback recovery strategy"""
        # This will be customized based on specific error types
        fallback_message = "Using alternative approach"

        if error_context.category == ErrorCategory.LLM_PROVIDER:
            fallback_message = "Using cached responses or local processing"
        elif error_context.category == ErrorCategory.STORAGE:
            fallback_message = "Using temporary storage or memory-only mode"
        elif error_context.category == ErrorCategory.NETWORK:
            fallback_message = "Using offline mode or cached data"

        return RecoveryResult(
            success=True,
            strategy_used=ErrorRecoveryStrategy.FALLBACK,
            recovery_time=0.0,
            message=fallback_message,
            data={"fallback_mode": True}
        )

    async def _graceful_degradation_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Implement graceful degradation recovery strategy"""
        degradation_message = "Continuing with reduced functionality"

        if error_context.category == ErrorCategory.LLM_PROVIDER:
            degradation_message = "Semantic analysis disabled, using basic metrics only"
        elif error_context.category == ErrorCategory.PERFORMANCE:
            degradation_message = "Performance optimizations disabled"
        elif error_context.category == ErrorCategory.MEMORY:
            degradation_message = "Memory usage optimized, some features limited"

        return RecoveryResult(
            success=True,
            strategy_used=ErrorRecoveryStrategy.GRACEFUL_DEGRADATION,
            recovery_time=0.0,
            message=degradation_message,
            data={"degraded_mode": True}
        )

    async def _user_intervention_recovery(self, error_context: ErrorContext) -> RecoveryResult:
        """Implement user intervention recovery strategy"""
        intervention_message = "User action required to resolve issue"

        if error_context.category == ErrorCategory.PERMISSION:
            intervention_message = "Please check file permissions and try again"
        elif error_context.category == ErrorCategory.LLM_PROVIDER:
            intervention_message = "Please check API key configuration"
        elif error_context.category == ErrorCategory.STORAGE:
            intervention_message = "Please check disk space and permissions"

        return RecoveryResult(
            success=False,
            strategy_used=ErrorRecoveryStrategy.USER_INTERVENTION,
            recovery_time=0.0,
            message=intervention_message,
            data={"requires_user_action": True}
        )

    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """Register callback for specific error category"""
        with self._lock:
            if category not in self._error_callbacks:
                self._error_callbacks[category] = []
            self._error_callbacks[category].append(callback)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and patterns"""
        with self._lock:
            if not self._error_history:
                return {"total_errors": 0, "categories": {}, "severity_distribution": {}}

            category_counts = {}
            severity_counts = {}
            recent_errors = [e for e in self._error_history if time.time() - e.timestamp < 3600]  # Last hour

            for error in self._error_history:
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1

            return {
                "total_errors": len(self._error_history),
                "recent_errors": len(recent_errors),
                "categories": category_counts,
                "severity_distribution": severity_counts,
                "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
            }

    def clear_error_history(self):
        """Clear error history (useful for testing)"""
        with self._lock:
            self._error_history.clear()


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    return _error_handler
