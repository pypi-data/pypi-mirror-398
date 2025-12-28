import sys
import os
import unittest
import gc

# Add the parent directory to sys.path to import lite_model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lite_model import (
    Database,
    Model,
    IntegerField,
    TextField,
    FloatField,
    BooleanField,
)


class User(Model):
    name = TextField(required=True)
    age = IntegerField()
    score = FloatField(default=0.0)


class TestLiteModel(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_db.sqlite"
        self.db = Database(self.db_path)
        self.db.connect()
        User.create_table(self.db)

    def tearDown(self):
        self.db.close()
        gc.collect()  # Force garbage collection to release file handles
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_crud(self):
        # Create
        user = User(name="Alice", age=30)
        user.save(self.db)
        self.assertIsNotNone(user.id)
        self.assertEqual(user.score, 0.0)  # Default value

        # Read
        fetched_user = User.get(self.db, user.id)
        self.assertIsNotNone(fetched_user)
        self.assertEqual(fetched_user.name, "Alice")
        self.assertEqual(fetched_user.age, 30)

        # Update
        user.age = 31
        user.save(self.db)

        fetched_user_updated = User.get(self.db, user.id)
        self.assertEqual(fetched_user_updated.age, 31)

        # Delete
        user.delete(self.db)
        fetched_user_deleted = User.get(self.db, user.id)
        self.assertIsNone(fetched_user_deleted)

    def test_all(self):
        User(name="Bob", age=25).save(self.db)
        User(name="Charlie", age=35).save(self.db)

        users = User.all(self.db)
        self.assertEqual(len(users), 2)

    def test_filter(self):
        User(name="Alice", age=30).save(self.db)
        User(name="Bob", age=25).save(self.db)
        User(name="Charlie", age=30).save(self.db)

        users_30 = User.filter(self.db, age=30)
        self.assertEqual(len(users_30), 2)
        self.assertEqual(users_30[0].name, "Alice")
        self.assertEqual(users_30[1].name, "Charlie")

        users_alice = User.filter(self.db, name="Alice")
        self.assertEqual(len(users_alice), 1)
        self.assertEqual(users_alice[0].age, 30)

    def test_foreign_key(self):
        from lite_model import ForeignKey

        class Post(Model):
            title = TextField()
            user_id = ForeignKey("user")

        Post.create_table(self.db)

        user = User(name="Blogger", age=25)
        user.save(self.db)

        post = Post(title="My First Post", user_id=user.id)
        post.save(self.db)

        fetched_post = Post.get(self.db, post.id)
        self.assertEqual(fetched_post.user_id, user.id)

    def test_boolean(self):
        from lite_model import BooleanField

        class ActiveUser(Model):
            is_active = BooleanField()

        ActiveUser.create_table(self.db)

        u1 = ActiveUser(is_active=True)
        u1.save(self.db)

        u2 = ActiveUser(is_active=False)
        u2.save(self.db)

        self.assertTrue(ActiveUser.get(self.db, u1.id).is_active)
        self.assertFalse(ActiveUser.get(self.db, u2.id).is_active)

    def test_advanced_querying(self):
        User(name="A", age=10).save(self.db)
        User(name="B", age=30).save(self.db)
        User(name="C", age=20).save(self.db)

        # Ordering
        users = User.all(self.db, order_by="age")
        self.assertEqual([u.age for u in users], [10, 20, 30])

        users_desc = User.all(self.db, order_by="-age")
        self.assertEqual([u.age for u in users_desc], [30, 20, 10])

        # Limit
        users_limit = User.all(self.db, limit=2)
        self.assertEqual(len(users_limit), 2)

        # First
        first = User.first(self.db, order_by="age")
        self.assertEqual(first.age, 10)

        none_user = User.first(self.db, name="NonExistent")
        self.assertIsNone(none_user)

    def test_datetime(self):
        from lite_model import DateTimeField
        import datetime

        class Event(Model):
            when = DateTimeField()

        Event.create_table(self.db)

        now = datetime.datetime.now()
        e = Event(when=now)
        e.save(self.db)

        fetched = Event.get(self.db, e.id)
        self.assertIsInstance(fetched.when, datetime.datetime)
        self.assertEqual(fetched.when.isoformat(), now.isoformat())

    def test_validation(self):
        class ValidatedUser(Model):
            age = IntegerField()

            def validate(self):
                if self.age < 0:
                    raise ValueError("Age cannot be negative")

        ValidatedUser.create_table(self.db)

        u = ValidatedUser(age=-5)
        with self.assertRaises(ValueError):
            u.save(self.db)

    def test_hooks(self):
        class HookedModel(Model):
            name = TextField()

            def before_save(self, db):
                self.name = "Modified"

        HookedModel.create_table(self.db)

        m = HookedModel(name="Original")
        m.save(self.db)

        fetched = HookedModel.get(self.db, m.id)
        self.assertEqual(fetched.name, "Modified")

    def test_json(self):
        from lite_model import JSONField

        class Config(Model):
            data = JSONField()

        Config.create_table(self.db)

        c = Config(data={"key": "value", "list": [1, 2, 3]})
        c.save(self.db)

        fetched = Config.get(self.db, c.id)
        self.assertEqual(fetched.data["key"], "value")
        self.assertEqual(fetched.data["list"], [1, 2, 3])

    def test_count(self):
        User(name="A", age=10).save(self.db)
        User(name="B", age=10).save(self.db)
        User(name="C", age=20).save(self.db)

        self.assertEqual(User.count(self.db), 3)
        self.assertEqual(User.count(self.db, age=10), 2)

    def test_bulk_ops(self):
        User(name="A", age=10).save(self.db)
        User(name="B", age=10).save(self.db)
        User(name="C", age=20).save(self.db)

        # Update Many
        User.update_many(self.db, updates={"age": 15}, age=10)
        self.assertEqual(User.count(self.db, age=15), 2)
        self.assertEqual(User.count(self.db, age=10), 0)

        # Delete Many
        User.delete_many(self.db, age=15)
        self.assertEqual(User.count(self.db), 1)

    def test_time_travel(self):
        from lite_model import HistoryModel

        class Document(HistoryModel):
            content = TextField()

        Document.create_table(self.db)

        doc = Document(content="Draft 1")
        doc.save(self.db)

        doc.content = "Draft 2"
        doc.save(self.db)

        doc.content = "Final"
        doc.save(self.db)

        # Check history
        history = Document.history(self.db, doc.id)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["content"], "Final")
        self.assertEqual(history[1]["content"], "Draft 2")
        self.assertEqual(history[2]["content"], "Draft 1")

        # Revert to Draft 1
        draft_1_id = history[2]["history_id"]
        doc.revert(self.db, draft_1_id)

        fetched = Document.get(self.db, doc.id)
        self.assertEqual(fetched.content, "Draft 1")

        # Verify new history entry created for revert
        history_new = Document.history(self.db, doc.id)
        self.assertEqual(len(history_new), 4)
        self.assertEqual(history_new[0]["content"], "Draft 1")

    def test_search(self):
        from lite_model import SearchableModel

        class Article(SearchableModel):
            title = TextField()
            body = TextField()

        Article.create_table(self.db)

        Article(title="Python Guide", body="Python is a great language").save(self.db)
        Article(title="Cooking 101", body="How to cook pasta").save(self.db)
        Article(title="Tech News", body="New Python version released").save(self.db)

        # Search for "Python"
        results = Article.search(self.db, "Python")
        self.assertEqual(len(results), 2)
        titles = sorted([r.title for r in results])
        self.assertEqual(titles, ["Python Guide", "Tech News"])

        # Search for "pasta"
        results = Article.search(self.db, "pasta")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Cooking 101")

    def test_migration(self):
        # 1. Create table with initial schema
        class UserV1(Model):
            _table_name = "migrated_users"
            name = TextField()

        UserV1.create_table(self.db)
        UserV1(name="Alice").save(self.db)

        # 2. Define new model with added field
        class UserV2(Model):
            _table_name = "migrated_users"
            name = TextField()
            age = IntegerField()

        # 3. Migrate
        UserV2.migrate(self.db)

        # 4. Verify new field works
        UserV2(name="Bob", age=30).save(self.db)

        bob = UserV2.first(self.db, name="Bob")
        self.assertEqual(bob.age, 30)

        alice = UserV2.first(self.db, name="Alice")
        self.assertIsNone(alice.age)  # Should be None for existing records

    def test_relationships(self):
        from lite_model import ForeignKey, ManyToManyField

        class Author(Model):
            name = TextField()

        class Book(Model):
            title = TextField()
            author_id = ForeignKey("author")

        class Tag(Model):
            name = TextField()

        class Post(Model):
            title = TextField()
            tags = ManyToManyField("tag")

        Author.create_table(self.db)
        Book.create_table(self.db)
        Tag.create_table(self.db)
        Post.create_table(self.db)

        # Test ForeignKey traversal
        a = Author(name="J.K. Rowling")
        a.save(self.db)

        b = Book(title="Harry Potter", author_id=a.id)
        b.save(self.db)

        fetched_author = b.related(self.db, "author_id")
        self.assertEqual(fetched_author.name, "J.K. Rowling")

        # Test ManyToMany
        t1 = Tag(name="Tech")
        t1.save(self.db)
        t2 = Tag(name="News")
        t2.save(self.db)

        p = Post(title="New Release")
        p.save(self.db)

        p.m2m_add(self.db, "tags", t1)
        p.m2m_add(self.db, "tags", t2)

        tags = p.m2m_get(self.db, "tags")
        self.assertEqual(len(tags), 2)
        tag_names = sorted([t.name for t in tags])
        self.assertEqual(tag_names, ["News", "Tech"])

        p.m2m_remove(self.db, "tags", t1)
        tags = p.m2m_get(self.db, "tags")
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].name, "News")

    def test_encryption(self):
        from lite_model import EncryptedField

        class Secret(Model):
            api_key = EncryptedField(key="my_secret_key_123")

        Secret.create_table(self.db)

        s = Secret(api_key="super_secret_value_12345")
        s.save(self.db)

        # Fetch and verify decryption
        fetched = Secret.get(self.db, s.id)
        self.assertEqual(fetched.api_key, "super_secret_value_12345")

        # Verify it's actually encrypted in the database
        cursor = self.db.execute("SELECT api_key FROM secret WHERE id = ?", (s.id,))
        row = cursor.fetchone()
        encrypted_value = row[0]
        self.assertNotEqual(encrypted_value, "super_secret_value_12345")
        self.assertTrue(len(encrypted_value) > 0)

    def test_caching(self):
        # Create and save a user
        u = User(name="CacheTest", age=25)
        u.save(self.db)
        user_id = u.id

        # First get - should hit database and cache
        fetched1 = User.get(self.db, user_id)
        self.assertEqual(fetched1.name, "CacheTest")

        # Second get - should hit cache (we can verify by checking it's the same object)
        fetched2 = User.get(self.db, user_id)
        self.assertIs(fetched1, fetched2)  # Same object from cache

        # Update should update cache
        u.age = 30
        u.save(self.db)

        fetched3 = User.get(self.db, user_id)
        self.assertEqual(fetched3.age, 30)

        # Delete should remove from cache
        u.delete(self.db)
        fetched4 = User.get(self.db, user_id)
        self.assertIsNone(fetched4)

    def test_query_builder(self):
        User(name="Alice", age=25).save(self.db)
        User(name="Bob", age=30).save(self.db)
        User(name="Charlie", age=20).save(self.db)

        # Test where with operators
        results = User.query(self.db).where(age__gt=22).execute()
        self.assertEqual(len(results), 2)

        results = User.query(self.db).where(age__gte=25).execute()
        self.assertEqual(len(results), 2)

        results = User.query(self.db).where(name__contains="li").execute()
        self.assertEqual(len(results), 2)  # Alice and Charlie

        # Test chaining
        result = User.query(self.db).where(age__gt=20).order_by("-age").first()
        self.assertEqual(result.name, "Bob")

        # Test count
        count = User.query(self.db).where(age__gt=20).count()
        self.assertEqual(count, 2)

    def test_serialization(self):
        u = User(name="Alice", age=30)
        u.save(self.db)

        # to_dict
        data = u.to_dict()
        self.assertEqual(data["name"], "Alice")
        self.assertEqual(data["age"], 30)
        self.assertIn("id", data)

        # to_json
        json_str = u.to_json()
        self.assertIn("Alice", json_str)

        # from_dict
        new_user = User.from_dict({"id": 99, "name": "Bob", "age": 25})
        self.assertEqual(new_user.id, 99)
        self.assertEqual(new_user.name, "Bob")

    def test_pagination(self):
        for i in range(25):
            User(name=f"User{i}", age=20 + i).save(self.db)

        # Page 1
        page1 = User.paginate(self.db, page=1, per_page=10)
        self.assertEqual(len(page1.items), 10)
        self.assertEqual(page1.total, 25)
        self.assertEqual(page1.pages, 3)
        self.assertFalse(page1.has_prev)
        self.assertTrue(page1.has_next)

        # Page 2
        page2 = User.paginate(self.db, page=2, per_page=10)
        self.assertEqual(len(page2.items), 10)
        self.assertTrue(page2.has_prev)
        self.assertTrue(page2.has_next)

        # Page 3 (last)
        page3 = User.paginate(self.db, page=3, per_page=10)
        self.assertEqual(len(page3.items), 5)
        self.assertTrue(page3.has_prev)
        self.assertFalse(page3.has_next)

    def test_transactions(self):
        u1 = User(name="User1", age=10)
        u1.save(self.db)

        # Successful transaction
        with self.db.transaction():
            u2 = User(name="User2", age=20)
            u2.save(self.db)
            u3 = User(name="User3", age=30)
            u3.save(self.db)

        self.assertEqual(User.count(self.db), 3)

        # Rollback on error
        try:
            with self.db.transaction():
                u4 = User(name="User4", age=40)
                u4.save(self.db)
                raise Exception("Test rollback")
        except Exception:
            pass

        # User4 should not be saved due to rollback
        self.assertEqual(User.count(self.db), 3)

    def test_soft_delete(self):
        from lite_model import SoftDeleteModel

        class Document(SoftDeleteModel):
            title = TextField()

        Document.create_table(self.db)

        d1 = Document(title="Doc1")
        d1.save(self.db)
        d2 = Document(title="Doc2")
        d2.save(self.db)

        # Soft delete
        d1.delete(self.db)

        # Should not appear in normal queries
        all_docs = Document.all(self.db)
        self.assertEqual(len(all_docs), 1)
        self.assertEqual(all_docs[0].title, "Doc2")

        # But appears in with_trashed
        with_trashed = Document.with_trashed(self.db)
        self.assertEqual(len(with_trashed), 2)

        # Only trashed
        only_trashed = Document.only_trashed(self.db)
        self.assertEqual(len(only_trashed), 1)
        self.assertEqual(only_trashed[0].title, "Doc1")

        # Restore
        d1.restore(self.db)
        all_docs = Document.all(self.db)
        self.assertEqual(len(all_docs), 2)

    def test_eager_loading(self):
        from lite_model import ForeignKey

        class Author(Model):
            name = TextField()

        class Post(Model):
            title = TextField()
            author_id = ForeignKey("author")

        Author.create_table(self.db)
        Post.create_table(self.db)

        # Create test data
        a1 = Author(name="Alice")
        a1.save(self.db)
        a2 = Author(name="Bob")
        a2.save(self.db)

        Post(title="Post 1", author_id=a1.id).save(self.db)
        Post(title="Post 2", author_id=a1.id).save(self.db)
        Post(title="Post 3", author_id=a2.id).save(self.db)

        # Eager load authors
        posts = Post.query(self.db).with_("author_id").execute()

        # Check cached relationships
        self.assertTrue(hasattr(posts[0], "_author_id_cached"))
        self.assertEqual(posts[0]._author_id_cached.name, "Alice")
        self.assertEqual(posts[2]._author_id_cached.name, "Bob")

    def test_scopes(self):
        from lite_model import scope

        class Product(Model):
            name = TextField()
            price = FloatField()
            is_active = BooleanField()

            @scope
            def active(query):
                return query.where(is_active=True)

            @scope
            def expensive(query):
                return query.where(price__gt=100)

        Product.create_table(self.db)

        Product(name="Cheap Active", price=50, is_active=True).save(self.db)
        Product(name="Expensive Active", price=150, is_active=True).save(self.db)
        Product(name="Expensive Inactive", price=200, is_active=False).save(self.db)

        # Test individual scopes
        active = Product.active(self.db).execute()
        self.assertEqual(len(active), 2)

        expensive = Product.expensive(self.db).execute()
        self.assertEqual(len(expensive), 2)

        # Test chained scopes
        active_expensive = Product.active(self.db).expensive().execute()
        self.assertEqual(len(active_expensive), 1)
        self.assertEqual(active_expensive[0].name, "Expensive Active")

    def test_indexes(self):
        class IndexedUser(Model):
            email = TextField()
            username = TextField()
            age = IntegerField()

            class Meta:
                indexes = [
                    ("email", True),  # Unique index
                    "username",  # Simple index
                    ("username", "age"),  # Composite index
                ]

        IndexedUser.create_table(self.db)

        # Verify indexes were created by querying sqlite_master
        cursor = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='indexeduser'"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        # Check that our custom indexes exist
        self.assertTrue(any("email" in idx for idx in indexes))
        self.assertTrue(any("username" in idx for idx in indexes))

    def test_aggregations(self):
        User(name="Alice", age=25, score=85.5).save(self.db)
        User(name="Bob", age=30, score=92.0).save(self.db)
        User(name="Charlie", age=35, score=78.5).save(self.db)

        # Test aggregations
        result = User.query(self.db).aggregate(
            avg_age="age", max_score="score", min_score="score", count="*"
        )

        self.assertEqual(result["avg_age"], 30.0)
        self.assertEqual(result["max_score"], 92.0)
        self.assertEqual(result["min_score"], 78.5)
        self.assertEqual(result["count"], 3)

        # Test with WHERE clause
        result = User.query(self.db).where(age__gte=30).aggregate(avg_age="age")
        self.assertEqual(result["avg_age"], 32.5)

    def test_raw_sql(self):
        User(name="Alice", age=25).save(self.db)
        User(name="Bob", age=30).save(self.db)

        # Execute raw SQL
        results = User.raw(self.db, "SELECT * FROM user WHERE age > ?", (26,))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Bob")
        self.assertEqual(results[0].age, 30)

    def test_seeders(self):
        from lite_model import Seeder, SeederRegistry, seeder

        @seeder
        class UserSeeder(Seeder):
            def run(self, db):
                User(name="Seeded User 1", age=20).save(db)
                User(name="Seeded User 2", age=21).save(db)

        # Run all seeders
        SeederRegistry.run_all(self.db)

        # Verify seeded data
        users = User.all(self.db)
        seeded_names = [u.name for u in users if "Seeded" in u.name]
        self.assertEqual(len(seeded_names), 2)

    def test_multi_database(self):
        # Create a second database
        db2_path = "test_db2.sqlite"
        db2 = Database(db2_path)
        db2.connect()

        try:
            User.create_table(db2)

            # Add data to first database
            User(name="DB1 User", age=25).save(self.db)

            # Add data to second database using using()
            u2 = User(name="DB2 User", age=30)
            u2.save(db2)

            # Verify isolation
            db1_users = User.using(self.db).all()
            db2_users = User.using(db2).all()

            self.assertTrue(any(u.name == "DB1 User" for u in db1_users))
            self.assertTrue(any(u.name == "DB2 User" for u in db2_users))

        finally:
            db2.close()
            gc.collect()
            if os.path.exists(db2_path):
                os.remove(db2_path)

    def test_connection_pooling(self):
        # Create database with pooling
        pooled_db = Database("test_pool.db", pool_size=3)

        try:
            pooled_db.connect()
            User.create_table(pooled_db)
            pooled_db.close()

            # Verify pool has connection
            self.assertEqual(len(Database._pools.get("test_pool.db", [])), 1)

            # Connect again - should reuse
            pooled_db.connect()
            self.assertIsNotNone(pooled_db.connection)
            pooled_db.close()

        finally:
            # Cleanup pool
            if "test_pool.db" in Database._pools:
                for conn in Database._pools["test_pool.db"]:
                    conn.close()
                del Database._pools["test_pool.db"]
            gc.collect()
            if os.path.exists("test_pool.db"):
                os.remove("test_pool.db")


if __name__ == "__main__":
    unittest.main()
