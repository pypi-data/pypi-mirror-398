"""
Redis Caching - Distributed Query Cache

Uses Redis as a backend for query caching, enabling distributed
performance and persistence.
"""

import json
import hashlib
import time
from typing import Any, Dict, List, Optional, Sequence, Union, Iterator

try:
    import redis
except ImportError:
    redis = None


class MockCursor:
    """Wraps a list of rows to behave like a sqlite3 Cursor"""

    def __init__(self, rows: List[Dict[str, Any]]) -> None:
        self.rows: List[Dict[str, Any]] = rows
        self.idx: int = 0

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self.rows)

    def fetchall(self) -> List[Dict[str, Any]]:
        return self.rows

    def fetchone(self) -> Optional[Dict[str, Any]]:
        if self.idx < len(self.rows):
            res = self.rows[self.idx]
            self.idx += 1
            # Ensure result supports indexing (dict doesn't support [0] unless we wrap it or use tuple)
            # But Model expects dict(row) or row['col'].
            # If we stored dicts, row['col'] works.
            # But Model.count expects cursor.fetchone()[0].
            # So we need to support both dict access and tuple indexing?
            # SQLite Row supports both.
            # We can use a custom Row class or just ensure we store something compatible.
            # For simplicity, let's store dicts, but for count/aggregates we might have issues.
            # Actually, Model.count uses fetchone()[0].
            # If we store {'COUNT(*)': 5}, accessing [0] fails.
            # We should probably store tuples for values and map columns?
            # Or just make a smart wrapper.
            return SmartRow(res)
        return None


class SmartRow(dict):
    """Dict that also supports index access (values only)"""

    def __getitem__(self, key: Union[int, str]) -> Any:
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class RedisCache:
    """Redis backend for query caching"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None, ttl: int = 60) -> None:
        if not redis:
            raise ImportError("redis package is required. pip install redis")

        self.client: Any = redis.Redis(
            host=host, port=port, db=db, password=password, decode_responses=True
        )
        self.ttl: int = ttl
        self.hit_count: int = 0
        self.miss_count: int = 0

    def _make_key(self, sql: str, params: Optional[Sequence[Any]]) -> str:
        if params:
            key_str = f"{sql}:{str(params)}"
        else:
            key_str = sql
        return "lite_model:" + hashlib.md5(key_str.encode()).hexdigest()

    def get(self, sql: str, params: Optional[Sequence[Any]] = None) -> Optional[MockCursor]:
        key = self._make_key(sql, params)
        try:
            cached = self.client.get(key)
            if cached:
                self.hit_count += 1
                data = json.loads(cached)
                # data expected to be List[Dict[str, Any]]
                return MockCursor(data)
        except Exception as e:
            print(f"Redis Get Error: {e}")

        self.miss_count += 1
        return None

    def set(self, sql: str, params: Optional[Sequence[Any]], rows: List[Dict[str, Any]]) -> None:
        key = self._make_key(sql, params)
        try:
            # rows is a list of dicts (or SmartRows)
            # Convert to standard dicts for JSON
            data = [dict(r) for r in rows]
            self.client.setex(key, self.ttl, json.dumps(data))
        except Exception as e:
            print(f"Redis Set Error: {e}")

    def clear(self) -> None:
        # Flush DB (careful!) or just scan and delete
        # For safety, we won't flushdb by default
        pass

    def stats(self) -> Dict[str, Any]:
        return {"hits": self.hit_count, "misses": self.miss_count, "type": "redis"}


def add_redis_caching_to_database(host: str = "localhost", port: int = 6379, **kwargs: Any) -> None:
    """Enable Redis caching on Database"""
    from .database import Database

    # Store original execute if not already stored
    if not hasattr(Database, "_original_execute_for_redis"):
        Database._original_execute_for_redis = Database.execute

    original_execute = Database._original_execute_for_redis

    def execute_with_redis(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        # Initialize cache if needed
        if not hasattr(self, "_redis_cache"):
            try:
                self._redis_cache = RedisCache(host=host, port=port, **kwargs)
                print(f"✓ Redis Cache connected to {host}:{port}")
            except Exception as e:
                print(f"✗ Redis Cache failed: {e}")
                self._redis_cache = None

        # Try cache for SELECT
        if self._redis_cache and sql.strip().upper().startswith("SELECT"):
            cached = self._redis_cache.get(sql, params)
            if cached:
                return cached

        # Execute real query
        cursor = original_execute(self, sql, params)

        # Cache result if SELECT
        if self._redis_cache and sql.strip().upper().startswith("SELECT"):
            # Fetch all to cache
            rows = [dict(row) for row in cursor.fetchall()]
            self._redis_cache.set(sql, params, rows)
            return MockCursor(rows)

        return cursor

    Database.execute = execute_with_redis
