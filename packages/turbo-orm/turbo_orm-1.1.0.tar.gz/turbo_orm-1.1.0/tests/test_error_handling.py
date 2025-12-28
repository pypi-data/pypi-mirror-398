import unittest
import sqlite3
import os
import tempfile
from turbo.database import Database
from turbo.model import Model
from turbo.fields import TextField
from turbo.performance import add_caching_to_database

class TestModel(Model):
    name = TextField(required=True)

class TestErrorHandling(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Add caching to database
        add_caching_to_database()
        
    def tearDown(self):
        # Remove the temporary database file
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
            
    def test_database_connection_error_handling(self):
        # Test that connection errors are properly handled
        db = Database("/invalid/path/to/database.db")
        with self.assertRaises(ConnectionError):
            db.connect()
            
    def test_transaction_rollback_on_error(self):
        # Test that transactions are properly rolled back on error
        db = Database(self.db_path)
        db.connect()
        TestModel.create_table(db)
        
        try:
            with db.transaction():
                instance = TestModel(name="test")
                instance.save(db)
                # Force an error to trigger rollback
                raise Exception("Force rollback")
        except Exception:
            pass
        finally:
            db.close()
            
        # Verify that the instance was not saved
        db2 = Database(self.db_path)
        db2.connect()
        instances = TestModel.all(db2)
        self.assertEqual(len(instances), 0)
        db2.close()
        
    def test_cache_error_handling(self):
        # Test that cache errors are properly handled
        db = Database(self.db_path)
        db.connect()
        TestModel.create_table(db)
        
        # Add some data
        instance = TestModel(name="test")
        instance.save(db)
        
        # Test normal operation
        instances = TestModel.all(db)
        self.assertEqual(len(instances), 1)
        
        # Test cache stats
        stats = db.get_cache_stats()
        self.assertIsInstance(stats, dict)
        
        db.close()
        
    def test_connection_health_check(self):
        # Test that connection health checks work
        db = Database(self.db_path)
        db.connect()
        
        # Normal operation should work
        TestModel.create_table(db)
        
        # Close the connection to simulate a broken connection
        db.connection.close()
        db.connection = None
        
        # Reconnect should work
        db.connect()
        
        # Health check should pass
        TestModel.create_table(db)
        
        db.close()

if __name__ == '__main__':
    unittest.main()