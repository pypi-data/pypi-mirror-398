"""
Live Query Dashboard - Real-Time Database Monitoring

Monitor all database activity in real-time through a web interface.
Perfect for development, debugging, and performance optimization.
"""

import time
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class QueryMetrics:
    """Collect and store query metrics"""

    def __init__(self):
        self.queries = []
        self.stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "query_types": {},
            "avg_duration": 0,
        }
        self.lock = threading.Lock()

    def record_query(self, sql, params, duration):
        """Record a query execution"""
        with self.lock:
            query_type = sql.strip().split()[0].upper()

            query_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "sql": sql[:200],  # Truncate long queries
                "params": str(params)[:100] if params else "",
                "duration": round(duration * 1000, 2),  # Convert to ms
                "type": query_type,
                "slow": duration > 0.1,  # Flag queries > 100ms as slow
            }

            self.queries.append(query_data)
            if len(self.queries) > 1000:  # Keep last 1000 queries
                self.queries.pop(0)

            # Update stats
            self.stats["total_queries"] += 1
            if query_data["slow"]:
                self.stats["slow_queries"] += 1

            self.stats["query_types"][query_type] = (
                self.stats["query_types"].get(query_type, 0) + 1
            )

            # Calculate avg duration
            total_duration = sum(q["duration"] for q in self.queries)
            self.stats["avg_duration"] = round(total_duration / len(self.queries), 2)

    def get_recent_queries(self, limit=50):
        """Get recent queries"""
        with self.lock:
            return self.queries[-limit:]

    def get_stats(self):
        """Get current statistics"""
        with self.lock:
            return self.stats.copy()

    def clear(self):
        """Clear all metrics"""
        with self.lock:
            self.queries = []
            self.stats = {
                "total_queries": 0,
                "slow_queries": 0,
                "query_types": {},
                "avg_duration": 0,
            }


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for dashboard"""

    metrics = None  # Will be set by Dashboard

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/":
            # Serve dashboard HTML
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self._get_dashboard_html().encode())

        elif self.path == "/api/queries":
            # Return recent queries as JSON
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            queries = self.metrics.get_recent_queries()
            self.wfile.write(json.dumps(queries).encode())

        elif self.path == "/api/stats":
            # Return stats as JSON
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            stats = self.metrics.get_stats()
            self.wfile.write(json.dumps(stats).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def _get_dashboard_html(self):
        """Generate dashboard HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Live Query Dashboard</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #1a1a1a; color: #fff; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background: #2a2a2a; padding: 15px; border-radius: 8px; flex: 1; }
        .stat-value { font-size: 32px; font-weight: bold; color: #667eea; }
        .stat-label { color: #888; margin-top: 5px; }
        .query-log { background: #2a2a2a; padding: 15px; border-radius: 8px; }
        .query { padding: 10px; margin: 5px 0; background: #333; border-radius: 5px; 
                 border-left: 3px solid #667eea; }
        .query.slow { border-left-color: #ff4444; }
        .query-type { display: inline-block; padding: 2px 8px; background: #667eea; 
                      border-radius: 3px; font-size: 12px; margin-right: 10px; }
        .duration { color: #888; float: right; }
        .slow-warning { color: #ff4444; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Live Query Dashboard</h1>
        <p>Real-time database monitoring</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value" id="total">0</div>
            <div class="stat-label">Total Queries</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="avg">0ms</div>
            <div class="stat-label">Avg Duration</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="slow">0</div>
            <div class="stat-label">Slow Queries</div>
        </div>
    </div>
    
    <div class="query-log">
        <h2>Recent Queries</h2>
        <div id="queries"></div>
    </div>
    
    <script>
        function updateDashboard() {
            // Fetch stats
            fetch('/api/stats')
                .then(r => r.json())
                .then(stats => {
                    document.getElementById('total').textContent = stats.total_queries;
                    document.getElementById('avg').textContent = stats.avg_duration + 'ms';
                    document.getElementById('slow').textContent = stats.slow_queries;
                });
            
            // Fetch queries
            fetch('/api/queries')
                .then(r => r.json())
                .then(queries => {
                    const container = document.getElementById('queries');
                    container.innerHTML = queries.reverse().map(q => `
                        <div class="query ${q.slow ? 'slow' : ''}">
                            <span class="query-type">${q.type}</span>
                            <code>${q.sql}</code>
                            <span class="duration ${q.slow ? 'slow-warning' : ''}">${q.duration}ms</span>
                        </div>
                    `).join('');
                });
        }
        
        // Update every second
        setInterval(updateDashboard, 1000);
        updateDashboard();
    </script>
</body>
</html>
        """

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


class Dashboard:
    """Live query dashboard"""

    def __init__(self, db, port=8080):
        self.db = db
        self.port = port
        self.metrics = QueryMetrics()
        self.server = None
        self.server_thread = None
        self.original_execute = None

    def start(self):
        """Start the dashboard"""
        # Set metrics for handler
        DashboardHandler.metrics = self.metrics

        # Intercept database queries
        self.original_execute = self.db.execute

        def intercepting_execute(sql, params=None):
            start_time = time.time()
            result = self.original_execute(sql, params)
            duration = time.time() - start_time

            # Record query
            self.metrics.record_query(sql, params, duration)

            return result

        self.db.execute = intercepting_execute

        # Start HTTP server in background thread
        self.server = HTTPServer(("localhost", self.port), DashboardHandler)
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()

        print(f"\n📊 Dashboard started at http://localhost:{self.port}")
        print(f"   Open this URL in your browser to see live queries!")

    def stop(self):
        """Stop the dashboard"""
        if self.server:
            self.server.shutdown()
            print("\n✓ Dashboard stopped")

        # Restore original execute
        if self.original_execute:
            self.db.execute = self.original_execute

    def export_metrics(self, filename="query_metrics.json"):
        """Export metrics to file"""
        data = {
            "stats": self.metrics.get_stats(),
            "queries": self.metrics.get_recent_queries(1000),
            "exported_at": datetime.datetime.now().isoformat(),
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Metrics exported to {filename}")


# Add to Database class
def add_dashboard_to_database():
    """Extend Database with dashboard functionality"""
    from .database import Database

    def start_dashboard(self, port=8080):
        """Start live query dashboard"""
        dashboard = Dashboard(self, port)
        dashboard.start()
        return dashboard

    Database.start_dashboard = start_dashboard
