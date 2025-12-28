"""
Change Data Capture (CDC) Stream - Real-time database change stream
Append-only change log with MVCC ordering and replay capability.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from queue import Queue, PriorityQueue
import json


class ChangeType(Enum):
    """Type of database change"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


@dataclass
class Change:
    """Represents a single database change"""
    sequence: int
    timestamp: datetime
    table_name: str
    change_type: ChangeType
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    transaction_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat(),
            "table": self.table_name,
            "type": self.change_type.value,
            "before": self.before,
            "after": self.after,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class ChangeFilter:
    """Filter for changes"""
    table_names: Optional[List[str]] = None
    change_types: Optional[List[ChangeType]] = None
    since_sequence: Optional[int] = None
    since_timestamp: Optional[datetime] = None
    columns: Optional[List[str]] = None
    
    def matches(self, change: Change) -> bool:
        """Check if change matches filter"""
        if self.table_names and change.table_name not in self.table_names:
            return False
        
        if self.change_types and change.change_type not in self.change_types:
            return False
        
        if self.since_sequence and change.sequence < self.since_sequence:
            return False
        
        if self.since_timestamp and change.timestamp < self.since_timestamp:
            return False
        
        return True


class ChangeLog:
    """Append-only change log"""
    
    def __init__(self, max_size: int = 100000):
        self.changes: List[Change] = []
        self.max_size = max_size
        self.sequence: int = 0
        self.transactions: Dict[int, List[int]] = {}  # transaction_id -> change sequences
        self.current_transaction_id: Optional[int] = None
    
    def begin_transaction(self) -> int:
        """Start a transaction"""
        self.current_transaction_id = len(self.transactions)
        self.transactions[self.current_transaction_id] = []
        return self.current_transaction_id
    
    def commit_transaction(self):
        """Commit a transaction"""
        self.current_transaction_id = None
    
    def rollback_transaction(self):
        """Rollback a transaction"""
        if self.current_transaction_id and self.current_transaction_id in self.transactions:
            del self.transactions[self.current_transaction_id]
        self.current_transaction_id = None
    
    def record_insert(self, table_name: str, after: Dict[str, Any], 
                     metadata: Optional[Dict] = None) -> int:
        """Record an insert"""
        self.sequence += 1
        
        change = Change(
            sequence=self.sequence,
            timestamp=datetime.now(),
            table_name=table_name,
            change_type=ChangeType.INSERT,
            after=after.copy(),
            metadata=metadata or {},
            transaction_id=self.current_transaction_id
        )
        
        self.changes.append(change)
        
        if self.current_transaction_id is not None:
            self.transactions[self.current_transaction_id].append(self.sequence)
        
        # Keep within max size with circular buffer
        if len(self.changes) > self.max_size:
            self.changes.pop(0)
        
        return self.sequence
    
    def record_update(self, table_name: str, before: Dict[str, Any], 
                     after: Dict[str, Any], metadata: Optional[Dict] = None) -> int:
        """Record an update"""
        self.sequence += 1
        
        change = Change(
            sequence=self.sequence,
            timestamp=datetime.now(),
            table_name=table_name,
            change_type=ChangeType.UPDATE,
            before=before.copy(),
            after=after.copy(),
            metadata=metadata or {},
            transaction_id=self.current_transaction_id
        )
        
        self.changes.append(change)
        
        if self.current_transaction_id is not None:
            self.transactions[self.current_transaction_id].append(self.sequence)
        
        if len(self.changes) > self.max_size:
            self.changes.pop(0)
        
        return self.sequence
    
    def record_delete(self, table_name: str, before: Dict[str, Any], 
                     metadata: Optional[Dict] = None) -> int:
        """Record a delete"""
        self.sequence += 1
        
        change = Change(
            sequence=self.sequence,
            timestamp=datetime.now(),
            table_name=table_name,
            change_type=ChangeType.DELETE,
            before=before.copy(),
            metadata=metadata or {},
            transaction_id=self.current_transaction_id
        )
        
        self.changes.append(change)
        
        if self.current_transaction_id is not None:
            self.transactions[self.current_transaction_id].append(self.sequence)
        
        if len(self.changes) > self.max_size:
            self.changes.pop(0)
        
        return self.sequence
    
    def get_changes(self, filter: Optional[ChangeFilter] = None) -> List[Change]:
        """Get changes matching filter"""
        results = []
        
        for change in self.changes:
            if filter and not filter.matches(change):
                continue
            results.append(change)
        
        return results
    
    def get_since(self, sequence: int, limit: Optional[int] = None) -> List[Change]:
        """Get changes since sequence"""
        results = []
        for change in self.changes:
            if change.sequence > sequence:
                results.append(change)
                if limit and len(results) >= limit:
                    break
        return results
    
    def get_transaction_changes(self, transaction_id: int) -> List[Change]:
        """Get all changes in a transaction"""
        if transaction_id not in self.transactions:
            return []
        
        sequences = self.transactions[transaction_id]
        return [c for c in self.changes if c.sequence in sequences]


class ChangeStream:
    """Streaming interface for changes"""
    
    def __init__(self, changelog: ChangeLog):
        self.changelog = changelog
        self.current_position = 0
        self.queue: Queue[Change] = Queue()
        self.subscribers: List[Callable[[Change], None]] = []
    
    def subscribe(self, callback: Callable[[Change], None]):
        """Subscribe to changes"""
        self.subscribers.append(callback)
    
    def publish_change(self, change: Change):
        """Publish a change to all subscribers"""
        self.queue.put(change)
        
        for subscriber in self.subscribers:
            try:
                subscriber(change)
            except Exception as e:
                print(f"Error in subscriber: {e}")
    
    def consume(self, filter: Optional[ChangeFilter] = None, 
               timeout: Optional[float] = None) -> Optional[Change]:
        """Consume a change from stream"""
        try:
            change = self.queue.get(timeout=timeout)
            if filter and filter.matches(change):
                return change
            # Try again if doesn't match
            return self.consume(filter, timeout)
        except:
            return None
    
    def replay(self, from_sequence: int = 0, 
              filter: Optional[ChangeFilter] = None) -> List[Change]:
        """Replay changes from sequence"""
        changes = self.changelog.get_since(from_sequence)
        
        if filter:
            changes = [c for c in changes if filter.matches(c)]
        
        return changes


class CDCStream:
    """Main Change Data Capture stream"""
    
    def __init__(self, max_changelog_size: int = 100000):
        self.changelog = ChangeLog(max_changelog_size)
        self.streams: Dict[str, ChangeStream] = {}
    
    def create_stream(self, name: str) -> ChangeStream:
        """Create a named change stream"""
        stream = ChangeStream(self.changelog)
        self.streams[name] = stream
        return stream
    
    def get_stream(self, name: str) -> Optional[ChangeStream]:
        """Get a named stream"""
        return self.streams.get(name)
    
    def record_change(self, table_name: str, change_type: ChangeType,
                     before: Optional[Dict] = None, after: Optional[Dict] = None,
                     metadata: Optional[Dict] = None):
        """Record a database change"""
        sequence = None
        
        if change_type == ChangeType.INSERT:
            sequence = self.changelog.record_insert(table_name, after or {}, metadata)
        elif change_type == ChangeType.UPDATE:
            sequence = self.changelog.record_update(table_name, before or {}, 
                                                   after or {}, metadata)
        elif change_type == ChangeType.DELETE:
            sequence = self.changelog.record_delete(table_name, before or {}, metadata)
        
        # Publish to all streams
        if sequence:
            change = self.changelog.changes[-1]
            for stream in self.streams.values():
                stream.publish_change(change)
    
    def begin_transaction(self) -> int:
        """Start a transaction"""
        return self.changelog.begin_transaction()
    
    def commit_transaction(self):
        """Commit current transaction"""
        self.changelog.commit_transaction()
    
    def get_changelog(self, filter: Optional[ChangeFilter] = None) -> List[Dict]:
        """Get changelog as list of dicts"""
        changes = self.changelog.get_changes(filter)
        return [c.to_dict() for c in changes]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get CDC statistics"""
        return {
            "total_changes": len(self.changelog.changes),
            "current_sequence": self.changelog.sequence,
            "active_streams": len(self.streams),
            "transactions": len(self.changelog.transactions),
            "max_changelog_size": self.changelog.max_size
        }


if __name__ == "__main__":
    print("✓ Change Data Capture stream module loaded successfully")
