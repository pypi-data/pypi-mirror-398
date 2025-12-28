"""
Online DDL - Zero-downtime schema changes
Dual-write, validation, and atomic cut-over without table locks.
"""

from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class MigrationStatus(Enum):
    """Status of an online migration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    READY_CUTOVER = "READY_CUTOVER"
    CUTOVER_IN_PROGRESS = "CUTOVER_IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


@dataclass
class SchemaChange:
    """Represents a schema change operation"""
    id: str
    table: str
    description: str
    old_schema: Dict[str, Any]
    new_schema: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MigrationProgress:
    """Tracks migration progress"""
    migration_id: str
    status: MigrationStatus
    rows_processed: int = 0
    rows_total: int = 0
    consistency_errors: int = 0
    shadow_traffic_errors: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def progress_percent(self) -> float:
        """Get progress percentage"""
        if self.rows_total == 0:
            return 0.0
        return (self.rows_processed / self.rows_total) * 100
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed seconds"""
        if self.start_time is None:
            return 0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


class DualWriteManager:
    """Manages dual-write to old and new schema"""
    
    def __init__(self):
        self.writes_to_old: List[Dict] = []
        self.writes_to_new: List[Dict] = []
        self.write_enabled = False
    
    def enable_dual_write(self):
        """Enable dual-write mode"""
        self.write_enabled = True
    
    def disable_dual_write(self):
        """Disable dual-write mode"""
        self.write_enabled = False
    
    def write(self, data: Dict[str, Any], schema_version: int = 1):
        """Write to both schemas"""
        if not self.write_enabled:
            return
        
        if schema_version == 1:
            self.writes_to_old.append(data.copy())
            # Transform and write to new
            transformed = self._transform_to_new(data)
            self.writes_to_new.append(transformed)
        else:
            self.writes_to_new.append(data.copy())
            # Transform and write to old
            transformed = self._transform_to_old(data)
            self.writes_to_old.append(transformed)
    
    def _transform_to_new(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data from old to new schema"""
        # This is where schema transformation logic goes
        return data.copy()
    
    def _transform_to_old(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data from new to old schema"""
        return data.copy()
    
    def get_write_lag(self) -> int:
        """Get lag between old and new writes"""
        return abs(len(self.writes_to_old) - len(self.writes_to_new))


class ConsistencyValidator:
    """Validates data consistency between old and new schema"""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
    
    def validate_row(self, old_row: Dict, new_row: Dict, row_id: Any) -> bool:
        """Validate a single row consistency"""
        errors = []
        
        # Check all columns exist
        for key in old_row:
            if key not in new_row:
                errors.append(f"Column {key} missing in new schema")
        
        # Check data types (simplified)
        for key in old_row:
            if key in new_row:
                old_val = old_row[key]
                new_val = new_row[key]
                
                if type(old_val) != type(new_val):
                    # Allow some type conversions
                    if not self._is_compatible_type(old_val, new_val):
                        errors.append(f"Type mismatch for {key}: {type(old_val)} vs {type(new_val)}")
        
        if errors:
            self.errors.append({
                "row_id": row_id,
                "errors": errors
            })
            return False
        
        return True
    
    def _is_compatible_type(self, old_val: Any, new_val: Any) -> bool:
        """Check if types are compatible"""
        # String to int, int to string conversions allowed
        if isinstance(old_val, (int, str)) and isinstance(new_val, (int, str)):
            return True
        return False
    
    def validate_batch(self, old_rows: List[Dict], new_rows: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Validate a batch of rows"""
        if len(old_rows) != len(new_rows):
            return False, [{"error": "Row count mismatch"}]
        
        errors = []
        for i, (old_row, new_row) in enumerate(zip(old_rows, new_rows)):
            if not self.validate_row(old_row, new_row, i):
                errors.extend(self.errors)
        
        return len(errors) == 0, errors
    
    def get_error_count(self) -> int:
        """Get total error count"""
        return len(self.errors)


class ShadowTrafficTester:
    """Tests new schema with shadow traffic"""
    
    def __init__(self):
        self.traffic_log: List[Dict] = []
        self.errors: List[Dict] = []
    
    def test_query(self, query: str, old_result: Any, new_result: Any) -> bool:
        """Test query result matches"""
        log_entry = {
            "query": query,
            "old_result": old_result,
            "new_result": new_result,
            "match": old_result == new_result
        }
        self.traffic_log.append(log_entry)
        
        if not log_entry["match"]:
            self.errors.append({
                "query": query,
                "error": "Results don't match"
            })
            return False
        
        return True
    
    def get_error_rate(self) -> float:
        """Get error rate percentage"""
        if len(self.traffic_log) == 0:
            return 0.0
        return (len(self.errors) / len(self.traffic_log)) * 100


class OnlineDDL:
    """Main online DDL manager"""
    
    def __init__(self):
        self.migrations: Dict[str, MigrationProgress] = {}
        self.dual_write_manager = DualWriteManager()
        self.consistency_validator = ConsistencyValidator()
        self.shadow_traffic_tester = ShadowTrafficTester()
        self.migration_count = 0
    
    def start_migration(self, table: str, schema_change: SchemaChange) -> str:
        """Start an online DDL migration"""
        migration_id = f"migration_{self.migration_count}"
        self.migration_count += 1
        
        progress = MigrationProgress(
            migration_id=migration_id,
            status=MigrationStatus.PENDING,
            start_time=datetime.now()
        )
        
        self.migrations[migration_id] = progress
        
        # Start dual-write mode
        self.dual_write_manager.enable_dual_write()
        
        return migration_id
    
    def get_migration_status(self, migration_id: str) -> Optional[MigrationProgress]:
        """Get status of a migration"""
        return self.migrations.get(migration_id)
    
    def simulate_progress(self, migration_id: str, rows_processed: int):
        """Simulate migration progress"""
        if migration_id in self.migrations:
            progress = self.migrations[migration_id]
            progress.rows_processed = rows_processed
            progress.status = MigrationStatus.RUNNING
    
    def validate_migration(self, migration_id: str, 
                          old_rows: List[Dict], new_rows: List[Dict]) -> bool:
        """Validate migration correctness"""
        if migration_id not in self.migrations:
            return False
        
        progress = self.migrations[migration_id]
        progress.status = MigrationStatus.VALIDATING
        
        valid, errors = self.consistency_validator.validate_batch(old_rows, new_rows)
        progress.consistency_errors = len(errors)
        
        return valid
    
    def test_shadow_traffic(self, migration_id: str, query: str,
                           old_result: Any, new_result: Any) -> bool:
        """Test shadow traffic"""
        if migration_id not in self.migrations:
            return False
        
        return self.shadow_traffic_tester.test_query(query, old_result, new_result)
    
    def ready_cutover(self, migration_id: str) -> bool:
        """Check if migration is ready for cutover"""
        if migration_id not in self.migrations:
            return False
        
        progress = self.migrations[migration_id]
        
        # Check conditions
        if progress.consistency_errors > 0:
            return False
        
        error_rate = self.shadow_traffic_tester.get_error_rate()
        if error_rate > 1.0:  # Allow 1% error tolerance
            return False
        
        progress.status = MigrationStatus.READY_CUTOVER
        return True
    
    def perform_cutover(self, migration_id: str) -> bool:
        """Perform atomic cutover to new schema"""
        if migration_id not in self.migrations:
            return False
        
        progress = self.migrations[migration_id]
        progress.status = MigrationStatus.CUTOVER_IN_PROGRESS
        
        # Stop dual-write
        self.dual_write_manager.disable_dual_write()
        
        # Atomic switch (in real implementation, this would be database-level)
        progress.status = MigrationStatus.COMPLETED
        progress.end_time = datetime.now()
        
        return True
    
    def rollback_migration(self, migration_id: str) -> bool:
        """Rollback a migration"""
        if migration_id not in self.migrations:
            return False
        
        progress = self.migrations[migration_id]
        progress.status = MigrationStatus.ROLLED_BACK
        progress.end_time = datetime.now()
        
        self.dual_write_manager.disable_dual_write()
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get DDL statistics"""
        completed = sum(1 for m in self.migrations.values() 
                       if m.status == MigrationStatus.COMPLETED)
        failed = sum(1 for m in self.migrations.values() 
                    if m.status == MigrationStatus.FAILED)
        
        return {
            "total_migrations": len(self.migrations),
            "completed": completed,
            "failed": failed,
            "dual_write_lag": self.dual_write_manager.get_write_lag(),
            "consistency_errors": self.consistency_validator.get_error_count(),
            "shadow_traffic_errors": len(self.shadow_traffic_tester.errors)
        }


if __name__ == "__main__":
    print("✓ Online DDL module loaded successfully")
