"""
Smart Data Diff - Git for Your Database

Track, compare, and rollback data changes like version control for code.
Perfect for debugging production issues and auditing data changes.
"""

import datetime
from collections import defaultdict


class DataDiff:
    """Compare database states across time"""

    def __init__(self, db, model_class):
        self.db = db
        self.model_class = model_class

    def diff(self, before=None, after=None):
        """
        Generate diff between two timestamps

        Args:
            before: datetime or "beginning"
            after: datetime or "now"
        """
        if not hasattr(self.model_class, "history"):
            raise ValueError(
                f"{self.model_class.__name__} must inherit from HistoryModel"
            )

        # Parse timestamps
        if after == "now" or after is None:
            after_time = datetime.datetime.now()
        else:
            after_time = (
                after
                if isinstance(after, datetime.datetime)
                else datetime.datetime.fromisoformat(after)
            )

        if before == "beginning" or before is None:
            before_time = datetime.datetime.min
        else:
            before_time = (
                before
                if isinstance(before, datetime.datetime)
                else datetime.datetime.fromisoformat(before)
            )

        # Get all history records in range
        history_table = f"{self.model_class._table_name}_history"

        # Get state at 'before' time
        before_state = self._get_state_at(before_time)
        after_state = self._get_state_at(after_time)

        # Calculate differences
        changes = {"added": [], "removed": [], "modified": []}

        before_ids = set(before_state.keys())
        after_ids = set(after_state.keys())

        # Added records
        for id in after_ids - before_ids:
            changes["added"].append(after_state[id])

        # Removed records
        for id in before_ids - after_ids:
            changes["removed"].append(before_state[id])

        # Modified records
        for id in before_ids & after_ids:
            if before_state[id] != after_state[id]:
                changes["modified"].append(
                    {
                        "id": id,
                        "before": before_state[id],
                        "after": after_state[id],
                        "changes": self._field_diff(before_state[id], after_state[id]),
                    }
                )

        return DiffResult(self.model_class, before_time, after_time, changes)

    def _get_state_at(self, timestamp):
        """Get database state at specific timestamp"""
        history_table = f"{self.model_class._table_name}_history"

        # Get latest history record for each ID before timestamp
        sql = f"""
            SELECT h1.*
            FROM {history_table} h1
            INNER JOIN (
                SELECT original_id, MAX(timestamp) as max_time
                FROM {history_table}
                WHERE timestamp <= ?
                GROUP BY original_id
            ) h2 ON h1.original_id = h2.original_id AND h1.timestamp = h2.max_time
        """

        cursor = self.db.execute(sql, (timestamp.isoformat(),))

        state = {}
        for row in cursor.fetchall():
            data = dict(row)
            record_id = data["original_id"]
            state[record_id] = data

        return state

    def _field_diff(self, before, after):
        """Calculate field-level differences"""
        diffs = {}
        for key in before.keys():
            if key in ["history_id", "original_id", "timestamp", "action"]:
                continue
            if before.get(key) != after.get(key):
                diffs[key] = {"before": before.get(key), "after": after.get(key)}
        return diffs


class DiffResult:
    """Container for diff results"""

    def __init__(self, model_class, before_time, after_time, changes):
        self.model_class = model_class
        self.before_time = before_time
        self.after_time = after_time
        self.changes = changes

    def summary(self):
        """Print summary of changes"""
        print(f"\n📊 Data Diff: {self.model_class.__name__}")
        print(f"   From: {self.before_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   To:   {self.after_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n   ➕ Added: {len(self.changes['added'])} records")
        print(f"   ➖ Removed: {len(self.changes['removed'])} records")
        print(f"   📝 Modified: {len(self.changes['modified'])} records")

    def visualize(self):
        """Visual diff output"""
        print("\n" + "=" * 60)
        print(f"📊 DETAILED DIFF: {self.model_class.__name__}")
        print("=" * 60)

        # Show added
        if self.changes["added"]:
            print(f"\n➕ ADDED ({len(self.changes['added'])} records):")
            for record in self.changes["added"][:5]:  # Show first 5
                print(f"   + ID {record['original_id']}")

        # Show removed
        if self.changes["removed"]:
            print(f"\n➖ REMOVED ({len(self.changes['removed'])} records):")
            for record in self.changes["removed"][:5]:
                print(f"   - ID {record['original_id']}")

        # Show modified
        if self.changes["modified"]:
            print(f"\n📝 MODIFIED ({len(self.changes['modified'])} records):")
            for mod in self.changes["modified"][:5]:
                print(f"\n   Record ID {mod['id']}:")
                for field, change in mod["changes"].items():
                    print(f"      {field}: {change['before']} → {change['after']}")

    def export_patch(self, filename="diff_patch.json"):
        """Export diff as a patch file"""
        import json

        patch_data = {
            "model": self.model_class.__name__,
            "before": self.before_time.isoformat(),
            "after": self.after_time.isoformat(),
            "changes": self.changes,
        }

        # Convert datetime objects to strings
        def serialize(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return str(obj)

        with open(filename, "w") as f:
            json.dump(patch_data, f, indent=2, default=serialize)

        print(f"\n✓ Patch exported to {filename}")

    def rollback(self, db):
        """Rollback changes to before state"""
        print(f"\n🔄 Rolling back {len(self.changes['modified'])} changes...")

        count = 0
        for mod in self.changes["modified"]:
            # Restore to 'before' state
            instance = self.model_class.get(db, mod["id"])
            if instance:
                for field, change in mod["changes"].items():
                    setattr(instance, field, change["before"])
                instance.save(db)
                count += 1

        print(f"✓ Rolled back {count} records to previous state")


# Add to Database or Model
def add_diff_to_model():
    """Add diff functionality to HistoryModel"""
    from .history import HistoryModel

    @classmethod
    def data_diff(cls, db, before=None, after=None):
        """Generate data diff"""
        differ = DataDiff(db, cls)
        return differ.diff(before, after)

    HistoryModel.data_diff = data_diff
