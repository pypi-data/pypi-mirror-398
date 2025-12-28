import unittest
import inspect
from turbo.database import Database
from turbo.model import Model, ModelMeta
from turbo.sql_utils import validate_identifier, sanitize_identifier, sanitize_order_by_field, quote_identifier
from turbo.cache_redis import RedisCache, MockCursor, SmartRow

class TestDocumentationCompleteness(unittest.TestCase):
    """Comprehensive tests for documentation completeness"""

    def test_database_class_documentation(self):
        """Test that Database class has comprehensive documentation"""
        # Test class docstring
        self.assertIsNotNone(Database.__doc__)
        self.assertGreater(len(Database.__doc__), 50)  # Should be substantial

        # Test key methods have documentation
        methods_to_check = [
            'connect', 'close', 'execute', 'executemany', 'commit',
            'transaction', 'connection_context'
        ]

        for method_name in methods_to_check:
            method = getattr(Database, method_name)
            self.assertIsNotNone(method.__doc__, f"Method {method_name} should have docstring")

            # Check for key documentation sections
            doc = method.__doc__
            if method_name in ['execute', 'executemany']:
                self.assertIn("Args:", doc, f"Method {method_name} should document arguments")
                self.assertIn("Returns:", doc, f"Method {method_name} should document return value")
                self.assertIn("Raises:", doc, f"Method {method_name} should document exceptions")

    def test_model_class_documentation(self):
        """Test that Model class has comprehensive documentation"""
        # Test class docstring
        self.assertIsNotNone(Model.__doc__)
        self.assertGreater(len(Model.__doc__), 100)  # Should be substantial

        # Test metaclass documentation
        self.assertIsNotNone(ModelMeta.__doc__)
        self.assertGreater(len(ModelMeta.__doc__), 50)

        # Test key methods have documentation
        methods_to_check = [
            'save', 'validate', 'before_save', 'after_save', 'get', 'delete',
            'filter', 'all', 'first', 'count', 'create_table', 'query',
            '_cache_get', '_cache_set', '_cache_remove'
        ]

        for method_name in methods_to_check:
            method = getattr(Model, method_name)
            self.assertIsNotNone(method.__doc__, f"Method {method_name} should have docstring")

            # Check for key documentation sections in public methods
            if method_name in ['save', 'get', 'filter', 'all']:
                doc = method.__doc__
                if "Args:" not in doc and "Parameters:" not in doc:
                    self.assertIn("Args:", doc, f"Method {method_name} should document arguments")
                if "Returns:" not in doc:
                    self.assertIn("Returns:", doc, f"Method {method_name} should document return value")

    def test_sql_utils_documentation(self):
        """Test that SQL utilities have comprehensive documentation"""
        functions_to_check = [
            validate_identifier, sanitize_identifier,
            sanitize_order_by_field, quote_identifier
        ]

        for func in functions_to_check:
            self.assertIsNotNone(func.__doc__, f"Function {func.__name__} should have docstring")

            # Check for key documentation sections
            doc = func.__doc__
            self.assertIn("Args:", doc, f"Function {func.__name__} should document arguments")
            self.assertIn("Returns:", doc, f"Function {func.__name__} should document return value")

            # Check for Raises section where applicable
            if func.__name__ in ['sanitize_identifier', 'sanitize_order_by_field']:
                self.assertIn("Raises:", doc, f"Function {func.__name__} should document exceptions")

    def test_cache_classes_documentation(self):
        """Test that cache classes have comprehensive documentation"""
        # Test RedisCache class
        self.assertIsNotNone(RedisCache.__doc__)
        self.assertGreater(len(RedisCache.__doc__), 30)

        # Test MockCursor class
        self.assertIsNotNone(MockCursor.__doc__)
        self.assertGreater(len(MockCursor.__doc__), 20)

        # Test SmartRow class
        self.assertIsNotNone(SmartRow.__doc__)
        self.assertGreater(len(SmartRow.__doc__), 20)

        # Test key methods
        methods_to_check = ['get', 'set', 'clear', '_make_key']
        for method_name in methods_to_check:
            method = getattr(RedisCache, method_name)
            self.assertIsNotNone(method.__doc__, f"RedisCache.{method_name} should have docstring")

    def test_extension_points_documentation(self):
        """Test that extension points and hooks are properly documented"""
        # Test that Model class documents extension points
        model_doc = Model.__doc__
        self.assertIn("Extension Points:", model_doc, "Model should document extension points")

        # Test that key extension methods are documented
        extension_methods = ['validate', 'before_save', 'after_save']
        for method_name in extension_methods:
            method = getattr(Model, method_name)
            self.assertIsNotNone(method.__doc__, f"Extension method {method_name} should have docstring")

            # These should mention they can be overridden
            doc = method.__doc__
            self.assertIn("override", doc.lower() or "extend", "Should mention this can be overridden")

    def test_method_level_documentation_completeness(self):
        """Test that method-level documentation is complete and accurate"""
        # Test Database.execute method
        execute_doc = Database.execute.__doc__
        self.assertIn("sql", execute_doc, "Should document sql parameter")
        self.assertIn("params", execute_doc, "Should document params parameter")
        self.assertIn("timeout", execute_doc, "Should document timeout parameter")
        self.assertIn("sqlite3.Cursor", execute_doc, "Should document return type")
        self.assertIn("ConnectionError", execute_doc, "Should document ConnectionError")
        self.assertIn("TimeoutError", execute_doc, "Should document TimeoutError")

        # Test Model.save method
        save_doc = Model.save.__doc__
        self.assertIn("db", save_doc, "Should document db parameter")
        self.assertIn("validate", save_doc.lower(), "Should mention validation")
        self.assertIn("cache", save_doc.lower(), "Should mention caching")

        # Test Model.query method
        query_doc = Model.query.__doc__
        self.assertIn("QueryBuilder", query_doc, "Should mention QueryBuilder")
        self.assertIn("fluent", query_doc.lower() or "chain", "Should mention fluent API")

    def test_usage_examples_in_documentation(self):
        """Test that documentation includes usage examples"""
        # Test Database class has usage examples
        db_doc = Database.__doc__
        self.assertIn("Example:", db_doc or "Usage:", "Should include usage examples")

        # Test Model class has usage examples
        model_doc = Model.__doc__
        self.assertIn("Example:", model_doc or "Usage:", "Should include usage examples")

        # Test Transaction class has usage examples
        from turbo.database import Transaction
        transaction_doc = Transaction.__doc__
        self.assertIn("Example:", transaction_doc or "Usage:", "Should include usage examples")

        # Test key methods have examples
        execute_doc = Database.execute.__doc__
        self.assertIn("Example:", execute_doc or "Usage:", "Should include usage examples")

    def test_type_information_in_docstrings(self):
        """Test that docstrings include type information"""
        # Test Database.execute
        execute_doc = Database.execute.__doc__
        self.assertIn("str", execute_doc, "Should mention string types")
        self.assertIn("sqlite3.Cursor", execute_doc, "Should mention return type")

        # Test Model.save
        save_doc = Model.save.__doc__
        self.assertIn("Database", save_doc, "Should mention Database type")

        # Test Model.get
        get_doc = Model.get.__doc__
        self.assertIn("int", get_doc, "Should mention int type for id")

    def test_documentation_consistency(self):
        """Test that documentation is consistent across related methods"""
        # Compare filter and all methods
        filter_doc = Model.filter.__doc__
        all_doc = Model.all.__doc__

        # Both should mention similar concepts
        self.assertIn("order_by", filter_doc, "filter should document order_by")
        self.assertIn("order_by", all_doc, "all should document order_by")

        # Both should mention return types
        self.assertIn("List", filter_doc or "list", "filter should mention list return")
        self.assertIn("List", all_doc or "list", "all should mention list return")

    def test_private_methods_documentation(self):
        """Test that even private methods have documentation"""
        # Test cache methods
        cache_methods = ['_cache_get', '_cache_set', '_cache_remove', '_get_cache_key']
        for method_name in cache_methods:
            method = getattr(Model, method_name)
            self.assertIsNotNone(method.__doc__, f"Private method {method_name} should have docstring")

            # Should mention thread safety for cache methods
            if method_name.startswith('_cache_'):
                doc = method.__doc__
                self.assertIn("thread", doc.lower() or "lock", "Cache methods should mention thread safety")

    def test_documentation_for_new_features(self):
        """Test that new features have proper documentation"""
        # Test connection_context method
        context_doc = Database.connection_context.__doc__
        self.assertIsNotNone(context_doc, "connection_context should have docstring")
        self.assertIn("Context manager", context_doc, "Should mention context manager")
        self.assertIn("Yields:", context_doc or "Returns:", "Should document what it yields")

        # Test Transaction class
        from turbo.database import Transaction
        transaction_doc = Transaction.__doc__
        self.assertIsNotNone(transaction_doc, "Transaction class should have docstring")
        self.assertIn("commit", transaction_doc.lower(), "Should mention commit behavior")
        self.assertIn("rollback", transaction_doc.lower(), "Should mention rollback behavior")

    def test_error_documentation(self):
        """Test that error conditions are well documented"""
        # Test Database.execute documents errors
        execute_doc = Database.execute.__doc__
        self.assertIn("Raises:", execute_doc, "Should have Raises section")
        self.assertIn("ConnectionError", execute_doc, "Should document ConnectionError")

        # Test Model.save documents errors
        save_doc = Model.save.__doc__
        self.assertIn("Raises:", save_doc or "Exception", "Should mention exceptions")

        # Test that exceptions include context
        execute_doc = Database.execute.__doc__
        self.assertIn("unhealthy", execute_doc.lower(), "Should mention connection health")

    def test_documentation_coverage(self):
        """Test that all public methods have documentation"""
        # Check Database class
        db_methods = [method for method in dir(Database)
                     if not method.startswith('_') and callable(getattr(Database, method))]

        for method_name in db_methods:
            method = getattr(Database, method_name)
            self.assertIsNotNone(method.__doc__, f"Database.{method_name} should have docstring")

        # Check Model class (excluding metaclass methods)
        model_methods = [method for method in dir(Model)
                        if not method.startswith('_') and callable(getattr(Model, method))
                        and method not in ['__init__', '__new__', '__class__']]

        for method_name in model_methods:
            method = getattr(Model, method_name)
            # Some methods might be properties or descriptors
            if hasattr(method, '__doc__'):
                self.assertIsNotNone(method.__doc__, f"Model.{method_name} should have docstring")

if __name__ == '__main__':
    unittest.main()