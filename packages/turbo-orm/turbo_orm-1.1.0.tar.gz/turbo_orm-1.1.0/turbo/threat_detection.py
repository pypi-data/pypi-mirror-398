"""
Threat Detection - Real-time anomaly detection and security threat scoring
Identifies suspicious patterns, unusual access, and potential attacks.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics


class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyType(Enum):
    """Types of detected anomalies"""
    UNUSUAL_ACCESS_TIME = "UNUSUAL_ACCESS_TIME"
    BULK_DATA_EXPORT = "BULK_DATA_EXPORT"
    FAILED_LOGIN_ATTEMPTS = "FAILED_LOGIN_ATTEMPTS"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    UNUSUAL_QUERY_PATTERN = "UNUSUAL_QUERY_PATTERN"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    CONCURRENT_ACCESS = "CONCURRENT_ACCESS"
    LATERAL_MOVEMENT = "LATERAL_MOVEMENT"
    MALFORMED_QUERY = "MALFORMED_QUERY"


@dataclass
class ThreatAlert:
    """Security threat alert"""
    alert_id: str
    timestamp: datetime
    threat_level: ThreatLevel
    anomaly_type: AnomalyType
    
    user_id: str
    ip_address: Optional[str] = None
    table_affected: Optional[str] = None
    
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    threat_score: float = 0.0
    recommended_action: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "threat_level": self.threat_level.value,
            "anomaly_type": self.anomaly_type.value,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "table_affected": self.table_affected,
            "description": self.description,
            "evidence": self.evidence,
            "threat_score": self.threat_score,
            "recommended_action": self.recommended_action
        }


class UserBehaviorProfile:
    """User behavior baseline for anomaly detection"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.access_times: deque = deque(maxlen=100)
        self.accessed_tables: Dict[str, int] = defaultdict(int)
        self.query_sizes: deque = deque(maxlen=100)
        self.failed_attempts = 0
        self.last_access: Optional[datetime] = None
        self.ip_addresses: set = set()
    
    def record_access(self, timestamp: datetime, table: str, rows: int, ip: str):
        """Record user access"""
        hour = timestamp.hour
        self.access_times.append(hour)
        self.accessed_tables[table] += 1
        self.query_sizes.append(rows)
        self.last_access = timestamp
        self.ip_addresses.add(ip)
    
    def is_unusual_time(self, timestamp: datetime) -> bool:
        """Detect access at unusual times"""
        if len(self.access_times) < 10:
            return False
        
        current_hour = timestamp.hour
        hours = list(self.access_times)
        
        # Check if access is outside normal hours
        avg_hour = statistics.mean(hours)
        std_dev = statistics.stdev(hours) if len(hours) > 1 else 0
        
        if std_dev > 0:
            z_score = abs(current_hour - avg_hour) / std_dev
            return z_score > 2.5  # More than 2.5 std devs away
        
        return False
    
    def get_avg_query_size(self) -> float:
        """Get average query size"""
        if not self.query_sizes:
            return 0
        return statistics.mean(self.query_sizes)
    
    def is_bulk_export(self, rows: int) -> bool:
        """Detect bulk data export"""
        if len(self.query_sizes) < 5:
            return False
        
        avg_size = self.get_avg_query_size()
        return rows > avg_size * 10  # 10x normal query size


class AnomalyDetector:
    """Detects security anomalies"""
    
    def __init__(self):
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.alert_count = 0
    
    def get_or_create_profile(self, user_id: str) -> UserBehaviorProfile:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(user_id)
        return self.user_profiles[user_id]
    
    def check_unusual_access_time(self, user_id: str, timestamp: datetime, 
                                  ip: str) -> Optional[ThreatAlert]:
        """Detect unusual access time"""
        profile = self.get_or_create_profile(user_id)
        
        if profile.is_unusual_time(timestamp):
            alert_id = f"threat_{self.alert_count:06d}"
            self.alert_count += 1
            
            return ThreatAlert(
                alert_id=alert_id,
                timestamp=timestamp,
                threat_level=ThreatLevel.LOW,
                anomaly_type=AnomalyType.UNUSUAL_ACCESS_TIME,
                user_id=user_id,
                ip_address=ip,
                description=f"User accessed database at unusual hour: {timestamp.hour}:00",
                threat_score=0.3
            )
        
        return None
    
    def check_bulk_export(self, user_id: str, table: str, rows: int,
                         timestamp: datetime, ip: str) -> Optional[ThreatAlert]:
        """Detect bulk data export"""
        profile = self.get_or_create_profile(user_id)
        
        if profile.is_bulk_export(rows):
            alert_id = f"threat_{self.alert_count:06d}"
            self.alert_count += 1
            
            return ThreatAlert(
                alert_id=alert_id,
                timestamp=timestamp,
                threat_level=ThreatLevel.HIGH,
                anomaly_type=AnomalyType.BULK_DATA_EXPORT,
                user_id=user_id,
                ip_address=ip,
                table_affected=table,
                description=f"Bulk data export detected: {rows} rows (avg: {profile.get_avg_query_size():.0f})",
                evidence={"rows_exported": rows, "user_avg_query": profile.get_avg_query_size()},
                threat_score=0.8,
                recommended_action="Review user permissions and monitor for data exfiltration"
            )
        
        return None
    
    def check_new_ip_address(self, user_id: str, ip: str, 
                            timestamp: datetime) -> Optional[ThreatAlert]:
        """Detect access from new IP address"""
        profile = self.get_or_create_profile(user_id)
        
        if len(profile.ip_addresses) > 0 and ip not in profile.ip_addresses:
            alert_id = f"threat_{self.alert_count:06d}"
            self.alert_count += 1
            
            return ThreatAlert(
                alert_id=alert_id,
                timestamp=timestamp,
                threat_level=ThreatLevel.MEDIUM,
                anomaly_type=AnomalyType.LATERAL_MOVEMENT,
                user_id=user_id,
                ip_address=ip,
                description=f"Access from new IP address: {ip}",
                evidence={"new_ip": ip, "known_ips": list(profile.ip_addresses)},
                threat_score=0.5,
                recommended_action="Verify user identity and account access"
            )
        
        return None


class ThreatScorer:
    """Calculates threat scores based on multiple factors"""
    
    @staticmethod
    def calculate_threat_score(
        anomaly_indicators: Dict[str, float],
        user_risk_level: float = 0.0,
        historical_severity: float = 0.0
    ) -> float:
        """Calculate overall threat score (0.0 - 1.0)"""
        
        # Weight factors
        weights = {
            "bulk_export": 0.35,
            "unusual_access": 0.20,
            "privilege_escalation": 0.25,
            "failed_attempts": 0.15,
            "malformed_query": 0.05
        }
        
        weighted_score = 0.0
        
        for factor, weight in weights.items():
            if factor in anomaly_indicators:
                weighted_score += anomaly_indicators[factor] * weight
        
        # Apply user risk multiplier
        weighted_score *= (1.0 + user_risk_level * 0.5)
        
        # Consider historical severity
        weighted_score = (weighted_score * 0.8) + (historical_severity * 0.2)
        
        return min(1.0, max(0.0, weighted_score))
    
    @staticmethod
    def get_threat_level(score: float) -> ThreatLevel:
        """Get threat level from score"""
        if score < 0.3:
            return ThreatLevel.LOW
        elif score < 0.6:
            return ThreatLevel.MEDIUM
        elif score < 0.8:
            return ThreatLevel.HIGH
        else:
            return ThreatLevel.CRITICAL


class ThreatDetection:
    """Main threat detection system"""
    
    def __init__(self):
        self.detector = AnomalyDetector()
        self.scorer = ThreatScorer()
        self.alerts: List[ThreatAlert] = []
        self.blocked_users: set = set()
        self.failed_attempt_tracking: Dict[str, deque] = defaultdict(lambda: deque(maxlen=5))
    
    def analyze_query(self, user_id: str, query_type: str, table: str,
                     rows_affected: int, ip_address: str) -> Optional[ThreatAlert]:
        """Analyze query for threats"""
        timestamp = datetime.now()
        profile = self.detector.get_or_create_profile(user_id)
        profile.record_access(timestamp, table, rows_affected, ip_address)
        
        alerts = []
        
        # Check for unusual access time
        alert = self.detector.check_unusual_access_time(user_id, timestamp, ip_address)
        if alert:
            alerts.append(alert)
        
        # Check for bulk export
        alert = self.detector.check_bulk_export(user_id, table, rows_affected, timestamp, ip_address)
        if alert:
            alerts.append(alert)
        
        # Check for new IP
        alert = self.detector.check_new_ip_address(user_id, ip_address, timestamp)
        if alert:
            alerts.append(alert)
        
        # Record alerts
        for alert in alerts:
            self.alerts.append(alert)
            if alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                self.blocked_users.add(user_id)
        
        return alerts[0] if alerts else None
    
    def record_failed_login(self, user_id: str, ip_address: str) -> Optional[ThreatAlert]:
        """Track failed login attempts"""
        timestamp = datetime.now()
        self.failed_attempt_tracking[user_id].append(timestamp)
        
        if len(self.failed_attempt_tracking[user_id]) >= 3:
            alert_id = f"threat_{len(self.alerts):06d}"
            
            alert = ThreatAlert(
                alert_id=alert_id,
                timestamp=timestamp,
                threat_level=ThreatLevel.HIGH,
                anomaly_type=AnomalyType.FAILED_LOGIN_ATTEMPTS,
                user_id=user_id,
                ip_address=ip_address,
                description=f"Multiple failed login attempts: {len(self.failed_attempt_tracking[user_id])}",
                evidence={"attempts": len(self.failed_attempt_tracking[user_id])},
                threat_score=0.7,
                recommended_action="Block user temporarily and require password reset"
            )
            
            self.alerts.append(alert)
            self.blocked_users.add(user_id)
            
            return alert
        
        return None
    
    def get_alerts(self, user_id: Optional[str] = None,
                  threat_level: Optional[ThreatLevel] = None) -> List[ThreatAlert]:
        """Get alerts with optional filtering"""
        results = self.alerts
        
        if user_id:
            results = [a for a in results if a.user_id == user_id]
        
        if threat_level:
            results = [a for a in results if a.threat_level == threat_level]
        
        return sorted(results, key=lambda a: a.timestamp, reverse=True)
    
    def get_critical_alerts(self) -> List[ThreatAlert]:
        """Get all critical alerts"""
        return self.get_alerts(threat_level=ThreatLevel.CRITICAL)
    
    def is_user_blocked(self, user_id: str) -> bool:
        """Check if user is blocked"""
        return user_id in self.blocked_users
    
    def unblock_user(self, user_id: str):
        """Unblock user after review"""
        self.blocked_users.discard(user_id)
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get threat detection summary"""
        threat_counts = defaultdict(int)
        user_threats = defaultdict(int)
        
        for alert in self.alerts:
            threat_counts[alert.threat_level.value] += 1
            user_threats[alert.user_id] += 1
        
        return {
            "total_alerts": len(self.alerts),
            "by_threat_level": dict(threat_counts),
            "critical_alerts": threat_counts[ThreatLevel.CRITICAL.value],
            "blocked_users": len(self.blocked_users),
            "top_threatened_users": sorted(
                user_threats.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "anomaly_types": list(set(a.anomaly_type.value for a in self.alerts))
        }


if __name__ == "__main__":
    print("✓ Threat detection module loaded successfully")
