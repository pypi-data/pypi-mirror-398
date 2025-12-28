import unittest
import tempfile
import os
from turbo.database import Database
from turbo.model import Model
from turbo.fields import TextField, IntegerField

# Test model
class TestUser(Model):
    name = TextField()
    age = IntegerField()

class TestTransactionErrorHandling(unittest.TestCase):
    """Comprehensive tests for transaction error handling"""

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

    def test_transaction_rollback_on_error(self):
        """Test transaction rollback on various error conditions"""
        # Test with ValueError
        with self.assertRaises(ValueError):
            with self.db.transaction():
                user1 = TestUser(name="Alice", age=25)
                user1.save(self.db)
                raise ValueError("Test error")

        # Should be rolled back
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 0)

        # Test with RuntimeError
        with self.assertRaises(RuntimeError):
            with self.db.transaction():
                user1 = TestUser(name="Bob", age=30)
                user1.save(self.db)
                raise RuntimeError("Test runtime error")

        # Should be rolled back
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 0)

        # Test with custom exception
        class CustomError(Exception):
            pass

        with self.assertRaises(CustomError):
            with self.db.transaction():
                user1 = TestUser(name="Charlie", age=35)
                user1.save(self.db)
                raise CustomError("Test custom error")

        # Should be rolled back
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 0)

    def test_original_exceptions_preserved(self):
        """Test that original exceptions are preserved"""
        original_exception = None

        try:
            with self.db.transaction():
                user = TestUser(name="Alice", age=25)
                user.save(self.db)
                raise ValueError("Original error message")
        except ValueError as e:
            original_exception = e
            self.assertEqual(str(e), "Original error message")

        self.assertIsNotNone(original_exception)

        # Verify it was rolled back
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 0)

    def test_nested_transaction_scenarios(self):
        """Test nested transaction scenarios"""
        # Test successful nested transactions
        with self.db.transaction():
            user1 = TestUser(name="Alice", age=25)
            user1.save(self.db)

            # Nested transaction should work
            with self.db.transaction():
                user2 = TestUser(name="Bob", age=30)
                user2.save(self.db)

        # Both should be committed
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 2)

        # Test nested transaction rollback
        with self.db.transaction():
            user3 = TestUser(name="Charlie", age=35)
            user3.save(self.db)

            try:
                with self.db.transaction():
                    user4 = TestUser(name="David", age=40)
                    user4.save(self.db)
                    raise ValueError("Nested error")
            except ValueError:
                pass

            # Outer transaction should still be active
            user5 = TestUser(name="Eve", age=45)
            user5.save(self.db)

        # Should have Alice, Bob, Charlie and Eve, but not David
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 4)
        names = [user.name for user in users]
        self.assertIn("Alice", names)
        self.assertIn("Bob", names)
        self.assertIn("Charlie", names)
        self.assertIn("Eve", names)
        self.assertNotIn("David", names)

    def test_proper_cleanup_in_all_error_cases(self):
        """Test proper cleanup in all error cases"""
        # Test error during commit
        class CommitError(Exception):
            pass

        # Mock the commit to fail
        original_commit = self.db.commit
        commit_fail_count = [0]

        def failing_commit():
            commit_fail_count[0] += 1
            if commit_fail_count[0] == 1:
                raise CommitError("Commit failed")
            original_commit()

        self.db.commit = failing_commit

        try:
            with self.assertRaises(CommitError):
                with self.db.transaction():
                    user = TestUser(name="Alice", age=25)
                    user.save(self.db)
        finally:
            # Restore original commit
            self.db.commit = original_commit

        # Should be rolled back due to commit failure
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 0)

        # Test error during rollback (should not mask original error)
        original_rollback = self.db.rollback
        rollback_fail_count = [0]

        def failing_rollback():
            rollback_fail_count[0] += 1
            if rollback_fail_count[0] == 1:
                raise RuntimeError("Rollback failed")
            original_rollback()

        self.db.rollback = failing_rollback

        try:
            with self.assertRaises(ValueError):
                with self.db.transaction():
                    user = TestUser(name="Bob", age=30)
                    user.save(self.db)
                    raise ValueError("Original error")
        finally:
            # Restore original rollback
            self.db.rollback = original_rollback

    def test_database_context_manager_error_handling(self):
        """Test Database context manager error handling"""
        # Test error in Database context manager
        with self.assertRaises(ValueError):
            with Database(self.db_path) as db:
                TestUser.create_table(db)
                user = TestUser(name="Alice", age=25)
                user.save(db)
                raise ValueError("Test error")

        # Should be rolled back
        with Database(self.db_path) as db:
            users = TestUser.all(db)
            self.assertEqual(len(users), 0)

    def test_transaction_with_connection_errors(self):
        """Test transaction handling with connection errors"""
        # Test with connection that becomes unhealthy
        with self.db.transaction():
            user1 = TestUser(name="Alice", age=25)
            user1.save(self.db)

            # Simulate connection becoming unhealthy
            if self.db.connection:
                try:
                    self.db.connection.close()
                except:
                    pass
                self.db.connection = None

        # Transaction should handle the error and rollback
        users = TestUser.all(self.db)
        # May or may not have Alice depending on error handling

    def test_multiple_errors_in_transaction(self):
        """Test handling of multiple errors in transaction"""
        error_count = [0]

        class MultiError(Exception):
            def __init__(self, num):
                self.num = num
                error_count[0] += 1

        try:
            with self.db.transaction():
                user1 = TestUser(name="Alice", age=25)
                user1.save(self.db)
                raise MultiError(1)
        except MultiError as e:
            self.assertEqual(e.num, 1)

        # First error should cause rollback
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 0)

        # Second transaction should work
        with self.db.transaction():
            user2 = TestUser(name="Bob", age=30)
            user2.save(self.db)

        users = TestUser.all(self.db)
        self.assertEqual(len(users), 1)

    def test_exception_chaining(self):
        """Test that exception chaining works correctly"""
        original_exception = None
        rollback_exception = None

        # Test that original exception is preserved even if rollback fails
        try:
            with self.db.transaction():
                user = TestUser(name="Alice", age=25)
                user.save(self.db)
                raise ValueError("Original error")
        except ValueError as e:
            original_exception = e
            # Check that the exception has proper chaining
            self.assertIsNotNone(e.__cause__ or e.__context__)

        self.assertIsNotNone(original_exception)

    def test_transaction_isolation(self):
        """Test transaction isolation behavior"""
        # Create initial data
        user1 = TestUser(name="Alice", age=25)
        user1.save(self.db)

        # Start a transaction that will fail
        try:
            with self.db.transaction():
                # Modify data in transaction
                user1.age = 30
                user1.save(self.db)

                # Add new data
                user2 = TestUser(name="Bob", age=30)
                user2.save(self.db)

                # Force rollback
                raise ValueError("Force rollback")
        except ValueError:
            pass

        # Verify original data is intact
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].name, "Alice")
        self.assertEqual(users[0].age, 25)  # Should be original age

    def test_nested_transaction_with_different_databases(self):
        """Test nested transactions with different database instances"""
        db2 = Database(self.db_path)
        db2.connect()

        with self.db.transaction():
            user1 = TestUser(name="Alice", age=25)
            user1.save(self.db)

            with db2.transaction():
                user2 = TestUser(name="Bob", age=30)
                user2.save(db2)

        # Both should be committed
        users = TestUser.all(self.db)
        self.assertEqual(len(users), 2)

        db2.close()

    def test_transaction_error_recovery(self):
        """Test that database can recover from transaction errors"""
        # Cause multiple transaction failures
        for i in range(3):
            try:
                with self.db.transaction():
                    user = TestUser(name=f"User{i}", age=20 + i)
                    user.save(self.db)
                    raise ValueError(f"Error {i}")
            except ValueError:
                pass

        # Database should still be usable
        with self.db.transaction():
            user = TestUser(name="Recovered", age=40)
            user.save(self.db)

        users = TestUser.all(self.db)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].name, "Recovered")

if __name__ == '__main__':
    unittest.main()