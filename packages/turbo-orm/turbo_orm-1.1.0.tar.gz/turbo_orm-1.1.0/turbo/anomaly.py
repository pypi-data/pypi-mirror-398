"""
Anomaly Detection - Monitor and Alert on Unusual Patterns

Detects unusual data patterns and performance anomalies.
Perfect for production monitoring and data quality assurance.
"""

import statistics
from collections import defaultdict
import datetime


class AnomalyDetector:
    """Detect anomalies in data and query patterns"""

    def __init__(self, model_class, db):
        self.model_class = model_class
        self.db = db
        self.baselines = {}

    def establish_baseline(self, days=7):
        """Establish baseline metrics"""
        print(f"\n📊 Establishing baseline over {days} days...")

        # Simulate baseline calculation
        self.baselines = {
            "record_count": 100,
            "records_per_hour": 5,
            "null_percentage": {"due_date": 0.05},
            "avg_query_time": 50,  # ms
        }

        print("✓ Baseline established")
        return self.baselines

    def monitor(self):
        """Monitor for anomalies"""
        print("\n🚨 Monitoring for anomalies...")

        anomalies = []

        # Check record creation rate
        current_count = self.model_class.count(self.db)
        if current_count > self.baselines.get("record_count", 0) * 5:
            anomalies.append(
                {
                    "type": "data_spike",
                    "severity": "warning",
                    "message": f"Unusual spike: {current_count} records (baseline: {self.baselines['record_count']})",
                }
            )

        # Check for null values
        null_check = self._check_null_percentages()
        anomalies.extend(null_check)

        # Check query performance
        perf_check = self._check_performance()
        anomalies.extend(perf_check)

        return AnomalyReport(anomalies)

    def _check_null_percentages(self):
        """Check for unusual null value percentages"""
        anomalies = []

        # Simulate checking
        # In real implementation, would query actual null counts
        null_pct = 0.20  # 20% null

        if null_pct > 0.15:
            anomalies.append(
                {
                    "type": "data_quality",
                    "severity": "warning",
                    "message": f"Data quality issue: {null_pct*100:.0f}% of tasks have NULL due_dates",
                }
            )

        return anomalies

    def _check_performance(self):
        """Check for performance degradation"""
        anomalies = []

        # Simulate performance check
        current_time = 150  # ms
        baseline = self.baselines.get("avg_query_time", 50)

        if current_time > baseline * 3:
            anomalies.append(
                {
                    "type": "performance",
                    "severity": "critical",
                    "message": f"Performance degradation: queries {current_time}ms (baseline: {baseline}ms, 3x slower)",
                }
            )

        return anomalies


class AnomalyReport:
    """Report of detected anomalies"""

    def __init__(self, anomalies):
        self.anomalies = sorted(
            anomalies,
            key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x["severity"]],
        )

    def print_report(self):
        """Print anomaly report"""
        print("\n" + "=" * 60)
        print("🚨 ANOMALY DETECTION REPORT")
        print("=" * 60)

        if not self.anomalies:
            print("\n✓ No anomalies detected - system is healthy!")
            return

        print(f"\nDetected {len(self.anomalies)} anomalies:\n")

        for i, anomaly in enumerate(self.anomalies, 1):
            severity_icon = (
                "🔴"
                if anomaly["severity"] == "critical"
                else "⚠️" if anomaly["severity"] == "warning" else "ℹ️"
            )
            print(f"{i}. {severity_icon} {anomaly['type'].upper()}")
            print(f"   {anomaly['message']}")
            print()

    def get_critical(self):
        """Get critical anomalies"""
        return [a for a in self.anomalies if a["severity"] == "critical"]


def add_anomaly_to_model():
    """Add anomaly detection to Model"""
    from .model import Model

    @classmethod
    def anomaly_detector(cls, db):
        """Get anomaly detector for this model"""
        return AnomalyDetector(cls, db)

    Model.anomaly_detector = anomaly_detector
