# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Memory management and cleanup for long-running sessions"""


import gc
import psutil
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from threading import Lock
import weakref

from ..session.models import SessionMetrics, FunctionExecution


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    process_memory_mb: float
    system_memory_percent: float
    session_count: int
    total_function_executions: int
    cache_entries: int
    timestamp: float


class MemoryManager:
    """Manages memory usage and cleanup for long-running sessions"""

    def __init__(self, memory_threshold_mb: float = 500.0, cleanup_interval_seconds: float = 300.0):
        self.memory_threshold_mb = memory_threshold_mb
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._last_cleanup = time.time()
        self._lock = Lock()
        self._session_refs: List[weakref.ReferenceType] = []
        self._memory_stats: List[MemoryStats] = []

    def register_session(self, session: SessionMetrics) -> None:
        """Register a session for memory tracking"""
        with self._lock:
            self._session_refs.append(weakref.ref(session))

    def check_memory_usage(self) -> MemoryStats:
        """Check current memory usage and return statistics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            process_memory_mb = memory_info.rss / 1024 / 1024

            system_memory = psutil.virtual_memory()
            system_memory_percent = system_memory.percent

            # Count active sessions
            with self._lock:
                # Clean up dead references
                self._session_refs = [ref for ref in self._session_refs if ref() is not None]
                active_sessions = len(self._session_refs)

            # Count total function executions
            total_executions = sum(
                len(ref().function_executions) for ref in self._session_refs
                if ref() is not None
            )

            # Get cache statistics
            from . import get_cache_stats
            cache_stats = get_cache_stats()
            cache_entries = cache_stats.get('token_cache', {}).get('size', 0) + \
                          cache_stats.get('prompt_cache', {}).get('size', 0)

            stats = MemoryStats(
                process_memory_mb=process_memory_mb,
                system_memory_percent=system_memory_percent,
                session_count=active_sessions,
                total_function_executions=total_executions,
                cache_entries=cache_entries,
                timestamp=time.time()
            )

            # Store stats for history
            self._memory_stats.append(stats)
            if len(self._memory_stats) > 100:  # Keep only last 100 entries
                self._memory_stats = self._memory_stats[-100:]

            return stats

        except Exception:
            # Fallback if psutil is not available
            return MemoryStats(
                process_memory_mb=0.0,
                system_memory_percent=0.0,
                session_count=0,
                total_function_executions=0,
                cache_entries=0,
                timestamp=time.time()
            )

    def should_cleanup(self) -> bool:
        """Determine if memory cleanup should be performed"""
        current_time = time.time()
        time_since_cleanup = current_time - self._last_cleanup

        # Cleanup based on time interval
        if time_since_cleanup >= self.cleanup_interval_seconds:
            return True

        # Cleanup based on memory usage
        stats = self.check_memory_usage()
        if stats.process_memory_mb > self.memory_threshold_mb:
            return True

        # Cleanup based on excessive data accumulation
        if stats.total_function_executions > 1000:
            return True

        return False

    def cleanup_memory(self, force: bool = False) -> Dict[str, Any]:
        """Perform memory cleanup and return cleanup statistics"""
        if not force and not self.should_cleanup():
            return {'performed': False, 'reason': 'cleanup not needed'}

        cleanup_stats = {
            'performed': True,
            'timestamp': time.time(),
            'actions': []
        }

        # 1. Clean up dead session references
        with self._lock:
            initial_sessions = len(self._session_refs)
            self._session_refs = [ref for ref in self._session_refs if ref() is not None]
            cleaned_sessions = initial_sessions - len(self._session_refs)
            if cleaned_sessions > 0:
                cleanup_stats['actions'].append(f'Removed {cleaned_sessions} dead session references')

        # 2. Trim old function executions from active sessions
        trimmed_executions = 0
        with self._lock:
            for session_ref in self._session_refs:
                session = session_ref()
                if session and len(session.function_executions) > 50:
                    # Keep only the most recent 50 executions
                    old_count = len(session.function_executions)
                    session.function_executions = session.function_executions[-50:]
                    trimmed_executions += old_count - len(session.function_executions)

        if trimmed_executions > 0:
            cleanup_stats['actions'].append(f'Trimmed {trimmed_executions} old function executions')

        # 3. Clean up caches if they're too large
        from . import get_cache_stats, clear_all_caches
        cache_stats = get_cache_stats()
        total_cache_entries = cache_stats.get('token_cache', {}).get('size', 0) + \
                             cache_stats.get('prompt_cache', {}).get('size', 0)

        if total_cache_entries > 1000:
            clear_all_caches()
            cleanup_stats['actions'].append(f'Cleared {total_cache_entries} cache entries')

        # 4. Force garbage collection
        collected = gc.collect()
        if collected > 0:
            cleanup_stats['actions'].append(f'Garbage collected {collected} objects')

        # 5. Clear old memory statistics
        if len(self._memory_stats) > 50:
            removed_stats = len(self._memory_stats) - 50
            self._memory_stats = self._memory_stats[-50:]
            cleanup_stats['actions'].append(f'Removed {removed_stats} old memory statistics')

        self._last_cleanup = time.time()
        return cleanup_stats

    def get_memory_trend(self) -> Dict[str, Any]:
        """Get memory usage trend over time"""
        if len(self._memory_stats) < 2:
            return {'trend': 'insufficient_data'}

        recent_stats = self._memory_stats[-10:]  # Last 10 measurements
        early_avg = sum(s.process_memory_mb for s in recent_stats[:5]) / 5
        late_avg = sum(s.process_memory_mb for s in recent_stats[-5:]) / 5

        memory_change = late_avg - early_avg
        trend = 'increasing' if memory_change > 10 else 'decreasing' if memory_change < -10 else 'stable'

        return {
            'trend': trend,
            'memory_change_mb': memory_change,
            'current_memory_mb': recent_stats[-1].process_memory_mb,
            'peak_memory_mb': max(s.process_memory_mb for s in self._memory_stats),
            'measurements': len(self._memory_stats)
        }

    def optimize_session_storage(self, session: SessionMetrics) -> None:
        """Optimize storage for a specific session"""
        if not session:
            return

        # Remove redundant artifact entries
        if session.artifacts_created:
            session.artifacts_created = list(set(session.artifacts_created))

        # Compress function execution data for old executions
        if len(session.function_executions) > 20:
            # Keep detailed data for recent executions, summarize older ones
            recent_executions = session.function_executions[-20:]
            older_executions = session.function_executions[:-20]

            # Create summary of older executions
            if older_executions:
                # This could be expanded to create compressed summaries
                pass

            # For now, just keep recent executions
            session.function_executions = recent_executions

    def get_recommendations(self) -> List[str]:
        """Get memory optimization recommendations"""
        recommendations = []
        stats = self.check_memory_usage()

        if stats.process_memory_mb > self.memory_threshold_mb:
            recommendations.append(f"Memory usage ({stats.process_memory_mb:.1f}MB) exceeds threshold. Consider cleanup.")

        if stats.total_function_executions > 500:
            recommendations.append("High number of function executions. Consider session cleanup.")

        if stats.cache_entries > 800:
            recommendations.append("Cache size is large. Consider clearing old entries.")

        trend = self.get_memory_trend()
        if trend['trend'] == 'increasing':
            recommendations.append("Memory usage is trending upward. Monitor for leaks.")

        return recommendations


# Global memory manager instance
_memory_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    """Get global memory manager"""
    return _memory_manager


def auto_cleanup_if_needed() -> Dict[str, Any]:
    """Automatically cleanup if memory usage is too high"""
    return _memory_manager.cleanup_memory(force=False)


def get_memory_stats() -> MemoryStats:
    """Get current memory statistics"""
    return _memory_manager.check_memory_usage()
