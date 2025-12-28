"""
Query Result Caching Layer for Turbo ORM

Provides LRU caching for frequently-accessed queries with automatic
invalidation on model updates. Significantly improves performance
for repeated queries.
"""

import time
from typing import Any, Dict, Optional, Tuple, List
from functools import wraps
import threading


class QueryCache:
    """LRU cache for query results with TTL support"""

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        """
        Initialize query cache

        Args:
            max_size: Maximum number of cached entries (default: 1000)
            ttl: Time-to-live in seconds for cached entries (default: 300)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_times: Dict[str, float] = {}
        self.access_count: Dict[str, int] = {}
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()

    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None

            value, timestamp = self.cache[key]
            current_time = time.time()

            # Check if expired
            if current_time - timestamp > self.ttl:
                del self.cache[key]
                del self.access_times[key]
                self.access_count.pop(key, None)
                self.misses += 1
                return None

            # Update access info
            self.hits += 1
            self.access_times[key] = current_time
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return value

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Evict LRU if at capacity
            if len(self.cache) >= self.max_size:
                lru_key = min(self.access_times, key=self.access_times.get)
                del self.cache[lru_key]
                del self.access_times[lru_key]
                self.access_count.pop(lru_key, None)

            self.cache[key] = (value, time.time())
            self.access_times[key] = time.time()
            self.access_count[key] = 1

    def delete(self, key: str) -> None:
        """Delete specific cache entry"""
        with self._lock:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
            self.access_count.pop(key, None)

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all entries matching pattern

        Args:
            pattern: Pattern to match (e.g., "user:*" matches all user keys)

        Returns:
            Number of invalidated entries
        """
        with self._lock:
            keys_to_delete = []
            pattern_prefix = pattern.rstrip("*")

            for key in self.cache:
                if key.startswith(pattern_prefix):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self.cache[key]
                del self.access_times[key]
                self.access_count.pop(key, None)

            return len(keys_to_delete)

    def clear(self) -> None:
        """Clear all cached entries"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()
            self.access_count.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0

            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "size": len(self.cache),
                "max_size": self.max_size,
                "most_accessed": sorted(
                    self.access_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }

    def warm_cache(self, entries: Dict[str, Any]) -> None:
        """
        Pre-populate cache with entries

        Args:
            entries: Dictionary of key-value pairs to cache
        """
        with self._lock:
            for key, value in entries.items():
                self.set(key, value)


class CachedQueryMixin:
    """Mixin to add caching capabilities to models"""

    _query_cache: Optional[QueryCache] = None
    _caching_enabled: bool = True

    @classmethod
    def enable_caching(cls, enabled: bool = True) -> None:
        """Enable or disable query caching for this model"""
        cls._caching_enabled = enabled

    @classmethod
    def init_cache(cls, max_size: int = 1000, ttl: int = 300) -> QueryCache:
        """
        Initialize query cache for this model

        Args:
            max_size: Maximum cache size
            ttl: Time-to-live for cache entries

        Returns:
            QueryCache instance
        """
        cls._query_cache = QueryCache(max_size=max_size, ttl=ttl)
        return cls._query_cache

    @classmethod
    def get_cache(cls) -> Optional[QueryCache]:
        """Get the query cache instance"""
        return cls._query_cache

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the query cache"""
        if cls._query_cache:
            cls._query_cache.clear()

    @classmethod
    def cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        if cls._query_cache:
            return cls._query_cache.get_stats()
        return {}


def cached_query(ttl: int = 300):
    """
    Decorator to cache query results

    Args:
        ttl: Time-to-live for cached results in seconds

    Example:
        @cached_query(ttl=600)
        def get_active_users(db):
            return User.filter(db, is_active=True)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}|{args}|{kwargs}"
            
            # Check cache
            if hasattr(func, "_cache"):
                cached_result = func._cache.get(cache_key)
                if cached_result is not None:
                    return cached_result

            # Execute and cache
            result = func(*args, **kwargs)
            if hasattr(func, "_cache"):
                func._cache.set(cache_key, result)

            return result

        # Initialize cache on first access
        if not hasattr(wrapper, "_cache"):
            wrapper._cache = QueryCache(ttl=ttl)

        return wrapper
    return decorator


class QueryCachingStrategy:
    """Strategy for managing cache invalidation"""

    def __init__(self):
        self.model_caches: Dict[str, QueryCache] = {}

    def register_model(self, model_class, cache: QueryCache) -> None:
        """Register a model with its cache"""
        self.model_caches[model_class._table_name] = cache

    def invalidate_model(self, table_name: str) -> None:
        """Invalidate cache for a specific model"""
        if table_name in self.model_caches:
            self.model_caches[table_name].clear()

    def invalidate_pattern(self, table_name: str, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        if table_name in self.model_caches:
            return self.model_caches[table_name].invalidate_pattern(pattern)
        return 0

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all model caches"""
        return {
            table_name: cache.get_stats()
            for table_name, cache in self.model_caches.items()
        }


# Global caching strategy instance
_caching_strategy = QueryCachingStrategy()


def get_caching_strategy() -> QueryCachingStrategy:
    """Get the global caching strategy"""
    return _caching_strategy
