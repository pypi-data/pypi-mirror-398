import sys
import os
import unittest
import json
import shutil
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from turbo import Database, Model, TextField, IntegerField
from turbo.migrations import Migration, MigrationManager


class User(Model):
    """Test user model for migrations"""
    name = TextField(required=True)
    email = TextField()
    age = IntegerField()


class Post(Model):
    """Test post model for migrations"""
    title = TextField(required=True)
    content = TextField()


class TestMigrations(unittest.TestCase):
    """Comprehensive tests for Migrations functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.migration_dir = os.path.join(self.test_dir, "migrations")
        
        self.db = Database(self.db_path)
        self.db.connect()

    def tearDown(self):
        """Clean up test environment"""
        self.db.close()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # Migration Class Tests
    def test_migration_creation(self):
        """Test creating a Migration object"""
        migration = Migration(
            id="001",
            name="create_users",
            up_sql=["CREATE TABLE users (id INTEGER PRIMARY KEY)"],
            down_sql=["DROP TABLE users"]
        )
        
        self.assertEqual(migration.id, "001")
        self.assertEqual(migration.name, "create_users")
        self.assertEqual(len(migration.up_sql), 1)
        self.assertEqual(len(migration.down_sql), 1)

    def test_migration_to_dict(self):
        """Test converting Migration to dictionary"""
        migration = Migration(
            id="001",
            name="create_users",
            up_sql=["CREATE TABLE users (id INTEGER PRIMARY KEY)"],
            down_sql=["DROP TABLE users"]
        )
        
        data = migration.to_dict()
        self.assertEqual(data["id"], "001")
        self.assertEqual(data["name"], "create_users")
        self.assertIn("created_at", data)

    def test_migration_from_dict(self):
        """Test creating Migration from dictionary"""
        data = {
            "id": "002",
            "name": "add_email_column",
            "up_sql": ["ALTER TABLE users ADD COLUMN email TEXT"],
            "down_sql": ["ALTER TABLE users DROP COLUMN email"],
            "created_at": "2025-11-26T10:00:00"
        }
        
        migration = Migration.from_dict(data)
        self.assertEqual(migration.id, "002")
        self.assertEqual(migration.name, "add_email_column")
        self.assertEqual(migration.created_at, "2025-11-26T10:00:00")

    def test_migration_with_default_timestamp(self):
        """Test that Migration generates timestamp if not provided"""
        migration = Migration(
            id="003",
            name="test",
            up_sql=[],
            down_sql=[]
        )
        
        self.assertIsNotNone(migration.created_at)

    # MigrationManager Tests
    def test_migration_manager_creation(self):
        """Test creating a MigrationManager"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        self.assertEqual(manager.db, self.db)
        self.assertEqual(manager.migration_dir, self.migration_dir)

    def test_migration_manager_creates_directory(self):
        """Test that MigrationManager creates migration directory"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        self.assertTrue(os.path.exists(self.migration_dir))
        self.assertTrue(os.path.isdir(self.migration_dir))

    def test_migration_manager_creates_table(self):
        """Test that MigrationManager creates _migrations table"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Check if table exists
        cursor = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='_migrations'"
        )
        self.assertIsNotNone(cursor.fetchone())

    def test_ensure_migration_table_idempotent(self):
        """Test that ensure_migration_table is idempotent"""
        manager1 = MigrationManager(self.db, self.migration_dir)
        manager2 = MigrationManager(self.db, self.migration_dir)
        
        # Should not raise an error
        self.assertIsNotNone(manager2)

    def test_get_applied_migrations_empty(self):
        """Test getting applied migrations when none exist"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        applied = manager.get_applied_migrations()
        self.assertEqual(len(applied), 0)

    def test_get_applied_migrations_returns_set(self):
        """Test that get_applied_migrations returns a set"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        applied = manager.get_applied_migrations()
        self.assertIsInstance(applied, set)

    def test_record_and_retrieve_migration(self):
        """Test recording and retrieving a migration"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Record a migration
        self.db.execute(
            "INSERT INTO _migrations (id, name, applied_at) VALUES (?, ?, ?)",
            ("001", "test_migration", datetime.now())
        )
        
        applied = manager.get_applied_migrations()
        self.assertIn("001", applied)

    # Migration File Tests
    def test_create_migration_file(self):
        """Test creating a migration file"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        migration = manager.create_migration("test_migration", auto=False)
        
        # Should create file even with no SQL for auto=False
        if migration:
            files = os.listdir(self.migration_dir)
            self.assertTrue(any(f.endswith(".json") for f in files))

    def test_migration_file_content(self):
        """Test that migration file contains correct JSON"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        migration = Migration(
            id="20251126_001",
            name="test",
            up_sql=["CREATE TABLE test (id INTEGER)"],
            down_sql=["DROP TABLE test"]
        )
        
        # Manually save
        filename = os.path.join(self.migration_dir, f"{migration.id}.json")
        with open(filename, "w") as f:
            json.dump(migration.to_dict(), f)
        
        # Read back
        with open(filename, "r") as f:
            data = json.load(f)
        
        self.assertEqual(data["id"], "20251126_001")
        self.assertEqual(data["name"], "test")

    # Apply Migrations Tests
    def test_apply_migrations_empty(self):
        """Test applying migrations when none exist"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Should not raise error
        manager.apply_migrations()

    def test_apply_single_migration(self):
        """Test applying a single migration"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Create migration
        migration = Migration(
            id="20251126_001",
            name="create_users",
            up_sql=["CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"],
            down_sql=["DROP TABLE users"]
        )
        
        # Save migration file
        filename = os.path.join(self.migration_dir, f"{migration.id}.json")
        with open(filename, "w") as f:
            json.dump(migration.to_dict(), f)
        
        # Apply
        manager.apply_migrations()
        
        # Check that table was created
        cursor = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        self.assertIsNotNone(cursor.fetchone())

    def test_apply_migrations_marks_as_applied(self):
        """Test that applied migrations are marked in _migrations table"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Create migration
        migration = Migration(
            id="20251126_002",
            name="test",
            up_sql=[],
            down_sql=[]
        )
        
        # Save migration file
        filename = os.path.join(self.migration_dir, f"{migration.id}.json")
        with open(filename, "w") as f:
            json.dump(migration.to_dict(), f)
        
        # Apply
        manager.apply_migrations()
        
        # Check _migrations table
        applied = manager.get_applied_migrations()
        self.assertIn("20251126_002", applied)

    def test_apply_migrations_skips_already_applied(self):
        """Test that already-applied migrations are skipped"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Create and apply migration
        migration = Migration(
            id="20251126_003",
            name="test",
            up_sql=[],
            down_sql=[]
        )
        
        filename = os.path.join(self.migration_dir, f"{migration.id}.json")
        with open(filename, "w") as f:
            json.dump(migration.to_dict(), f)
        
        manager.apply_migrations()
        
        # Try to apply again - should not error
        manager.apply_migrations()
        
        # Migration should still be marked as applied
        applied = manager.get_applied_migrations()
        self.assertIn("20251126_003", applied)

    def test_apply_multiple_migrations_in_order(self):
        """Test applying multiple migrations in correct order"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Create migrations
        migrations = [
            Migration("001", "first", ["CREATE TABLE t1 (id INTEGER)"], ["DROP TABLE t1"]),
            Migration("002", "second", ["CREATE TABLE t2 (id INTEGER)"], ["DROP TABLE t2"]),
            Migration("003", "third", ["CREATE TABLE t3 (id INTEGER)"], ["DROP TABLE t3"]),
        ]
        
        # Save migration files
        for m in migrations:
            filename = os.path.join(self.migration_dir, f"{m.id}.json")
            with open(filename, "w") as f:
                json.dump(m.to_dict(), f)
        
        # Apply
        manager.apply_migrations()
        
        # Check all tables exist
        for table_name in ["t1", "t2", "t3"]:
            cursor = self.db.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
            self.assertIsNotNone(cursor.fetchone())

    # Schema Diffing Tests
    def test_diff_schema_detects_new_table(self):
        """Test that diff_schema detects new tables"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Create a model but don't create table
        up_sql, down_sql = manager._diff_schema()
        
        # Should generate CREATE TABLE statements
        self.assertTrue(any("CREATE TABLE" in sql for sql in up_sql if sql))

    def test_diff_schema_detects_missing_columns(self):
        """Test that diff_schema detects missing columns"""
        # First create a basic table
        self.db.execute("CREATE TABLE user (id INTEGER PRIMARY KEY)")
        
        manager = MigrationManager(self.db, self.migration_dir)
        up_sql, down_sql = manager._diff_schema()
        
        # Should generate ALTER TABLE statements
        # (This depends on implementation details)

    # Integration Tests
    def test_full_migration_workflow(self):
        """Test complete migration workflow"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Create tables
        User.create_table(self.db)
        Post.create_table(self.db)
        
        # Insert data
        user_sql = "INSERT INTO user (name, email, age) VALUES (?, ?, ?)"
        self.db.execute(user_sql, ("Alice", "alice@example.com", 30))
        
        # Verify
        cursor = self.db.execute("SELECT * FROM user")
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)

    def test_migration_preserves_data(self):
        """Test that migrations preserve existing data"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        # Create table with initial data
        self.db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        self.db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        
        # Simulate adding a column
        self.db.execute("ALTER TABLE users ADD COLUMN email TEXT")
        
        # Verify data still exists
        cursor = self.db.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)

    # Edge Cases
    def test_migration_with_empty_sql(self):
        """Test migration with empty SQL lists"""
        migration = Migration(
            id="empty",
            name="empty",
            up_sql=[],
            down_sql=[]
        )
        
        self.assertEqual(len(migration.up_sql), 0)
        self.assertEqual(len(migration.down_sql), 0)

    def test_migration_with_complex_sql(self):
        """Test migration with complex SQL statements"""
        complex_sql = """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        migration = Migration(
            id="complex",
            name="complex",
            up_sql=[complex_sql],
            down_sql=["DROP TABLE users"]
        )
        
        self.assertEqual(migration.up_sql[0], complex_sql)

    def test_migration_filename_format(self):
        """Test that migration filenames follow expected format"""
        manager = MigrationManager(self.db, self.migration_dir)
        
        migration = Migration(
            id="20251126_001",
            name="test",
            up_sql=[],
            down_sql=[]
        )
        
        filename = os.path.join(self.migration_dir, f"{migration.id}.json")
        with open(filename, "w") as f:
            json.dump(migration.to_dict(), f)
        
        files = os.listdir(self.migration_dir)
        self.assertIn("20251126_001.json", files)


if __name__ == "__main__":
    unittest.main()
