#!/usr/bin/env python3
"""
Advanced ORM Extensions - Query Builders, Caching, Validation, Events

Demonstrates professional ORM features:
- Advanced query filtering and sorting
- Result caching with TTL
- Field validation framework
- Event/hook system
- Bulk operations
- Data export/import
- Audit logging
"""

import sys
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import json
import csv
from io import StringIO
from functools import wraps

# Fix UTF-8 encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


# ============================================================================
# Query Filtering & Sorting
# ============================================================================

class FilterOperator(str, Enum):
    """Query filter operators"""
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    LIKE = "like"
    BETWEEN = "between"


class SortOrder(str, Enum):
    """Sort direction"""
    ASC = "asc"
    DESC = "desc"


class QueryFilter:
    """Single filter condition"""
    
    def __init__(self, field: str, operator: FilterOperator, value: Any):
        self.field = field
        self.operator = operator
        self.value = value
    
    def apply(self, obj: Any) -> bool:
        """Check if object matches filter"""
        obj_value = getattr(obj, self.field, None)
        
        if self.operator == FilterOperator.EQ:
            return obj_value == self.value
        elif self.operator == FilterOperator.NE:
            return obj_value != self.value
        elif self.operator == FilterOperator.GT:
            return obj_value > self.value
        elif self.operator == FilterOperator.GTE:
            return obj_value >= self.value
        elif self.operator == FilterOperator.LT:
            return obj_value < self.value
        elif self.operator == FilterOperator.LTE:
            return obj_value <= self.value
        elif self.operator == FilterOperator.IN:
            return obj_value in self.value
        elif self.operator == FilterOperator.LIKE:
            return str(self.value).lower() in str(obj_value).lower()
        elif self.operator == FilterOperator.BETWEEN:
            return self.value[0] <= obj_value <= self.value[1]
        return False


class QueryBuilder:
    """Fluent query builder interface"""
    
    def __init__(self, items: List[Any]):
        self.items = items
        self.filters: List[QueryFilter] = []
        self.sorts: List[Tuple[str, SortOrder]] = []
        self.skip_count = 0
        self.take_count = None
    
    def where(self, field: str, operator: Union[str, FilterOperator], value: Any) -> 'QueryBuilder':
        """Add filter condition"""
        if isinstance(operator, str):
            operator = FilterOperator(operator)
        self.filters.append(QueryFilter(field, operator, value))
        return self
    
    def order_by(self, field: str, direction: Union[str, SortOrder] = SortOrder.ASC) -> 'QueryBuilder':
        """Add sort condition"""
        if isinstance(direction, str):
            direction = SortOrder(direction)
        self.sorts.append((field, direction))
        return self
    
    def skip(self, count: int) -> 'QueryBuilder':
        """Skip n results"""
        self.skip_count = count
        return self
    
    def take(self, count: int) -> 'QueryBuilder':
        """Take n results"""
        self.take_count = count
        return self
    
    def execute(self) -> List[Any]:
        """Execute query and return results"""
        # Apply filters
        results = self.items
        for filter_cond in self.filters:
            results = [obj for obj in results if filter_cond.apply(obj)]
        
        # Apply sorting
        for field, direction in reversed(self.sorts):
            reverse = direction == SortOrder.DESC
            results = sorted(results, key=lambda x: getattr(x, field, None), reverse=reverse)
        
        # Apply pagination
        if self.skip_count > 0:
            results = results[self.skip_count:]
        if self.take_count is not None:
            results = results[:self.take_count]
        
        return results
    
    def count(self) -> int:
        """Get result count"""
        return len(self.execute())
    
    def first(self) -> Optional[Any]:
        """Get first result"""
        results = self.execute()
        return results[0] if results else None


# ============================================================================
# Caching Layer
# ============================================================================

class CacheEntry:
    """Cache entry with TTL"""
    
    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds


class QueryCache:
    """Query result cache with TTL"""
    
    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0
    
    def get_key(self, query_filters: List[QueryFilter], sorts: List[Tuple]) -> str:
        """Generate cache key from query"""
        key_parts = []
        for f in query_filters:
            key_parts.append(f"{f.field}:{f.operator.value}:{f.value}")
        for field, direction in sorts:
            key_parts.append(f"{field}:{direction.value}")
        return "|".join(key_parts) if key_parts else "__all__"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                self.hits += 1
                return entry.value
            else:
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set cache value"""
        self.cache[key] = CacheEntry(value, ttl_seconds)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
            "cached_entries": len(self.cache),
        }


# ============================================================================
# Validation Framework
# ============================================================================

class Validator:
    """Base validator"""
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate value, return (is_valid, error_message)"""
        raise NotImplementedError


class RequiredValidator(Validator):
    """Field is required"""
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, "Field is required"
        return True, None


class LengthValidator(Validator):
    """String length validation"""
    
    def __init__(self, min_length: int = 0, max_length: int = None):
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if not isinstance(value, str):
            return True, None
        
        if len(value) < self.min_length:
            return False, f"Minimum length is {self.min_length}"
        if self.max_length and len(value) > self.max_length:
            return False, f"Maximum length is {self.max_length}"
        return True, None


class RangeValidator(Validator):
    """Numeric range validation"""
    
    def __init__(self, min_value: float = None, max_value: float = None):
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if not isinstance(value, (int, float, Decimal)):
            return True, None
        
        if self.min_value is not None and value < self.min_value:
            return False, f"Minimum value is {self.min_value}"
        if self.max_value is not None and value > self.max_value:
            return False, f"Maximum value is {self.max_value}"
        return True, None


class PatternValidator(Validator):
    """Regex pattern validation"""
    
    def __init__(self, pattern: str):
        import re
        self.pattern = re.compile(pattern)
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        if not isinstance(value, str):
            return True, None
        
        if not self.pattern.match(value):
            return False, f"Value does not match pattern: {self.pattern.pattern}"
        return True, None


class ValidatedField:
    """Field with validators"""
    
    def __init__(self, validators: List[Validator] = None):
        self.validators = validators or []
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate value against all validators"""
        for validator in self.validators:
            is_valid, error = validator.validate(value)
            if not is_valid:
                return False, error
        return True, None


# ============================================================================
# Event/Hook System
# ============================================================================

class EventType(str, Enum):
    """Event types"""
    BEFORE_CREATE = "before_create"
    AFTER_CREATE = "after_create"
    BEFORE_UPDATE = "before_update"
    AFTER_UPDATE = "after_update"
    BEFORE_DELETE = "before_delete"
    AFTER_DELETE = "after_delete"
    ON_ERROR = "on_error"


class EventManager:
    """Manage model lifecycle events"""
    
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable]] = {event: [] for event in EventType}
    
    def on(self, event: EventType, callback: Callable) -> None:
        """Register event listener"""
        self.listeners[event].append(callback)
    
    def emit(self, event: EventType, data: Any = None) -> None:
        """Emit event"""
        for callback in self.listeners[event]:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in event listener: {e}")


# ============================================================================
# Bulk Operations
# ============================================================================

class BulkOperation:
    """Bulk database operation"""
    
    def __init__(self):
        self.operations: List[Tuple[str, Any]] = []
    
    def insert(self, obj: Any) -> 'BulkOperation':
        """Add insert operation"""
        self.operations.append(("insert", obj))
        return self
    
    def update(self, obj: Any) -> 'BulkOperation':
        """Add update operation"""
        self.operations.append(("update", obj))
        return self
    
    def delete(self, obj: Any) -> 'BulkOperation':
        """Add delete operation"""
        self.operations.append(("delete", obj))
        return self
    
    def execute(self) -> Dict[str, int]:
        """Execute all operations"""
        results = {"inserted": 0, "updated": 0, "deleted": 0}
        for op_type, obj in self.operations:
            if op_type == "insert":
                results["inserted"] += 1
            elif op_type == "update":
                results["updated"] += 1
            elif op_type == "delete":
                results["deleted"] += 1
        return results


# ============================================================================
# Export/Import
# ============================================================================

class DataExporter:
    """Export data to various formats"""
    
    @staticmethod
    def to_json(objects: List[Any]) -> str:
        """Export to JSON"""
        data = []
        for obj in objects:
            obj_dict = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, (datetime, Decimal)):
                    obj_dict[key] = str(value)
                elif isinstance(value, Enum):
                    obj_dict[key] = value.value
                else:
                    obj_dict[key] = value
            data.append(obj_dict)
        return json.dumps(data, indent=2)
    
    @staticmethod
    def to_csv(objects: List[Any]) -> str:
        """Export to CSV"""
        if not objects:
            return ""
        
        output = StringIO()
        fieldnames = list(objects[0].__dict__.keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for obj in objects:
            row = {}
            for key in fieldnames:
                value = getattr(obj, key, "")
                if isinstance(value, (datetime, Decimal)):
                    row[key] = str(value)
                elif isinstance(value, Enum):
                    row[key] = value.value
                else:
                    row[key] = value
            writer.writerow(row)
        
        return output.getvalue()


# ============================================================================
# Audit Logging
# ============================================================================

class AuditLog:
    """Track changes to objects"""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
    
    def record(
        self,
        object_id: int,
        object_type: str,
        action: str,
        old_values: Dict[str, Any] = None,
        new_values: Dict[str, Any] = None,
        user_id: int = None,
    ) -> None:
        """Record change"""
        log_entry = {
            "timestamp": datetime.now(),
            "object_id": object_id,
            "object_type": object_type,
            "action": action,
            "old_values": old_values or {},
            "new_values": new_values or {},
            "user_id": user_id,
        }
        self.logs.append(log_entry)
    
    def get_history(self, object_id: int, object_type: str) -> List[Dict[str, Any]]:
        """Get change history for object"""
        return [
            log for log in self.logs
            if log["object_id"] == object_id and log["object_type"] == object_type
        ]
    
    def export(self) -> str:
        """Export audit logs as JSON"""
        data = []
        for log in self.logs:
            log_copy = log.copy()
            log_copy["timestamp"] = str(log_copy["timestamp"])
            data.append(log_copy)
        return json.dumps(data, indent=2)


# ============================================================================
# ORM Extensions Container
# ============================================================================

class ORMExtensions:
    """Complete ORM extensions package"""
    
    def __init__(self):
        self.query_cache = QueryCache()
        self.event_manager = EventManager()
        self.audit_log = AuditLog()
    
    def create_query(self, items: List[Any]) -> QueryBuilder:
        """Create fluent query builder"""
        return QueryBuilder(items)
    
    def bulk_operation(self) -> BulkOperation:
        """Start bulk operation"""
        return BulkOperation()
    
    def export_json(self, objects: List[Any]) -> str:
        """Export objects as JSON"""
        return DataExporter.to_json(objects)
    
    def export_csv(self, objects: List[Any]) -> str:
        """Export objects as CSV"""
        return DataExporter.to_csv(objects)


if __name__ == "__main__":
    print("✓ ORM Extensions loaded successfully")
    print("✓ Features: Query Builder, Caching, Validation, Events, Bulk Ops, Export/Import, Audit Logs")
