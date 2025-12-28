# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Performance Cache Manager - Caching for repeated operations"""


import hashlib
import time
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass
from threading import Lock

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with expiration and metadata"""
    value: T
    timestamp: float
    hit_count: int = 0
    last_access: float = 0.0

    def is_expired(self, ttl_seconds: float) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.timestamp > ttl_seconds

    def access(self) -> T:
        """Mark entry as accessed and return value"""
        self.hit_count += 1
        self.last_access = time.time()
        return self.value


class LRUCache(Generic[T]):
    """Thread-safe LRU cache with TTL support"""

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 300.0):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._access_order: Dict[str, float] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[T]:
        """Get value from cache"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired(self.ttl_seconds):
                self._remove(key)
                return None

            # Update access order
            self._access_order[key] = time.time()
            return entry.access()

    def put(self, key: str, value: T) -> None:
        """Put value into cache"""
        with self._lock:
            # Remove expired entries periodically
            if len(self._cache) % 100 == 0:
                self._cleanup_expired()

            # Remove LRU entries if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            # Add new entry
            entry = CacheEntry(value=value, timestamp=time.time())
            self._cache[key] = entry
            self._access_order[key] = time.time()

    def _remove(self, key: str) -> None:
        """Remove entry from cache"""
        self._cache.pop(key, None)
        self._access_order.pop(key, None)

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self._access_order:
            return

        lru_key = min(self._access_order, key=self._access_order.get)
        self._remove(lru_key)

    def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired(self.ttl_seconds)
        ]
        for key in expired_keys:
            self._remove(key)

    def clear(self) -> None:
        """Clear all entries"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_hits = sum(entry.hit_count for entry in self._cache.values())
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'total_hits': total_hits,
                'ttl_seconds': self.ttl_seconds
            }


class TokenEstimationCache:
    """Cache for token estimation to avoid repeated calculations"""

    def __init__(self, max_size: int = 500, ttl_seconds: float = 3600.0):
        self._cache = LRUCache[int](max_size, ttl_seconds)

    def get_token_estimate(self, text: str) -> Optional[int]:
        """Get cached token estimate for text"""
        cache_key = self._make_cache_key(text)
        return self._cache.get(cache_key)

    def put_token_estimate(self, text: str, token_count: int) -> None:
        """Cache token estimate for text"""
        cache_key = self._make_cache_key(text)
        self._cache.put(cache_key, token_count)

    def estimate_tokens_with_cache(self, text: str) -> int:
        """Get token estimate with caching fallback"""
        # Try cache first
        cached_estimate = self.get_token_estimate(text)
        if cached_estimate is not None:
            return cached_estimate

        # Calculate estimate using simple heuristic
        estimate = self._calculate_token_estimate(text)

        # Cache the result
        self.put_token_estimate(text, estimate)

        return estimate

    def _make_cache_key(self, text: str) -> str:
        """Create cache key for text"""
        # Use hash for consistent, memory-efficient keys
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _calculate_token_estimate(self, text: str) -> int:
        """Calculate token estimate using improved heuristics"""
        if not text:
            return 0

        # Improved token estimation
        # Account for different types of content
        words = text.split()
        word_count = len(words)

        # Base estimation: ~1.3 tokens per word for English
        base_estimate = word_count * 1.3

        # Adjust for special content
        char_count = len(text)

        # Code content (higher token density)
        if any(keyword in text.lower() for keyword in ['def ', 'class ', 'import ', 'function']):
            base_estimate *= 1.2

        # JSON content (structured data)
        elif text.strip().startswith(('{', '[')):
            base_estimate *= 1.1

        # Very short text (higher relative overhead)
        elif word_count < 10:
            base_estimate += 5

        # Very long text (slight efficiency gain)
        elif word_count > 1000:
            base_estimate *= 0.95

        return max(1, int(base_estimate))

    def clear(self) -> None:
        """Clear token estimation cache"""
        self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Get token estimation cache statistics"""
        return self._cache.stats()


class PromptCache:
    """Cache for LLM prompts and responses"""

    def __init__(self, max_size: int = 200, ttl_seconds: float = 1800.0):
        self._cache = LRUCache[Dict[str, Any]](max_size, ttl_seconds)

    def get_prompt_response(self, prompt: str, model: str) -> Optional[Dict[str, Any]]:
        """Get cached response for prompt+model combination"""
        cache_key = self._make_prompt_key(prompt, model)
        return self._cache.get(cache_key)

    def put_prompt_response(self, prompt: str, model: str, response: Dict[str, Any]) -> None:
        """Cache response for prompt+model combination"""
        cache_key = self._make_prompt_key(prompt, model)
        self._cache.put(cache_key, response)

    def _make_prompt_key(self, prompt: str, model: str) -> str:
        """Create cache key for prompt+model"""
        combined = f"{model}:{prompt}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()

    def clear(self) -> None:
        """Clear prompt cache"""
        self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Get prompt cache statistics"""
        return self._cache.stats()


# Global cache instances
_token_cache = TokenEstimationCache()
_prompt_cache = PromptCache()


def get_token_cache() -> TokenEstimationCache:
    """Get global token estimation cache"""
    return _token_cache


def get_prompt_cache() -> PromptCache:
    """Get global prompt cache"""
    return _prompt_cache


def clear_all_caches() -> None:
    """Clear all performance caches"""
    _token_cache.clear()
    _prompt_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        'token_cache': _token_cache.stats(),
        'prompt_cache': _prompt_cache.stats()
    }
