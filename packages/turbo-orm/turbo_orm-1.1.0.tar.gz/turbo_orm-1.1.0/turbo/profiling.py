"""
Performance Hot Path Optimization

Critical path profiling and optimization for:
- Query execution
- Caching layer
- Database operations
"""

import cProfile
import pstats
import io
import time
from typing import Dict, List, Any, Callable
from functools import wraps
from datetime import datetime


# ============================================================================
# PROFILER
# ============================================================================

class HotPathProfiler:
    """Profile code to identify hot paths"""
    
    def __init__(self):
        self.profiles: Dict[str, pstats.Stats] = {}
        self.measurements: Dict[str, List[float]] = {}
        
    def profile_function(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Profile a single function execution"""
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        # Store profile
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        self.profiles[name] = ps
        
        return result
        
    def profile_decorator(self, name: str):
        """Decorator to profile functions"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.profile_function(name, func, *args, **kwargs)
            return wrapper
        return decorator
        
    def measure_execution_time(self, name: str, func: Callable, iterations: int = 100) -> float:
        """Measure function execution time"""
        if name not in self.measurements:
            self.measurements[name] = []
            
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)  # Convert to ms
            
        self.measurements[name].extend(times)
        return sum(times) / len(times)
        
    def get_bottlenecks(self, name: str, top_n: int = 10) -> List[str]:
        """Get top bottlenecks for profiled function"""
        if name not in self.profiles:
            return []
            
        profile = self.profiles[name]
        s = io.StringIO()
        profile.stream = s
        profile.print_stats(top_n)
        
        return s.getvalue().split('\n')
        
    def report(self) -> str:
        """Generate profiling report"""
        report = "HOT PATH PROFILING REPORT\n"
        report += "=" * 70 + "\n\n"
        
        for name, times in self.measurements.items():
            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                report += f"{name}:\n"
                report += f"  Average: {avg_time:.4f}ms\n"
                report += f"  Min: {min_time:.4f}ms\n"
                report += f"  Max: {max_time:.4f}ms\n"
                report += f"  Samples: {len(times)}\n\n"
                
        return report


# ============================================================================
# QUERY EXECUTION OPTIMIZATION
# ============================================================================

class QueryOptimizer:
    """Optimize query execution paths"""
    
    def __init__(self):
        self.query_cache: Dict[str, Any] = {}
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        
    def analyze_query_pattern(self, query: str) -> Dict[str, Any]:
        """Analyze query for optimization opportunities"""
        analysis = {
            "query": query,
            "has_index_opportunity": False,
            "has_cache_opportunity": False,
            "has_join_optimization": False,
            "estimated_improvement": 0
        }
        
        # Check for index opportunities
        if "WHERE" in query.upper():
            analysis["has_index_opportunity"] = True
            analysis["estimated_improvement"] += 20
            
        # Check for caching opportunities
        if "SELECT" in query.upper() and "WHERE" not in query.upper():
            analysis["has_cache_opportunity"] = True
            analysis["estimated_improvement"] += 100
            
        # Check for join optimization
        if "JOIN" in query.upper():
            analysis["has_join_optimization"] = True
            analysis["estimated_improvement"] += 30
            
        return analysis
        
    def recommend_optimizations(self, query: str) -> List[str]:
        """Recommend optimizations for query"""
        recommendations = []
        analysis = self.analyze_query_pattern(query)
        
        if analysis["has_index_opportunity"]:
            recommendations.append("Add index on WHERE clause columns")
            
        if analysis["has_cache_opportunity"]:
            recommendations.append("Cache full query results")
            
        if analysis["has_join_optimization"]:
            recommendations.append("Review JOIN order and conditions")
            
        if analysis["estimated_improvement"] > 0:
            recommendations.append(f"Estimated improvement: {analysis['estimated_improvement']}%")
            
        return recommendations


# ============================================================================
# CACHING LAYER OPTIMIZATION
# ============================================================================

class CacheLayerOptimizer:
    """Optimize caching layer performance"""
    
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_evictions = 0
        self.entry_sizes: Dict[str, int] = {}
        
    def record_hit(self) -> None:
        """Record cache hit"""
        self.cache_hits += 1
        
    def record_miss(self) -> None:
        """Record cache miss"""
        self.cache_misses += 1
        
    def record_eviction(self) -> None:
        """Record cache eviction"""
        self.cache_evictions += 1
        
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0
        return (self.cache_hits / total) * 100
        
    def analyze_cache_efficiency(self) -> Dict[str, Any]:
        """Analyze cache efficiency"""
        hit_rate = self.get_hit_rate()
        
        analysis = {
            "total_hits": self.cache_hits,
            "total_misses": self.cache_misses,
            "total_evictions": self.cache_evictions,
            "hit_rate": f"{hit_rate:.1f}%",
            "efficiency": "High" if hit_rate > 80 else "Medium" if hit_rate > 50 else "Low",
            "recommendations": []
        }
        
        if hit_rate < 50:
            analysis["recommendations"].append("Increase cache size")
            analysis["recommendations"].append("Review cache TTL settings")
        elif self.cache_evictions > self.cache_hits:
            analysis["recommendations"].append("Increase cache capacity")
            
        return analysis
        
    def recommend_cache_strategy(self) -> str:
        """Recommend caching strategy"""
        hit_rate = self.get_hit_rate()
        
        if hit_rate > 80:
            return "AGGRESSIVE: Current caching strategy is very effective"
        elif hit_rate > 60:
            return "MODERATE: Consider increasing cache capacity slightly"
        elif hit_rate > 40:
            return "CONSERVATIVE: Review cache invalidation patterns"
        else:
            return "MINIMAL: Cache is ineffective, consider different approach"


# ============================================================================
# DATABASE OPERATION OPTIMIZATION
# ============================================================================

class DatabaseOperationOptimizer:
    """Optimize database operation performance"""
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = {}
        self.slow_operations: List[Dict[str, Any]] = []
        self.slow_query_threshold = 10  # ms
        
    def record_operation(self, operation: str, duration: float) -> None:
        """Record operation duration"""
        duration_ms = duration * 1000
        
        if operation not in self.operation_times:
            self.operation_times[operation] = []
            
        self.operation_times[operation].append(duration_ms)
        
        # Track slow operations
        if duration_ms > self.slow_query_threshold:
            self.slow_operations.append({
                "operation": operation,
                "duration": duration_ms,
                "timestamp": datetime.now()
            })
            
    def get_operation_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations"""
        stats = {}
        
        for op, times in self.operation_times.items():
            stats[op] = {
                "average": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "count": len(times)
            }
            
        return stats
        
    def identify_slow_operations(self, threshold: float = 10) -> List[Dict[str, Any]]:
        """Identify operations exceeding threshold"""
        slow = []
        
        for op, times in self.operation_times.items():
            avg_time = sum(times) / len(times)
            if avg_time > threshold:
                slow.append({
                    "operation": op,
                    "average_time": avg_time,
                    "count": len(times),
                    "total_time": sum(times)
                })
                
        return sorted(slow, key=lambda x: x["average_time"], reverse=True)
        
    def recommend_optimizations(self) -> List[str]:
        """Recommend database optimizations"""
        recommendations = []
        
        slow_ops = self.identify_slow_operations()
        for op in slow_ops[:3]:  # Top 3 slow operations
            if op["operation"].upper().startswith("SELECT"):
                recommendations.append(f"Add indexes for {op['operation']}")
                recommendations.append(f"Consider caching {op['operation']}")
            elif op["operation"].upper().startswith("INSERT"):
                recommendations.append(f"Batch inserts for {op['operation']}")
            elif op["operation"].upper().startswith("UPDATE"):
                recommendations.append(f"Use bulk updates for {op['operation']}")
                
        return recommendations


# ============================================================================
# PERFORMANCE REPORT GENERATOR
# ============================================================================

class PerformanceReportGenerator:
    """Generate comprehensive performance reports"""
    
    def __init__(self):
        self.profiler = HotPathProfiler()
        self.query_optimizer = QueryOptimizer()
        self.cache_optimizer = CacheLayerOptimizer()
        self.db_optimizer = DatabaseOperationOptimizer()
        
    def generate_report(self) -> str:
        """Generate comprehensive performance report"""
        report = "=" * 70 + "\n"
        report += "PERFORMANCE HOT PATH ANALYSIS REPORT\n"
        report += "=" * 70 + "\n\n"
        
        # Profiler section
        report += "1. EXECUTION TIME ANALYSIS\n"
        report += "-" * 70 + "\n"
        report += self.profiler.report()
        
        # Cache section
        report += "\n2. CACHE LAYER ANALYSIS\n"
        report += "-" * 70 + "\n"
        cache_analysis = self.cache_optimizer.analyze_cache_efficiency()
        for key, value in cache_analysis.items():
            report += f"{key}: {value}\n"
        report += f"Strategy: {self.cache_optimizer.recommend_cache_strategy()}\n"
        
        # Database section
        report += "\n3. DATABASE OPERATION ANALYSIS\n"
        report += "-" * 70 + "\n"
        db_stats = self.db_optimizer.get_operation_stats()
        for op, stats in db_stats.items():
            report += f"{op}:\n"
            report += f"  Average: {stats['average']:.2f}ms\n"
            report += f"  Min/Max: {stats['min']:.2f}ms / {stats['max']:.2f}ms\n"
            report += f"  Operations: {stats['count']}\n"
            
        slow_ops = self.db_optimizer.identify_slow_operations()
        if slow_ops:
            report += "\nSlow Operations:\n"
            for op in slow_ops:
                report += f"  {op['operation']}: {op['average_time']:.2f}ms avg\n"
                
        # Recommendations
        report += "\n4. OPTIMIZATION RECOMMENDATIONS\n"
        report += "-" * 70 + "\n"
        
        db_recommendations = self.db_optimizer.recommend_optimizations()
        for rec in db_recommendations:
            report += f"• {rec}\n"
            
        report += "\n" + "=" * 70 + "\n"
        return report


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demonstrate_hot_path_optimization():
    """Demonstrate hot path optimization"""
    print("\n" + "=" * 70)
    print("HOT PATH OPTIMIZATION DEMONSTRATION")
    print("=" * 70)
    
    # Initialize optimizers
    profiler = HotPathProfiler()
    query_opt = QueryOptimizer()
    cache_opt = CacheLayerOptimizer()
    db_opt = DatabaseOperationOptimizer()
    
    # Simulate operations
    print("\n1. QUERY ANALYSIS")
    print("-" * 70)
    
    queries = [
        "SELECT * FROM users",
        "SELECT * FROM users WHERE age > 18",
        "SELECT u.* FROM users u JOIN posts p ON u.id = p.author_id"
    ]
    
    for query in queries:
        recommendations = query_opt.recommend_optimizations(query)
        print(f"\nQuery: {query[:50]}...")
        for rec in recommendations:
            print(f"  • {rec}")
            
    # Simulate cache operations
    print("\n\n2. CACHE LAYER ANALYSIS")
    print("-" * 70)
    
    for i in range(100):
        if i % 3 == 0:
            cache_opt.record_hit()
        else:
            cache_opt.record_miss()
            
    cache_analysis = cache_opt.analyze_cache_efficiency()
    print(f"Cache Hit Rate: {cache_analysis['hit_rate']}")
    print(f"Efficiency: {cache_analysis['efficiency']}")
    print(f"Strategy: {cache_opt.recommend_cache_strategy()}")
    
    # Simulate database operations
    print("\n\n3. DATABASE OPERATION ANALYSIS")
    print("-" * 70)
    
    import random
    operations = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    for op in operations:
        for _ in range(10):
            duration = random.uniform(0.005, 0.02)
            db_opt.record_operation(op, duration)
            
    db_stats = db_opt.get_operation_stats()
    for op, stats in db_stats.items():
        print(f"\n{op}:")
        print(f"  Average: {stats['average']:.4f}ms")
        print(f"  Count: {stats['count']}")
        
    # Generate full report
    print("\n\n4. FULL PERFORMANCE REPORT")
    print("-" * 70)
    
    report_gen = PerformanceReportGenerator()
    report_gen.profiler = profiler
    report_gen.query_optimizer = query_opt
    report_gen.cache_optimizer = cache_opt
    report_gen.db_optimizer = db_opt
    
    print(report_gen.generate_report())


if __name__ == "__main__":
    demonstrate_hot_path_optimization()
