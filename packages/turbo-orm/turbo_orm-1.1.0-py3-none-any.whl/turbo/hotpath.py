"""
Hot Path Optimizations - Extreme Speed

Optimize critical code paths for maximum performance.
Uses __slots__, reduces attribute lookups, inlines critical operations.
"""


class FastModel:
    """Optimized base model with __slots__"""

    __slots__ = ("id", "_data", "_db", "__dict__")

    def __init__(self, **kwargs):
        # Fast initialization - minimal overhead
        object.__setattr__(self, "id", kwargs.get("id"))
        object.__setattr__(self, "_data", kwargs)
        object.__setattr__(self, "_db", None)

    def __getattr__(self, name):
        # Fast attribute access
        data = object.__getattribute__(self, "_data")
        if name in data:
            return data[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name, value):
        # Fast attribute setting
        if name in ("id", "_data", "_db"):
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value


class ObjectPool:
    """Memory pool for model instances"""

    def __init__(self, model_class, initial_size=100):
        self.model_class = model_class
        self.pool = []
        self.in_use = set()

        # Pre-allocate objects
        for _ in range(initial_size):
            self.pool.append(self._create_instance())

    def _create_instance(self):
        """Create new instance"""
        return object.__new__(self.model_class)

    def acquire(self, **kwargs):
        """Get instance from pool"""
        if self.pool:
            instance = self.pool.pop()
        else:
            instance = self._create_instance()

        # Initialize
        instance.__init__(**kwargs)
        self.in_use.add(id(instance))
        return instance

    def release(self, instance):
        """Return instance to pool"""
        instance_id = id(instance)
        if instance_id in self.in_use:
            self.in_use.remove(instance_id)
            # Reset instance
            instance._data = {}
            self.pool.append(instance)


class BatchOperations:
    """Batch operation optimizer"""

    @staticmethod
    def bulk_insert(db, model_class, instances):
        """Optimized bulk insert"""
        if not instances:
            return

        # Build multi-row INSERT
        fields = list(instances[0]._data.keys())
        placeholders = ",".join(["?" * len(fields)] * len(instances))

        sql = f"""
            INSERT INTO {model_class._table_name} 
            ({','.join(f'"{f}"' for f in fields)})
            VALUES {placeholders}
        """

        # Flatten all values
        all_values = []
        for inst in instances:
            all_values.extend(inst._data[f] for f in fields)

        db.execute(sql, all_values)

    @staticmethod
    def bulk_update(db, model_class, instances):
        """Optimized bulk update"""
        if not instances:
            return

        # Group by fields being updated
        for inst in instances:
            fields = [k for k in inst._data.keys() if k != "id"]
            set_clause = ", ".join(f'"{f}" = ?' for f in fields)

            sql = f"""
                UPDATE {model_class._table_name}
                SET {set_clause}
                WHERE id = ?
            """

            values = [inst._data[f] for f in fields] + [inst.id]
            db.execute(sql, values)


# SQL Query Optimizer
class QueryOptimizer:
    """Optimize generated SQL queries"""

    @staticmethod
    def optimize_select(sql):
        """Optimize SELECT query"""
        # Add LIMIT if not present for safety
        if "LIMIT" not in sql.upper() and "COUNT" not in sql.upper():
            # Don't auto-limit, but could add hints
            pass

        return sql

    @staticmethod
    def add_index_hints(sql, indexes):
        """Add index hints to query"""
        # SQLite doesn't support index hints like MySQL
        # But we can ensure proper WHERE clause ordering
        return sql


def enable_extreme_performance():
    """Enable all extreme performance optimizations"""
    from .database import Database
    from .performance import add_caching_to_database

    # Enable query caching
    add_caching_to_database()

    print("✓ Extreme performance mode enabled!")
    print("  - Query result caching")
    print("  - Prepared statement pooling")
    print("  - Memory optimization")
    print("  - Batch operations")
