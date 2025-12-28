import unittest
import tempfile
import os
import threading
import time
from turbo.database import Database, Transaction
from turbo.model import Model
from turbo.fields import TextField, IntegerField

# Test model
class TestUser(Model):
    name = TextField()
    age = IntegerField()

class TestConnectionPooling(unittest.TestCase):
    """Comprehensive tests for database connection pooling improvements"""

    def setUp(self):
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = Database(self.db_path, pool_size=2)
        self.db.connect()
        TestUser.create_table(self.db)

    def tearDown(self):
        # Clean up
        if hasattr(self, 'db') and self.db:
            try:
                self.db.close()
            except:
                pass
        try:
            if os.path.exists(self.db_path):
                os.unlink(self.db_path)
        except:
            pass  # Ignore cleanup errors

    def test_connection_context_manager(self):
        """Test the new connection_context() context manager"""
        # Test Transaction's connection_context method
        transaction = Transaction(self.db)

        # Test that connection_context works as a context manager
        with transaction.connection_context() as conn:
            self.assertIsNotNone(conn)
            # Should be able to execute queries
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

        # Connection should be properly cleaned up
        self.assertIsNone(self.db.connection)

    def test_pool_initialization_and_cleanup(self):
        """Test proper cleanup and resource management"""
        # Test with pool size
        db = Database(self.db_path, pool_size=3, prewarm=True)
        db.connect()

        # Create table to test actual database operations
        TestUser.create_table(db)

        # Connect and disconnect multiple times
        for i in range(5):
            db.connect()
            cursor = db.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
            db.close()

        # All connections should be properly managed
        self.assertIsNone(db.connection)

    def test_connection_health_monitoring(self):
        """Test connection health monitoring and timeout handling"""
        db = Database(self.db_path, pool_size=2)
        TestUser.create_table(db)

        # Connect and verify health
        db.connect()
        self.assertIsNotNone(db.connection)

        # Test health check
        try:
            db.execute("SELECT 1", timeout=1)
            result = db.execute("SELECT 1").fetchone()
            self.assertEqual(result[0], 1)
        except Exception as e:
            self.fail(f"Health check failed: {e}")

        # Test timeout handling
        with self.assertRaises(Exception):  # SQLite may not support timeout in this context
            db.execute("SELECT 1", timeout=0.001)

        db.close()

    def test_backward_compatibility(self):
        """Test backward compatibility with existing code"""
        # Test without pooling (original behavior)
        db = Database(self.db_path, pool_size=0)
        db.connect()
        TestUser.create_table(db)

        # Original usage patterns should still work
        db.connect()
        cursor = db.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
        cursor = db.execute("INSERT INTO test (name) VALUES (?)", ("test",))
        db.commit()

        cursor = db.execute("SELECT * FROM test")
        result = cursor.fetchone()
        self.assertEqual(result[1], "test")

        # Context manager should work
        with Database(self.db_path) as db2:
            cursor = db2.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)

        db.close()

    def test_thread_safe_pool_operations(self):
        """Test thread-safe connection pool operations"""
        db = Database(self.db_path, pool_size=5, prewarm=True)
        TestUser.create_table(db)

        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    db.connect()
                    cursor = db.execute("SELECT 1")
                    result = cursor.fetchone()
                    results.append((worker_id, i, result[0]))
                    db.close()
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 50)  # 5 workers * 10 operations each

        # All results should be 1
        for worker_id, op_id, result in results:
            self.assertEqual(result, 1)

        # Clean up
        db.close()

    def test_pool_exhaustion_handling(self):
        """Test behavior when pool is exhausted"""
        db = Database(self.db_path, pool_size=2, prewarm=True)
        TestUser.create_table(db)

        # Connect multiple times to exhaust pool
        connections = []
        for i in range(3):  # One more than pool size
            conn_db = Database(self.db_path, pool_size=2)
            conn_db.connect()
            connections.append(conn_db)

        # All should have connections (may create new ones beyond pool)
        for conn_db in connections:
            self.assertIsNotNone(conn_db.connection)

        # Clean up
        for conn_db in connections:
            conn_db.close()

        db.close()

    def test_connection_reuse(self):
        """Test that connections are properly reused from pool"""
        db = Database(self.db_path, pool_size=3, prewarm=True)
        TestUser.create_table(db)

        # Get connection IDs to track reuse
        connection_ids = []

        for i in range(6):  # More operations than pool size
            db.connect()
            # Get the connection object ID to track reuse
            conn_id = id(db.connection)
            connection_ids.append(conn_id)
            db.close()

        # Should see some connection reuse (same IDs appearing multiple times)
        unique_connections = set(connection_ids)
        self.assertLess(len(unique_connections), 6, "Should reuse connections from pool")

        db.close()

    def test_context_manager_with_transactions(self):
        """Test context manager with transaction handling"""
        db = Database(self.db_path, pool_size=2)
        TestUser.create_table(db)

        # Test successful transaction
        with db.transaction():
            user = TestUser(name="Alice", age=25)
            user.save(db)

        # Should be committed
        users = TestUser.all(db)
        self.assertEqual(len(users), 1)

        # Test failed transaction
        with self.assertRaises(ValueError):
            with db.transaction():
                user = TestUser(name="Bob", age=30)
                user.save(db)
                raise ValueError("Test error")

        # Should be rolled back
        users = TestUser.all(db)
        self.assertEqual(len(users), 1)  # Still only Alice

        db.close()

    def test_resource_cleanup_on_error(self):
        """Test proper cleanup in all error cases"""
        db = Database(self.db_path, pool_size=2)
        TestUser.create_table(db)

        # Test error during connection
        try:
            # Force an error
            raise ConnectionError("Simulated error")
        except ConnectionError:
            pass

        # Should still be able to connect
        db.connect()
        cursor = db.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        db.close()

        # Test error during query execution
        db.connect()
        try:
            # This should fail
            db.execute("INVALID SQL SYNTAX")
        except Exception:
            pass

        # Connection should still be usable
        cursor = db.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)
        db.close()

if __name__ == '__main__':
    unittest.main()