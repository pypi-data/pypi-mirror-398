# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Fallback management for graceful service degradation"""


import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from threading import Lock

logger = logging.getLogger(__name__)


class FallbackStrategy(ABC):
    """Abstract base class for fallback strategies"""

    @abstractmethod
    async def execute_fallback(self, original_error: Exception, context: Dict[str, Any]) -> Any:
        """Execute fallback logic"""
        pass

    @abstractmethod
    def is_applicable(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Check if this fallback is applicable for the given error"""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Priority of this fallback (lower numbers = higher priority)"""
        pass


class CachedResponseFallback(FallbackStrategy):
    """Fallback to cached responses when LLM provider is unavailable"""

    def __init__(self, cache_manager=None):
        self.cache_manager = cache_manager
        self._priority = 1

    async def execute_fallback(self, original_error: Exception, context: Dict[str, Any]) -> Any:
        """Try to use cached response"""
        if not self.cache_manager:
            from ..performance import get_prompt_cache
            self.cache_manager = get_prompt_cache()

        prompt = context.get('prompt', '')
        model = context.get('model', 'default')

        cached_response = self.cache_manager.get_prompt_response(prompt, model)
        if cached_response:
            logger.info("Using cached response due to LLM provider unavailability")
            return {
                'content': cached_response['content'],
                'usage': cached_response['usage'],
                'cached': True,
                'fallback_reason': 'llm_provider_unavailable'
            }

        raise ValueError("No cached response available for fallback")

    def is_applicable(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Check if this fallback applies to LLM provider errors"""
        error_str = str(error).lower()
        return any(term in error_str for term in [
            'api', 'connection', 'timeout', 'rate_limit', 'quota',
            'authentication', 'service unavailable', 'network'
        ])

    @property
    def priority(self) -> int:
        return self._priority


class LocalProcessingFallback(FallbackStrategy):
    """Fallback to local processing when remote services fail"""

    def __init__(self):
        self._priority = 2

    async def execute_fallback(self, original_error: Exception, context: Dict[str, Any]) -> Any:
        """Use local processing instead of remote services"""
        operation = context.get('operation', 'unknown')

        if operation == 'semantic_analysis':
            return await self._local_semantic_analysis(context)
        elif operation == 'token_estimation':
            return await self._local_token_estimation(context)
        else:
            raise ValueError(f"Local processing not available for operation: {operation}")

    async def _local_semantic_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic local semantic analysis"""
        session = context.get('session')
        if not session:
            raise ValueError("Session required for local semantic analysis")

        # Basic analysis without LLM
        total_functions = getattr(session, 'total_functions', 0)
        success_rate = getattr(session, 'success_rate', 0.0)
        total_cost = getattr(session, 'total_cost', 0.0)

        # Generate simple summary based on metrics
        if success_rate >= 0.9:
            summary = f"Successful session with {total_functions} function(s) executed"
        elif success_rate >= 0.7:
            summary = f"Mostly successful session with {total_functions} function(s), some issues encountered"
        else:
            summary = f"Challenging session with {total_functions} function(s), multiple issues encountered"

        return {
            'session_summary': summary,
            'analysis_confidence': 0.6,  # Lower confidence for local analysis
            'insights': {
                'performance_rating': 'good' if success_rate >= 0.8 else 'needs_improvement',
                'cost_efficiency': 'efficient' if total_cost < 0.10 else 'moderate',
                'session_complexity': 'high' if total_functions > 10 else 'moderate'
            },
            'fallback_mode': 'local_analysis',
            'usage': {'input_tokens': 0, 'output_tokens': 0}
        }

    async def _local_token_estimation(self, context: Dict[str, Any]) -> int:
        """Provide basic local token estimation"""
        text = context.get('text', '')
        if not text:
            return 0

        # Simple token estimation: roughly 4 characters per token
        return max(1, len(text) // 4)

    def is_applicable(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Check if local processing fallback is applicable"""
        operation = context.get('operation', '')
        return operation in ['semantic_analysis', 'token_estimation']

    @property
    def priority(self) -> int:
        return self._priority


class MinimalModeFallback(FallbackStrategy):
    """Fallback to minimal functionality mode"""

    def __init__(self):
        self._priority = 3

    async def execute_fallback(self, original_error: Exception, context: Dict[str, Any]) -> Any:
        """Provide minimal functionality"""
        operation = context.get('operation', 'unknown')

        return {
            'minimal_mode': True,
            'operation': operation,
            'message': f"Operating in minimal mode due to {type(original_error).__name__}",
            'functionality': 'limited',
            'timestamp': time.time()
        }

    def is_applicable(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Always applicable as last resort"""
        return True

    @property
    def priority(self) -> int:
        return self._priority


@dataclass
class FallbackResult:
    """Result of fallback execution"""
    success: bool
    strategy_used: str
    result: Any
    fallback_time: float
    original_error: Exception
    message: str
    degraded_functionality: bool = False


class FallbackManager:
    """Manages fallback strategies for service degradation"""

    def __init__(self):
        self._lock = Lock()
        self._strategies: List[FallbackStrategy] = []
        self._fallback_history: List[Dict[str, Any]] = []
        self._register_default_strategies()

    def _register_default_strategies(self):
        """Register default fallback strategies"""
        self.register_strategy(CachedResponseFallback())
        self.register_strategy(LocalProcessingFallback())
        self.register_strategy(MinimalModeFallback())

    def register_strategy(self, strategy: FallbackStrategy):
        """Register a new fallback strategy"""
        with self._lock:
            self._strategies.append(strategy)
            # Sort by priority (lower numbers first)
            self._strategies.sort(key=lambda s: s.priority)

    async def execute_fallback(self, error: Exception, context: Dict[str, Any]) -> FallbackResult:
        """Execute appropriate fallback strategy"""
        start_time = time.time()

        with self._lock:
            applicable_strategies = [
                strategy for strategy in self._strategies
                if strategy.is_applicable(error, context)
            ]

        if not applicable_strategies:
            return FallbackResult(
                success=False,
                strategy_used="none",
                result=None,
                fallback_time=time.time() - start_time,
                original_error=error,
                message="No applicable fallback strategies found"
            )

        # Try strategies in priority order
        for strategy in applicable_strategies:
            try:
                result = await strategy.execute_fallback(error, context)
                fallback_time = time.time() - start_time

                # Record successful fallback
                self._record_fallback(strategy.__class__.__name__, True, fallback_time, context)

                return FallbackResult(
                    success=True,
                    strategy_used=strategy.__class__.__name__,
                    result=result,
                    fallback_time=fallback_time,
                    original_error=error,
                    message=f"Successfully used {strategy.__class__.__name__}",
                    degraded_functionality=strategy.priority > 1
                )

            except Exception as fallback_error:
                logger.warning(f"Fallback strategy {strategy.__class__.__name__} failed: {fallback_error}")
                continue

        # All strategies failed
        fallback_time = time.time() - start_time
        self._record_fallback("all_failed", False, fallback_time, context)

        return FallbackResult(
            success=False,
            strategy_used="all_failed",
            result=None,
            fallback_time=fallback_time,
            original_error=error,
            message="All fallback strategies failed"
        )

    def _record_fallback(self, strategy_name: str, success: bool,
                        execution_time: float, context: Dict[str, Any]):
        """Record fallback execution for analytics"""
        with self._lock:
            record = {
                'strategy': strategy_name,
                'success': success,
                'execution_time': execution_time,
                'timestamp': time.time(),
                'operation': context.get('operation', 'unknown')
            }
            self._fallback_history.append(record)

            # Keep only recent history
            if len(self._fallback_history) > 1000:
                self._fallback_history = self._fallback_history[-1000:]

    def get_fallback_statistics(self) -> Dict[str, Any]:
        """Get fallback usage statistics"""
        with self._lock:
            if not self._fallback_history:
                return {"total_fallbacks": 0, "strategies": {}, "success_rate": 0.0}

            strategy_stats = {}
            successful_fallbacks = 0

            for record in self._fallback_history:
                strategy = record['strategy']
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {'count': 0, 'successes': 0, 'avg_time': 0.0}

                strategy_stats[strategy]['count'] += 1
                if record['success']:
                    strategy_stats[strategy]['successes'] += 1
                    successful_fallbacks += 1

            # Calculate average times
            for strategy, stats in strategy_stats.items():
                relevant_records = [r for r in self._fallback_history if r['strategy'] == strategy]
                if relevant_records:
                    stats['avg_time'] = sum(r['execution_time'] for r in relevant_records) / len(relevant_records)

            return {
                "total_fallbacks": len(self._fallback_history),
                "strategies": strategy_stats,
                "success_rate": successful_fallbacks / len(self._fallback_history) if self._fallback_history else 0.0,
                "registered_strategies": len(self._strategies)
            }

    def clear_history(self):
        """Clear fallback history (useful for testing)"""
        with self._lock:
            self._fallback_history.clear()


# Global fallback manager instance
_fallback_manager = FallbackManager()


def get_fallback_manager() -> FallbackManager:
    """Get global fallback manager instance"""
    return _fallback_manager
