"""
Async Optimized Model - Extreme Performance for Async I/O
"""

from .optimized import OptimizedModel
from .async_support import AsyncModel


class AsyncOptimizedModel(OptimizedModel, AsyncModel):
    """
    High-performance async model.
    Inherits __slots__ and optimizations from OptimizedModel.
    Inherits async capabilities from AsyncModel.
    """

    __slots__ = ()

    async def save_fast_async(self, db):
        """
        Async version of save_fast.
        Bypasses DB wrapper and uses aiosqlite connection directly.
        """
        # Skip hooks and contracts for maximum speed
        is_new = self.id is None
        cls = self.__class__

        if is_new:
            # INSERT
            if not hasattr(cls, "_cached_insert_sql"):
                fields = [k for k in self._fields.keys() if k != "id"]
                placeholders = ",".join("?" * len(fields))
                cls._cached_insert_sql = f'INSERT INTO {self._table_name} ({",".join(fields)}) VALUES ({placeholders})'
                cls._cached_insert_fields = fields

            # Use _data directly for speed
            values = [self._data.get(f) for f in cls._cached_insert_fields]

            # Bypass DB wrapper for speed - access aiosqlite connection directly
            cursor = await db.connection.execute(cls._cached_insert_sql, values)
            self.id = cursor.lastrowid
        else:
            # UPDATE
            if not hasattr(cls, "_cached_update_sql"):
                fields = [k for k in self._fields.keys() if k != "id"]
                set_clause = ",".join(f"{f}=?" for f in fields)
                cls._cached_update_sql = (
                    f"UPDATE {self._table_name} SET {set_clause} WHERE id=?"
                )
                cls._cached_update_fields = fields

            values = [self._data.get(f) for f in cls._cached_update_fields] + [self.id]
            await db.connection.execute(cls._cached_update_sql, values)

    @classmethod
    async def save_many_fast_async(cls, db, instances):
        """
        Async bulk insert using executemany.
        """
        if not instances:
            return

        # Ensure SQL is cached
        if not hasattr(cls, "_cached_insert_sql"):
            fields = [k for k in cls._fields.keys() if k != "id"]
            placeholders = ",".join("?" * len(fields))
            cls._cached_insert_sql = f'INSERT INTO {cls._table_name} ({",".join(fields)}) VALUES ({placeholders})'
            cls._cached_insert_fields = fields

        fields = cls._cached_insert_fields

        # Build values list
        values = [tuple(inst._data.get(f) for f in fields) for inst in instances]

        # Execute
        await db.connection.executemany(cls._cached_insert_sql, values)

    @classmethod
    async def async_bulk_create(cls, db, instances):
        """Optimized async bulk creation of multiple instances"""
        if not instances:
            return instances
            
        # Use the optimized save_many_fast_async method for bulk creation
        await cls.save_many_fast_async(db, instances)
        return instances
