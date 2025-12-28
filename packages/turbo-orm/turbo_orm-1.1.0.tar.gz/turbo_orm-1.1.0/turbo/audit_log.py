"""
Audit Logging - Comprehensive audit trails for compliance and forensics
Records all database operations with user, timestamp, changes, and context.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict
import json


class AuditLevel(Enum):
    """Audit logging levels"""
    BASIC = "BASIC"           # Only operation type and table
    DETAILED = "DETAILED"     # Include before/after values
    COMPREHENSIVE = "COMPREHENSIVE"  # Full context, user, IP, stack trace


class OperationType(Enum):
    """Database operations to audit"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRUNCATE = "TRUNCATE"
    ALTER_TABLE = "ALTER_TABLE"
    CREATE_TABLE = "CREATE_TABLE"
    DROP_TABLE = "DROP_TABLE"
    GRANT = "GRANT"
    REVOKE = "REVOKE"


@dataclass
class AuditEntry:
    """Single audit log entry"""
    entry_id: str
    timestamp: datetime
    operation_type: OperationType
    table_name: str
    user_id: str
    session_id: str
    
    # Change tracking
    record_id: Optional[str] = None
    before_values: Dict[str, Any] = field(default_factory=dict)
    after_values: Dict[str, Any] = field(default_factory=dict)
    affected_rows: int = 0
    
    # Context
    ip_address: Optional[str] = None
    application_name: Optional[str] = None
    error_message: Optional[str] = None
    
    # Query details
    query_text: Optional[str] = None
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "operation_type": self.operation_type.value,
            "table_name": self.table_name,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "record_id": self.record_id,
            "before_values": self.before_values,
            "after_values": self.after_values,
            "affected_rows": self.affected_rows,
            "ip_address": self.ip_address,
            "application_name": self.application_name,
            "error_message": self.error_message,
            "query_text": self.query_text,
            "execution_time_ms": self.execution_time_ms
        }


class ChangeTracker:
    """Track changes for audit entries"""
    
    @staticmethod
    def get_changes(before: Dict[str, Any], after: Dict[str, Any]) -> Tuple[Dict, Dict]:
        """Compare before/after values"""
        changed_before = {}
        changed_after = {}
        
        all_keys = set(before.keys()) | set(after.keys())
        
        for key in all_keys:
            before_val = before.get(key)
            after_val = after.get(key)
            
            if before_val != after_val:
                changed_before[key] = before_val
                changed_after[key] = after_val
        
        return changed_before, changed_after
    
    @staticmethod
    def generate_change_summary(before: Dict, after: Dict) -> str:
        """Generate human-readable change summary"""
        changed_before, changed_after = ChangeTracker.get_changes(before, after)
        
        if not changed_before:
            return "No changes"
        
        summaries = []
        for key in changed_before.keys():
            summaries.append(f"{key}: {changed_before[key]} → {changed_after[key]}")
        
        return "; ".join(summaries)


class AuditLogger:
    """Main audit logging system"""
    
    def __init__(self, level: AuditLevel = AuditLevel.DETAILED):
        self.audit_level = level
        self.audit_trail: List[AuditEntry] = []
        self.entry_count = 0
        self.statistics = defaultdict(int)
    
    def log_operation(
        self,
        operation: OperationType,
        table_name: str,
        user_id: str,
        session_id: str,
        record_id: Optional[str] = None,
        before_values: Optional[Dict] = None,
        after_values: Optional[Dict] = None,
        affected_rows: int = 0,
        ip_address: Optional[str] = None,
        application_name: Optional[str] = None,
        query_text: Optional[str] = None,
        execution_time_ms: float = 0.0
    ) -> AuditEntry:
        """Log a database operation"""
        
        entry_id = f"audit_{self.entry_count:08d}"
        self.entry_count += 1
        
        # Filter sensitive data based on audit level
        if self.audit_level == AuditLevel.BASIC:
            before_values = {}
            after_values = {}
        elif self.audit_level == AuditLevel.DETAILED:
            query_text = None
        
        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            operation_type=operation,
            table_name=table_name,
            user_id=user_id,
            session_id=session_id,
            record_id=record_id,
            before_values=before_values or {},
            after_values=after_values or {},
            affected_rows=affected_rows,
            ip_address=ip_address,
            application_name=application_name,
            query_text=query_text,
            execution_time_ms=execution_time_ms
        )
        
        self.audit_trail.append(entry)
        self.statistics[operation.value] += 1
        self.statistics["total_operations"] += 1
        
        return entry
    
    def log_select(self, table: str, user_id: str, session_id: str, 
                   rows_returned: int = 0, **kwargs) -> AuditEntry:
        """Log SELECT operation"""
        return self.log_operation(OperationType.SELECT, table, user_id, session_id,
                                affected_rows=rows_returned, **kwargs)
    
    def log_insert(self, table: str, user_id: str, session_id: str,
                   record_id: str, values: Dict, **kwargs) -> AuditEntry:
        """Log INSERT operation"""
        return self.log_operation(OperationType.INSERT, table, user_id, session_id,
                                record_id=record_id, after_values=values,
                                affected_rows=1, **kwargs)
    
    def log_update(self, table: str, user_id: str, session_id: str,
                   record_id: str, before: Dict, after: Dict, **kwargs) -> AuditEntry:
        """Log UPDATE operation"""
        return self.log_operation(OperationType.UPDATE, table, user_id, session_id,
                                record_id=record_id, before_values=before,
                                after_values=after, affected_rows=1, **kwargs)
    
    def log_delete(self, table: str, user_id: str, session_id: str,
                   record_id: str, values: Dict, **kwargs) -> AuditEntry:
        """Log DELETE operation"""
        return self.log_operation(OperationType.DELETE, table, user_id, session_id,
                                record_id=record_id, before_values=values,
                                affected_rows=1, **kwargs)
    
    def log_schema_change(self, operation: str, table: str, user_id: str, 
                         session_id: str, changes: str, **kwargs) -> AuditEntry:
        """Log schema changes (ALTER, CREATE, DROP)"""
        op_type = OperationType[operation.upper()]
        return self.log_operation(op_type, table, user_id, session_id,
                                after_values={"changes": changes}, **kwargs)
    
    def get_audit_trail(self, 
                       table_name: Optional[str] = None,
                       user_id: Optional[str] = None,
                       operation_type: Optional[OperationType] = None,
                       limit: int = 100) -> List[AuditEntry]:
        """Query audit trail with filters"""
        results = self.audit_trail
        
        if table_name:
            results = [e for e in results if e.table_name == table_name]
        
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        
        if operation_type:
            results = [e for e in results if e.operation_type == operation_type]
        
        # Return most recent first
        return sorted(results, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def get_user_activity(self, user_id: str, limit: int = 50) -> List[AuditEntry]:
        """Get all activities by a user"""
        return sorted(
            [e for e in self.audit_trail if e.user_id == user_id],
            key=lambda e: e.timestamp,
            reverse=True
        )[:limit]
    
    def get_table_changes(self, table_name: str, limit: int = 100) -> List[AuditEntry]:
        """Get all changes to a specific table"""
        changes = [e for e in self.audit_trail 
                  if e.table_name == table_name 
                  and e.operation_type in [OperationType.INSERT, OperationType.UPDATE, OperationType.DELETE]]
        return sorted(changes, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def get_record_history(self, table_name: str, record_id: str) -> List[AuditEntry]:
        """Get complete history of a single record"""
        return sorted(
            [e for e in self.audit_trail 
             if e.table_name == table_name and e.record_id == record_id],
            key=lambda e: e.timestamp
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        operations_by_type = defaultdict(int)
        operations_by_user = defaultdict(int)
        operations_by_table = defaultdict(int)
        
        for entry in self.audit_trail:
            operations_by_type[entry.operation_type.value] += 1
            operations_by_user[entry.user_id] += 1
            operations_by_table[entry.table_name] += 1
        
        return {
            "total_operations": len(self.audit_trail),
            "operations_by_type": dict(operations_by_type),
            "operations_by_user": dict(operations_by_user),
            "operations_by_table": dict(operations_by_table),
            "total_users": len(operations_by_user),
            "total_tables": len(operations_by_table)
        }


class ComplianceReporter:
    """Generate compliance reports from audit logs"""
    
    def __init__(self, audit_logger: AuditLogger):
        self.logger = audit_logger
    
    def generate_access_report(self, table_name: str) -> Dict[str, Any]:
        """Generate table access report"""
        entries = self.logger.get_table_changes(table_name, limit=1000)
        
        users = set(e.user_id for e in entries)
        operations = defaultdict(int)
        
        for entry in entries:
            operations[entry.operation_type.value] += 1
        
        return {
            "table_name": table_name,
            "total_access_count": len(entries),
            "unique_users": len(users),
            "users": list(users),
            "operations": dict(operations),
            "date_range": {
                "earliest": entries[-1].timestamp.isoformat() if entries else None,
                "latest": entries[0].timestamp.isoformat() if entries else None
            }
        }
    
    def generate_user_activity_report(self, user_id: str) -> Dict[str, Any]:
        """Generate user activity report"""
        entries = self.logger.get_user_activity(user_id, limit=1000)
        
        operations = defaultdict(int)
        tables = set()
        
        for entry in entries:
            operations[entry.operation_type.value] += 1
            tables.add(entry.table_name)
        
        return {
            "user_id": user_id,
            "total_operations": len(entries),
            "tables_accessed": len(tables),
            "operations": dict(operations),
            "tables": list(tables),
            "date_range": {
                "earliest": entries[-1].timestamp.isoformat() if entries else None,
                "latest": entries[0].timestamp.isoformat() if entries else None
            }
        }
    
    def generate_compliance_summary(self) -> Dict[str, Any]:
        """Generate overall compliance summary"""
        stats = self.logger.get_statistics()
        
        return {
            "audit_level": self.logger.audit_level.value,
            "total_entries": stats["total_operations"],
            "coverage": {
                "tables": stats["total_tables"],
                "users": stats["total_users"],
                "operation_types": len(stats["operations_by_type"])
            },
            "top_operations": sorted(
                stats["operations_by_type"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "top_users": sorted(
                stats["operations_by_user"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


if __name__ == "__main__":
    print("✓ Audit logging module loaded successfully")
