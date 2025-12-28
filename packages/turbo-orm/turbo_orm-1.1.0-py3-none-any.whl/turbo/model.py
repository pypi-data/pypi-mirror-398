from .fields import Field
import datetime
import logging
import threading
from typing import Dict, Any, Optional, List, Union, Type, TypeVar, TYPE_CHECKING, cast

from .multi_db import ModelDatabaseProxy
from .sql_utils import sanitize_identifier, quote_identifier

if TYPE_CHECKING:
    from .query_builder import QueryBuilder
    from .pagination import Paginator
    from .database import Database

T = TypeVar('T', bound='Model')


class ModelMeta(type):
    """Metaclass for Model classes that provides ORM functionality.

    This metaclass handles:
    - Model registration and lookup via _registry
    - Field discovery and validation
    - Table name generation and validation
    - Scope method binding for query chaining
    - Index definition processing

    Attributes:
        _registry (Dict[str, Type['Model']]): Registry of all model classes by table name

    Extension Points:
        - Custom field types can be added by subclassing Field
        - Custom scopes can be defined as class methods with _is_scope attribute
        - Custom indexes can be defined via Meta.indexes
    """
    _registry: Dict[str, Type['Model']] = {}

    def __new__(cls, name: str, bases: tuple, attrs: dict) -> Any:
        if name == "Model":
            return super().__new__(cls, name, bases, attrs)

        fields: Dict[str, Field] = {}
        scopes: Dict[str, Any] = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                fields[key] = value
                value.name = key  # Set the field name
            elif hasattr(value, "_is_scope"):
                scopes[key] = value

        attrs["_fields"] = fields
        attrs["_scopes"] = scopes
        if "_table_name" not in attrs:
            # Validate table name
            from .sql_utils import sanitize_identifier
            table_name = name.lower()
            sanitize_identifier(table_name)
            attrs["_table_name"] = table_name

        # Handle Meta class for indexes
        meta = attrs.get("Meta")
        if meta:
            attrs["_indexes"] = getattr(meta, "indexes", [])
        else:
            attrs["_indexes"] = []

        new_class = super().__new__(cls, name, bases, attrs)
        cls._registry[attrs["_table_name"]] = new_class  # type: ignore

        # Bind scopes to class - they should return QueryBuilder
        for scope_name, scope_func in scopes.items():

            def make_scope_method(func):
                def scope_method(cls_or_self, db=None):
                    # If called on Model class
                    if isinstance(cls_or_self, type):
                        return func(cls_or_self.query(db))
                    # If called on QueryBuilder (for chaining)
                    else:
                        return func(cls_or_self)

                return scope_method

            bound_method = make_scope_method(scope_func)
            setattr(new_class, scope_name, classmethod(bound_method))

        return new_class  # type: ignore[return-value]


class Model(metaclass=ModelMeta):
    """Base Model class for ORM functionality.

    This class provides the core ORM functionality including:
    - Database persistence (create, read, update, delete)
    - Field validation and type conversion
    - Relationship management (ForeignKey, ManyToMany)
    - Query building and execution
    - Caching and performance optimization
    - Lifecycle hooks (validate, before_save, after_save)

    Class Attributes:
        _cache (Dict[str, Dict[int, 'Model']]): Class-level cache for model instances
        _cache_lock (threading.Lock): Thread-safe lock for cache operations
        _fields (Dict[str, Field]): Model field definitions
        _table_name (str): Database table name
        _scopes (Dict[str, Any]): Query scope methods
        _indexes (List): Database index definitions

    Instance Attributes:
        id (Optional[int]): Primary key identifier

    Extension Points:
        - Override validate(), before_save(), after_save() for lifecycle hooks
        - Define custom field types by subclassing Field
        - Add query scopes as class methods with _is_scope attribute
        - Define indexes via Meta.indexes in subclass

    Example:
        class User(Model):
            name = fields.CharField()
            email = fields.EmailField(unique=True)

            def validate(self):
                if not self.email or '@' not in self.email:
                    raise ValueError("Invalid email format")
    """
    _cache: Dict[str, Dict[int, 'Model']] = {}  # Class-level cache: {table_name: {id: instance}}
    _cache_lock: threading.Lock = threading.Lock()  # Thread-safe lock for cache operations
    _fields: Dict[str, Field]
    _table_name: str
    _scopes: Dict[str, Any]
    _indexes: List[Any]
    id: Optional[int]

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            # Validate field name
            from .sql_utils import sanitize_identifier
            sanitize_identifier(key)
            if key not in self._fields:
                raise ValueError(f"Invalid field: {key}")
            setattr(self, key, value)

        # Set defaults
        for name, field in self._fields.items():
            # Validate field name
            sanitize_identifier(name)
            if name not in kwargs:
                if field.default is not None:
                    setattr(self, name, field.default)
                else:
                    setattr(self, name, None)

            # Auto-convert strings to datetime objects if applicable
            val = getattr(self, name)
            if val and field.get_sql_type() == "TEXT" and isinstance(val, str):
                if field.__class__.__name__ == "DateTimeField":
                    try:
                        setattr(self, name, datetime.datetime.fromisoformat(val))
                    except ValueError:
                        pass
                elif field.__class__.__name__ == "JSONField":
                    import json

                    try:
                        setattr(self, name, json.loads(val))
                    except json.JSONDecodeError:
                        pass
                elif field.__class__.__name__ == "EncryptedField":
                    try:
                        setattr(self, name, field.decrypt(val))
                    except Exception:
                        pass

        self.id = None

    @classmethod
    def _get_cache_key(cls: Type[T]) -> str:
        """Get the cache key for this model class.

        Returns:
            str: Cache key based on the model's table name
        """
        return cls._table_name

    @classmethod
    def _cache_get(cls: Type[T], id: int) -> Optional[T]:
        """Get a model instance from cache by ID.

        Args:
            id: The primary key ID of the model instance

        Returns:
            Optional[T]: Cached model instance or None if not found

        Note:
            This method is thread-safe using the class-level cache lock.
        """
        cache_key = cls._get_cache_key()
        with cls._cache_lock:
            if cache_key in cls._cache and id in cls._cache[cache_key]:
                cached = cls._cache[cache_key][id]
                # Type cast for the type checker
                return cast(T, cached)
        return None

    @classmethod
    def _cache_set(cls: Type[T], id: int, instance: T) -> None:
        """Set a model instance in cache.

        Args:
            id: The primary key ID of the model instance
            instance: The model instance to cache

        Note:
            This method is thread-safe using the class-level cache lock.
        """
        cache_key = cls._get_cache_key()
        with cls._cache_lock:
            if cache_key not in cls._cache:
                cls._cache[cache_key] = {}
            cls._cache[cache_key][id] = instance

    @classmethod
    def _cache_remove(cls: Type[T], id: int) -> None:
        """Remove a model instance from cache.

        Args:
            id: The primary key ID of the model instance to remove

        Note:
            This method is thread-safe using the class-level cache lock.
        """
        cache_key = cls._get_cache_key()
        with cls._cache_lock:
            if cache_key in cls._cache and id in cls._cache[cache_key]:
                del cls._cache[cache_key][id]

    @classmethod
    def create_table(cls: Type[T], db: 'Database') -> None:
        # Validate table name
        sanitize_identifier(cls._table_name)
        fields_sql = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        m2m_fields: List[tuple] = []

        for name, field in cls._fields.items():
            if field.__class__.__name__ == "ManyToManyField":
                m2m_fields.append((name, field))
                continue

            # Validate field name
            sanitize_identifier(name)
            sql_type = field.get_sql_type()
            definition = f'{quote_identifier(name)} {sql_type}'
            if field.required:
                definition += " NOT NULL"
            fields_sql.append(definition)

        sql = f"CREATE TABLE IF NOT EXISTS {quote_identifier(cls._table_name)} ({', '.join(fields_sql)})"
        
        # Handle both sync Database and async AsyncDatabase
        if hasattr(db, 'execute_sync'):
            # AsyncDatabase - use sync execute for DDL
            db.execute_sync(sql)
        else:
            # Sync Database
            db.execute(sql)

        # Create junction tables for M2M
        for name, field in m2m_fields:
            junction_table = f"{cls._table_name}_{name}"
            # Validate junction table name
            sanitize_identifier(junction_table)
            sql = f"""
                CREATE TABLE IF NOT EXISTS {quote_identifier(junction_table)} (
                    source_id INTEGER,
                    target_id INTEGER,
                    PRIMARY KEY (source_id, target_id)
                )
            """
            if hasattr(db, 'execute_sync'):
                db.execute_sync(sql)
            else:
                db.execute(sql)

        # Create indexes
        if hasattr(cls, "_indexes"):
            for idx in cls._indexes:
                if isinstance(idx, tuple):
                    # Composite index or (field, unique)
                    if len(idx) == 2 and isinstance(idx[1], bool):
                        # Single field with unique flag
                        field_name, unique = idx
                        # Validate field name
                        sanitize_identifier(field_name)
                        idx_name = f"idx_{cls._table_name}_{field_name}"
                        # Validate index name
                        sanitize_identifier(idx_name)
                        unique_sql = "UNIQUE " if unique else ""
                        sql = f"CREATE {unique_sql}INDEX IF NOT EXISTS {quote_identifier(idx_name)} ON {quote_identifier(cls._table_name)} ({quote_identifier(field_name)})"
                        if hasattr(db, 'execute_sync'):
                            db.execute_sync(sql)
                        else:
                            db.execute(sql)
                    else:
                        # Composite index
                        # Validate field names
                        validated_fields = []
                        for field in idx:
                            sanitize_identifier(field)
                            validated_fields.append(quote_identifier(field))
                        fields = ", ".join(validated_fields)
                        idx_name = f"idx_{cls._table_name}_{'_'.join(idx)}"
                        # Validate index name
                        sanitize_identifier(idx_name)
                        sql = f"CREATE INDEX IF NOT EXISTS {quote_identifier(idx_name)} ON {quote_identifier(cls._table_name)} ({fields})"
                        if hasattr(db, 'execute_sync'):
                            db.execute_sync(sql)
                        else:
                            db.execute(sql)
                elif isinstance(idx, str):
                    # Simple index
                    # Validate field name
                    sanitize_identifier(idx)
                    idx_name = f"idx_{cls._table_name}_{idx}"
                    # Validate index name
                    sanitize_identifier(idx_name)
                    sql = f"CREATE INDEX IF NOT EXISTS {quote_identifier(idx_name)} ON {quote_identifier(cls._table_name)} ({quote_identifier(idx)})"
                    if hasattr(db, 'execute_sync'):
                        db.execute_sync(sql)
                    else:
                        db.execute(sql)

    @classmethod
    async def async_create_table(cls: Type[T], db: 'Database') -> None:
        """Async version of create_table for AsyncDatabase"""
        # Validate table name
        sanitize_identifier(cls._table_name)
        fields_sql = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        m2m_fields: List[tuple] = []

        for name, field in cls._fields.items():
            if field.__class__.__name__ == "ManyToManyField":
                m2m_fields.append((name, field))
                continue

            # Validate field name
            sanitize_identifier(name)
            sql_type = field.get_sql_type()
            definition = f'{quote_identifier(name)} {sql_type}'
            if field.required:
                definition += " NOT NULL"
            fields_sql.append(definition)

        sql = f"CREATE TABLE IF NOT EXISTS {quote_identifier(cls._table_name)} ({', '.join(fields_sql)})"
        
        # Use async execute if available
        if hasattr(db, 'execute') and hasattr(db, 'connection') and db.connection:
            await db.execute(sql)  # type: ignore
        else:
            # Fallback to sync
            db.execute(sql)

        # Create junction tables for M2M
        for name, field in m2m_fields:
            junction_table = f"{cls._table_name}_{name}"
            # Validate junction table name
            sanitize_identifier(junction_table)
            sql = f"""
                CREATE TABLE IF NOT EXISTS {quote_identifier(junction_table)} (
                    source_id INTEGER,
                    target_id INTEGER,
                    PRIMARY KEY (source_id, target_id)
                )
            """
            if hasattr(db, 'execute') and hasattr(db, 'connection') and db.connection:
                await db.execute(sql)  # type: ignore
            else:
                db.execute(sql)

        # Create indexes
        if hasattr(cls, "_indexes"):
            for idx in cls._indexes:
                if isinstance(idx, tuple):
                    if len(idx) == 2 and isinstance(idx[1], bool):
                        field_name, unique = idx
                        sanitize_identifier(field_name)
                        idx_name = f"idx_{cls._table_name}_{field_name}"
                        sanitize_identifier(idx_name)
                        unique_sql = "UNIQUE " if unique else ""
                        sql = f"CREATE {unique_sql}INDEX IF NOT EXISTS {quote_identifier(idx_name)} ON {quote_identifier(cls._table_name)} ({quote_identifier(field_name)})"
                        if hasattr(db, 'execute') and hasattr(db, 'connection') and db.connection:
                            await db.execute(sql)  # type: ignore
                        else:
                            db.execute(sql)
                    else:
                        validated_fields = []
                        for field in idx:
                            sanitize_identifier(field)
                            validated_fields.append(quote_identifier(field))
                        fields = ", ".join(validated_fields)
                        idx_name = f"idx_{cls._table_name}_{'_'.join(idx)}"
                        sanitize_identifier(idx_name)
                        sql = f"CREATE INDEX IF NOT EXISTS {quote_identifier(idx_name)} ON {quote_identifier(cls._table_name)} ({fields})"
                        if hasattr(db, 'execute') and hasattr(db, 'connection') and db.connection:
                            await db.execute(sql)  # type: ignore
                        else:
                            db.execute(sql)
                elif isinstance(idx, str):
                    sanitize_identifier(idx)
                    idx_name = f"idx_{cls._table_name}_{idx}"
                    sanitize_identifier(idx_name)
                    sql = f"CREATE INDEX IF NOT EXISTS {quote_identifier(idx_name)} ON {quote_identifier(cls._table_name)} ({quote_identifier(idx)})"
                    if hasattr(db, 'execute') and hasattr(db, 'connection') and db.connection:
                        await db.execute(sql)  # type: ignore
                    else:
                        db.execute(sql)

    def save(self, db: 'Database') -> None:
        """Enhanced save with detailed error handling"""
        from turbo.exceptions import ModelSaveError
        
        self.validate()
        self.before_save(db)

        # Validate table name
        sanitize_identifier(self._table_name)
        
        # Filter out ManyToManyField
        fields = [
            f
            for f in self._fields.keys()
            if self._fields[f].__class__.__name__ != "ManyToManyField"
        ]
        
        # Validate field names
        for f in fields:
            sanitize_identifier(f)
            
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
            elif hasattr(field, "to_sql"):
                val = field.to_sql(val)

            values.append(val)

        placeholders = ", ".join(["?"] * len(fields))

        try:
            if self.id is None:
                # Insert
                columns = ", ".join([quote_identifier(f) for f in fields])
                sql = f"INSERT INTO {quote_identifier(self._table_name)} ({columns}) VALUES ({placeholders})"
                cursor = db.execute(sql, values)
                self.id = cursor.lastrowid
            else:
                # Update
                set_clause = ", ".join([f'{quote_identifier(f)} = ?' for f in fields])
                sql = f"UPDATE {quote_identifier(self._table_name)} SET {set_clause} WHERE id = ?"
                db.execute(sql, values + [self.id])

            # Auto-commit if not in a transaction
            if not getattr(db, '_in_transaction', False):
                db.commit()

            # Update cache
            if self.id is not None:
                self._cache_set(self.id, self)
            self.after_save(db)
        except Exception as e:
            # Enhanced error with context
            context = {
                'table': self._table_name,
                'fields': fields,
                'values': values,
                'sql': sql if 'sql' in locals() else 'N/A',
                'db_path': db.path if hasattr(db, 'path') else 'unknown',
                'operation': 'insert' if self.id is None else 'update'
            }
            raise ModelSaveError(self, context['operation'], e, context) from e

    def validate(self) -> None:
        pass

    def before_save(self, db: 'Database') -> None:
        pass

    def after_save(self, db: 'Database') -> None:
        pass

    @classmethod
    def get(cls: Type[T], db: 'Database', id: int) -> Optional[T]:
        try:
            # Check cache first
            cached = cls._cache_get(id)
            if cached:
                return cached

            # Validate table name
            sanitize_identifier(cls._table_name)
            sql = f"SELECT * FROM {quote_identifier(cls._table_name)} WHERE id = ?"
            cursor = db.execute(sql, (id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                id_val = data.pop("id")
                instance = cls(**data)
                instance.id = id_val

                # Store in cache
                cls._cache_set(id_val, instance)
                return instance
            return None
        except Exception as e:
            logging.error(f"Failed to get model {cls.__name__} with id {id}: {e}")
            raise RuntimeError(f"Failed to get model {cls.__name__} with id {id}") from e

    def delete(self, db: 'Database') -> None:
        if self.id:
            try:
                # Validate table name
                sanitize_identifier(self._table_name)
                sql = f"DELETE FROM {quote_identifier(self._table_name)} WHERE id = ?"
                db.execute(sql, (self.id,))
                self._cache_remove(self.id)
                self.id = None
            except Exception as e:
                logging.error(f"Failed to delete model {self.__class__.__name__} with id {self.id}: {e}")
                raise RuntimeError(f"Failed to delete model {self.__class__.__name__}") from e

    @classmethod
    def filter(cls: Type[T], db: 'Database', order_by: Optional[str] = None, limit: Optional[int] = None,
               offset: Optional[int] = None, **kwargs: Any) -> List[T]:
        try:
            from .sql_utils import sanitize_order_by_field
            # Validate table name
            sanitize_identifier(cls._table_name)
        
            conditions: List[str] = []
            values: List[Any] = []
            for key, value in kwargs.items():
                # Validate field name
                sanitize_identifier(key)
                conditions.append(f'{quote_identifier(key)} = ?')
                values.append(value)

            where_clause = " AND ".join(conditions)
            if where_clause:
                sql = f"SELECT * FROM {quote_identifier(cls._table_name)} WHERE {where_clause}"
            else:
                sql = f"SELECT * FROM {quote_identifier(cls._table_name)}"

            if order_by:
                # Validate order by field
                order_by = sanitize_order_by_field(order_by)
                direction = "DESC" if order_by.startswith("-") else "ASC"
                column = order_by.lstrip("-")
                # Validate column name
                sanitize_identifier(column)
                sql += f" ORDER BY {quote_identifier(column)} {direction}"

            if limit:
                sql += f" LIMIT {limit}"

            if offset:
                sql += f" OFFSET {offset}"

            cursor = db.execute(sql, values)
            instances: List[T] = []
            for row in cursor.fetchall():
                data = dict(row)
                id_val = data.pop("id")
                instance = cls(**data)
                instance.id = id_val
                instances.append(instance)
            return instances
        except Exception as e:
            logging.error(f"Failed to filter models {cls.__name__}: {e}")
            raise RuntimeError(f"Failed to filter models {cls.__name__}") from e

    @classmethod
    def all(cls: Type[T], db: 'Database', order_by: Optional[str] = None, limit: Optional[int] = None) -> List[T]:
        try:
            from .sql_utils import sanitize_order_by_field
            # Validate table name
            sanitize_identifier(cls._table_name)
            sql = f"SELECT * FROM {quote_identifier(cls._table_name)}"

            if order_by:
                # Validate order by field
                order_by = sanitize_order_by_field(order_by)
                direction = "DESC" if order_by.startswith("-") else "ASC"
                column = order_by.lstrip("-")
                # Validate column name
                sanitize_identifier(column)
                sql += f" ORDER BY {quote_identifier(column)} {direction}"

            if limit:
                sql += f" LIMIT {limit}"

            cursor = db.execute(sql)
            instances: List[T] = []
            for row in cursor.fetchall():
                data = dict(row)
                id_val = data.pop("id")
                instance = cls(**data)
                instance.id = id_val
                instances.append(instance)
            return instances
        except Exception as e:
            logging.error(f"Failed to fetch all models {cls.__name__}: {e}")
            raise RuntimeError(f"Failed to fetch all models {cls.__name__}") from e

    @classmethod
    def first(cls: Type[T], db: 'Database', order_by: Optional[str] = None, **kwargs: Any) -> Optional[T]:
        # Validate order_by parameter if provided
        if order_by is not None:
            from .sql_utils import sanitize_order_by_field
            order_by = sanitize_order_by_field(order_by)
        results = cls.filter(db, order_by=order_by, limit=1, **kwargs)
        return results[0] if results else None

    @classmethod
    def count(cls: Type[T], db: 'Database', **kwargs: Any) -> int:
        try:
            # Validate table name
            sanitize_identifier(cls._table_name)
        
            conditions: List[str] = []
            values: List[Any] = []
            for key, value in kwargs.items():
                # Validate field name
                sanitize_identifier(key)
                conditions.append(f'{quote_identifier(key)} = ?')
                values.append(value)

            where_clause = " AND ".join(conditions)
            if where_clause:
                sql = f"SELECT COUNT(*) FROM {quote_identifier(cls._table_name)} WHERE {where_clause}"
            else:
                sql = f"SELECT COUNT(*) FROM {quote_identifier(cls._table_name)}"

            cursor = db.execute(sql, values)
            return cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"Failed to count models {cls.__name__}: {e}")
            raise RuntimeError(f"Failed to count models {cls.__name__}") from e

    @classmethod
    def delete_many(cls: Type[T], db: 'Database', **kwargs: Any) -> None:
        try:
            # Validate table name
            sanitize_identifier(cls._table_name)
        
            conditions: List[str] = []
            values: List[Any] = []
            for key, value in kwargs.items():
                # Validate field name
                sanitize_identifier(key)
                conditions.append(f'{quote_identifier(key)} = ?')
                values.append(value)

            where_clause = " AND ".join(conditions)
            if where_clause:
                sql = f"DELETE FROM {quote_identifier(cls._table_name)} WHERE {where_clause}"
            else:
                sql = f"DELETE FROM {quote_identifier(cls._table_name)}"

            db.execute(sql, values)
        except Exception as e:
            logging.error(f"Failed to delete many models {cls.__name__}: {e}")
            raise RuntimeError(f"Failed to delete many models {cls.__name__}") from e

    @classmethod
    def update_many(cls: Type[T], db: 'Database', updates: Dict[str, Any], **kwargs: Any) -> None:
        try:
            # Validate table name
            sanitize_identifier(cls._table_name)
        
            set_clauses: List[str] = []
            values: List[Any] = []
            for key, value in updates.items():
                # Validate field name
                sanitize_identifier(key)
                set_clauses.append(f'{quote_identifier(key)} = ?')
                values.append(value)

            conditions: List[str] = []
            for key, value in kwargs.items():
                # Validate field name
                sanitize_identifier(key)
                conditions.append(f'{quote_identifier(key)} = ?')
                values.append(value)

            set_clause = ", ".join(set_clauses)
            where_clause = " AND ".join(conditions)

            if where_clause:
                sql = f"UPDATE {quote_identifier(cls._table_name)} SET {set_clause} WHERE {where_clause}"
            else:
                sql = f"UPDATE {quote_identifier(cls._table_name)} SET {set_clause}"

            db.execute(sql, values)
        except Exception as e:
            logging.error(f"Failed to update many models {cls.__name__}: {e}")
            raise RuntimeError(f"Failed to update many models {cls.__name__}") from e

    @classmethod
    def migrate(cls: Type[T], db: 'Database') -> None:
        # Validate table name
        sanitize_identifier(cls._table_name)
        
        # Get current columns
        sql = f"PRAGMA table_info({quote_identifier(cls._table_name)})"
        cursor = db.execute(sql)
        current_columns = {row["name"] for row in cursor.fetchall()}

        # Check for missing columns
        for name, field in cls._fields.items():
            if name not in current_columns:
                # Validate field name
                sanitize_identifier(name)
                sql_type = field.get_sql_type()
                definition = f'{quote_identifier(name)} {sql_type}'
                # Note: SQLite does not support adding NOT NULL columns without a default value easily in older versions,
                # but modern SQLite handles it if we provide a default or if it's nullable.
                # For simplicity, we won't enforce NOT NULL on added columns unless they have a default.
                if field.default is not None:
                    # This is tricky with SQLite ALTER TABLE, so we'll just add it as nullable for now
                    # or rely on the field definition.
                    pass

                print(f"Migrating: Adding column {name} to {cls._table_name}")
                sql = f"ALTER TABLE {quote_identifier(cls._table_name)} ADD COLUMN {definition}"
                db.execute(sql)

    def related(self, db: 'Database', field_name: str) -> Optional['Model']:
        # Validate field_name parameter
        if not isinstance(field_name, str):
            raise ValueError("Field name must be a string")
        
        if field_name not in self._fields:
            raise ValueError(f"Unknown field: {field_name}")

        field = self._fields[field_name]
        if field.__class__.__name__ != "ForeignKey":
            raise ValueError(f"Field {field_name} is not a ForeignKey")

        related_id = getattr(self, field_name)
        if related_id is None:
            return None

        # Look up model class
        related_table = field.table_name
        # Validate related_table parameter
        from .sql_utils import sanitize_identifier
        if related_table:
            sanitize_identifier(related_table)
        if related_table not in ModelMeta._registry:
            raise ValueError(f"Model for table '{related_table}' not found in registry")

        RelatedModel = ModelMeta._registry[related_table]
        return RelatedModel.get(db, related_id)

    def m2m_add(self, db: 'Database', field_name: str, item: 'Model') -> None:
        if field_name not in self._fields:
            raise ValueError(f"Unknown field: {field_name}")

        junction_table = f"{self._table_name}_{field_name}"
        # Validate junction table name
        sanitize_identifier(junction_table)
        sql = f"INSERT OR IGNORE INTO {quote_identifier(junction_table)} (source_id, target_id) VALUES (?, ?)"
        db.execute(sql, (self.id, item.id))

    def m2m_remove(self, db: 'Database', field_name: str, item: 'Model') -> None:
        if field_name not in self._fields:
            raise ValueError(f"Unknown field: {field_name}")

        junction_table = f"{self._table_name}_{field_name}"
        # Validate junction table name
        sanitize_identifier(junction_table)
        sql = f"DELETE FROM {quote_identifier(junction_table)} WHERE source_id = ? AND target_id = ?"
        db.execute(sql, (self.id, item.id))

    def m2m_get(self, db: 'Database', field_name: str) -> List['Model']:
        if field_name not in self._fields:
            raise ValueError(f"Unknown field: {field_name}")

        field = self._fields[field_name]
        related_table = field.table_name
        # Validate related table name
        if related_table:
            sanitize_identifier(related_table)
        if related_table not in ModelMeta._registry:
            raise ValueError(f"Model for table '{related_table}' not found in registry")

        RelatedModel = ModelMeta._registry[related_table]
        junction_table = f"{self._table_name}_{field_name}"
        # Validate junction table name
        sanitize_identifier(junction_table)

        sql = f"""
            SELECT T.* FROM {quote_identifier(related_table)} T
            JOIN {quote_identifier(junction_table)} J ON T.id = J.target_id
            WHERE J.source_id = ?
        """
        cursor = db.execute(sql, (self.id,))

        instances: List['Model'] = []
        for row in cursor.fetchall():
            data = dict(row)
            id_val = data.pop("id")
            instance = RelatedModel(**data)
            instance.id = id_val
            instances.append(instance)
        return instances

    @classmethod
    def query(cls: Type[T], db: 'Database') -> 'QueryBuilder':
        """Return QueryBuilder for fluent API"""
        # Validate db parameter
        if not hasattr(db, 'execute'):
            raise ValueError("db must be a Database instance")
        from .query_builder import QueryBuilder

        return QueryBuilder(cls, db)

    def to_dict(self) -> Dict[str, Any]:
        """Convert instance to dictionary"""
        result = {"id": self.id}
        for name in self._fields.keys():
            if self._fields[name].__class__.__name__ != "ManyToManyField":
                # Validate field name
                from .sql_utils import sanitize_identifier
                sanitize_identifier(name)
                result[name] = getattr(self, name)
        return result

    def to_json(self) -> str:
        """Convert instance to JSON string"""
        import json

        def json_serializer(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        return json.dumps(self.to_dict(), default=json_serializer)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create instance from dictionary"""
        # Validate data parameter
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        data_copy = data.copy()
        id_val = data_copy.pop("id", None)
        instance = cls(**data_copy)
        if id_val:
            instance.id = id_val
        return instance

    @classmethod
    def paginate(cls: Type[T], db: 'Database', page: int = 1, per_page: int = 20, **kwargs: Any) -> 'Paginator':
        """Paginate results"""
        from .pagination import Paginator

        # Validate page and per_page parameters
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
        elif per_page > 1000:  # Reasonable upper limit
            per_page = 1000

        return Paginator(cls, db, page, per_page, **kwargs)

    @classmethod
    def raw(cls: Type[T], db: 'Database', sql: str, params: Optional[List[Any]] = None) -> List[T]:
        """
        Execute raw SQL and return model instances.
        
        Warning:
            This method should only be used with trusted SQL queries.
            Never pass user input directly to this method without proper validation and sanitization.
        """
        cursor = db.execute(sql, params or [])
        instances: List[T] = []
        for row in cursor.fetchall():
            data = dict(row)
            id_val = data.pop("id", None)
            instance = cls(**data)
            if id_val:
                instance.id = id_val
            instances.append(instance)
        return instances

    @classmethod
    def using(cls: Type[T], db: 'Database') -> ModelDatabaseProxy:
        """Specify database for query (multi-database support)"""
        # Validate db parameter
        if not hasattr(db, 'execute'):
            raise ValueError("db must be a Database instance")
        # Return a proxy that passes db to all methods
        return ModelDatabaseProxy(cls, db)

    @classmethod
    def bulk_create(cls: Type[T], db: 'Database', instances: List[T]) -> List[T]:
        """Optimized bulk creation of multiple instances"""
        # Validate instances parameter
        if not isinstance(instances, list):
            raise ValueError("instances must be a list")
        if not instances:
            return instances
            
        # Use QueryBuilder for optimized bulk insert
        query_builder = cls.query(db)
        query_builder.bulk_insert(instances)
        return instances

    @classmethod
    def bulk_update(cls: Type[T], db: 'Database', instances: List[T]) -> None:
        """Optimized bulk update of multiple instances"""
        if not instances:
            return
            
        # Validate table name
        sanitize_identifier(cls._table_name)
            
        # Group instances by fields to update
        for instance in instances:
            # Collect fields to update (excluding id)
            fields = [f for f in cls._fields.keys() if f != "id"]
            # Validate field names
            for f in fields:
                sanitize_identifier(f)
            set_clauses = ", ".join([f'{quote_identifier(f)} = ?' for f in fields])
            values = []
            
            # Collect values for each field
            for f in fields:
                val = getattr(instance, f)
                field = cls._fields[f]
                
                # Handle special field types
                if isinstance(val, datetime.datetime):
                    val = val.isoformat()
                elif field.__class__.__name__ == "JSONField" and not isinstance(val, str):
                    import json
                    val = json.dumps(val)
                elif field.__class__.__name__ == "EncryptedField":
                    val = field.encrypt(val)
                elif hasattr(field, "to_sql"):
                    val = field.to_sql(val)
                    
                values.append(val)
            
            # Add id for WHERE clause
            values.append(instance.id)
            
            # Execute update
            sql = f"UPDATE {quote_identifier(cls._table_name)} SET {set_clauses} WHERE id = ?"
            db.execute(sql, values)
            
            # Update cache
            if instance.id is not None:
                cls._cache_set(instance.id, instance)
