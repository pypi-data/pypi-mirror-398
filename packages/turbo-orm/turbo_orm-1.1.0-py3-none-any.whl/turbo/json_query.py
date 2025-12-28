"""
JSON Query Support - Hybrid JSON/document querying
Natural syntax for querying JSON fields with full FTS and indexing support.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import json
import re


@dataclass
class JSONPath:
    """Represents a JSON path"""
    path: str
    value: Any = None
    
    def extract(self, data: Dict[str, Any]) -> Any:
        """Extract value from data using path"""
        parts = self.path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    index = int(part.replace("[", "").replace("]", ""))
                    current = current[index]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        
        return current


class JSONOperator:
    """Represents a JSON query operator"""
    
    # Comparison operators
    EQ = "="
    NE = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    
    # Array operators
    CONTAINS = "CONTAINS"
    IN = "IN"
    OVERLAPS = "OVERLAPS"
    
    # Type operators
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"
    IS_ARRAY = "IS_ARRAY"
    IS_OBJECT = "IS_OBJECT"


class JSONQuery:
    """Build JSON queries"""
    
    def __init__(self, table: str):
        self.table = table
        self.conditions: List[Dict[str, Any]] = []
        self.selected_fields: List[str] = []
        self.order_by: Optional[tuple[str, str]] = None
        self.limit_val: Optional[int] = None
    
    def where_json(self, json_path: str, operator: str, value: Any) -> "JSONQuery":
        """Add JSON WHERE condition"""
        self.conditions.append({
            "path": json_path,
            "operator": operator,
            "value": value
        })
        return self
    
    def select(self, *fields: str) -> "JSONQuery":
        """Select specific fields"""
        self.selected_fields = list(fields)
        return self
    
    def order_by_json(self, json_path: str, direction: str = "ASC") -> "JSONQuery":
        """Order by JSON field"""
        self.order_by = (json_path, direction)
        return self
    
    def limit(self, limit: int) -> "JSONQuery":
        """Limit results"""
        self.limit_val = limit
        return self
    
    def to_sql(self) -> str:
        """Convert to SQL query"""
        parts = ["SELECT"]
        
        if self.selected_fields:
            parts.append(", ".join(self.selected_fields))
        else:
            parts.append("*")
        
        parts.append(f"FROM {self.table}")
        
        if self.conditions:
            where_parts = []
            for cond in self.conditions:
                where_parts.append(self._build_where_clause(cond))
            parts.append("WHERE " + " AND ".join(where_parts))
        
        if self.order_by:
            path, direction = self.order_by
            parts.append(f"ORDER BY {path} {direction}")
        
        if self.limit_val:
            parts.append(f"LIMIT {self.limit_val}")
        
        return " ".join(parts)
    
    def _build_where_clause(self, condition: Dict[str, Any]) -> str:
        """Build WHERE clause from condition"""
        path = condition["path"]
        operator = condition["operator"]
        value = condition["value"]
        
        if operator == JSONOperator.CONTAINS:
            return f"{path} @> '{json.dumps(value)}'"
        elif operator == JSONOperator.OVERLAPS:
            return f"{path} && '{json.dumps(value)}'"
        elif operator in (JSONOperator.GT, JSONOperator.LT, JSONOperator.GTE, JSONOperator.LTE):
            return f"CAST({path}->>'value' AS INTEGER) {operator} {value}"
        elif operator == JSONOperator.IS_NULL:
            return f"{path} IS NULL"
        elif operator == JSONOperator.IS_NOT_NULL:
            return f"{path} IS NOT NULL"
        elif operator == JSONOperator.IS_ARRAY:
            return f"json_typeof({path}) = 'array'"
        elif operator == JSONOperator.IS_OBJECT:
            return f"json_typeof({path}) = 'object'"
        else:
            return f"{path} {operator} '{value}'"


class JSONFilter:
    """Filters JSON data"""
    
    @staticmethod
    def filter_data(data: List[Dict[str, Any]], conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter data by JSON conditions"""
        results = []
        
        for row in data:
            if JSONFilter._matches_conditions(row, conditions):
                results.append(row)
        
        return results
    
    @staticmethod
    def _matches_conditions(row: Dict[str, Any], conditions: List[Dict[str, Any]]) -> bool:
        """Check if row matches all conditions"""
        for condition in conditions:
            if not JSONFilter._matches_condition(row, condition):
                return False
        return True
    
    @staticmethod
    def _matches_condition(row: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Check if row matches a condition"""
        path = condition["path"]
        operator = condition["operator"]
        value = condition["value"]
        
        json_path = JSONPath(path)
        extracted = json_path.extract(row)
        
        if operator == "=":
            return extracted == value
        elif operator == "!=":
            return extracted != value
        elif operator == ">":
            return extracted > value if extracted else False
        elif operator == "<":
            return extracted < value if extracted else False
        elif operator == ">=":
            return extracted >= value if extracted else False
        elif operator == "<=":
            return extracted <= value if extracted else False
        elif operator == JSONOperator.CONTAINS:
            if isinstance(extracted, list):
                return value in extracted
            elif isinstance(extracted, dict):
                return value in extracted.values()
            return False
        elif operator == JSONOperator.IN:
            return extracted in value if isinstance(value, list) else False
        elif operator == JSONOperator.OVERLAPS:
            if isinstance(extracted, list) and isinstance(value, list):
                return len(set(extracted) & set(value)) > 0
            return False
        elif operator == JSONOperator.IS_NULL:
            return extracted is None
        elif operator == JSONOperator.IS_NOT_NULL:
            return extracted is not None
        elif operator == JSONOperator.IS_ARRAY:
            return isinstance(extracted, list)
        elif operator == JSONOperator.IS_OBJECT:
            return isinstance(extracted, dict)
        
        return False


class JSONIndex:
    """Manages JSON field indexing"""
    
    def __init__(self, table: str, field: str, path: Optional[str] = None):
        self.table = table
        self.field = field
        self.path = path
        self.index_data: Dict[Any, List[int]] = {}
    
    def build_index(self, rows: List[Dict[str, Any]]):
        """Build index on JSON field"""
        for idx, row in enumerate(rows):
            value = row.get(self.field)
            
            if self.path:
                json_path = JSONPath(self.path)
                value = json_path.extract(row)
            
            if value not in self.index_data:
                self.index_data[value] = []
            self.index_data[value].append(idx)
    
    def lookup(self, value: Any) -> List[int]:
        """Lookup rows by value"""
        return self.index_data.get(value, [])
    
    def get_index_info(self) -> Dict[str, Any]:
        """Get index information"""
        return {
            "table": self.table,
            "field": self.field,
            "path": self.path,
            "unique_values": len(self.index_data),
            "total_entries": sum(len(v) for v in self.index_data.values())
        }


class FullTextSearchJSON:
    """Full-text search on JSON fields"""
    
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
    
    def index_documents(self, docs: List[Dict[str, Any]]):
        """Index documents for FTS"""
        self.documents = docs
    
    def search(self, query: str, json_field: str) -> List[Dict[str, Any]]:
        """Full-text search on JSON field"""
        query_terms = query.lower().split()
        results = []
        
        for doc in self.documents:
            json_data = doc.get(json_field, "")
            json_str = json.dumps(json_data).lower()
            
            # Simple term matching
            if all(term in json_str for term in query_terms):
                results.append(doc)
        
        return results
    
    def search_and_filter(self, fts_query: str, json_field: str,
                         filters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Full-text search with JSON filtering"""
        # First do FTS
        fts_results = self.search(fts_query, json_field)
        
        # Then apply JSON filters
        return JSONFilter.filter_data(fts_results, filters)


class JSONDocument:
    """Represents a JSON document in database"""
    
    def __init__(self, table: str, id: Any, data: Dict[str, Any]):
        self.table = table
        self.id = id
        self.data = data
    
    def get_path(self, path: str) -> Any:
        """Get value by path"""
        json_path = JSONPath(path)
        return json_path.extract(self.data)
    
    def set_path(self, path: str, value: Any):
        """Set value by path"""
        parts = path.split(".")
        current = self.data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "id": self.id,
            "table": self.table,
            "data": self.data
        }


class JSONQueryEngine:
    """Main JSON query engine"""
    
    def __init__(self):
        self.indexes: Dict[str, JSONIndex] = {}
        self.fts: FullTextSearchJSON = FullTextSearchJSON()
        self.documents: List[Dict[str, Any]] = []
    
    def insert_document(self, table: str, data: Dict[str, Any]) -> JSONDocument:
        """Insert a JSON document"""
        doc_id = len(self.documents)
        doc = JSONDocument(table, doc_id, data)
        self.documents.append(data)
        return doc
    
    def create_index(self, table: str, field: str, path: Optional[str] = None) -> JSONIndex:
        """Create index on JSON field"""
        index = JSONIndex(table, field, path)
        index.build_index(self.documents)
        key = f"{table}.{field}"
        self.indexes[key] = index
        return index
    
    def query(self, table: str) -> JSONQuery:
        """Start a JSON query"""
        return JSONQuery(table)
    
    def execute_query(self, query: JSONQuery) -> List[Dict[str, Any]]:
        """Execute a JSON query"""
        results = self.documents
        
        if query.conditions:
            results = JSONFilter.filter_data(results, query.conditions)
        
        if query.order_by:
            path, direction = query.order_by
            results = sorted(results, key=lambda x: JSONPath(path).extract(x) or "",
                           reverse=(direction == "DESC"))
        
        if query.limit_val:
            results = results[:query.limit_val]
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "total_documents": len(self.documents),
            "indexes": len(self.indexes),
            "index_details": [idx.get_index_info() for idx in self.indexes.values()]
        }


if __name__ == "__main__":
    print("✓ JSON query engine module loaded successfully")
