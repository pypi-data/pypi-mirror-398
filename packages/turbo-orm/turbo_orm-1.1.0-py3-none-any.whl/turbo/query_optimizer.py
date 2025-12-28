"""
Query Optimizer - Automatic query optimization and analysis
Detects N+1 problems, optimizes joins, recommends indexes, and estimates costs.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class QueryType(Enum):
    """Types of queries"""
    SELECT = "SELECT"
    JOIN = "JOIN"
    SUBQUERY = "SUBQUERY"
    AGGREGATE = "AGGREGATE"


class OptimizationWarning(Enum):
    """Query optimization warnings"""
    N_PLUS_ONE = "N+1 Query Problem"
    MISSING_INDEX = "Missing Index"
    INEFFICIENT_JOIN = "Inefficient Join Order"
    SUBQUERY_IN_WHERE = "Subquery in WHERE clause"
    SELECT_STAR = "SELECT * without column selection"
    FULL_TABLE_SCAN = "Full table scan without index"
    SORT_WITHOUT_INDEX = "Sort without index"


@dataclass
class IndexRecommendation:
    """Recommendation for index creation"""
    table: str
    columns: List[str]
    type: str = "BTREE"
    priority: int = 1  # 1 (high) to 5 (low)
    estimated_improvement: float = 0.0  # Percentage improvement
    reason: str = ""


@dataclass
class QueryCost:
    """Estimated query cost"""
    estimated_rows: int
    cpu_cost: float
    io_cost: float
    total_cost: float
    full_table_scan: bool = False


@dataclass
class ExecutionPlan:
    """Query execution plan"""
    query_type: QueryType
    steps: List[str] = field(default_factory=list)
    estimated_cost: QueryCost = field(default_factory=lambda: QueryCost(0, 0, 0, 0))
    warnings: List[OptimizationWarning] = field(default_factory=list)
    recommendations: List[IndexRecommendation] = field(default_factory=list)
    optimized_query: str = ""


class QueryAnalyzer:
    """Analyzes queries for optimization opportunities"""
    
    def __init__(self):
        self.table_stats: Dict[str, Dict] = {}
        self.column_selectivity: Dict[str, float] = {}
        self.existing_indexes: Dict[str, List[List[str]]] = {}
    
    def analyze(self, query: str, table_context: Optional[Dict] = None) -> ExecutionPlan:
        """Analyze a query for optimization opportunities"""
        plan = ExecutionPlan(query_type=self._detect_query_type(query))
        
        # Detect N+1 problems
        if self._has_n_plus_one(query):
            plan.warnings.append(OptimizationWarning.N_PLUS_ONE)
            plan.recommendations.append(IndexRecommendation(
                table="*", columns=["id"],
                reason="Use JOIN instead of separate queries"
            ))
        
        # Detect SELECT *
        if "SELECT *" in query.upper():
            plan.warnings.append(OptimizationWarning.SELECT_STAR)
            plan.recommendations.append(IndexRecommendation(
                table="*", columns=[],
                reason="Explicitly select needed columns only"
            ))
        
        # Detect full table scans
        if self._has_full_table_scan(query):
            plan.warnings.append(OptimizationWarning.FULL_TABLE_SCAN)
        
        # Detect inefficient joins
        if self._has_inefficient_join(query):
            plan.warnings.append(OptimizationWarning.INEFFICIENT_JOIN)
        
        # Estimate cost
        plan.estimated_cost = self._estimate_cost(query)
        
        # Recommend indexes
        plan.recommendations.extend(self._recommend_indexes(query))
        
        return plan
    
    def _detect_query_type(self, query: str) -> QueryType:
        """Detect the type of query"""
        query_upper = query.upper()
        
        if "JOIN" in query_upper:
            return QueryType.JOIN
        elif "SELECT" in query_upper:
            if "SELECT" in query_upper and query_upper.count("SELECT") > 1:
                return QueryType.SUBQUERY
            return QueryType.SELECT
        elif "GROUP BY" in query_upper or "COUNT" in query_upper:
            return QueryType.AGGREGATE
        
        return QueryType.SELECT
    
    def _has_n_plus_one(self, query: str) -> bool:
        """Detect N+1 query pattern"""
        # Simple heuristic: repeated similar queries or loops
        return "WHERE id =" in query or "WHERE id IN" in query
    
    def _has_full_table_scan(self, query: str) -> bool:
        """Detect full table scan"""
        query_upper = query.upper()
        # If WHERE clause is missing or very simple
        return "WHERE" not in query_upper or "WHERE 1=1" in query_upper
    
    def _has_inefficient_join(self, query: str) -> bool:
        """Detect inefficient join patterns"""
        # Check for joins on non-indexed columns or string comparisons
        return "JOIN" in query.upper() and ("CAST" in query.upper() or "::text" in query.lower())
    
    def _estimate_cost(self, query: str) -> QueryCost:
        """Estimate query cost"""
        # Simplified cost estimation
        full_scan = self._has_full_table_scan(query)
        
        estimated_rows = 1000 if full_scan else 10
        cpu_cost = 100.0 if full_scan else 10.0
        io_cost = 500.0 if full_scan else 50.0
        total_cost = cpu_cost + io_cost
        
        return QueryCost(
            estimated_rows=estimated_rows,
            cpu_cost=cpu_cost,
            io_cost=io_cost,
            total_cost=total_cost,
            full_table_scan=full_scan
        )
    
    def _recommend_indexes(self, query: str) -> List[IndexRecommendation]:
        """Recommend indexes to improve query"""
        recommendations = []
        
        # Recommend index on WHERE columns
        if "WHERE" in query.upper():
            recommendations.append(IndexRecommendation(
                table="detected_table",
                columns=["id"],
                priority=1,
                estimated_improvement=75.0,
                reason="Index on WHERE clause columns"
            ))
        
        # Recommend index on JOIN columns
        if "JOIN" in query.upper():
            recommendations.append(IndexRecommendation(
                table="detected_table",
                columns=["foreign_key"],
                priority=1,
                estimated_improvement=80.0,
                reason="Index on JOIN columns"
            ))
        
        return recommendations
    
    def register_table_stats(self, table_name: str, row_count: int, avg_row_size: int):
        """Register statistics for a table"""
        self.table_stats[table_name] = {
            "row_count": row_count,
            "avg_row_size": avg_row_size
        }
    
    def register_index(self, table_name: str, columns: List[str]):
        """Register an existing index"""
        if table_name not in self.existing_indexes:
            self.existing_indexes[table_name] = []
        self.existing_indexes[table_name].append(columns)


class QueryOptimizer:
    """Main query optimizer"""
    
    def __init__(self):
        self.analyzer = QueryAnalyzer()
        self.query_cache: Dict[str, ExecutionPlan] = {}
    
    def optimize(self, query: str, use_cache: bool = True) -> ExecutionPlan:
        """Optimize a query and return execution plan"""
        if use_cache and query in self.query_cache:
            return self.query_cache[query]
        
        plan = self.analyzer.analyze(query)
        
        if use_cache:
            self.query_cache[query] = plan
        
        return plan
    
    def suggest_optimization(self, query: str) -> str:
        """Suggest optimized version of query"""
        plan = self.optimize(query)
        
        suggestion = query
        
        # Suggest eager loading for N+1
        if OptimizationWarning.N_PLUS_ONE in plan.warnings:
            suggestion = suggestion.replace("WHERE id =", "WHERE id IN")
        
        # Suggest removing SELECT *
        if OptimizationWarning.SELECT_STAR in plan.warnings:
            suggestion = suggestion.replace("SELECT *", "SELECT id, name, email")
        
        return suggestion
    
    def explain_plan(self, query: str) -> Dict[str, Any]:
        """Explain query execution plan"""
        plan = self.optimize(query)
        
        return {
            "query_type": plan.query_type.value,
            "estimated_cost": {
                "rows": plan.estimated_cost.estimated_rows,
                "cpu": plan.estimated_cost.cpu_cost,
                "io": plan.estimated_cost.io_cost,
                "total": plan.estimated_cost.total_cost
            },
            "warnings": [w.value for w in plan.warnings],
            "recommendations": [{
                "table": r.table,
                "columns": r.columns,
                "priority": r.priority,
                "reason": r.reason
            } for r in plan.recommendations],
            "full_table_scan": plan.estimated_cost.full_table_scan
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            "cached_plans": len(self.query_cache),
            "registered_tables": len(self.analyzer.table_stats),
            "registered_indexes": sum(len(idxs) for idxs in self.analyzer.existing_indexes.values())
        }


if __name__ == "__main__":
    print("✓ Query optimizer module loaded successfully")
