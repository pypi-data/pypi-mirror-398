"""
Query Replay System - Revolutionary Testing & Debugging Tool

Record entire sequences of database operations and replay them with different data.
Perfect for:
- Testing complex workflows
- Debugging production issues
- Cloning user journeys
- A/B testing scenarios
"""

import json
import datetime
import time


class QueryRecorder:
    """Context manager that records all database operations"""

    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.recordings = []
        self.start_time = None
        self.original_execute = None

    def __enter__(self):
        self.start_time = time.time()
        self.original_execute = self.db.execute

        # Wrap the execute method to capture queries
        def recording_execute(sql, params=None):
            result = self.original_execute(sql, params)

            # Record the query
            self.recordings.append(
                {
                    "timestamp": time.time() - self.start_time,
                    "sql": sql,
                    "params": list(params) if params else [],
                    "type": self._classify_query(sql),
                }
            )

            return result

        self.db.execute = recording_execute
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original execute
        self.db.execute = self.original_execute

        # Save recording
        if not exc_type:  # Only save if no error
            self._save_recording()

    def _classify_query(self, sql):
        """Classify query type"""
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        elif sql_upper.startswith("CREATE"):
            return "CREATE"
        return "OTHER"

    def _save_recording(self):
        """Save recording to file"""
        recording_data = {
            "name": self.name,
            "recorded_at": datetime.datetime.now().isoformat(),
            "duration": time.time() - self.start_time,
            "query_count": len(self.recordings),
            "queries": self.recordings,
        }

        filename = f"recordings/{self.name}.json"
        import os

        os.makedirs("recordings", exist_ok=True)

        with open(filename, "w") as f:
            json.dump(recording_data, f, indent=2)

        print(f"✓ Recorded {len(self.recordings)} queries to {filename}")


class ReplayEngine:
    """Replay recorded query sequences"""

    def __init__(self, db):
        self.db = db

    def replay(self, recording_name, variable_map=None):
        """
        Replay a recorded sequence

        Args:
            recording_name: Name of the recording to replay
            variable_map: Dict mapping old values to new values for substitution
        """
        filename = f"recordings/{recording_name}.json"

        try:
            with open(filename, "r") as f:
                recording = json.load(f)
        except FileNotFoundError:
            print(f"❌ Recording '{recording_name}' not found")
            return None

        print(f"\n🎬 Replaying: {recording['name']}")
        print(
            f"   Original: {recording['query_count']} queries in {recording['duration']:.2f}s"
        )
        print(f"   Recorded: {recording['recorded_at']}")

        variable_map = variable_map or {}
        results = []
        start_time = time.time()

        for i, query_data in enumerate(recording["queries"], 1):
            sql = query_data["sql"]
            params = query_data["params"]

            # Apply variable substitution
            if variable_map:
                params = [variable_map.get(p, p) for p in params]

            # Execute query
            try:
                result = self.db.execute(sql, params)
                results.append(
                    {"success": True, "type": query_data["type"], "result": result}
                )
                print(f"   [{i}/{recording['query_count']}] {query_data['type']} ✓")
            except Exception as e:
                results.append(
                    {"success": False, "type": query_data["type"], "error": str(e)}
                )
                print(f"   [{i}/{recording['query_count']}] {query_data['type']} ✗ {e}")

        duration = time.time() - start_time
        success_count = sum(1 for r in results if r["success"])

        print(
            f"\n✓ Replay complete: {success_count}/{len(results)} successful in {duration:.2f}s"
        )

        return results

    def list_recordings(self):
        """List all available recordings"""
        import os

        if not os.path.exists("recordings"):
            print("No recordings found")
            return []

        recordings = []
        for filename in os.listdir("recordings"):
            if filename.endswith(".json"):
                with open(f"recordings/{filename}", "r") as f:
                    data = json.load(f)
                    recordings.append(
                        {
                            "name": data["name"],
                            "queries": data["query_count"],
                            "duration": data["duration"],
                            "recorded_at": data["recorded_at"],
                        }
                    )

        return recordings

    def compare_recordings(self, name1, name2):
        """Compare two recordings"""
        # Load both recordings
        with open(f"recordings/{name1}.json", "r") as f:
            rec1 = json.load(f)
        with open(f"recordings/{name2}.json", "r") as f:
            rec2 = json.load(f)

        print(f"\n📊 Comparing Recordings:")
        print(f"   {name1}: {rec1['query_count']} queries, {rec1['duration']:.2f}s")
        print(f"   {name2}: {rec2['query_count']} queries, {rec2['duration']:.2f}s")
        print(
            f"\n   Difference: {abs(rec1['query_count'] - rec2['query_count'])} queries"
        )


# Add to Database class
def add_replay_to_database():
    """Extend Database with replay functionality"""
    from .database import Database

    def recorder(self, name):
        """Start recording queries"""
        return QueryRecorder(self, name)

    def replayer(self):
        """Get replay engine"""
        return ReplayEngine(self)

    Database.recorder = recorder
    Database.replayer = replayer
