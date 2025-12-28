"""
HA Manager - Automatic database failover
Real-time replica health monitoring and automatic promotion.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading


class ReplicaStatus(Enum):
    """Status of a database replica"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class FailoverStrategy(Enum):
    """Strategy for failover"""
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"
    CONSENSUS = "CONSENSUS"


@dataclass
class ReplicaHealth:
    """Health metrics for a replica"""
    replica_id: str
    status: ReplicaStatus = ReplicaStatus.UNKNOWN
    lag_seconds: float = 0.0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    successful_pings: int = 0
    failed_pings: int = 0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    
    @property
    def is_healthy(self) -> bool:
        return self.status == ReplicaStatus.HEALTHY
    
    @property
    def is_up_to_date(self) -> bool:
        return self.lag_seconds < 1.0  # Less than 1 second lag


@dataclass
class Database:
    """Database instance"""
    id: str
    host: str
    port: int = 5432
    is_primary: bool = False
    is_read_only: bool = False
    health: ReplicaHealth = field(default_factory=lambda: ReplicaHealth(""))
    
    def __post_init__(self):
        self.health.replica_id = self.id


class HealthMonitor:
    """Monitors replica health"""
    
    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self.replicas: Dict[str, ReplicaHealth] = {}
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
    
    def register_replica(self, replica_id: str) -> ReplicaHealth:
        """Register a replica to monitor"""
        health = ReplicaHealth(replica_id=replica_id)
        self.replicas[replica_id] = health
        return health
    
    def start_monitoring(self):
        """Start health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            for replica_id, health in self.replicas.items():
                self._check_replica_health(health)
            
            # Sleep before next check
            threading.Event().wait(self.check_interval)
    
    def _check_replica_health(self, health: ReplicaHealth):
        """Check health of a single replica"""
        # Simulate health check
        import random
        
        health.last_heartbeat = datetime.now()
        
        # Simulate response
        is_responding = random.random() > 0.1  # 90% healthy
        
        if is_responding:
            health.successful_pings += 1
            health.lag_seconds = random.uniform(0, 2)
            health.cpu_percent = random.uniform(10, 80)
            health.memory_percent = random.uniform(20, 70)
            health.disk_percent = random.uniform(30, 90)
            
            # Determine status based on metrics
            if health.lag_seconds > 5:
                health.status = ReplicaStatus.DEGRADED
            else:
                health.status = ReplicaStatus.HEALTHY
        else:
            health.failed_pings += 1
            health.status = ReplicaStatus.UNHEALTHY
    
    def get_healthy_replicas(self) -> List[ReplicaHealth]:
        """Get all healthy replicas"""
        return [h for h in self.replicas.values() if h.is_healthy]
    
    def get_best_replica(self) -> Optional[ReplicaHealth]:
        """Get replica with best health"""
        healthy = self.get_healthy_replicas()
        if not healthy:
            return None
        
        # Return replica with lowest lag
        return min(healthy, key=lambda h: h.lag_seconds)


class FailoverCoordinator:
    """Coordinates failover operations"""
    
    def __init__(self, strategy: FailoverStrategy = FailoverStrategy.AUTOMATIC):
        self.strategy = strategy
        self.failover_history: List[Dict[str, Any]] = []
        self.failover_in_progress = False
    
    def should_failover(self, primary_health: ReplicaHealth) -> bool:
        """Check if failover should occur"""
        if self.failover_in_progress:
            return False
        
        # Failover if primary is unhealthy
        return primary_health.status == ReplicaStatus.UNHEALTHY
    
    def execute_failover(self, current_primary: Database, 
                        new_primary: Database,
                        replicas: List[Database]) -> bool:
        """Execute failover to new primary"""
        if self.failover_in_progress:
            return False
        
        self.failover_in_progress = True
        
        try:
            # Log failover
            self.failover_history.append({
                "timestamp": datetime.now().isoformat(),
                "old_primary": current_primary.id,
                "new_primary": new_primary.id,
                "status": "IN_PROGRESS"
            })
            
            # Stop replication on new primary
            new_primary.is_read_only = False
            
            # Read-only old primary
            current_primary.is_read_only = True
            
            # Update DNS/connection strings
            current_primary.is_primary = False
            new_primary.is_primary = True
            
            # Update other replicas to replicate from new primary
            for replica in replicas:
                if replica.id != new_primary.id:
                    # Reset replication source
                    pass
            
            # Update history
            self.failover_history[-1]["status"] = "COMPLETED"
            
            return True
        
        except Exception as e:
            self.failover_history[-1]["status"] = "FAILED"
            self.failover_history[-1]["error"] = str(e)
            return False
        
        finally:
            self.failover_in_progress = False
    
    def consensus_failover(self, primary: Database, replicas: List[Database],
                          voting_threshold: float = 0.5) -> Optional[Database]:
        """Perform consensus-based failover"""
        healthy_replicas = [r for r in replicas if r.health.is_healthy]
        
        if not healthy_replicas:
            return None
        
        # Majority vote on new primary
        votes = {}
        for replica in healthy_replicas:
            # In real implementation, query replica for readiness
            votes[replica.id] = 1
        
        total_votes = len(votes)
        if total_votes == 0:
            return None
        
        # Winner needs majority
        for replica_id, count in votes.items():
            if count / total_votes >= voting_threshold:
                return next((r for r in replicas if r.id == replica_id), None)
        
        return None


class HAManager:
    """Main HA management system"""
    
    def __init__(self, strategy: FailoverStrategy = FailoverStrategy.AUTOMATIC):
        self.strategy = strategy
        self.primary: Optional[Database] = None
        self.replicas: List[Database] = []
        self.health_monitor = HealthMonitor()
        self.failover_coordinator = FailoverCoordinator(strategy)
        self.connection_pool_ready = False
    
    def register_primary(self, database: Database):
        """Register primary database"""
        database.is_primary = True
        database.health = ReplicaHealth(replica_id=database.id)
        self.primary = database
        self.health_monitor.register_replica(database.id)
    
    def register_replica(self, database: Database):
        """Register a replica"""
        database.is_primary = False
        database.health = ReplicaHealth(replica_id=database.id)
        self.replicas.append(database)
        self.health_monitor.register_replica(database.id)
    
    def start_monitoring(self):
        """Start health monitoring"""
        self.health_monitor.start_monitoring()
    
    def check_and_failover(self) -> bool:
        """Check health and perform failover if needed"""
        if not self.primary or not self.replicas:
            return False
        
        # Check if failover needed
        if not self.failover_coordinator.should_failover(self.primary.health):
            return False
        
        # Select new primary based on strategy
        if self.strategy == FailoverStrategy.AUTOMATIC:
            new_primary = self.health_monitor.get_best_replica()
        elif self.strategy == FailoverStrategy.CONSENSUS:
            new_primary = self.failover_coordinator.consensus_failover(
                self.primary, self.replicas
            )
        else:
            return False
        
        if not new_primary:
            return False
        
        # Execute failover
        success = self.failover_coordinator.execute_failover(
            self.primary, new_primary, self.replicas
        )
        
        if success:
            # Update topology
            self.primary = new_primary
            self.replicas = [r for r in self.replicas + [self.primary] if r.id != new_primary.id]
        
        return success
    
    def get_status(self) -> Dict[str, Any]:
        """Get HA status"""
        return {
            "primary": {
                "id": self.primary.id if self.primary else None,
                "status": self.primary.health.status.value if self.primary else None,
                "lag": self.primary.health.lag_seconds if self.primary else None
            },
            "replicas": [
                {
                    "id": r.id,
                    "status": r.health.status.value,
                    "lag": r.health.lag_seconds,
                    "healthy": r.health.is_healthy
                }
                for r in self.replicas
            ],
            "healthy_replicas": len(self.health_monitor.get_healthy_replicas()),
            "failover_count": len(self.failover_coordinator.failover_history),
            "failover_in_progress": self.failover_coordinator.failover_in_progress
        }
    
    def get_failover_history(self) -> List[Dict[str, Any]]:
        """Get failover history"""
        return self.failover_coordinator.failover_history


if __name__ == "__main__":
    print("✓ HA manager module loaded successfully")
