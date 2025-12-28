"""
Quantum Queries - Multi-Timeline Analytics

Query across multiple database states simultaneously for trend analysis.
Perfect for comparing data evolution over time.
"""

import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class QuantumQuery:
    """Execute queries across multiple timelines"""

    def __init__(self, db, model_class):
        self.db = db
        self.model_class = model_class

    def query_timelines(self, timelines, **filters):
        """
        Query multiple timelines simultaneously

        Args:
            timelines: List of timeline specifications
                - "current" for current state
                - datetime objects for historical states
                - Relative strings like "1d_ago", "1w_ago"
            filters: Query filters to apply

        Returns:
            Dict mapping timeline -> results
        """
        if not hasattr(self.model_class, "history"):
            raise ValueError(
                f"{self.model_class.__name__} must inherit from HistoryModel"
            )

        # Parse timelines
        timeline_datetimes = {}
        for timeline in timelines:
            if timeline == "current":
                timeline_datetimes[timeline] = datetime.datetime.now()
            elif isinstance(timeline, datetime.datetime):
                timeline_datetimes[timeline.isoformat()] = timeline
            elif isinstance(timeline, str):
                # Parse relative times
                timeline_datetimes[timeline] = self._parse_relative_time(timeline)
            else:
                timeline_datetimes[str(timeline)] = timeline

        # Query each timeline
        results = {}
        for name, dt in timeline_datetimes.items():
            results[name] = self._query_at_time(dt, filters)

        return QuantumResult(self.model_class, results, filters)

    def _parse_relative_time(self, relative_str):
        """Parse relative time strings like '1d_ago', '1w_ago'"""
        import re

        match = re.match(r"(\d+)([dwmy])_ago", relative_str)
        if not match:
            return datetime.datetime.now()

        amount, unit = match.groups()
        amount = int(amount)

        if unit == "d":  # days
            delta = datetime.timedelta(days=amount)
        elif unit == "w":  # weeks
            delta = datetime.timedelta(weeks=amount)
        elif unit == "m":  # months (approximate)
            delta = datetime.timedelta(days=amount * 30)
        elif unit == "y":  # years (approximate)
            delta = datetime.timedelta(days=amount * 365)
        else:
            delta = datetime.timedelta(0)

        return datetime.datetime.now() - delta

    def _query_at_time(self, timestamp, filters):
        """Query database state at specific time"""
        history_table = f"{self.model_class._table_name}_history"

        # Build WHERE clause for filters
        where_parts = []
        params = [timestamp.isoformat()]

        for key, value in filters.items():
            where_parts.append(f'h1."{key}" = ?')
            params.append(value)

        where_clause = " AND " + " AND ".join(where_parts) if where_parts else ""

        # Get latest state for each record before timestamp
        sql = f"""
            SELECT h1.*
            FROM {history_table} h1
            INNER JOIN (
                SELECT original_id, MAX(timestamp) as max_time
                FROM {history_table}
                WHERE timestamp <= ?
                GROUP BY original_id
            ) h2 ON h1.original_id = h2.original_id AND h1.timestamp = h2.max_time
            {where_clause}
        """

        cursor = self.db.execute(sql, params)

        results = []
        for row in cursor.fetchall():
            data = dict(row)
            results.append(data)

        return results


class QuantumResult:
    """Results from quantum query"""

    def __init__(self, model_class, timeline_results, filters):
        self.model_class = model_class
        self.timeline_results = timeline_results
        self.filters = filters

    def summary(self):
        """Print summary of results"""
        print(f"\n⚡ Quantum Query Results: {self.model_class.__name__}")
        print(f"   Filters: {self.filters}")
        print(f"\n   Results across {len(self.timeline_results)} timelines:")

        for timeline, results in self.timeline_results.items():
            print(f"      {timeline}: {len(results)} records")

    def compare(self):
        """Compare results across timelines"""
        print("\n" + "=" * 60)
        print(f"⚡ QUANTUM QUERY COMPARISON")
        print("=" * 60)

        # Get counts for each timeline
        counts = {name: len(results) for name, results in self.timeline_results.items()}

        # Show trends
        sorted_timelines = sorted(counts.items(), key=lambda x: x[0])

        print("\n📈 Trend Analysis:")
        for i, (timeline, count) in enumerate(sorted_timelines):
            if i > 0:
                prev_count = sorted_timelines[i - 1][1]
                change = count - prev_count
                change_pct = (change / prev_count * 100) if prev_count > 0 else 0
                trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                print(
                    f"   {timeline}: {count} records ({trend} {change:+d}, {change_pct:+.1f}%)"
                )
            else:
                print(f"   {timeline}: {count} records (baseline)")

    def visualize(self):
        """Visual representation of timeline data"""
        print("\n" + "=" * 60)
        print(f"⚡ TIMELINE VISUALIZATION")
        print("=" * 60)

        max_count = max(len(r) for r in self.timeline_results.values())

        for timeline, results in sorted(self.timeline_results.items()):
            count = len(results)
            bar_length = int((count / max_count * 40)) if max_count > 0 else 0
            bar = "█" * bar_length
            print(f"\n{timeline:15s} [{count:3d}] {bar}")

    def export(self, filename="quantum_results.json"):
        """Export quantum query results"""
        import json

        export_data = {
            "model": self.model_class.__name__,
            "filters": self.filters,
            "timelines": {},
        }

        for timeline, results in self.timeline_results.items():
            export_data["timelines"][timeline] = {
                "count": len(results),
                "records": results[:10],  # First 10 records
            }

        def serialize(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return str(obj)

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2, default=serialize)

        print(f"\n✓ Results exported to {filename}")


# Add to HistoryModel
def add_quantum_to_model():
    """Add quantum query capability to HistoryModel"""
    from .history import HistoryModel

    @classmethod
    def quantum_query(cls, db, timelines, **filters):
        """Execute quantum query across timelines"""
        quantum = QuantumQuery(db, cls)
        return quantum.query_timelines(timelines, **filters)

    HistoryModel.quantum_query = quantum_query
