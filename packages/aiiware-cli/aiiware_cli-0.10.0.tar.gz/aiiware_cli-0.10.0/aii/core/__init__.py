# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Core Engine Layer - Intent recognition, function registry, context management, execution"""

from .engine import AIIEngine
from .models import (
    ExecutionContext,
    ExecutionResult,
    FunctionDefinition,
    RecognitionResult,
    ValidationResult,
)

__all__ = [
    "AIIEngine",
    "RecognitionResult",
    "ExecutionResult",
    "ExecutionContext",
    "FunctionDefinition",
    "ValidationResult",
]
