"""
Auto-Scaling Connection Pool - Dynamic Resource Management

Automatically scales connection pool based on load.
Optimizes resource usage while maintaining performance.
"""

import threading
import time
from queue import Queue, Empty


class AutoScalingPool:
    """Dynamic connection pool that scales with load"""

    def __init__(self, db_path, min_size=2, max_size=20):
        self.db_path = db_path
        self.min_size = min_size
        self.max_size = max_size
        self.pool = Queue()
        self.active_connections = 0
        self.total_connections = 0
        self.lock = threading.Lock()
        self.metrics = {"requests": 0, "wait_times": [], "pool_sizes": []}

        # Initialize minimum connections
        self._initialize_pool()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_load, daemon=True)
        self.monitor_thread.start()

    def _initialize_pool(self):
        """Create initial connections"""
        import sqlite3

        for _ in range(self.min_size):
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            self.pool.put(conn)
            self.total_connections += 1

    def get_connection(self, timeout=5):
        """Get connection from pool"""
        start_time = time.time()

        try:
            conn = self.pool.get(timeout=timeout)
            wait_time = time.time() - start_time

            with self.lock:
                self.active_connections += 1
                self.metrics["requests"] += 1
                self.metrics["wait_times"].append(wait_time)

            return conn

        except Empty:
            # Pool exhausted - try to scale up
            if self.total_connections < self.max_size:
                return self._create_emergency_connection()
            raise RuntimeError("Connection pool exhausted")

    def release_connection(self, conn):
        """Return connection to pool"""
        with self.lock:
            self.active_connections -= 1
        self.pool.put(conn)

    def _create_emergency_connection(self):
        """Create additional connection under load"""
        import sqlite3

        with self.lock:
            if self.total_connections < self.max_size:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                self.total_connections += 1
                self.active_connections += 1
                print(f"   📈 Scaled up: pool size now {self.total_connections}")
                return conn

    def _monitor_load(self):
        """Monitor and adjust pool size"""
        while True:
            time.sleep(10)  # Check every 10 seconds

            with self.lock:
                utilization = (
                    self.active_connections / self.total_connections
                    if self.total_connections > 0
                    else 0
                )
                avg_wait = (
                    sum(self.metrics["wait_times"][-100:])
                    / len(self.metrics["wait_times"][-100:])
                    if self.metrics["wait_times"]
                    else 0
                )

                # Scale up if high utilization
                if utilization > 0.8 and self.total_connections < self.max_size:
                    self._add_connection()

                # Scale down if low utilization
                elif utilization < 0.2 and self.total_connections > self.min_size:
                    self._remove_connection()

                self.metrics["pool_sizes"].append(self.total_connections)

    def _add_connection(self):
        """Add connection to pool"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self.pool.put(conn)
        self.total_connections += 1
        print(f"   📈 Auto-scaled up: {self.total_connections} connections")

    def _remove_connection(self):
        """Remove connection from pool"""
        try:
            conn = self.pool.get_nowait()
            conn.close()
            self.total_connections -= 1
            print(f"   📉 Auto-scaled down: {self.total_connections} connections")
        except Empty:
            pass

    def get_metrics(self):
        """Get pool metrics"""
        with self.lock:
            return {
                "total_connections": self.total_connections,
                "active_connections": self.active_connections,
                "utilization": (
                    self.active_connections / self.total_connections
                    if self.total_connections > 0
                    else 0
                ),
                "total_requests": self.metrics["requests"],
                "avg_wait_time": (
                    sum(self.metrics["wait_times"][-100:])
                    / len(self.metrics["wait_times"][-100:])
                    if self.metrics["wait_times"]
                    else 0
                ),
            }


def add_autoscaling_to_database():
    """Add auto-scaling pool to Database"""
    from .database import Database

    original_init = Database.__init__

    def __init__(self, path, pool_size=0, auto_scale=False):
        if auto_scale:
            self.auto_pool = AutoScalingPool(path, min_size=2, max_size=pool_size or 10)
        else:
            original_init(self, path, pool_size)

    # Optionally override
    Database.__init__with_autoscale = __init__
