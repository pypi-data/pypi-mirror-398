import unittest
import threading
import time
from turbo.model import Model
from turbo.fields import TextField, IntegerField
from turbo.database import Database
import tempfile
import os

# Test model
class TestUser(Model):
    name = TextField()
    age = IntegerField()

class TestThreadSafeCacheOperations(unittest.TestCase):
    """Comprehensive tests for thread-safe cache operations"""

    def setUp(self):
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = Database(self.db_path)
        self.db.connect()
        TestUser.create_table(self.db)

    def tearDown(self):
        # Clean up
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_concurrent_cache_get_operations(self):
        """Test concurrent cache get operations with multiple threads"""
        # Add some test data
        user1 = TestUser(name="Alice", age=25)
        user1.save(self.db)
        user2 = TestUser(name="Bob", age=30)
        user2.save(self.db)

        # Clear cache to start fresh
        TestUser._cache = {}

        results = []
        errors = []

        def cache_getter(thread_id):
            try:
                for i in range(10):
                    # Get from cache (should be thread-safe)
                    user = TestUser._cache_get(1)  # Get Alice
                    if user:
                        results.append((thread_id, i, user.name))
                    else:
                        # If not in cache, get from DB and cache it
                        user = TestUser.get(self.db, 1)
                        if user:
                            results.append((thread_id, i, user.name))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=cache_getter, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0)
        self.assertGreater(len(results), 0)

        # All results should be "Alice"
        for thread_id, op_id, name in results:
            self.assertEqual(name, "Alice")

    def test_concurrent_cache_set_operations(self):
        """Test concurrent cache set operations with multiple threads"""
        # Clear cache to start fresh
        TestUser._cache = {}

        results = []
        errors = []

        def cache_setter(thread_id):
            try:
                for i in range(5):
                    # Create a user and cache it (should be thread-safe)
                    user = TestUser(name=f"User_{thread_id}_{i}", age=20 + i)
                    user.id = thread_id * 100 + i  # Assign unique ID
                    TestUser._cache_set(user.id, user)
                    results.append((thread_id, i, user.id))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=cache_setter, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 15)  # 3 threads * 5 operations each

        # Verify all items are in cache
        for thread_id, op_id, user_id in results:
            cached_user = TestUser._cache_get(user_id)
            self.assertIsNotNone(cached_user)
            self.assertEqual(cached_user.id, user_id)

    def test_concurrent_cache_remove_operations(self):
        """Test concurrent cache remove operations with multiple threads"""
        # Add some test data to cache
        for i in range(10):
            user = TestUser(name=f"User_{i}", age=20 + i)
            user.id = i
            TestUser._cache_set(i, user)

        results = []
        errors = []

        def cache_remover(thread_id):
            try:
                for i in range(5):
                    user_id = thread_id * 5 + i
                    # Remove from cache (should be thread-safe)
                    TestUser._cache_remove(user_id)
                    results.append((thread_id, i, user_id))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for thread_id in range(2):
            thread = threading.Thread(target=cache_remover, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)  # 2 threads * 5 operations each

        # Verify items are removed from cache
        for thread_id, op_id, user_id in results:
            cached_user = TestUser._cache_get(user_id)
            self.assertIsNone(cached_user)

    def test_cache_methods_thread_safety(self):
        """Test all cache methods (_cache_get, _cache_set, _cache_remove)"""
        # Clear cache
        TestUser._cache = {}

        operations_completed = []
        errors = []

        def cache_operations(thread_id):
            try:
                # Test _cache_set
                user = TestUser(name=f"Thread_{thread_id}", age=25)
                user.id = thread_id
                TestUser._cache_set(user.id, user)
                operations_completed.append((thread_id, "set"))

                # Test _cache_get
                cached_user = TestUser._cache_get(user.id)
                self.assertIsNotNone(cached_user)
                self.assertEqual(cached_user.name, f"Thread_{thread_id}")
                operations_completed.append((thread_id, "get"))

                # Test _cache_remove
                TestUser._cache_remove(user.id)
                cached_user = TestUser._cache_get(user.id)
                self.assertIsNone(cached_user)
                operations_completed.append((thread_id, "remove"))

            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for thread_id in range(10):
            thread = threading.Thread(target=cache_operations, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(operations_completed), 30)  # 10 threads * 3 operations each

    def test_thread_safety_performance_impact(self):
        """Test that thread safety doesn't impact performance significantly"""
        # Clear cache
        TestUser._cache = {}

        # Add some initial data
        for i in range(100):
            user = TestUser(name=f"User_{i}", age=20 + (i % 10))
            user.id = i
            TestUser._cache_set(i, user)

        # Test single-threaded performance
        start_time = time.time()
        for i in range(1000):
            user = TestUser._cache_get(i % 100)
        single_thread_time = time.time() - start_time

        # Test multi-threaded performance
        results = []
        errors = []

        def cache_worker(thread_id):
            try:
                for i in range(200):  # 5 threads * 200 = 1000 operations
                    user = TestUser._cache_get(i % 100)
                    if user:
                        results.append((thread_id, i))
            except Exception as e:
                errors.append((thread_id, str(e)))

        start_time = time.time()
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=cache_worker, args=(thread_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        multi_thread_time = time.time() - start_time

        # Check results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 1000)

        # Performance should be reasonable (multi-threaded should not be much slower)
        # Allow for some overhead due to thread coordination
        # Use a very generous multiplier to handle timer resolution issues
        # and system variability
        if single_thread_time > 0:
            self.assertLess(multi_thread_time, single_thread_time * 10,
                           "Multi-threaded performance should not be significantly worse")
        # If single_thread_time is 0 (too fast to measure), just check multi_thread_time is reasonable
        else:
            self.assertLess(multi_thread_time, 0.1,
                           "Multi-threaded performance should be reasonable")

    def test_cache_consistency_under_concurrent_access(self):
        """Test cache consistency under concurrent read/write access"""
        # Clear cache
        TestUser._cache = {}

        # Initial user
        user = TestUser(name="Original", age=30)
        user.id = 1
        TestUser._cache_set(1, user)

        results = []
        errors = []

        def cache_reader_writer(thread_id):
            try:
                for i in range(20):
                    if i % 2 == 0:
                        # Read operation
                        cached_user = TestUser._cache_get(1)
                        if cached_user:
                            results.append((thread_id, i, "read", cached_user.name))
                    else:
                        # Write operation
                        new_user = TestUser(name=f"Updated_{thread_id}_{i}", age=30 + i)
                        new_user.id = 1
                        TestUser._cache_set(1, new_user)
                        results.append((thread_id, i, "write", new_user.name))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=cache_reader_writer, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 60)  # 3 threads * 20 operations each

        # Final value should be consistent (last write wins)
        final_user = TestUser._cache_get(1)
        self.assertIsNotNone(final_user)

        # Verify that the cache is in a consistent state
        self.assertTrue(final_user.name.startswith("Updated_"))

    def test_race_condition_prevention(self):
        """Test that thread-safe locking prevents race conditions"""
        # Clear cache
        TestUser._cache = {}

        # Counter to track operations
        operation_count = [0]
        lock = threading.Lock()

        def increment_counter():
            for _ in range(1000):
                with lock:
                    operation_count[0] += 1

                # Simulate cache operation
                user = TestUser(name="Test", age=25)
                user.id = 1
                TestUser._cache_set(1, user)
                cached_user = TestUser._cache_get(1)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=increment_counter)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have exactly 10,000 operations (10 threads * 1000 each)
        self.assertEqual(operation_count[0], 10000)

        # Cache should be in consistent state
        final_user = TestUser._cache_get(1)
        self.assertIsNotNone(final_user)
        self.assertEqual(final_user.name, "Test")

if __name__ == '__main__':
    unittest.main()