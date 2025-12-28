# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Core session models for tracking function executions and cumulative metrics"""


import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FunctionExecution:
    """Record of a single function execution with comprehensive metrics"""
    function_name: str
    start_time: float
    end_time: float
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int  # Track thinking/reasoning phases
    success: bool
    confidence: Optional[float] = None
    artifacts: List[str] = field(default_factory=list)  # Files created, commits, etc.
    # Cost tracking
    cost: float = 0.0  # Total cost for this function execution
    provider: Optional[str] = None  # LLM provider used
    model: Optional[str] = None

    # Performance optimization: cache computed values
    _execution_time: Optional[float] = field(default=None, init=False)
    _total_tokens: Optional[int] = field(default=None, init=False)

    def __post_init__(self):
        """Pre-compute expensive calculations for performance"""
        self._execution_time = self.end_time - self.start_time
        self._total_tokens = self.input_tokens + self.output_tokens + self.reasoning_tokens  # Model used

    @property
    def execution_time(self) -> float:
        """Get cached execution duration in seconds"""
        return self._execution_time if self._execution_time is not None else (self.end_time - self.start_time)

    @property
    def total_tokens(self) -> int:
        """Get cached total tokens consumed by this function"""
        return self._total_tokens if self._total_tokens is not None else (self.input_tokens + self.output_tokens + self.reasoning_tokens)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "function_name": self.function_name,
            "execution_time": self.execution_time,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "total_tokens": self.total_tokens,
            "success": self.success,
            "confidence": self.confidence,
            "artifacts": self.artifacts.copy(),
            "cost": self.cost,
            "provider": self.provider,
            "model": self.model
        }


@dataclass
class SessionMetrics:
    """Global session metrics accumulator with thread-safe operations"""
    session_id: str
    user_input: str
    start_time: float
    end_time: Optional[float] = None

    # Cumulative counters
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_reasoning_tokens: int = 0
    total_functions: int = 0
    successful_functions: int = 0
    # Cost tracking
    total_cost: float = 0.0

    # Execution tracking
    function_executions: List[FunctionExecution] = field(default_factory=list)
    artifacts_created: List[str] = field(default_factory=list)

    # State management
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add_function_execution(self, execution: FunctionExecution) -> None:
        """Thread-safe addition of function execution metrics"""
        with self._lock:
            self.function_executions.append(execution)
            self.total_input_tokens += execution.input_tokens
            self.total_output_tokens += execution.output_tokens
            self.total_reasoning_tokens += execution.reasoning_tokens
            self.total_cost += execution.cost
            self.total_functions += 1

            if execution.success:
                self.successful_functions += 1

            # Accumulate artifacts (commits, files, etc.)
            self.artifacts_created.extend(execution.artifacts)

    def finalize_session(self) -> None:
        """Mark session as complete"""
        with self._lock:
            if self.end_time is None:
                self.end_time = time.time()

    @property
    def session_duration(self) -> float:
        """Calculate session duration in seconds"""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens consumed across all functions"""
        return self.total_input_tokens + self.total_output_tokens + self.total_reasoning_tokens

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage"""
        return self.successful_functions / self.total_functions if self.total_functions > 0 else 0.0

    @property
    def average_function_time(self) -> float:
        """Calculate average execution time per function"""
        if not self.function_executions:
            return 0.0
        total_time = sum(exec.execution_time for exec in self.function_executions)
        return total_time / len(self.function_executions)

    @property
    def is_finalized(self) -> bool:
        """Check if session has been finalized"""
        return self.end_time is not None

    @property
    def average_cost_per_function(self) -> float:
        """Calculate average cost per function"""
        return self.total_cost / self.total_functions if self.total_functions > 0 else 0.0

    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token across the session"""
        return self.total_cost / self.total_tokens if self.total_tokens > 0 else 0.0

    def get_function_breakdown(self) -> List[Dict]:
        """Get detailed breakdown of all function executions"""
        with self._lock:
            return [exec.to_dict() for exec in self.function_executions]

    def to_summary_dict(self) -> Dict:
        """Convert session to summary dictionary for analysis"""
        # Calculate session duration safely
        end = self.end_time if self.end_time else time.time()
        duration = end - self.start_time

        # Calculate average function time safely
        avg_time = 0.0
        if self.function_executions:
            total_time = sum(exec.execution_time for exec in self.function_executions)
            avg_time = total_time / len(self.function_executions)

        return {
            "session_id": self.session_id,
            "user_input": self.user_input,
            "session_duration": duration,
            "total_functions": self.total_functions,
            "successful_functions": self.successful_functions,
            "success_rate": self.successful_functions / self.total_functions if self.total_functions > 0 else 0.0,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_reasoning_tokens": self.total_reasoning_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens + self.total_reasoning_tokens,
            "total_cost": self.total_cost,
            "average_cost_per_function": self.average_cost_per_function,
            "cost_per_token": self.cost_per_token,
            "average_function_time": avg_time,
            "artifacts_created": self.artifacts_created.copy() if self.artifacts_created else [],
            "is_finalized": self.end_time is not None
        }
