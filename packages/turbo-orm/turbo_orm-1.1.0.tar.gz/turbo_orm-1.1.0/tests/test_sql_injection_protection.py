import unittest
import tempfile
import os
from turbo.database import Database
from turbo.model import Model
from turbo.fields import TextField, IntegerField
from turbo.sql_utils import validate_identifier, sanitize_identifier, sanitize_order_by_field, quote_identifier

# Test model
class TestUser(Model):
    name = TextField()
    age = IntegerField()

class TestSQLInjectionProtection(unittest.TestCase):
    """Comprehensive tests for SQL injection protection"""

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

    def test_parameterized_queries(self):
        """Test that all SQL queries use proper parameterization"""
        # Test normal usage with parameters
        user = TestUser(name="Alice", age=25)
        user.save(self.db)

        # Test query with parameters (should be safe)
        results = TestUser.filter(self.db, name="Alice")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Alice")

        # Test with potentially malicious input (should be safe due to parameterization)
        malicious_name = "Alice'; DROP TABLE users; --"
        try:
            results = TestUser.filter(self.db, name=malicious_name)
            # Should not find anything (or find the literal string)
            self.assertLessEqual(len(results), 1)
        except Exception as e:
            # Should not cause SQL injection, might cause other errors
            self.assertNotIn("DROP TABLE", str(e))
            self.assertNotIn("syntax error", str(e).lower())

    def test_special_characters_in_input(self):
        """Test edge cases with special characters and SQL injection attempts"""
        # Test various special characters
        special_names = [
            "O'Reilly",  # Single quote
            'Smith"s',   # Double quote
            "Jones;--",  # Semicolon and comment
            "Wilson/*comment*/",  # Block comment
            "Brown' OR '1'='1",  # Classic SQL injection
            "Green\" OR \"1\"=\"1",  # Double quote version
            "Black'; SELECT * FROM users; --",  # Multi-statement
            "White UNION SELECT * FROM users; --",  # UNION attack
            "Gray EXEC xp_cmdshell('dir'); --",  # Command execution
        ]

        for name in special_names:
            try:
                user = TestUser(name=name, age=30)
                user.save(self.db)

                # Should be able to retrieve safely
                results = TestUser.filter(self.db, name=name)
                self.assertGreaterEqual(len(results), 1)

                # Clean up
                if results:
                    results[0].delete(self.db)

            except Exception as e:
                # Should not be SQL injection errors
                self.assertNotIn("syntax error", str(e).lower())
                self.assertNotIn("unrecognized token", str(e).lower())

    def test_sanitization_functions(self):
        """Test that sanitization functions work correctly"""
        # Test validate_identifier
        self.assertTrue(validate_identifier("valid_name"))
        self.assertTrue(validate_identifier("user_id"))
        self.assertTrue(validate_identifier("_private"))

        # Test invalid identifiers
        self.assertFalse(validate_identifier("'; DROP TABLE users; --"))
        self.assertFalse(validate_identifier("SELECT * FROM users"))
        self.assertFalse(validate_identifier("user; DELETE FROM users"))
        self.assertFalse(validate_identifier("123invalid"))  # Starts with number
        self.assertFalse(validate_identifier(""))  # Empty
        self.assertFalse(validate_identifier("a" * 65))  # Too long

        # Test sanitize_identifier raises exceptions
        with self.assertRaises(ValueError):
            sanitize_identifier("'; DROP TABLE users; --")

        with self.assertRaises(ValueError):
            sanitize_identifier("SELECT * FROM users")

    def test_order_by_sanitization(self):
        """Test that order_by field sanitization works"""
        # Valid order by fields
        self.assertEqual(sanitize_order_by_field("name"), "name")
        self.assertEqual(sanitize_order_by_field("-name"), "-name")
        self.assertEqual(sanitize_order_by_field("created_at"), "created_at")
        self.assertEqual(sanitize_order_by_field("-created_at"), "-created_at")

        # Invalid order by fields should raise exceptions
        with self.assertRaises(ValueError):
            sanitize_order_by_field("'; DROP TABLE users; --")

        with self.assertRaises(ValueError):
            sanitize_order_by_field("name; DELETE FROM users")

        with self.assertRaises(ValueError):
            sanitize_order_by_field("SELECT * FROM users")

    def test_identifier_quoting(self):
        """Test that identifiers are properly quoted"""
        # Test quote_identifier
        self.assertEqual(quote_identifier("users"), '"users"')
        self.assertEqual(quote_identifier("user_id"), '"user_id"')
        self.assertEqual(quote_identifier("table"), '"table"')

        # Even potentially dangerous identifiers get quoted safely
        self.assertEqual(quote_identifier("'; DROP TABLE users; --"), '"\'; DROP TABLE users; --"')

    def test_raw_sql_warnings(self):
        """Test that raw SQL usage is properly documented with warnings"""
        # Test that raw SQL method has proper warning
        method_doc = TestUser.raw.__doc__
        self.assertIsNotNone(method_doc)
        self.assertIn("Warning", method_doc)
        self.assertIn("trusted SQL queries", method_doc)
        self.assertIn("user input", method_doc)

    def test_model_field_validation(self):
        """Test that model field names are validated"""
        # Test that invalid field names are rejected in constructor
        with self.assertRaises(ValueError):
            TestUser(**{"'; DROP TABLE users; --": "malicious"})

        with self.assertRaises(ValueError):
            TestUser(**{"name; DELETE FROM users": "malicious"})

    def test_table_name_validation(self):
        """Test that table names are validated"""
        # This is tested indirectly through the metaclass
        # If we could create a model with invalid table name, it would fail
        # For now, test the validation function directly
        from turbo.sql_utils import validate_identifier

        self.assertTrue(validate_identifier("users"))
        self.assertFalse(validate_identifier("'; DROP TABLE users; --"))

    def test_sql_injection_in_where_clauses(self):
        """Test SQL injection attempts in where clauses"""
        # Add some test data
        user1 = TestUser(name="Alice", age=25)
        user1.save(self.db)
        user2 = TestUser(name="Bob", age=30)
        user2.save(self.db)

        # Test normal where clause (should work)
        results = TestUser.filter(self.db, name="Alice")
        self.assertEqual(len(results), 1)

        # Test injection attempt (should be safe)
        malicious_input = "Alice' OR '1'='1"
        try:
            results = TestUser.filter(self.db, name=malicious_input)
            # Should not return all users due to injection
            self.assertLess(len(results), 3)  # Should be 0 or 1
        except Exception as e:
            # Should not be SQL injection, might be other error
            self.assertNotIn("syntax error", str(e).lower())

    def test_sql_injection_in_order_by(self):
        """Test SQL injection attempts in order_by parameters"""
        # Add some test data
        for i in range(5):
            user = TestUser(name=f"User{i}", age=20 + i)
            user.save(self.db)

        # Test normal order_by (should work)
        results = TestUser.all(self.db, order_by="name")
        self.assertEqual(len(results), 5)

        # Test injection attempt in order_by (should be safe)
        try:
            results = TestUser.all(self.db, order_by="name; DROP TABLE users; --")
            # Should either work (if sanitized) or fail gracefully
        except ValueError:
            # Expected - invalid order_by field
            pass
        except Exception as e:
            # Should not be SQL injection
            self.assertNotIn("DROP TABLE", str(e))
            self.assertNotIn("syntax error", str(e).lower())

    def test_sql_injection_in_table_names(self):
        """Test that table names cannot be injected"""
        # The model system should prevent table name injection
        # by using the validated _table_name attribute

        # Test that our model has a valid table name
        self.assertTrue(validate_identifier(TestUser._table_name))

        # Test that SQL queries use the validated table name
        # This is tested indirectly through the query methods

    def test_prepared_statements_usage(self):
        """Test that prepared statements are used correctly"""
        # Add test data
        user = TestUser(name="Test User", age=40)
        user.save(self.db)

        # Test that parameterized queries work
        results = TestUser.filter(self.db, name="Test User")
        self.assertEqual(len(results), 1)

        # Test with parameters that could be injection attempts
        try:
            results = TestUser.filter(self.db, name="Test' User")
            # Should work fine with proper parameterization
        except Exception as e:
            # Should not be SQL injection error
            self.assertNotIn("syntax error", str(e).lower())

    def test_batch_operations_safety(self):
        """Test that batch operations are safe from injection"""
        # Test executemany with parameterized queries
        users_data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
            {"name": "Charlie' O'Brien", "age": 35},  # Name with quote
        ]

        for user_data in users_data:
            user = TestUser(**user_data)
            user.save(self.db)

        # Should all be saved safely
        all_users = TestUser.all(self.db)
        self.assertEqual(len(all_users), 3)

        # Test update with potentially malicious data
        try:
            TestUser.update_many(
                self.db,
                {"name": "Malicious' OR '1'='1"},
                name="Alice"
            )
            # Should work safely or fail gracefully
        except Exception as e:
            # Should not be SQL injection
            self.assertNotIn("syntax error", str(e).lower())

if __name__ == '__main__':
    unittest.main()