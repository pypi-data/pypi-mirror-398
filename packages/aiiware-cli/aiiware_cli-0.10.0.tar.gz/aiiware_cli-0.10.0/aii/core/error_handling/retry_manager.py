# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Retry management with exponential backoff and intelligent strategies"""


import asyncio
import functools
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Union, Type, Tuple
from threading import Lock

logger = logging.getLogger(__name__)


class RetryStrategy(ABC):
    """Abstract base class for retry strategies"""

    @abstractmethod
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-based)"""
        pass

    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if we should retry for this attempt and error"""
        pass


class ExponentialBackoff(RetryStrategy):
    """Exponential backoff retry strategy with jitter"""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0,
                 exponential_base: float = 2.0, jitter: bool = True,
                 max_attempts: int = 3):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.max_attempts = max_attempts

    def calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with optional jitter"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add jitter to prevent thundering herd
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Check if we should retry based on attempt count and error type"""
        if attempt >= self.max_attempts:
            return False

        # Don't retry certain types of errors
        non_retryable_errors = (
            ValueError,  # Invalid input
            TypeError,   # Programming errors
            KeyError,    # Configuration errors
        )

        return not isinstance(error, non_retryable_errors)


class FixedDelay(RetryStrategy):
    """Fixed delay retry strategy"""

    def __init__(self, delay: float = 1.0, max_attempts: int = 3):
        self.delay = delay
        self.max_attempts = max_attempts

    def calculate_delay(self, attempt: int) -> float:
        """Return fixed delay"""
        return self.delay

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Check if we should retry based on attempt count"""
        return attempt < self.max_attempts


class LinearBackoff(RetryStrategy):
    """Linear backoff retry strategy"""

    def __init__(self, base_delay: float = 1.0, increment: float = 1.0,
                 max_delay: float = 30.0, max_attempts: int = 5):
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay
        self.max_attempts = max_attempts

    def calculate_delay(self, attempt: int) -> float:
        """Calculate linear backoff delay"""
        delay = self.base_delay + (self.increment * attempt)
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Check if we should retry"""
        return attempt < self.max_attempts


@dataclass
class RetryResult:
    """Result of retry operation"""
    success: bool
    attempts: int
    total_time: float
    last_error: Optional[Exception] = None
    result: Any = None


class RetryManager:
    """Manages retry operations with various strategies"""

    def __init__(self):
        self._lock = Lock()
        self._retry_stats = {}

    async def retry_async(self, func: Callable, strategy: RetryStrategy,
                         *args, **kwargs) -> RetryResult:
        """Retry an async function with given strategy"""
        start_time = time.time()
        attempt = 0
        last_error = None

        while True:
            try:
                result = await func(*args, **kwargs)
                total_time = time.time() - start_time

                # Record successful retry stats
                self._record_retry_stats(func.__name__, attempt, True, total_time)

                return RetryResult(
                    success=True,
                    attempts=attempt + 1,
                    total_time=total_time,
                    result=result
                )

            except Exception as error:
                last_error = error

                if not strategy.should_retry(attempt, error):
                    total_time = time.time() - start_time

                    # Record failed retry stats
                    self._record_retry_stats(func.__name__, attempt, False, total_time)

                    return RetryResult(
                        success=False,
                        attempts=attempt + 1,
                        total_time=total_time,
                        last_error=error
                    )

                delay = strategy.calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {error}. "
                              f"Retrying in {delay:.2f}s")

                await asyncio.sleep(delay)
                attempt += 1

    def retry_sync(self, func: Callable, strategy: RetryStrategy,
                   *args, **kwargs) -> RetryResult:
        """Retry a synchronous function with given strategy"""
        start_time = time.time()
        attempt = 0
        last_error = None

        while True:
            try:
                result = func(*args, **kwargs)
                total_time = time.time() - start_time

                # Record successful retry stats
                self._record_retry_stats(func.__name__, attempt, True, total_time)

                return RetryResult(
                    success=True,
                    attempts=attempt + 1,
                    total_time=total_time,
                    result=result
                )

            except Exception as error:
                last_error = error

                if not strategy.should_retry(attempt, error):
                    total_time = time.time() - start_time

                    # Record failed retry stats
                    self._record_retry_stats(func.__name__, attempt, False, total_time)

                    return RetryResult(
                        success=False,
                        attempts=attempt + 1,
                        total_time=total_time,
                        last_error=error
                    )

                delay = strategy.calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {error}. "
                              f"Retrying in {delay:.2f}s")

                time.sleep(delay)
                attempt += 1

    def _record_retry_stats(self, func_name: str, attempts: int, success: bool, total_time: float):
        """Record retry statistics"""
        with self._lock:
            if func_name not in self._retry_stats:
                self._retry_stats[func_name] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'total_attempts': 0,
                    'total_time': 0.0,
                    'max_attempts': 0
                }

            stats = self._retry_stats[func_name]
            stats['total_calls'] += 1
            stats['total_attempts'] += attempts + 1
            stats['total_time'] += total_time
            stats['max_attempts'] = max(stats['max_attempts'], attempts + 1)

            if success:
                stats['successful_calls'] += 1

    def get_retry_stats(self, func_name: Optional[str] = None) -> dict:
        """Get retry statistics"""
        with self._lock:
            if func_name:
                return self._retry_stats.get(func_name, {})
            return self._retry_stats.copy()

    def clear_stats(self):
        """Clear retry statistics"""
        with self._lock:
            self._retry_stats.clear()


def with_retry(strategy: Optional[RetryStrategy] = None):
    """Decorator for automatic retry with specified strategy"""
    if strategy is None:
        strategy = ExponentialBackoff()

    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                retry_manager = get_retry_manager()
                result = await retry_manager.retry_async(func, strategy, *args, **kwargs)

                if not result.success:
                    raise result.last_error

                return result.result

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                retry_manager = get_retry_manager()
                result = retry_manager.retry_sync(func, strategy, *args, **kwargs)

                if not result.success:
                    raise result.last_error

                return result.result

            return sync_wrapper

    return decorator


# Predefined retry strategies for common use cases
NETWORK_RETRY = ExponentialBackoff(base_delay=1.0, max_delay=30.0, max_attempts=3)
LLM_PROVIDER_RETRY = ExponentialBackoff(base_delay=2.0, max_delay=60.0, max_attempts=3)
STORAGE_RETRY = LinearBackoff(base_delay=0.5, increment=0.5, max_attempts=3)
QUICK_RETRY = FixedDelay(delay=0.1, max_attempts=2)


# Global retry manager instance
_retry_manager = RetryManager()


def get_retry_manager() -> RetryManager:
    """Get global retry manager instance"""
    return _retry_manager
