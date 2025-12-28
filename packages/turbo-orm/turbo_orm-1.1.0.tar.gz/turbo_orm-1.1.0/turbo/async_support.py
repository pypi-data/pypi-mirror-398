"""
Async support for lite_model ORM using aiosqlite
"""
import datetime
from typing import List, TypeVar, Type, Any, Tuple, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .database import Database

T = TypeVar('T', bound='AsyncModel')

try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False
    aiosqlite = None


class AsyncDatabase:
    """Async wrapper for aiosqlite database connections.
    
    Provides async context manager support for automatic connection management.
    """
    
    def __init__(self, path: str) -> None:
        """Initialize async database connection.
        
        Args:
            path: Path to SQLite database file
            
        Raises:
            ImportError: If aiosqlite is not installed
        """
        if not AIOSQLITE_AVAILABLE:
            raise ImportError(
                "aiosqlite is required for async support. Install with: pip install aiosqlite"
            )
        self.path = path
        self.connection: Optional[Any] = None

    async def connect(self) -> 'AsyncDatabase':
        """Connect to the async database.
        
        Returns:
            AsyncDatabase: Self for method chaining
        """
        self.connection = await aiosqlite.connect(self.path)
        self.connection.row_factory = aiosqlite.Row
        return self

    async def close(self) -> None:
        """Close the async database connection."""
        if self.connection:
            await self.connection.commit()
            await self.connection.close()
            self.connection = None

    async def execute(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> Any:
        """Execute a SQL statement asynchronously.
        
        Args:
            sql: The SQL statement to execute
            params: Optional parameters to substitute in the SQL statement
            
        Returns:
            Async cursor object
            
        Raises:
            ConnectionError: If database is not connected
        """
        if not self.connection:
            raise ConnectionError("Database not connected")
        if params:
            cursor = await self.connection.execute(sql, params)
        else:
            cursor = await self.connection.execute(sql)
        return cursor

    def execute_sync(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> Any:
        """Execute a SQL statement synchronously (for table creation).
        
        This is a workaround for sync operations that need to work with AsyncDatabase.
        Should only be used for DDL operations like CREATE TABLE.
        
        Args:
            sql: The SQL statement to execute
            params: Optional parameters to substitute in the SQL statement
            
        Returns:
            Cursor object
        """
        import sqlite3
        # Create a temporary sync connection for DDL operations
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        conn.close()
        return cursor

    async def executemany(self, sql: str, params: List[Tuple[Any, ...]]) -> Any:
        """Execute multiple statements with different parameters.
        
        Args:
            sql: The SQL statement to execute
            params: List of parameter tuples to substitute in the SQL statement
            
        Returns:
            Async cursor object
            
        Raises:
            ConnectionError: If database is not connected
        """
        if not self.connection:
            raise ConnectionError("Database not connected")
        cursor = await self.connection.executemany(sql, params)
        return cursor

    async def commit(self) -> None:
        """Commit pending transactions."""
        if self.connection:
            await self.connection.commit()

    async def __aenter__(self) -> 'AsyncDatabase':
        """Async context manager entry.
        
        Returns:
            AsyncDatabase: Self
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        """Async context manager exit with automatic transaction handling.
        
        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred
        """
        if exc_type:
            if self.connection:
                await self.connection.rollback()
        else:
            await self.commit()
        await self.close()


class AsyncModel:
    """
    Async version of Model - requires models to inherit from both Model and AsyncModel.
    
    Example:
        class User(Model, AsyncModel):
            name = TextField()

        async with AsyncDatabase("db.sqlite") as db:
            User.create_table(db)  # Still sync for table creation
            user = User(name="Alice")
            await user.async_save(db)
            fetched = await User.async_get(db, user.id)
    """

    async def async_save(self, db: 'AsyncDatabase') -> None:
        """Async version of save.
        
        Args:
            db: AsyncDatabase instance
        """
        self.validate()
        self.before_save(db)

        fields = [
            f
            for f in self._fields.keys()
            if self._fields[f].__class__.__name__ != "ManyToManyField"
        ]
        values: List[Any] = []
        for f in fields:
            val = getattr(self, f)
            field = self._fields[f]

            if isinstance(val, datetime.datetime):
                val = val.isoformat()
            elif field.__class__.__name__ == "JSONField" and not isinstance(val, str):
                import json
                val = json.dumps(val)
            elif field.__class__.__name__ == "EncryptedField":
                val = field.encrypt(val)

            values.append(val)

        placeholders = ", ".join(["?"] * len(fields))

        if self.id is None:
            from .sql_utils import sanitize_identifier, quote_identifier
            sanitize_identifier(self._table_name)  # Validate table name
            columns = ", ".join([f'"{f}"' for f in fields])
            sql = f"INSERT INTO {quote_identifier(self._table_name)} ({columns}) VALUES ({placeholders})"
            cursor = await db.execute(sql, values)
            self.id = cursor.lastrowid
        else:
            from .sql_utils import sanitize_identifier, quote_identifier
            sanitize_identifier(self._table_name)  # Validate table name
            set_clause = ", ".join([f'"{f}" = ?' for f in fields])
            sql = f"UPDATE {quote_identifier(self._table_name)} SET {set_clause} WHERE id = ?"
            await db.execute(sql, values + [self.id])

        self._cache_set(self.id, self)
        self.after_save(db)

    @classmethod
    async def async_get(cls, db: 'AsyncDatabase', id: int) -> Optional[T]:
        """Async version of get"""
        cached = cls._cache_get(id)
        if cached:
            return cached

        sql = f"SELECT * FROM {cls._table_name} WHERE id = ?"
        cursor = await db.execute(sql, (id,))
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            id_val = data.pop("id")
            instance = cls(**data)
            instance.id = id_val
            cls._cache_set(id_val, instance)
            return instance
        return None

    @classmethod
    async def async_all(cls: Type[T], db: 'AsyncDatabase', order_by: Optional[str] = None, limit: Optional[int] = None) -> List[T]:
        """Async version of all"""
        from .sql_utils import sanitize_identifier, quote_identifier
        sanitize_identifier(cls._table_name)  # Validate table name
        sql = f"SELECT * FROM {quote_identifier(cls._table_name)}"

        if order_by:
            from .sql_utils import sanitize_order_by_field
            order_by = sanitize_order_by_field(order_by)
            direction = "DESC" if order_by.startswith("-") else "ASC"
            column = order_by.lstrip("-")
            sql += f" ORDER BY {quote_identifier(column)} {direction}"

        if limit:
            sql += f" LIMIT {limit}"

        cursor = await db.execute(sql)
        instances: List[T] = []
        rows = await cursor.fetchall()
        for row in rows:
            data = dict(row)
            id_val = data.pop("id", None)
            instance = cls(**data)
            if id_val is not None:
                instance.id = id_val
            instances.append(instance)
        return instances

    @classmethod
    async def async_bulk_create(cls: Type[T], db: 'AsyncDatabase', instances: List[T]) -> List[T]:
        """Optimized async bulk creation of multiple instances"""
        if not instances:
            return instances

        # Get field names (excluding id and M2M fields)
        fields = [
            f
            for f in cls._fields.keys()
            if f != "id" and cls._fields[f].__class__.__name__ != "ManyToManyField"
        ]

        # Create SQL with placeholders
        placeholders = ", ".join(["?"] * len(fields))
        sql = f"INSERT INTO {cls._table_name} ({', '.join(fields)}) VALUES ({placeholders})"

        # Prepare data for executemany
        values: List[Tuple[Any, ...]] = []
        for instance in instances:
            instance_values: List[Any] = []
            for field_name in fields:
                value = getattr(instance, field_name, None)
                field = cls._fields[field_name]
                # Handle special field types
                if isinstance(value, datetime.datetime):
                    value = value.isoformat()
                elif field.__class__.__name__ == "JSONField" and not isinstance(value, str):
                    import json
                    value = json.dumps(value)
                elif field.__class__.__name__ == "EncryptedField":
                    value = field.encrypt(value)
                elif hasattr(field, "to_sql"):
                    value = field.to_sql(value)
                instance_values.append(value)
            values.append(tuple(instance_values))

        # Execute bulk insert
        await db.executemany(sql, values)

        # Update cache for each instance (id will be set by caller if needed)
        for instance in instances:
            if instance.id is not None:
                cls._cache_set(instance.id, instance)

        return instances
