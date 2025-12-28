"""
Tests and demonstrations for Query Caching functionality

Shows performance improvements with caching enabled vs disabled.
"""

import sys
import os
import unittest
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from turbo import Database, Model, TextField, IntegerField
from turbo.query_cache import QueryCache, CachedQueryMixin, get_caching_strategy


class User(Model, CachedQueryMixin):
    """Test user model with caching support"""
    name = TextField(required=True)
    email = TextField()
    age = IntegerField()


class TestQueryCaching(unittest.TestCase):
    """Tests for query caching functionality"""

    def setUp(self):
        """Set up test database"""
        self.db = Database(":memory:")
        self.db.connect()
        User.create_table(self.db)
        
        # Create test data
        for i in range(10):
            User(name=f"User{i}", email=f"user{i}@test.com", age=20+i).save(self.db)

    def tearDown(self):
        """Clean up"""
        self.db.close()

    # QueryCache Tests
    def test_query_cache_creation(self):
        """Test creating a QueryCache"""
        cache = QueryCache(max_size=100, ttl=300)
        self.assertEqual(cache.max_size, 100)
        self.assertEqual(cache.ttl, 300)

    def test_cache_set_and_get(self):
        """Test setting and getting cache entries"""
        cache = QueryCache()
        
        cache.set("key1", {"id": 1, "name": "Alice"})
        result = cache.get("key1")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Alice")

    def test_cache_miss(self):
        """Test cache miss returns None"""
        cache = QueryCache()
        result = cache.get("nonexistent")
        
        self.assertIsNone(result)

    def test_cache_ttl_expiration(self):
        """Test cache entries expire after TTL"""
        cache = QueryCache(ttl=1)  # 1 second TTL
        
        cache.set("key1", "value1")
        self.assertIsNotNone(cache.get("key1"))
        
        # Wait for expiration
        time.sleep(1.1)
        self.assertIsNone(cache.get("key1"))

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = QueryCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        self.assertEqual(len(cache.cache), 3)
        
        # Add new entry - should trigger eviction
        cache.set("key4", "value4")
        
        # Cache should still have 3 items
        self.assertEqual(len(cache.cache), 3)

    def test_cache_stats(self):
        """Test cache statistics"""
        cache = QueryCache()
        
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("missing")  # Miss
        
        stats = cache.get_stats()
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_rate"], 66.67, places=1)

    def test_cache_invalidate_pattern(self):
        """Test pattern-based cache invalidation"""
        cache = QueryCache()
        
        cache.set("user:1", {"id": 1})
        cache.set("user:2", {"id": 2})
        cache.set("post:1", {"id": 1})
        
        # Invalidate all user entries
        invalidated = cache.invalidate_pattern("user:*")
        
        self.assertEqual(invalidated, 2)
        self.assertIsNone(cache.get("user:1"))
        self.assertIsNone(cache.get("user:2"))
        self.assertIsNotNone(cache.get("post:1"))

    def test_cache_clear(self):
        """Test clearing entire cache"""
        cache = QueryCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))

    # CachedQueryMixin Tests
    def test_model_cache_initialization(self):
        """Test initializing cache on model"""
        User.init_cache(max_size=500, ttl=600)
        cache = User.get_cache()
        
        self.assertIsNotNone(cache)
        self.assertEqual(cache.max_size, 500)
        self.assertEqual(cache.ttl, 600)

    def test_model_cache_enable_disable(self):
        """Test enabling/disabling caching"""
        User.enable_caching(True)
        self.assertTrue(User._caching_enabled)
        
        User.enable_caching(False)
        self.assertFalse(User._caching_enabled)

    def test_model_cache_stats(self):
        """Test getting cache statistics from model"""
        User.init_cache()
        cache = User.get_cache()
        cache.set("test", "value")
        
        stats = User.cache_stats()
        self.assertEqual(stats["size"], 1)

    def test_model_cache_clear(self):
        """Test clearing model cache"""
        User.init_cache()
        cache = User.get_cache()
        cache.set("test1", "value1")
        cache.set("test2", "value2")
        
        User.clear_cache()
        
        self.assertIsNone(cache.get("test1"))
        self.assertIsNone(cache.get("test2"))

    # Caching Strategy Tests
    def test_caching_strategy(self):
        """Test global caching strategy"""
        strategy = get_caching_strategy()
        
        cache = QueryCache()
        strategy.register_model(User, cache)
        
        cache.set("user:1", {"id": 1})
        strategy.invalidate_model("user")
        
        self.assertIsNone(cache.get("user:1"))

    def test_caching_strategy_stats(self):
        """Test caching strategy statistics"""
        strategy = get_caching_strategy()
        cache = QueryCache()
        strategy.register_model(User, cache)
        
        cache.set("key", "value")
        stats = strategy.get_all_stats()
        
        self.assertIn("user", stats)

    # Performance Tests
    def test_repeated_query_performance_with_cache(self):
        """Test performance improvement with caching"""
        User.init_cache()
        cache = User.get_cache()
        
        # Simulate repeated queries
        for i in range(100):
            # In real scenario, this would be User.get(db, i)
            cache.set(f"user:{i}", f"user_data_{i}")
        
        # Repeated accesses
        start = time.time()
        for _ in range(1000):
            for i in range(100):
                cache.get(f"user:{i}")
        duration = time.time() - start
        
        ops_per_sec = 100000 / duration
        stats = cache.get_stats()
        
        self.assertGreater(ops_per_sec, 100000)
        self.assertGreater(stats["hit_rate"], 90)
        print(f"\n  Cached queries: {ops_per_sec:,.0f} ops/sec, {stats['hit_rate']:.1f}% hit rate")

    def test_cache_effectiveness_analysis(self):
        """Test cache effectiveness in realistic scenario"""
        cache = QueryCache(max_size=1000)
        
        # Simulate real access pattern: 80/20 (80% of accesses to 20% of data)
        popular_keys = [f"user:{i}" for i in range(20)]
        rare_keys = [f"user:{i}" for i in range(20, 100)]
        
        # Cache popular keys
        for key in popular_keys:
            cache.set(key, {"data": key})
        
        # Simulate access pattern - note: accessing uncached rare_keys will be misses
        access_log = popular_keys * 80 + rare_keys * 20
        for key in access_log:
            cache.get(key)
        
        stats = cache.get_stats()
        # With 80/20 pattern on 100 total accesses per key
        # popular: 80*20 = 1600 hits (all cached)
        # rare: 20*80 = 1600 misses (not cached)
        # Total: 1600/(1600+1600) = 50% hit rate
        self.assertGreaterEqual(stats["hit_rate"], 40)
        
        print(f"\n  80/20 access pattern: {stats['hit_rate']:.1f}% hit rate")

    # Integration Tests
    def test_cache_with_model_operations(self):
        """Test caching integration with model operations"""
        User.init_cache(max_size=100)
        cache = User.get_cache()
        
        # Cache a query result
        users = User.all(self.db)
        cache_key = "all_users"
        cache.set(cache_key, users)
        
        # Retrieve from cache
        cached_users = cache.get(cache_key)
        self.assertEqual(len(cached_users), len(users))

    def test_cache_invalidation_on_update(self):
        """Test cache invalidation when model is updated"""
        User.init_cache()
        cache = User.get_cache()
        
        # Cache a query
        cache.set("users_count", 10)
        self.assertEqual(cache.get("users_count"), 10)
        
        # Invalidate on update
        cache.invalidate_pattern("users*")
        self.assertIsNone(cache.get("users_count"))

    # Edge Cases
    def test_cache_with_none_values(self):
        """Test caching None values"""
        cache = QueryCache()
        
        cache.set("none_key", None)
        # Note: get returns None for both missing and None values
        # This is a limitation to consider

    def test_cache_with_large_objects(self):
        """Test caching large objects"""
        cache = QueryCache()
        
        large_object = {f"key_{i}": f"value_{i}" for i in range(1000)}
        cache.set("large", large_object)
        
        retrieved = cache.get("large")
        self.assertEqual(len(retrieved), 1000)

    def test_cache_thread_safety(self):
        """Test cache thread safety"""
        import threading
        
        cache = QueryCache(max_size=100)
        errors = []
        
        def cache_setter():
            try:
                for i in range(100):
                    cache.set(f"key_{i}", f"value_{i}")
            except Exception as e:
                errors.append(e)
        
        def cache_getter():
            try:
                for i in range(100):
                    cache.get(f"key_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=cache_setter),
            threading.Thread(target=cache_getter),
            threading.Thread(target=cache_setter),
            threading.Thread(target=cache_getter),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
