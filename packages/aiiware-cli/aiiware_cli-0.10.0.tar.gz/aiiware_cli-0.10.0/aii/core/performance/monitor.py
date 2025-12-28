# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Performance monitoring and optimization for AII components"""


import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from threading import Lock
import functools


@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    operation: str
    duration: float
    timestamp: float
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Monitor and track performance metrics across the system"""

    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self._metrics: List[PerformanceMetric] = []
        self._lock = Lock()
        self._operation_stats: Dict[str, Dict[str, Any]] = {}

    def record_metric(self, operation: str, duration: float, success: bool = True, **metadata) -> None:
        """Record a performance metric"""
        with self._lock:
            metric = PerformanceMetric(
                operation=operation,
                duration=duration,
                timestamp=time.time(),
                success=success,
                metadata=metadata
            )

            self._metrics.append(metric)

            # Keep only recent metrics
            if len(self._metrics) > self.max_metrics:
                self._metrics = self._metrics[-self.max_metrics:]

            # Update operation statistics
            self._update_operation_stats(operation, duration, success)

    def _update_operation_stats(self, operation: str, duration: float, success: bool) -> None:
        """Update aggregated statistics for an operation"""
        if operation not in self._operation_stats:
            self._operation_stats[operation] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'failures': 0,
                'avg_time': 0.0
            }

        stats = self._operation_stats[operation]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        stats['avg_time'] = stats['total_time'] / stats['count']

        if not success:
            stats['failures'] += 1

    def get_operation_stats(self, operation: str = None) -> Dict[str, Any]:
        """Get performance statistics for operations"""
        with self._lock:
            if operation:
                return self._operation_stats.get(operation, {})
            return self._operation_stats.copy()

    def get_recent_metrics(self, operation: str = None, limit: int = 100) -> List[PerformanceMetric]:
        """Get recent performance metrics"""
        with self._lock:
            metrics = self._metrics[-limit:] if not operation else [
                m for m in self._metrics[-limit:] if m.operation == operation
            ]
            return metrics.copy()

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            total_operations = len(self._metrics)
            if total_operations == 0:
                return {'total_operations': 0}

            # Calculate overall statistics
            total_time = sum(m.duration for m in self._metrics)
            failures = sum(1 for m in self._metrics if not m.success)
            avg_duration = total_time / total_operations

            # Find slow operations
            slow_operations = [
                (op, stats['avg_time']) for op, stats in self._operation_stats.items()
                if stats['avg_time'] > 0.1  # More than 100ms average
            ]
            slow_operations.sort(key=lambda x: x[1], reverse=True)

            return {
                'total_operations': total_operations,
                'total_time': total_time,
                'avg_duration': avg_duration,
                'failure_rate': failures / total_operations,
                'slow_operations': slow_operations[:5],
                'operation_count': len(self._operation_stats)
            }

    def clear_metrics(self) -> None:
        """Clear all performance metrics"""
        with self._lock:
            self._metrics.clear()
            self._operation_stats.clear()


# Global performance monitor
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    return _performance_monitor


def performance_timed(operation_name: str = None):
    """Decorator to automatically time function execution"""
    def decorator(func):
        op_name = operation_name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                _performance_monitor.record_metric(op_name, duration, True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                _performance_monitor.record_metric(op_name, duration, False, error=str(e))
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                _performance_monitor.record_metric(op_name, duration, True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                _performance_monitor.record_metric(op_name, duration, False, error=str(e))
                raise

        # Return appropriate wrapper based on function type
        if hasattr(func, '__call__'):
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
        return sync_wrapper

    return decorator


class PerformanceOptimizer:
    """Automatic performance optimizations based on monitoring data"""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self._optimization_cache: Dict[str, Any] = {}

    def should_skip_expensive_operation(self, operation: str, threshold_ms: float = 100.0) -> bool:
        """Determine if an expensive operation should be skipped based on recent performance"""
        stats = self.monitor.get_operation_stats(operation)
        if not stats:
            return False

        # Skip if operation is consistently slow and has high failure rate
        avg_time_ms = stats.get('avg_time', 0) * 1000
        failure_rate = stats.get('failures', 0) / max(stats.get('count', 1), 1)

        return avg_time_ms > threshold_ms and failure_rate > 0.1

    def get_operation_priority(self, operation: str) -> int:
        """Get priority for operation based on performance characteristics"""
        stats = self.monitor.get_operation_stats(operation)
        if not stats:
            return 5  # Medium priority

        avg_time = stats.get('avg_time', 0)
        failure_rate = stats.get('failures', 0) / max(stats.get('count', 1), 1)

        # High priority for fast, reliable operations
        if avg_time < 0.05 and failure_rate < 0.01:
            return 9
        elif avg_time < 0.1 and failure_rate < 0.05:
            return 7
        elif avg_time > 1.0 or failure_rate > 0.2:
            return 2
        else:
            return 5

    def optimize_cache_settings(self) -> Dict[str, Any]:
        """Suggest cache settings based on performance data"""
        summary = self.monitor.get_performance_summary()

        # Increase cache size for high-volume operations
        total_ops = summary.get('total_operations', 0)
        if total_ops > 1000:
            token_cache_size = min(2000, total_ops // 10)
            prompt_cache_size = min(500, total_ops // 20)
        else:
            token_cache_size = 1000
            prompt_cache_size = 200

        # Adjust TTL based on operation frequency
        avg_duration = summary.get('avg_duration', 0)
        if avg_duration > 0.5:  # Slow operations - cache longer
            cache_ttl = 3600  # 1 hour
        else:
            cache_ttl = 1800  # 30 minutes

        return {
            'token_cache_size': token_cache_size,
            'prompt_cache_size': prompt_cache_size,
            'cache_ttl': cache_ttl
        }
