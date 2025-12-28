# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
AII Beta - LLM-powered CLI Assistant (v4 Architecture)

A comprehensive intelligent CLI assistant that recognizes user intent and executes
appropriate functions through a plugin-based architecture with chat history management.
"""

# Dynamic versioning - reads from pyproject.toml
try:
    from importlib.metadata import version
    __version__ = version("aiiware-cli")
except Exception:
    # Fallback for development/edge cases
    __version__ = "0.7.0"

__author__ = "AII Development Team"

from .core.context.manager import ContextManager
from .core.engine import AIIEngine
from .core.execution.executor import ExecutionEngine
from .core.intent.recognizer import IntentRecognizer
from .core.registry.function_registry import FunctionRegistry

__all__ = [
    "AIIEngine",
    "IntentRecognizer",
    "FunctionRegistry",
    "ContextManager",
    "ExecutionEngine",
]
