import unittest
import tempfile
import os
from turbo.database import Database
from turbo.model import Model
from turbo.fields import TextField, IntegerField

# Test model
class UserModel(Model):
    name = TextField()
    age = IntegerField()

class TestSQLInjection(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = Database(self.db_path)
        self.db.connect()
        
        # Create table
        UserModel.create_table(self.db)

    def tearDown(self):
        # Clean up
        self.db.close()
        os.unlink(self.db_path)

    def test_safe_where_query(self):
        """Test that where queries are safe from injection"""
        # This should work normally
        user = UserModel(name="John Doe", age=30)
        user.save(self.db)
        
        # Normal query should work
        results = UserModel.query(self.db).where(name="John Doe").execute()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "John Doe")

    def test_safe_order_by(self):
        """Test that order by clauses are safe"""
        user1 = UserModel(name="Alice", age=25)
        user2 = UserModel(name="Bob", age=30)
        user1.save(self.db)
        user2.save(self.db)
        
        # Normal order by should work
        results = UserModel.query(self.db).order_by("name").execute()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "Alice")
        self.assertEqual(results[1].name, "Bob")
        
        # Descending order should work
        results = UserModel.query(self.db).order_by("-name").execute()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "Bob")
        self.assertEqual(results[1].name, "Alice")

    def test_safe_table_names(self):
        """Test that table names are validated"""
        # This test ensures our validation is working
        # Since we can't easily create a model with an invalid name in Python,
        # we'll test the validation function directly
        from turbo.sql_utils import validate_identifier
        
        # Valid identifiers should pass
        self.assertTrue(validate_identifier("users"))
        self.assertTrue(validate_identifier("user_profiles"))
        self.assertTrue(validate_identifier("_private_table"))
        
        # Invalid identifiers should fail
        self.assertFalse(validate_identifier("'; DROP TABLE users; --"))
        self.assertFalse(validate_identifier("users; DELETE FROM users;"))
        self.assertFalse(validate_identifier("SELECT * FROM users"))

    def test_safe_field_names(self):
        """Test that field names are validated"""
        from turbo.sql_utils import validate_identifier
        
        # Valid field names should pass
        self.assertTrue(validate_identifier("name"))
        self.assertTrue(validate_identifier("user_id"))
        self.assertTrue(validate_identifier("first_name"))
        
        # Invalid field names should fail
        self.assertFalse(validate_identifier("'; DROP TABLE users; --"))
        self.assertFalse(validate_identifier("name; DELETE FROM users;"))
        self.assertFalse(validate_identifier("SELECT * FROM users"))

if __name__ == '__main__':
    unittest.main()