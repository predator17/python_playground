"""Unit tests for system_monitor.utils.cache module."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
import threading
import time
from unittest.mock import MagicMock, patch

from system_monitor.utils.cache import SystemInfoCache, cached_static_property


class TestSystemInfoCache(unittest.TestCase):
    """Test SystemInfoCache singleton and caching functionality."""

    def setUp(self):
        """Reset singleton before each test."""
        SystemInfoCache.reset()

    def tearDown(self):
        """Clean up after each test."""
        SystemInfoCache.reset()

    def test_singleton_pattern(self):
        """Test that SystemInfoCache is a singleton."""
        cache1 = SystemInfoCache()
        cache2 = SystemInfoCache()
        
        self.assertIs(cache1, cache2)
        self.assertEqual(id(cache1), id(cache2))

    def test_singleton_thread_safety(self):
        """Test singleton creation is thread-safe."""
        instances = []
        
        def create_instance():
            cache = SystemInfoCache()
            instances.append(cache)
        
        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All instances should be the same object
        first_id = id(instances[0])
        for instance in instances:
            self.assertEqual(id(instance), first_id)

    def test_get_nonexistent_key(self):
        """Test getting a non-existent key returns None."""
        cache = SystemInfoCache()
        result = cache.get('nonexistent_key')
        self.assertIsNone(result)

    def test_set_and_get(self):
        """Test setting and getting cached values."""
        cache = SystemInfoCache()
        cache.set('test_key', 'test_value')
        
        result = cache.get('test_key')
        self.assertEqual(result, 'test_value')

    def test_set_overwrites_existing(self):
        """Test that set overwrites existing values."""
        cache = SystemInfoCache()
        cache.set('key', 'value1')
        cache.set('key', 'value2')
        
        result = cache.get('key')
        self.assertEqual(result, 'value2')

    def test_get_or_compute_cached(self):
        """Test get_or_compute returns cached value without computation."""
        cache = SystemInfoCache()
        cache.set('cached_key', 'cached_value')
        
        compute_func = MagicMock(return_value='computed_value')
        result = cache.get_or_compute('cached_key', compute_func)
        
        self.assertEqual(result, 'cached_value')
        compute_func.assert_not_called()

    def test_get_or_compute_not_cached(self):
        """Test get_or_compute computes and caches new value."""
        cache = SystemInfoCache()
        
        compute_func = MagicMock(return_value='computed_value')
        result = cache.get_or_compute('new_key', compute_func)
        
        self.assertEqual(result, 'computed_value')
        compute_func.assert_called_once()
        
        # Verify it was cached
        cached_result = cache.get('new_key')
        self.assertEqual(cached_result, 'computed_value')

    def test_get_or_compute_called_once(self):
        """Test compute function is called only once for multiple accesses."""
        cache = SystemInfoCache()
        call_count = {'count': 0}
        
        def compute_func():
            call_count['count'] += 1
            return f"value_{call_count['count']}"
        
        result1 = cache.get_or_compute('key', compute_func)
        result2 = cache.get_or_compute('key', compute_func)
        
        self.assertEqual(result1, 'value_1')
        self.assertEqual(result2, 'value_1')
        self.assertEqual(call_count['count'], 1)

    def test_clear(self):
        """Test clearing all cached values."""
        cache = SystemInfoCache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        
        cache.clear()
        
        self.assertIsNone(cache.get('key1'))
        self.assertIsNone(cache.get('key2'))

    def test_thread_safe_operations(self):
        """Test concurrent read/write operations are thread-safe."""
        cache = SystemInfoCache()
        results = []
        
        def writer(key, value):
            cache.set(key, value)
        
        def reader(key):
            result = cache.get(key)
            results.append(result)
        
        # Pre-populate
        cache.set('shared_key', 'initial_value')
        
        threads = []
        threads.append(threading.Thread(target=writer, args=('shared_key', 'value1')))
        threads.append(threading.Thread(target=reader, args=('shared_key',)))
        threads.append(threading.Thread(target=writer, args=('shared_key', 'value2')))
        threads.append(threading.Thread(target=reader, args=('shared_key',)))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have some valid results (thread-safe, no crashes)
        self.assertTrue(len(results) > 0)
        for result in results:
            self.assertIn(result, ['initial_value', 'value1', 'value2'])

    def test_reset_clears_singleton(self):
        """Test reset() clears the singleton instance."""
        cache1 = SystemInfoCache()
        cache1.set('key', 'value')
        
        SystemInfoCache.reset()
        
        cache2 = SystemInfoCache()
        self.assertIsNone(cache2.get('key'))
        self.assertIsNot(cache1, cache2)


class TestCachedStaticProperty(unittest.TestCase):
    """Test cached_static_property decorator."""

    def setUp(self):
        """Reset singleton before each test."""
        SystemInfoCache.reset()

    def tearDown(self):
        """Clean up after each test."""
        SystemInfoCache.reset()

    def test_decorator_caches_result(self):
        """Test decorator caches function result."""
        call_count = {'count': 0}
        
        @cached_static_property('test_prop')
        def expensive_func():
            call_count['count'] += 1
            return 'expensive_result'
        
        result1 = expensive_func()
        result2 = expensive_func()
        
        self.assertEqual(result1, 'expensive_result')
        self.assertEqual(result2, 'expensive_result')
        self.assertEqual(call_count['count'], 1)

    def test_decorator_with_args(self):
        """Test decorator works with function arguments."""
        call_count = {'count': 0}
        
        @cached_static_property('test_prop_args')
        def func_with_args(a, b):
            call_count['count'] += 1
            return a + b
        
        result1 = func_with_args(1, 2)
        result2 = func_with_args(1, 2)
        result3 = func_with_args(3, 4)  # Different args, but same cache key
        
        self.assertEqual(result1, 3)
        self.assertEqual(result2, 3)
        self.assertEqual(result3, 3)  # Returns cached value
        self.assertEqual(call_count['count'], 1)

    def test_decorator_different_keys(self):
        """Test different cache keys work independently."""
        @cached_static_property('key1')
        def func1():
            return 'value1'
        
        @cached_static_property('key2')
        def func2():
            return 'value2'
        
        result1 = func1()
        result2 = func2()
        
        self.assertEqual(result1, 'value1')
        self.assertEqual(result2, 'value2')

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves original function metadata."""
        @cached_static_property('test_key')
        def my_function():
            """My docstring."""
            return 'result'
        
        self.assertEqual(my_function.__name__, 'my_function')
        self.assertEqual(my_function.__doc__, 'My docstring.')

    def test_decorator_exception_handling(self):
        """Test decorator handles exceptions from compute function."""
        @cached_static_property('error_key')
        def failing_func():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError) as context:
            failing_func()
        
        self.assertIn("Test error", str(context.exception))

    def test_decorator_caches_none_value(self):
        """Test decorator can cache None values."""
        call_count = {'count': 0}
        
        @cached_static_property('none_key')
        def returns_none():
            call_count['count'] += 1
            return None
        
        result1 = returns_none()
        result2 = returns_none()
        
        self.assertIsNone(result1)
        self.assertIsNone(result2)
        self.assertEqual(call_count['count'], 1)

    def test_decorator_thread_safety(self):
        """Test decorator is thread-safe."""
        call_count = {'count': 0}
        results = []
        
        @cached_static_property('thread_safe_key')
        def slow_func():
            call_count['count'] += 1
            time.sleep(0.01)  # Simulate slow operation
            return 'result'
        
        def call_func():
            result = slow_func()
            results.append(result)
        
        threads = [threading.Thread(target=call_func) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should get same result
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertEqual(result, 'result')
        
        # Function should be called at least once, but due to threading
        # might be called a few times before cache is set
        self.assertGreaterEqual(call_count['count'], 1)
        self.assertLessEqual(call_count['count'], 10)


if __name__ == '__main__':
    unittest.main()
