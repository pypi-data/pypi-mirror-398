from typing import List, Dict, Any, Optional, Set, Type, TYPE_CHECKING, TypeVar
from .sql_utils import sanitize_identifier, quote_identifier

if TYPE_CHECKING:
    from .model import Model, ModelMeta

T = TypeVar('T', bound='Model')

class QueryBuilder:
    """Fluent API for building complex queries"""

    def __init__(self, model_class: Type['Model'], db: 'Database') -> None:
        self.model_class = model_class
        self.db = db
        self._where_clauses: List[str] = []
        self._where_values: List[Any] = []
        self._order_by: Optional[str] = None
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
        self._eager_load: List[str] = []  # Fields to eager load

    def __getattr__(self, name: str):
        """Delegate to model scopes for chaining"""
        if hasattr(self.model_class, "_scopes") and name in self.model_class._scopes:
            scope_func = self.model_class._scopes[name]
            return lambda: scope_func(self)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def where(self, **kwargs: Dict[str, Any]) -> 'QueryBuilder':
        """Add WHERE conditions with operator support.
        
        Supports operators via double underscore syntax:
        - field__eq: equal to
        - field__gt: greater than
        - field__lt: less than
        - field__gte: greater than or equal
        - field__lte: less than or equal
        - field__contains: contains substring
        - field__in: value in list
        
        Args:
            **kwargs: Field conditions
            
        Returns:
            QueryBuilder: Self for method chaining
            
        Example:
            User.query(db).where(age__gte=18).where(name__contains="John")
        """
        for key, value in kwargs.items():
            # Parse field__operator format
            if "__" in key:
                parts = key.split("__")
                field = parts[0]
                operator = parts[1] if len(parts) > 1 else "eq"
            else:
                field = key
                operator = "eq"

            # Validate field name
            sanitize_identifier(field)

            # Build SQL based on operator
            quoted_field = quote_identifier(field)
            if operator == "eq":
                self._where_clauses.append(f'{quoted_field} = ?')
                self._where_values.append(value)
            elif operator == "gt":
                self._where_clauses.append(f'{quoted_field} > ?')
                self._where_values.append(value)
            elif operator == "lt":
                self._where_clauses.append(f'{quoted_field} < ?')
                self._where_values.append(value)
            elif operator == "gte":
                self._where_clauses.append(f'{quoted_field} >= ?')
                self._where_values.append(value)
            elif operator == "lte":
                self._where_clauses.append(f'{quoted_field} <= ?')
                self._where_values.append(value)
            elif operator == "contains":
                self._where_clauses.append(f'{quoted_field} LIKE ?')
                self._where_values.append(f"%{value}%")
            elif operator == "in":
                placeholders = ", ".join(["?"] * len(value))
                self._where_clauses.append(f'{quoted_field} IN ({placeholders})')
                self._where_values.extend(value)

        return self  # Chainable

    def order_by(self, field: str) -> 'QueryBuilder':
        """Set ORDER BY clause.
        
        Args:
            field: Field name to order by (prefix with '-' for DESC)
            
        Returns:
            QueryBuilder: Self for method chaining
            
        Example:
            User.query(db).order_by('-created_at')  # DESC
            User.query(db).order_by('name')  # ASC
        """
        from .sql_utils import sanitize_order_by_field
        self._order_by = sanitize_order_by_field(field)
        return self

    def limit(self, n: int) -> 'QueryBuilder':
        """Set LIMIT clause.
        
        Args:
            n: Maximum number of results
            
        Returns:
            QueryBuilder: Self for method chaining
        """
        self._limit_val = n
        return self

    def offset(self, n: int) -> 'QueryBuilder':
        """Set OFFSET clause.
        
        Args:
            n: Number of results to skip
            
        Returns:
            QueryBuilder: Self for method chaining
        """
        self._offset_val = n
        return self

    def with_(self, *field_names: str) -> 'QueryBuilder':
        """Mark relationships for eager loading.
        
        Args:
            *field_names: Relationship field names to eager load
            
        Returns:
            QueryBuilder: Self for method chaining
            
        Example:
            User.query(db).with_('posts', 'comments')
        """
        self._eager_load.extend(field_names)
        return self

    def execute(self) -> List['Model']:
        """Execute the query and return results.
        
        Builds and executes the SQL query based on all set conditions.
        Applies eager loading if specified via with_() method.
        
        Returns:
            List[Model]: List of model instances matching the query
        """
        from .sql_utils import sanitize_identifier, quote_identifier
        # Validate table name
        sanitize_identifier(self.model_class._table_name)
        sql = f"SELECT * FROM {quote_identifier(self.model_class._table_name)}"

        # WHERE
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)

        # ORDER BY
        if self._order_by:
            direction = "DESC" if self._order_by.startswith("-") else "ASC"
            column = self._order_by.lstrip("-")
            # Validate column name
            sanitize_identifier(column)
            sql += f" ORDER BY {quote_identifier(column)} {direction}"

        # LIMIT
        if self._limit_val:
            sql += f" LIMIT {self._limit_val}"

        # OFFSET
        if self._offset_val:
            sql += f" OFFSET {self._offset_val}"

        cursor = self.db.execute(sql, self._where_values)
        instances: List['Model'] = []
        for row in cursor.fetchall():
            data = dict(row)
            id_val = data.pop("id")
            instance = self.model_class(**data)
            instance.id = id_val
            instances.append(instance)

        # Eager load relationships
        if self._eager_load and instances:
            self._load_relationships(instances)

        return instances

    def _load_relationships(self, instances: List['Model']) -> None:
        """Eager load specified relationships"""
        from .model import ModelMeta
        from .sql_utils import sanitize_identifier, quote_identifier

        for field_name in self._eager_load:
            if field_name not in self.model_class._fields:
                continue

            field = self.model_class._fields[field_name]

            # ForeignKey eager loading
            if field.__class__.__name__ == "ForeignKey":
                # Collect all foreign IDs
                foreign_ids: Set[int] = set()
                for instance in instances:
                    fk_id = getattr(instance, field_name)
                    if fk_id:
                        foreign_ids.add(fk_id)

                if foreign_ids:
                    # Batch load related records
                    related_table = field.table_name
                    # Validate table name
                    sanitize_identifier(related_table)
                    if related_table in ModelMeta._registry:
                        RelatedModel = ModelMeta._registry[related_table]
                        placeholders = ", ".join(["?"] * len(foreign_ids))
                        sql = f"SELECT * FROM {quote_identifier(related_table)} WHERE id IN ({placeholders})"
                        cursor = self.db.execute(sql, list(foreign_ids))

                        # Build lookup map
                        related_map: Dict[int, 'Model'] = {}
                        for row in cursor.fetchall():
                            data = dict(row)
                            id_val = data.pop("id")
                            rel_instance = RelatedModel(**data)
                            rel_instance.id = id_val
                            related_map[id_val] = rel_instance

                        # Attach to instances
                        for instance in instances:
                            fk_id = getattr(instance, field_name)
                            if fk_id and fk_id in related_map:
                                setattr(
                                    instance,
                                    f"_{field_name}_cached",
                                    related_map[fk_id],
                                )

    def count(self) -> int:
        """Count matching records.
        
        Returns:
            int: Number of records matching the query conditions
        """
        from .sql_utils import sanitize_identifier, quote_identifier
        # Validate table name
        sanitize_identifier(self.model_class._table_name)
        sql = f"SELECT COUNT(*) FROM {quote_identifier(self.model_class._table_name)}"

        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)

        cursor = self.db.execute(sql, self._where_values)
        return cursor.fetchone()[0]

    def first(self) -> Optional['Model']:
        """Get first matching record.
        
        Returns:
            Optional[Model]: First model instance or None if no matches
        """
        results = self.limit(1).execute()
        return results[0] if results else None

    def aggregate(self, **aggregations: Dict[str, Any]) -> Dict[str, Any]:
        """Perform aggregation queries (AVG, MAX, MIN, SUM, COUNT).
        
        Args:
            **aggregations: Dictionary of aggregation functions
            
        Returns:
            Dict[str, Any]: Aggregation results
            
        Example:
            stats = User.query(db).aggregate(avg_age='age', max_age='age', count='id')
        """
        from .sql_utils import sanitize_identifier, quote_identifier
        agg_parts: List[str] = []
        for alias, field_or_func in aggregations.items():
            # Support 'avg_age' or 'avg'='age' syntax
            if isinstance(field_or_func, str):
                # Determine function from alias
                func = alias.split("_")[0].upper()
                field = field_or_func
            else:
                func = alias.upper()
                field = field_or_func

            # Validate field name if it's a simple field reference
            if isinstance(field, str) and field.isidentifier():
                sanitize_identifier(field)
                field = quote_identifier(field)
            
            agg_parts.append(f"{func}({field}) as {quote_identifier(alias)}")

        # Validate table name
        sanitize_identifier(self.model_class._table_name)
        sql = f"SELECT {', '.join(agg_parts)} FROM {quote_identifier(self.model_class._table_name)}"

        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)

        cursor = self.db.execute(sql, self._where_values)
        row = cursor.fetchone()

        if row:
            return dict(row)
        return {}

    def bulk_insert(self, instances: List[T]) -> None:
        """Optimized bulk insert of multiple instances.
        
        Uses executemany for efficient batch insertion.
        
        Args:
            instances: List of model instances to insert
        """
        from .sql_utils import sanitize_identifier, quote_identifier
        if not instances:
            return

        # Validate table name
        sanitize_identifier(self.model_class._table_name)
        
        # Get field names (excluding id for insert)
        fields = [f for f in self.model_class._fields.keys() if f != "id"]
        
        # Validate field names
        for field in fields:
            sanitize_identifier(field)
        
        # Create SQL with placeholders
        quoted_fields = [quote_identifier(f) for f in fields]
        placeholders = ", ".join(["?" for _ in fields])
        sql = f"INSERT INTO {quote_identifier(self.model_class._table_name)} ({', '.join(quoted_fields)}) VALUES ({placeholders})"
        
        # Prepare data for executemany
        values = []
        for instance in instances:
            instance_values = []
            for field_name in fields:
                value = getattr(instance, field_name, None)
                # Handle special field types
                if hasattr(value, 'isoformat'):  # datetime
                    value = value.isoformat()
                elif hasattr(self.model_class._fields[field_name], 'to_sql'):
                    value = self.model_class._fields[field_name].to_sql(value)
                instance_values.append(value)
            values.append(tuple(instance_values))
        
        # Execute bulk insert
        self.db.executemany(sql, values)
        
        # Update cache for each instance
        for instance in instances:
            if instance.id is not None:
                self.model_class._cache_set(instance.id, instance)
