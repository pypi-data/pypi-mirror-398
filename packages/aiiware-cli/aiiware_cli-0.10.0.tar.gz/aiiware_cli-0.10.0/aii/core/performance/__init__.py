# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Performance optimization module for AII"""

from .cache_manager import (
    TokenEstimationCache,
    PromptCache,
    get_token_cache,
    get_prompt_cache,
    clear_all_caches,
    get_cache_stats
)
from .monitor import (
    PerformanceMonitor,
    PerformanceOptimizer,
    get_performance_monitor,
    performance_timed
)
from .memory_manager import (
    MemoryManager,
    MemoryStats,
    get_memory_manager,
    auto_cleanup_if_needed,
    get_memory_stats
)

__all__ = [
    'TokenEstimationCache',
    'PromptCache',
    'get_token_cache',
    'get_prompt_cache',
    'clear_all_caches',
    'get_cache_stats',
    'PerformanceMonitor',
    'PerformanceOptimizer',
    'get_performance_monitor',
    'performance_timed',
    'MemoryManager',
    'MemoryStats',
    'get_memory_manager',
    'auto_cleanup_if_needed',
    'get_memory_stats'
]
