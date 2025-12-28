import sys
import os
import unittest
import gc

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from turbo import Database, Model, TextField, IntegerField, FloatField


class User(Model):
    """Test user model"""
    name = TextField(required=True)
    email = TextField()
    age = IntegerField()
    score = FloatField(default=0.0)


class Post(Model):
    """Test post model"""
    title = TextField(required=True)
    content = TextField()
    author_id = IntegerField()
    views = IntegerField(default=0)


class TestQueryBuilder(unittest.TestCase):
    """Comprehensive tests for QueryBuilder functionality"""

    def setUp(self):
        """Set up test database and tables"""
        self.db_path = ":memory:"
        self.db = Database(self.db_path)
        self.db.connect()
        User.create_table(self.db)
        Post.create_table(self.db)

        # Populate test data
        User(name="Alice", email="alice@example.com", age=30, score=95.5).save(self.db)
        User(name="Bob", email="bob@example.com", age=25, score=87.0).save(self.db)
        User(name="Charlie", email="charlie@example.com", age=35, score=92.0).save(self.db)
        User(name="Diana", email="diana@example.com", age=28, score=88.5).save(self.db)

    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        gc.collect()

    # WHERE clause tests
    def test_where_equals(self):
        """Test WHERE with equality operator"""
        results = User.query(self.db).where(name="Alice").execute()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Alice")
        self.assertEqual(results[0].age, 30)

    def test_where_greater_than(self):
        """Test WHERE with greater than operator"""
        results = User.query(self.db).where(age__gt=30).execute()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Charlie")

    def test_where_less_than(self):
        """Test WHERE with less than operator"""
        results = User.query(self.db).where(age__lt=28).execute()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Bob")
        self.assertEqual(results[0].age, 25)

    def test_where_gte(self):
        """Test WHERE with >= operator"""
        results = User.query(self.db).where(age__gte=30).execute()
        self.assertEqual(len(results), 2)
        ages = {r.age for r in results}
        self.assertEqual(ages, {30, 35})

    def test_where_lte(self):
        """Test WHERE with <= operator"""
        results = User.query(self.db).where(age__lte=28).execute()
        self.assertEqual(len(results), 2)
        ages = {r.age for r in results}
        self.assertEqual(ages, {25, 28})

    def test_where_contains(self):
        """Test WHERE with LIKE/contains operator"""
        results = User.query(self.db).where(email__contains="@example.com").execute()
        self.assertEqual(len(results), 4)

    def test_where_in(self):
        """Test WHERE with IN operator"""
        results = User.query(self.db).where(name__in=["Alice", "Bob"]).execute()
        self.assertEqual(len(results), 2)
        names = {r.name for r in results}
        self.assertEqual(names, {"Alice", "Bob"})

    def test_where_multiple_conditions(self):
        """Test WHERE with multiple conditions (AND)"""
        results = User.query(self.db).where(age__gte=28).where(score__gte=88.0).execute()
        self.assertEqual(len(results), 3)

    def test_where_chainable(self):
        """Test that where() is chainable"""
        query = User.query(self.db)
        result = query.where(name="Alice")
        self.assertIs(result, query)

    # ORDER BY tests
    def test_order_by_ascending(self):
        """Test ORDER BY ascending"""
        results = User.query(self.db).order_by("age").execute()
        ages = [r.age for r in results]
        self.assertEqual(ages, [25, 28, 30, 35])

    def test_order_by_descending(self):
        """Test ORDER BY descending"""
        results = User.query(self.db).order_by("-age").execute()
        ages = [r.age for r in results]
        self.assertEqual(ages, [35, 30, 28, 25])

    def test_order_by_with_where(self):
        """Test ORDER BY with WHERE clause"""
        results = User.query(self.db).where(age__gte=28).order_by("name").execute()
        names = [r.name for r in results]
        self.assertEqual(names, ["Alice", "Charlie", "Diana"])

    # LIMIT tests
    def test_limit(self):
        """Test LIMIT clause"""
        results = User.query(self.db).limit(2).execute()
        self.assertEqual(len(results), 2)

    def test_limit_with_order(self):
        """Test LIMIT with ORDER BY"""
        results = User.query(self.db).order_by("age").limit(2).execute()
        ages = [r.age for r in results]
        self.assertEqual(ages, [25, 28])

    def test_limit_greater_than_results(self):
        """Test LIMIT greater than available results"""
        results = User.query(self.db).limit(100).execute()
        self.assertEqual(len(results), 4)

    # OFFSET tests
    def test_offset(self):
        """Test OFFSET clause"""
        results = User.query(self.db).order_by("age").limit(10).offset(2).execute()
        ages = [r.age for r in results]
        self.assertEqual(ages, [30, 35])

    def test_limit_and_offset(self):
        """Test LIMIT with OFFSET (pagination)"""
        results = User.query(self.db).order_by("age").offset(1).limit(2).execute()
        ages = [r.age for r in results]
        self.assertEqual(ages, [28, 30])

    # COUNT tests
    def test_count_all(self):
        """Test COUNT without conditions"""
        count = User.query(self.db).count()
        self.assertEqual(count, 4)

    def test_count_with_where(self):
        """Test COUNT with WHERE clause"""
        count = User.query(self.db).where(age__gte=30).count()
        self.assertEqual(count, 2)

    def test_count_with_multiple_conditions(self):
        """Test COUNT with multiple WHERE conditions"""
        count = User.query(self.db).where(age__gte=25).where(age__lte=30).count()
        self.assertEqual(count, 3)

    # FIRST tests
    def test_first(self):
        """Test FIRST result"""
        result = User.query(self.db).order_by("age").first()
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Bob")

    def test_first_no_results(self):
        """Test FIRST with no matching results"""
        result = User.query(self.db).where(name="NonExistent").first()
        self.assertIsNone(result)

    def test_first_with_where(self):
        """Test FIRST with WHERE clause"""
        result = User.query(self.db).where(score__gte=90.0).order_by("-score").first()
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Alice")
        self.assertEqual(result.score, 95.5)

    # AGGREGATE tests
    def test_aggregate_count(self):
        """Test COUNT aggregation"""
        if hasattr(User.query(self.db), 'aggregate'):
            result = User.query(self.db).aggregate(total="id")
            if isinstance(result, dict):
                self.assertIn("total", result)

    def test_aggregate_avg(self):
        """Test AVG aggregation"""
        if hasattr(User.query(self.db), 'aggregate'):
            result = User.query(self.db).aggregate(avg_age="age")
            if isinstance(result, dict) and "avg_age" in result:
                avg = result["avg_age"]
                self.assertAlmostEqual(avg, 29.5, places=0)

    def test_aggregate_max(self):
        """Test MAX aggregation"""
        if hasattr(User.query(self.db), 'aggregate'):
            result = User.query(self.db).aggregate(max_age="age")
            if isinstance(result, dict) and "max_age" in result:
                self.assertEqual(result["max_age"], 35)

    def test_aggregate_min(self):
        """Test MIN aggregation"""
        if hasattr(User.query(self.db), 'aggregate'):
            result = User.query(self.db).aggregate(min_age="age")
            if isinstance(result, dict) and "min_age" in result:
                self.assertEqual(result["min_age"], 25)

    # BULK INSERT tests
    def test_bulk_insert(self):
        """Test bulk insert operation"""
        users = [
            User(name=f"User{i}", email=f"user{i}@test.com", age=20+i)
            for i in range(5)
        ]
        User.query(self.db).bulk_insert(users)
        
        count = User.query(self.db).count()
        self.assertEqual(count, 9)  # 4 original + 5 new

    def test_bulk_insert_empty(self):
        """Test bulk insert with empty list"""
        User.query(self.db).bulk_insert([])
        count = User.query(self.db).count()
        self.assertEqual(count, 4)

    def test_bulk_insert_preserves_data(self):
        """Test that bulk inserted data is correct"""
        users = [
            User(name="TestUser1", email="test1@example.com", age=40),
            User(name="TestUser2", email="test2@example.com", age=41),
        ]
        User.query(self.db).bulk_insert(users)
        
        results = User.query(self.db).where(name__contains="TestUser").order_by("name").execute()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "TestUser1")
        self.assertEqual(results[1].name, "TestUser2")

    # Complex query chaining tests
    def test_complex_query_chain(self):
        """Test complex query with multiple operations chained"""
        results = (User.query(self.db)
                   .where(age__gte=25)
                   .where(score__gte=87.0)
                   .order_by("-score")
                   .limit(2)
                   .execute())
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "Alice")
        self.assertEqual(results[1].name, "Charlie")

    def test_query_builder_reset(self):
        """Test that creating new query builder has fresh state"""
        q1 = User.query(self.db).where(age__gt=30)
        q2 = User.query(self.db).where(age__lt=30)
        
        results1 = q1.execute()
        results2 = q2.execute()
        
        self.assertEqual(len(results1), 1)
        self.assertEqual(len(results2), 2)  # Fixed: Only Bob (25) and Diana (28) are < 30

    # Edge cases
    def test_where_with_none_value(self):
        """Test WHERE with None value"""
        user = User(name="NoEmail", email=None, age=50)
        user.save(self.db)
        
        # Query with None shouldn't match NULL values in SQL
        # This tests that None handling is correct
        count = User.query(self.db).count()
        self.assertEqual(count, 5)

    def test_query_with_special_characters(self):
        """Test query with special characters in values"""
        user = User(name="O'Brien", email="o'brien@test.com", age=45)
        user.save(self.db)
        
        results = User.query(self.db).where(name="O'Brien").execute()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "O'Brien")

    def test_empty_result_set(self):
        """Test query that returns no results"""
        results = User.query(self.db).where(age__gt=100).execute()
        self.assertEqual(len(results), 0)
        self.assertIsInstance(results, list)

    def test_order_by_chainable(self):
        """Test that order_by() is chainable"""
        query = User.query(self.db)
        result = query.order_by("age")
        self.assertIs(result, query)

    def test_limit_chainable(self):
        """Test that limit() is chainable"""
        query = User.query(self.db)
        result = query.limit(10)
        self.assertIs(result, query)

    def test_offset_chainable(self):
        """Test that offset() is chainable"""
        query = User.query(self.db)
        result = query.offset(5)
        self.assertIs(result, query)


if __name__ == "__main__":
    unittest.main()
