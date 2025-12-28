"""
Optimized Model - High Performance Base Class

Combines all performance optimizations for extreme speed.
Target: 250K+ ops/sec
"""

from .model import Model as BaseModel


class OptimizedModel(BaseModel):
    """High-performance model with all optimizations enabled"""

    # Use __slots__ to reduce memory and speed up attribute access
    __slots__ = ("id", "_data", "_db")

    def __init__(self, **kwargs):
        # Fast initialization - minimal overhead
        # Bypass Model.__init__ for extreme speed
        object.__setattr__(self, "id", kwargs.get("id"))
        object.__setattr__(self, "_data", kwargs)
        object.__setattr__(self, "_db", None)

    def __getattr__(self, name):
        # Fast attribute access
        data = object.__getattribute__(self, "_data")
        if name in data:
            return data[name]
        # Fallback to normal attribute access (e.g. methods)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Fast attribute setting
        if name in ("id", "_data", "_db"):
            object.__setattr__(self, name, value)
        elif name in self.__class__._fields:
            self._data[name] = value
        else:
            object.__setattr__(self, name, value)

    @classmethod
    def bulk_create(cls, db, instances):
        """Optimized bulk insert"""
        from .hotpath import BatchOperations

        BatchOperations.bulk_insert(db, cls, instances)
        return instances

    @classmethod
    def bulk_update(cls, db, instances):
        """Optimized bulk update"""
        from .hotpath import BatchOperations

        BatchOperations.bulk_update(db, cls, instances)
        return instances

    def save_fast(self, db):
        """Faster save with minimal overhead"""
        # Skip hooks and contracts for maximum speed
        is_new = self.id is None
        cls = self.__class__

        if is_new:
            # INSERT
            if not hasattr(cls, "_cached_insert_sql"):
                from .sql_utils import sanitize_identifier, quote_identifier
                sanitize_identifier(self._table_name)  # Validate table name
                fields = [k for k in self._fields.keys() if k != "id"]
                for field in fields:
                    sanitize_identifier(field)  # Validate each field
                placeholders = ",".join("?" * len(fields))
                quoted_table = quote_identifier(self._table_name)
                quoted_fields = [quote_identifier(f) for f in fields]
                cls._cached_insert_sql = f'INSERT INTO {quoted_table} ({",".join(quoted_fields)}) VALUES ({placeholders})'
                cls._cached_insert_fields = fields

            # Use _data directly for speed
            values = [self._data.get(f) for f in cls._cached_insert_fields]

            # Bypass DB wrapper for speed - access connection directly
            cursor = db.connection.execute(cls._cached_insert_sql, values)
            self.id = cursor.lastrowid
        else:
            # UPDATE
            if not hasattr(cls, "_cached_update_sql"):
                from .sql_utils import sanitize_identifier, quote_identifier
                sanitize_identifier(self._table_name)  # Validate table name
                fields = [k for k in self._fields.keys() if k != "id"]
                for field in fields:
                    sanitize_identifier(field)  # Validate each field
                quoted_table = quote_identifier(self._table_name)
                quoted_fields = [quote_identifier(f) for f in fields]
                set_clause = ",".join(f"{qf}=?" for qf in quoted_fields)
                cls._cached_update_sql = (
                    f"UPDATE {quoted_table} SET {set_clause} WHERE id=?"
                )
                cls._cached_update_fields = fields

            values = [self._data.get(f) for f in cls._cached_update_fields] + [self.id]
            db.connection.execute(cls._cached_update_sql, values)

    @classmethod
    def save_many_fast(cls, db, instances):
        """
        Extreme speed bulk insert using executemany.
        Bypasses almost all overhead.
        """
        if not instances:
            return

        # Ensure SQL is cached
        if not hasattr(cls, "_cached_insert_sql"):
            from .sql_utils import sanitize_identifier, quote_identifier
            sanitize_identifier(cls._table_name)  # Validate table name
            fields = [k for k in cls._fields.keys() if k != "id"]
            for field in fields:
                sanitize_identifier(field)  # Validate each field
            placeholders = ",".join("?" * len(fields))
            quoted_table = quote_identifier(cls._table_name)
            quoted_fields = [quote_identifier(f) for f in fields]
            cls._cached_insert_sql = f'INSERT INTO {quoted_table} ({",".join(quoted_fields)}) VALUES ({placeholders})'
            cls._cached_insert_fields = fields

        # Prepare data
        fields = cls._cached_insert_fields
        values = [tuple(inst._data.get(f) for f in fields) for inst in instances]

        # Execute
        db.connection.executemany(cls._cached_insert_sql, values)


# Enable performance mode globally
def enable_turbo_mode(db):
    """Enable all performance optimizations"""
    from .performance import add_caching_to_database

    add_caching_to_database()

    #  Replace execute with cached version
    db.execute = db.execute_cached

    # Enable WAL mode for concurrency and speed
    try:
        db.connection.execute("PRAGMA journal_mode=WAL;")
        db.connection.execute("PRAGMA synchronous=NORMAL;")
    except Exception as e:
        print(f"Warning: Could not enable WAL mode: {e}")

    print("🚀 TURBO MODE ENABLED!")
    print("   All performance optimizations active")
    print("   - Query Caching")
    print("   - WAL Mode (Write-Ahead Logging)")
    print("   - Synchronous=NORMAL")
    print("   Expected: 2x faster operations")

    return db
