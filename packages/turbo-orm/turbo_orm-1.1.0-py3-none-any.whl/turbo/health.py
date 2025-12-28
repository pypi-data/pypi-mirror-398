"""
Health monitoring and diagnostics for Turbo ORM

Provides comprehensive health checks and performance monitoring.
"""

import time
from typing import Dict, Any


class DatabaseHealth:
    """Health check and monitoring for Turbo ORM"""
    
    def __init__(self, db):
        self.db = db
    
    def check_connection(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            start = time.time()
            self.db.execute("SELECT 1")
            latency = time.time() - start
            
            return {
                'status': 'healthy',
                'latency_ms': round(latency * 1000, 2),
                'pool_size': getattr(self.db, 'pool_size', 0),
                'thread_safe': True
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'latency_ms': None
            }
    
    def check_cache(self) -> Dict[str, Any]:
        """Check cache statistics"""
        from turbo.model import Model
        
        total_size = sum(len(cache) for cache in Model._cache.values())
        return {
            'total_entries': total_size,
            'tables': list(Model._cache.keys()),
            'memory_estimate_mb': round(total_size * 0.001, 2)
        }
    
    def check_performance(self) -> Dict[str, Any]:
        """Check performance metrics"""
        if hasattr(self.db, 'get_stats'):
            stats = self.db.get_stats()
            return {
                'query_count': stats.get('total_queries', 0),
                'slow_queries': stats.get('slow_queries', 0),
                'avg_query_time_ms': stats.get('avg_query_time_ms', 0)
            }
        return {'query_count': 0, 'slow_queries': 0, 'avg_query_time_ms': 0}
    
    def check_table_health(self, model_class) -> Dict[str, Any]:
        """Check specific model/table health"""
        try:
            # Check if table exists
            result = self.db.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{model_class._table_name}'"
            )
            exists = len(result.fetchall()) > 0
            
            if not exists:
                return {'exists': False, 'error': 'Table does not exist'}
            
            # Get row count
            count_result = self.db.execute(f"SELECT COUNT(*) FROM {model_class._table_name}")
            row_count = count_result.fetchone()[0]
            
            # Get column info
            info_result = self.db.execute(f"PRAGMA table_info({model_class._table_name})")
            columns = [dict(row) for row in info_result.fetchall()]
            
            return {
                'exists': True,
                'row_count': row_count,
                'columns': len(columns),
                'column_names': [col['name'] for col in columns]
            }
        except Exception as e:
            return {'exists': False, 'error': str(e)}
    
    def full_report(self) -> Dict[str, Any]:
        """Complete health report"""
        return {
            'timestamp': time.time(),
            'connection': self.check_connection(),
            'cache': self.check_cache(),
            'performance': self.check_performance(),
            'status': 'healthy' if self.check_connection()['status'] == 'healthy' else 'degraded'
        }


def monitor_database(db, interval: int = 60) -> None:
    """
    Continuously monitor database health.
    
    Args:
        db: Database instance to monitor
        interval: Check interval in seconds
    """
    import time
    
    health = DatabaseHealth(db)
    
    try:
        while True:
            report = health.full_report()
            
            if report['status'] == 'degraded':
                print(f"⚠️  Database degraded at {time.ctime()}: {report}")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def add_health_check_to_database(db):
    """Add health check methods to Database instance"""
    
    def health_check():
        """Quick health check"""
        return DatabaseHealth(db).check_connection()
    
    def health_report():
        """Full health report"""
        return DatabaseHealth(db).full_report()
    
    db.health_check = health_check
    db.health_report = health_report
    
    return db