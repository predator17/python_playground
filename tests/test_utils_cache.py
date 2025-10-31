"""Tests for caching utilities."""

#      Copyright (c) 2025 predator. All rights reserved.

import threading
import time
from unittest.mock import Mock
import pytest


class TestSystemInfoCache:
    """Test SystemInfoCache class."""

    def setup_method(self):
        """Reset cache before each test."""
        from system_monitor.utils.cache import SystemInfoCache
        SystemInfoCache.reset()

    def test_singleton_pattern(self):
        """Test that SystemInfoCache implements singleton pattern."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache1 = SystemInfoCache()
        cache2 = SystemInfoCache()
        
        assert cache1 is cache2

    def test_get_nonexistent_key(self):
        """Test get returns None for nonexistent key."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache = SystemInfoCache()
        result = cache.get('nonexistent')
        
        assert result is None

    def test_set_and_get(self):
        """Test set and get operations."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache = SystemInfoCache()
        cache.set('test_key', 'test_value')
        
        result = cache.get('test_key')
        assert result == 'test_value'

    def test_get_or_compute_not_cached(self):
        """Test get_or_compute computes value when not cached."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache = SystemInfoCache()
        compute_func = Mock(return_value='computed_value')
        
        result = cache.get_or_compute('new_key', compute_func)
        
        assert result == 'computed_value'
        compute_func.assert_called_once()
        
        # Verify it's cached
        assert cache.get('new_key') == 'computed_value'

    def test_get_or_compute_cached(self):
        """Test get_or_compute returns cached value without computing."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache = SystemInfoCache()
        cache.set('existing_key', 'cached_value')
        compute_func = Mock(return_value='computed_value')
        
        result = cache.get_or_compute('existing_key', compute_func)
        
        assert result == 'cached_value'
        compute_func.assert_not_called()

    def test_clear(self):
        """Test clear removes all cached values."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache = SystemInfoCache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        
        cache.clear()
        
        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_reset_class_method(self):
        """Test reset class method resets singleton instance."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache1 = SystemInfoCache()
        cache1.set('test', 'value')
        
        SystemInfoCache.reset()
        
        cache2 = SystemInfoCache()
        # After reset, should be a new instance with empty cache
        assert cache2.get('test') is None

    def test_thread_safety(self):
        """Test that cache operations are thread-safe."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache = SystemInfoCache()
        results = []
        errors = []
        
        def worker(thread_id):
            try:
                for i in range(100):
                    cache.set(f'key_{thread_id}_{i}', f'value_{thread_id}_{i}')
                    value = cache.get(f'key_{thread_id}_{i}')
                    results.append(value)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No errors should occur
        assert len(errors) == 0
        # All operations should succeed
        assert len(results) == 500

    def test_get_or_compute_thread_safety(self):
        """Test get_or_compute is thread-safe."""
        from system_monitor.utils.cache import SystemInfoCache
        
        cache = SystemInfoCache()
        call_count = []
        
        def expensive_computation():
            call_count.append(1)
            time.sleep(0.01)  # Simulate expensive operation
            return 'computed'
        
        results = []
        
        def worker():
            result = cache.get_or_compute('shared_key', expensive_computation)
            results.append(result)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should get the same result
        assert all(r == 'computed' for r in results)
        assert len(results) == 10
        # Computation should only happen once (or very few times due to race)
        assert len(call_count) <= 2


class TestCachedStaticPropertyDecorator:
    """Test cached_static_property decorator."""

    def setup_method(self):
        """Reset cache before each test."""
        from system_monitor.utils.cache import SystemInfoCache
        SystemInfoCache.reset()

    def test_decorator_caches_result(self):
        """Test decorator caches function result."""
        from system_monitor.utils.cache import cached_static_property
        
        call_count = []
        
        @cached_static_property('test_property')
        def expensive_function():
            call_count.append(1)
            return 'expensive_result'
        
        # First call should compute
        result1 = expensive_function()
        assert result1 == 'expensive_result'
        assert len(call_count) == 1
        
        # Second call should return cached value
        result2 = expensive_function()
        assert result2 == 'expensive_result'
        assert len(call_count) == 1  # Still 1, not called again

    def test_decorator_with_different_keys(self):
        """Test decorator with different cache keys."""
        from system_monitor.utils.cache import cached_static_property
        
        @cached_static_property('key1')
        def func1():
            return 'value1'
        
        @cached_static_property('key2')
        def func2():
            return 'value2'
        
        result1 = func1()
        result2 = func2()
        
        assert result1 == 'value1'
        assert result2 == 'value2'

    def test_decorator_with_args(self):
        """Test decorator works with function arguments."""
        from system_monitor.utils.cache import cached_static_property
        
        call_count = []
        
        @cached_static_property('test_with_args')
        def func_with_args(arg1, arg2):
            call_count.append(1)
            return f'{arg1}_{arg2}'
        
        # Note: decorator caches by key only, not by args
        # So same result regardless of args (by design for static properties)
        result1 = func_with_args('a', 'b')
        result2 = func_with_args('c', 'd')
        
        assert result1 == 'a_b'
        assert result2 == 'a_b'  # Returns cached value
        assert len(call_count) == 1  # Only called once
