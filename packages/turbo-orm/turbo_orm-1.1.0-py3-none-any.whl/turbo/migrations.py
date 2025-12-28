"""
Migration Engine - Schema Management & Auto-Diffing

Handles database schema versioning, auto-generation of migrations,
and applying upgrades/downgrades.
"""

import datetime
import json
import os
from .model import ModelMeta


class Migration:
    """Represents a single database migration"""

    def __init__(self, id, name, up_sql, down_sql, created_at=None):
        self.id = id
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.created_at = created_at or datetime.datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "up_sql": self.up_sql,
            "down_sql": self.down_sql,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
            up_sql=data["up_sql"],
            down_sql=data["down_sql"],
            created_at=data.get("created_at"),
        )


class MigrationManager:
    """Manages migrations for a database"""

    def __init__(self, db, migration_dir="migrations"):
        self.db = db
        self.migration_dir = migration_dir
        self.ensure_migration_table()

        if not os.path.exists(migration_dir):
            os.makedirs(migration_dir)

    def ensure_migration_table(self):
        """Create migrations table if not exists"""
        sql = """
            CREATE TABLE IF NOT EXISTS _migrations (
                id TEXT PRIMARY KEY,
                name TEXT,
                applied_at TIMESTAMP
            )
        """
        self.db.execute(sql)

    def get_applied_migrations(self):
        """Get list of applied migration IDs"""
        cursor = self.db.execute("SELECT id FROM _migrations ORDER BY applied_at")
        return {row["id"] for row in cursor.fetchall()}

    def create_migration(self, name, auto=True):
        """Create a new migration file"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        migration_id = f"{timestamp}_{name}"

        up_sql = []
        down_sql = []

        if auto:
            # Auto-detect changes
            up_sql, down_sql = self._diff_schema()

        if not up_sql and auto:
            print("No changes detected.")
            return None

        migration = Migration(migration_id, name, up_sql, down_sql)

        # Save to file
        filename = os.path.join(self.migration_dir, f"{migration_id}.json")
        with open(filename, "w") as f:
            json.dump(migration.to_dict(), f, indent=2)

        print(f"Created migration: {filename}")
        return migration

    def _diff_schema(self):
        """Compare Models with Database to generate SQL"""
        up_sql = []
        down_sql = []

        # Get all registered models
        models = ModelMeta._registry

        for table_name, model_cls in models.items():
            # Check if table exists
            cursor = self.db.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            if not cursor.fetchone():
                # Table doesn't exist - Create it
                # We can reuse Model.create_table logic but we need the SQL string
                # For now, let's extract the create logic or simulate it
                # Simplified:
                fields_sql = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
                for name, field in model_cls._fields.items():
                    if field.__class__.__name__ == "ManyToManyField":
                        continue
                    sql_type = field.get_sql_type()
                    definition = f'"{name}" {sql_type}'
                    if field.required:
                        definition += " NOT NULL"
                    fields_sql.append(definition)

                create_sql = f"CREATE TABLE {table_name} ({', '.join(fields_sql)})"
                up_sql.append(create_sql)
                down_sql.append(f"DROP TABLE {table_name}")

                # Indexes
                if hasattr(model_cls, "_indexes"):
                    # Add index creation SQL (simplified)
                    pass
            else:
                # Table exists - Check columns
                cursor = self.db.execute(f"PRAGMA table_info({table_name})")
                existing_columns = {row["name"] for row in cursor.fetchall()}

                for name, field in model_cls._fields.items():
                    if field.__class__.__name__ == "ManyToManyField":
                        continue

                    if name not in existing_columns:
                        # Add column
                        sql_type = field.get_sql_type()
                        definition = f'"{name}" {sql_type}'
                        # SQLite ADD COLUMN limitation: cannot add NOT NULL without default
                        # We'll assume nullable or default for now
                        up_sql.append(
                            f"ALTER TABLE {table_name} ADD COLUMN {definition}"
                        )
                        # SQLite doesn't support DROP COLUMN in older versions, but modern does
                        down_sql.append(f"ALTER TABLE {table_name} DROP COLUMN {name}")

        return up_sql, down_sql

    def apply_migrations(self):
        """Apply all pending migrations"""
        applied = self.get_applied_migrations()

        # Get all migration files
        files = sorted(
            [f for f in os.listdir(self.migration_dir) if f.endswith(".json")]
        )

        count = 0
        for filename in files:
            with open(os.path.join(self.migration_dir, filename), "r") as f:
                data = json.load(f)
                migration = Migration.from_dict(data)

            if migration.id not in applied:
                print(f"Applying {migration.id}...")

                # Run UP SQL
                for sql in migration.up_sql:
                    self.db.execute(sql)

                # Record as applied
                self.db.execute(
                    "INSERT INTO _migrations (id, name, applied_at) VALUES (?, ?, ?)",
                    (migration.id, migration.name, datetime.datetime.now()),
                )
                count += 1

        if count > 0:
            print(f"Applied {count} migrations.")
        else:
            print("Database is up to date.")
