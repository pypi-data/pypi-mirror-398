"""
Recursive Query Support - Hierarchical and graph queries
SQL WITH RECURSIVE support with materialization and cycle detection.
"""

from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, deque


@dataclass
class TreeNode:
    """Represents a node in a hierarchy"""
    id: Any
    value: Dict[str, Any]
    parent_id: Optional[Any] = None
    depth: int = 0
    path: List[Any] = None
    
    def __post_init__(self):
        if self.path is None:
            self.path = [self.id]


class HierarchyBuilder:
    """Builds hierarchies from flat data"""
    
    def __init__(self, parent_key: str = "parent_id", id_key: str = "id"):
        self.parent_key = parent_key
        self.id_key = id_key
    
    def build_tree(self, rows: List[Dict[str, Any]]) -> Dict[Any, TreeNode]:
        """Build tree from flat rows"""
        nodes = {}
        children = defaultdict(list)
        
        # Create nodes and build child relationships
        for row in rows:
            node_id = row[self.id_key]
            parent_id = row.get(self.parent_key)
            
            nodes[node_id] = TreeNode(
                id=node_id,
                value=row,
                parent_id=parent_id
            )
            
            if parent_id is not None:
                children[parent_id].append(node_id)
        
        # Set depth and path for each node
        self._set_depths(nodes, children)
        
        return nodes
    
    def _set_depths(self, nodes: Dict, children: Dict):
        """Set depth and path for each node"""
        queue = deque()
        
        # Find roots (nodes with no parent)
        for node_id, node in nodes.items():
            if node.parent_id is None:
                node.depth = 0
                queue.append(node_id)
        
        # BFS to set depths
        while queue:
            node_id = queue.popleft()
            node = nodes[node_id]
            
            for child_id in children.get(node_id, []):
                child = nodes[child_id]
                child.depth = node.depth + 1
                child.path = node.path + [child_id]
                queue.append(child_id)


class RecursiveQueryBuilder:
    """Builds recursive SQL queries"""
    
    @staticmethod
    def ancestors_of(table: str, id_key: str, parent_key: str, 
                    node_id: Any, max_depth: Optional[int] = None) -> str:
        """Build SQL to get all ancestors"""
        depth_check = f"AND depth < {max_depth}" if max_depth else ""
        
        query = f"""
WITH RECURSIVE ancestors AS (
    SELECT {id_key}, {parent_key}, 0 as depth
    FROM {table}
    WHERE {id_key} = {node_id}
    
    UNION ALL
    
    SELECT t.{id_key}, t.{parent_key}, a.depth + 1
    FROM {table} t
    INNER JOIN ancestors a ON t.{id_key} = a.{parent_key}
    WHERE a.{parent_key} IS NOT NULL
    {depth_check}
)
SELECT * FROM ancestors ORDER BY depth DESC
        """.strip()
        
        return query
    
    @staticmethod
    def descendants_of(table: str, id_key: str, parent_key: str,
                      node_id: Any, max_depth: Optional[int] = None) -> str:
        """Build SQL to get all descendants"""
        depth_check = f"AND depth < {max_depth}" if max_depth else ""
        
        query = f"""
WITH RECURSIVE descendants AS (
    SELECT {id_key}, {parent_key}, 0 as depth
    FROM {table}
    WHERE {id_key} = {node_id}
    
    UNION ALL
    
    SELECT t.{id_key}, t.{parent_key}, d.depth + 1
    FROM {table} t
    INNER JOIN descendants d ON t.{parent_key} = d.{id_key}
    {depth_check}
)
SELECT * FROM descendants ORDER BY depth
        """.strip()
        
        return query
    
    @staticmethod
    def path_between(table: str, id_key: str, parent_key: str,
                    from_id: Any, to_id: Any) -> str:
        """Build SQL to find path between two nodes"""
        query = f"""
WITH RECURSIVE path AS (
    SELECT {id_key}, {parent_key}, ARRAY[{id_key}] as path
    FROM {table}
    WHERE {id_key} = {from_id}
    
    UNION ALL
    
    SELECT t.{id_key}, t.{parent_key}, path || ARRAY[t.{id_key}]
    FROM {table} t
    INNER JOIN path p ON t.{parent_key} = p.{id_key}
    WHERE NOT t.{id_key} = ANY(p.path)
    AND array_length(p.path, 1) < 10
)
SELECT path FROM path WHERE {id_key} = {to_id}
        """.strip()
        
        return query


class CycleDetector:
    """Detects cycles in hierarchical data"""
    
    @staticmethod
    def has_cycle(parent_map: Dict[Any, Optional[Any]]) -> bool:
        """Check if there's a cycle in parent relationships"""
        visited = set()
        rec_stack = set()
        
        def dfs(node: Any) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            parent = parent_map.get(node)
            if parent is None:
                rec_stack.remove(node)
                return False
            
            if parent in rec_stack:
                return True  # Cycle found
            
            if parent not in visited:
                if dfs(parent):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in parent_map:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    @staticmethod
    def find_cycle(parent_map: Dict[Any, Optional[Any]]) -> Optional[List[Any]]:
        """Find a cycle if it exists"""
        visited = set()
        path = []
        
        def dfs(node: Any, current_path: List[Any]) -> Optional[List[Any]]:
            if node in current_path:
                # Found cycle
                cycle_start = current_path.index(node)
                return current_path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            parent = parent_map.get(node)
            
            if parent is None:
                return None
            
            result = dfs(parent, current_path + [node])
            return result
        
        for node in parent_map:
            if node not in visited:
                result = dfs(node, [])
                if result:
                    return result
        
        return None


class RecursiveQuery:
    """Recursive query executor"""
    
    def __init__(self):
        self.hierarchy_builder = HierarchyBuilder()
        self.cycle_detector = CycleDetector()
    
    def ancestors(self, data: List[Dict[str, Any]], node_id: Any,
                 id_key: str = "id", parent_key: str = "parent_id",
                 max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all ancestors of a node"""
        # Build parent map
        parent_map = {row[id_key]: row.get(parent_key) for row in data}
        
        # Check for cycles
        if self.cycle_detector.has_cycle(parent_map):
            return []
        
        # Traverse up
        ancestors = []
        current_id = node_id
        depth = 0
        
        while current_id is not None:
            if max_depth and depth >= max_depth:
                break
            
            # Find row with this id
            for row in data:
                if row[id_key] == current_id:
                    ancestors.append(row)
                    current_id = row.get(parent_key)
                    break
            else:
                break
            
            depth += 1
        
        return ancestors
    
    def descendants(self, data: List[Dict[str, Any]], node_id: Any,
                   id_key: str = "id", parent_key: str = "parent_id",
                   max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all descendants of a node"""
        # Build child map
        child_map = defaultdict(list)
        for row in data:
            parent = row.get(parent_key)
            if parent is not None:
                child_map[parent].append(row[id_key])
        
        # BFS to find descendants
        descendants = []
        queue = deque([(node_id, 0)])
        visited = set()
        
        while queue:
            current_id, depth = queue.popleft()
            
            if current_id in visited:
                continue
            visited.add(current_id)
            
            if max_depth and depth >= max_depth:
                continue
            
            # Find row with this id
            for row in data:
                if row[id_key] == current_id:
                    descendants.append(row)
                    break
            
            # Add children
            for child_id in child_map[current_id]:
                queue.append((child_id, depth + 1))
        
        return descendants[1:] if descendants else []  # Exclude root
    
    def tree_structure(self, data: List[Dict[str, Any]], root_id: Any,
                      id_key: str = "id", parent_key: str = "parent_id") -> Dict[str, Any]:
        """Build tree structure"""
        def build_node(node_id: Any) -> Dict[str, Any]:
            node_data = None
            for row in data:
                if row[id_key] == node_id:
                    node_data = row
                    break
            
            if node_data is None:
                return {}
            
            # Find children
            children = []
            for row in data:
                if row.get(parent_key) == node_id:
                    children.append(build_node(row[id_key]))
            
            return {
                "id": node_id,
                "data": node_data,
                "children": children
            }
        
        return build_node(root_id)
    
    def get_path(self, data: List[Dict[str, Any]], from_id: Any, to_id: Any,
                id_key: str = "id", parent_key: str = "parent_id") -> Optional[List[Any]]:
        """Find path between two nodes"""
        # Find path from to_id to root, then traverse to from_id
        ancestors_of_target = self.ancestors(data, to_id, id_key, parent_key)
        
        # Try to find connection from from_id
        current = from_id
        from_ancestors = []
        
        for row in data:
            if row[id_key] == current:
                from_ancestors.append(current)
                current = row.get(parent_key)
                if current is None:
                    break
        
        # Find common ancestor
        target_ids = {a[id_key] for a in ancestors_of_target}
        
        for i, ancestor in enumerate(from_ancestors):
            if ancestor in target_ids:
                # Found common ancestor
                path = from_ancestors[:i+1]
                # Add path down to target
                target_path = [a[id_key] for a in ancestors_of_target]
                target_path_down = target_path[:target_path.index(ancestor)]
                return path + target_path_down[::-1]
        
        return None


if __name__ == "__main__":
    print("✓ Recursive query module loaded successfully")
