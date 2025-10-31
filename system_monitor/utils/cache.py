"""Caching utilities for expensive system information queries."""

#      Copyright (c) 2025 predator. All rights reserved.

from __future__ import annotations

import threading
from typing import Optional, Dict, Any, Callable
from functools import wraps


class SystemInfoCache:
    """Thread-safe singleton cache for expensive system information queries.
    
    Uses lazy initialization and caches static system properties that never change
    (CPU model, memory frequency, etc.) to avoid repeated expensive subprocess calls.
    """
    
    _instance: Optional['SystemInfoCache'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'SystemInfoCache':
        """Singleton pattern: ensure only one cache instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize cache storage."""
        self._cache: Dict[str, Any] = {}
        self._cache_lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key (thread-safe)."""
        with self._cache_lock:
            return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set cached value by key (thread-safe)."""
        with self._cache_lock:
            self._cache[key] = value
    
    def get_or_compute(self, key: str, compute_func: Callable[[], Any]) -> Any:
        """Get cached value or compute and cache it if not present (thread-safe).
        
        Args:
            key: Cache key
            compute_func: Function to compute value if not cached
            
        Returns:
            Cached or newly computed value
        """
        with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            
            value = compute_func()
            self._cache[key] = value
            return value
    
    def clear(self) -> None:
        """Clear all cached values (thread-safe)."""
        with self._cache_lock:
            self._cache.clear()
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (mainly for testing)."""
        with cls._lock:
            cls._instance = None


def cached_static_property(key: str) -> Callable:
    """Decorator for caching static system properties that never change.
    
    Args:
        key: Unique cache key for this property
        
    Returns:
        Decorator function
        
    Example:
        @cached_static_property('cpu_model')
        def get_cpu_model() -> str:
            # expensive operation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache = SystemInfoCache()
            return cache.get_or_compute(key, lambda: func(*args, **kwargs))
        return wrapper
    return decorator
