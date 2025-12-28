# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Comprehensive error handling and recovery system for AII"""

from .error_handler import (
    ErrorHandler,
    ErrorRecoveryStrategy,
    ErrorSeverity,
    ErrorCategory,
    RecoveryResult,
    get_error_handler
)
from .retry_manager import (
    RetryManager,
    RetryStrategy,
    ExponentialBackoff,
    FixedDelay,
    get_retry_manager,
    with_retry,
    LLM_PROVIDER_RETRY
)
from .fallback_manager import (
    FallbackManager,
    FallbackStrategy,
    get_fallback_manager
)
from .session_recovery import (
    SessionRecoveryManager,
    SessionCorruptionDetector,
    RecoveryAction,
    get_session_recovery_manager
)

__all__ = [
    'ErrorHandler',
    'ErrorRecoveryStrategy',
    'ErrorSeverity',
    'ErrorCategory',
    'RecoveryResult',
    'get_error_handler',
    'RetryManager',
    'RetryStrategy',
    'ExponentialBackoff',
    'FixedDelay',
    'get_retry_manager',
    'with_retry',
    'LLM_PROVIDER_RETRY',
    'FallbackManager',
    'FallbackStrategy',
    'get_fallback_manager',
    'SessionRecoveryManager',
    'SessionCorruptionDetector',
    'RecoveryAction',
    'get_session_recovery_manager'
]
