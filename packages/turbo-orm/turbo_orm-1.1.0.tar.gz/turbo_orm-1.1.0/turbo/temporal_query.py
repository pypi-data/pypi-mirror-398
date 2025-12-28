"""
Temporal Query Engine - Time-Travel Queries
Query database state at any historical timestamp with automatic schema version detection
and point-in-time reconstruction.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, TypeVar
from dataclasses import dataclass, field
import json

T = TypeVar("T")


@dataclass
class TemporalSnapshot:
    """Represents a point-in-time state of an entity"""
    entity_id: Any
    timestamp: datetime
    data: Dict[str, Any]
    operation: str  # 'INSERT', 'UPDATE', 'DELETE'
    version: int
    schema_version: int


@dataclass
class TemporalRange:
    """Represents a time range for querying"""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    
    def contains(self, timestamp: datetime) -> bool:
        if self.start and timestamp < self.start:
            return False
        if self.end and timestamp > self.end:
            return False
        return True


class TemporalChangeLog:
    """Audit log for temporal queries with versioning"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.entries: List[Dict[str, Any]] = []
        self.schema_versions: Dict[int, Dict] = {}
        self.sequence: int = 0
    
    def record_insert(self, entity_id: Any, data: Dict, timestamp: Optional[datetime] = None):
        """Record an insert operation"""
        self.sequence += 1
        timestamp = timestamp or datetime.now()
        self.entries.append({
            "sequence": self.sequence,
            "entity_id": entity_id,
            "timestamp": timestamp,
            "operation": "INSERT",
            "data": data.copy(),
            "schema_version": self._get_current_schema_version()
        })
    
    def record_update(self, entity_id: Any, before: Dict, after: Dict, 
                     timestamp: Optional[datetime] = None):
        """Record an update operation with before/after snapshots"""
        self.sequence += 1
        timestamp = timestamp or datetime.now()
        self.entries.append({
            "sequence": self.sequence,
            "entity_id": entity_id,
            "timestamp": timestamp,
            "operation": "UPDATE",
            "before": before.copy(),
            "after": after.copy(),
            "data": after.copy(),
            "schema_version": self._get_current_schema_version()
        })
    
    def record_delete(self, entity_id: Any, data: Dict, timestamp: Optional[datetime] = None):
        """Record a delete operation"""
        self.sequence += 1
        timestamp = timestamp or datetime.now()
        self.entries.append({
            "sequence": self.sequence,
            "entity_id": entity_id,
            "timestamp": timestamp,
            "operation": "DELETE",
            "data": data.copy(),
            "schema_version": self._get_current_schema_version()
        })
    
    def register_schema_version(self, version: int, schema: Dict):
        """Register a schema version"""
        self.schema_versions[version] = schema
    
    def get_at_timestamp(self, entity_id: Any, timestamp: datetime) -> Optional[Dict]:
        """Reconstruct entity state at specific timestamp"""
        state = None
        
        for entry in self.entries:
            if entry["entity_id"] != entity_id:
                continue
            if entry["timestamp"] > timestamp:
                break
            
            if entry["operation"] == "INSERT":
                state = entry["data"].copy()
            elif entry["operation"] == "UPDATE":
                if state:
                    state.update(entry["after"])
                else:
                    state = entry["data"].copy()
            elif entry["operation"] == "DELETE":
                state = None
        
        return state
    
    def get_history(self, entity_id: Any, time_range: Optional[TemporalRange] = None) -> List[TemporalSnapshot]:
        """Get change history for entity within optional time range"""
        history = []
        
        for entry in self.entries:
            if entry["entity_id"] != entity_id:
                continue
            
            ts = entry["timestamp"]
            if time_range and not time_range.contains(ts):
                continue
            
            snapshot = TemporalSnapshot(
                entity_id=entity_id,
                timestamp=ts,
                data=entry["data"],
                operation=entry["operation"],
                version=entry["sequence"],
                schema_version=entry["schema_version"]
            )
            history.append(snapshot)
        
        return history
    
    def _get_current_schema_version(self) -> int:
        """Get the current schema version"""
        return max(self.schema_versions.keys()) if self.schema_versions else 1


class TemporalQuery:
    """Time-travel query builder"""
    
    def __init__(self, table_name: str, changelog: TemporalChangeLog):
        self.table_name = table_name
        self.changelog = changelog
        self._at_timestamp: Optional[datetime] = None
        self._entity_ids: List[Any] = []
        self._time_range: Optional[TemporalRange] = None
    
    def at(self, timestamp: datetime) -> "TemporalQuery":
        """Query state at specific timestamp"""
        self._at_timestamp = timestamp
        return self
    
    def between(self, start: datetime, end: datetime) -> "TemporalQuery":
        """Query state between two timestamps"""
        self._time_range = TemporalRange(start=start, end=end)
        return self
    
    def where_id(self, entity_id: Any) -> "TemporalQuery":
        """Filter by entity ID"""
        self._entity_ids = [entity_id]
        return self
    
    def where_ids(self, entity_ids: List[Any]) -> "TemporalQuery":
        """Filter by multiple entity IDs"""
        self._entity_ids = entity_ids
        return self
    
    def get(self) -> Optional[Dict]:
        """Get single entity at temporal point"""
        if not self._entity_ids:
            return None
        
        entity_id = self._entity_ids[0]
        
        if self._at_timestamp:
            return self.changelog.get_at_timestamp(entity_id, self._at_timestamp)
        return None
    
    def all(self) -> List[Dict]:
        """Get all entities at temporal point"""
        if not self._at_timestamp:
            return []
        
        results = []
        for entry in self.changelog.entries:
            if self._entity_ids and entry["entity_id"] not in self._entity_ids:
                continue
            
            state = self.changelog.get_at_timestamp(entry["entity_id"], self._at_timestamp)
            if state and entry["entity_id"] not in [r.get("id") for r in results]:
                state["id"] = entry["entity_id"]
                results.append(state)
        
        return results
    
    def history(self) -> List[TemporalSnapshot]:
        """Get change history"""
        if not self._entity_ids:
            return []
        
        history = []
        for entity_id in self._entity_ids:
            history.extend(self.changelog.get_history(entity_id, self._time_range))
        
        return sorted(history, key=lambda x: x.timestamp)
    
    def changes_between(self, start: datetime, end: datetime) -> List[Dict]:
        """Get all changes in time range"""
        changes = []
        
        for entry in self.changelog.entries:
            ts = entry["timestamp"]
            if start <= ts <= end:
                if not self._entity_ids or entry["entity_id"] in self._entity_ids:
                    changes.append({
                        "entity_id": entry["entity_id"],
                        "timestamp": ts,
                        "operation": entry["operation"],
                        "data": entry.get("data"),
                        "before": entry.get("before"),
                        "after": entry.get("after")
                    })
        
        return sorted(changes, key=lambda x: x["timestamp"])


class TemporalQueryEngine:
    """Main temporal query engine"""
    
    def __init__(self):
        self.changelogs: Dict[str, TemporalChangeLog] = {}
    
    def create_table(self, table_name: str) -> TemporalChangeLog:
        """Create changelog for a table"""
        changelog = TemporalChangeLog(table_name)
        self.changelogs[table_name] = changelog
        return changelog
    
    def query(self, table_name: str) -> TemporalQuery:
        """Start a temporal query"""
        if table_name not in self.changelogs:
            self.create_table(table_name)
        
        return TemporalQuery(table_name, self.changelogs[table_name])
    
    def record_insert(self, table_name: str, entity_id: Any, data: Dict):
        """Record an insert"""
        if table_name not in self.changelogs:
            self.create_table(table_name)
        self.changelogs[table_name].record_insert(entity_id, data)
    
    def record_update(self, table_name: str, entity_id: Any, before: Dict, after: Dict):
        """Record an update"""
        if table_name not in self.changelogs:
            self.create_table(table_name)
        self.changelogs[table_name].record_update(entity_id, before, after)
    
    def record_delete(self, table_name: str, entity_id: Any, data: Dict):
        """Record a delete"""
        if table_name not in self.changelogs:
            self.create_table(table_name)
        self.changelogs[table_name].record_delete(entity_id, data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        stats = {}
        for table_name, changelog in self.changelogs.items():
            stats[table_name] = {
                "total_entries": len(changelog.entries),
                "sequence": changelog.sequence,
                "schema_versions": len(changelog.schema_versions),
                "unique_entities": len(set(e["entity_id"] for e in changelog.entries))
            }
        return stats


if __name__ == "__main__":
    print("✓ Temporal query engine module loaded successfully")
