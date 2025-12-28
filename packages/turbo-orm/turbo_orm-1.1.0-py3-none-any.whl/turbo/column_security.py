"""
Column-Level Security - Fine-grained access control
Schema-based authorization with row and column policies.
"""

from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum


class AccessLevel(Enum):
    """Access levels for policies"""
    DENY = "DENY"
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"
    ADMIN = "ADMIN"


@dataclass
class ColumnPolicy:
    """Policy for a single column"""
    table: str
    column: str
    role: str
    access_level: AccessLevel
    row_filter: Optional[str] = None  # SQL WHERE clause for row-level
    sensitive: bool = False
    masking_function: Optional[Callable[[Any], Any]] = None
    audit_enabled: bool = True


@dataclass
class RowPolicy:
    """Policy for row access"""
    table: str
    role: str
    filter_expression: str  # e.g., "owner_id = current_user_id"
    access_level: AccessLevel = AccessLevel.READ_ONLY


@dataclass
class AccessContext:
    """Current access context"""
    user_id: str
    roles: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    current_organization: Optional[str] = None
    current_tenant: Optional[str] = None


class PolicyEngine:
    """Evaluates access policies"""
    
    def __init__(self):
        self.column_policies: List[ColumnPolicy] = []
        self.row_policies: List[RowPolicy] = []
        self.access_logs: List[Dict[str, Any]] = []
    
    def add_column_policy(self, policy: ColumnPolicy):
        """Add a column-level policy"""
        self.column_policies.append(policy)
    
    def add_row_policy(self, policy: RowPolicy):
        """Add a row-level policy"""
        self.row_policies.append(policy)
    
    def can_access_column(self, context: AccessContext, table: str, 
                         column: str) -> tuple[bool, Optional[str]]:
        """Check if user can access column"""
        # Find matching policy
        matching_policies = [
            p for p in self.column_policies
            if p.table == table and p.column == column
            and p.role in context.roles
        ]
        
        if not matching_policies:
            # No explicit policy = deny
            return False, "No access policy"
        
        # Check access level
        policy = matching_policies[0]  # Use first match
        
        if policy.access_level == AccessLevel.DENY:
            return False, f"Access denied by policy {policy.role}"
        
        return True, None
    
    def get_row_filter(self, context: AccessContext, table: str) -> Optional[str]:
        """Get row filter SQL for current context"""
        matching_policies = [
            p for p in self.row_policies
            if p.table == table and p.role in context.roles
        ]
        
        if not matching_policies:
            return None
        
        # Combine filters with OR
        filters = [p.filter_expression for p in matching_policies]
        return " OR ".join([f"({f})" for f in filters])
    
    def rewrite_query(self, query: str, context: AccessContext, 
                     table: str) -> tuple[str, bool]:
        """Rewrite query to apply row-level security"""
        row_filter = self.get_row_filter(context, table)
        
        if not row_filter:
            return query, True
        
        # Add WHERE clause if not exists
        if "WHERE" not in query.upper():
            return query + f" WHERE {row_filter}", True
        else:
            # Append to existing WHERE
            return query.replace("WHERE", f"WHERE {row_filter} AND"), True
    
    def log_access(self, context: AccessContext, table: str, column: str,
                  allowed: bool, reason: Optional[str] = None):
        """Log access attempt"""
        self.access_logs.append({
            "user_id": context.user_id,
            "roles": context.roles,
            "table": table,
            "column": column,
            "allowed": allowed,
            "reason": reason,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
    
    def mask_sensitive_data(self, data: Dict[str, Any], context: AccessContext,
                           table: str) -> Dict[str, Any]:
        """Mask sensitive columns based on context"""
        masked = data.copy()
        
        for column, value in data.items():
            # Find matching policies
            policies = [
                p for p in self.column_policies
                if p.table == table and p.column == column
                and p.role in context.roles
                and p.sensitive
            ]
            
            for policy in policies:
                if policy.masking_function:
                    masked[column] = policy.masking_function(value)
                else:
                    # Default masking
                    if isinstance(value, str):
                        masked[column] = "*" * len(value)
                    else:
                        masked[column] = "***MASKED***"
        
        return masked


class AttributeBasedAccessControl:
    """Attribute-based access control (ABAC)"""
    
    def __init__(self):
        self.rules: Dict[str, Callable[[AccessContext], bool]] = {}
    
    def add_rule(self, rule_id: str, condition: Callable[[AccessContext], bool]):
        """Add an access rule"""
        self.rules[rule_id] = condition
    
    def evaluate(self, context: AccessContext, rule_id: str) -> bool:
        """Evaluate a rule"""
        if rule_id not in self.rules:
            return False
        
        try:
            return self.rules[rule_id](context)
        except:
            return False
    
    def evaluate_all(self, context: AccessContext) -> Dict[str, bool]:
        """Evaluate all rules"""
        results = {}
        for rule_id, rule_func in self.rules.items():
            results[rule_id] = self.evaluate(context, rule_id)
        return results


class ColumnSecurity:
    """Main column security manager"""
    
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.abac = AttributeBasedAccessControl()
        self.current_context: Optional[AccessContext] = None
    
    def set_context(self, context: AccessContext):
        """Set current access context"""
        self.current_context = context
    
    def with_context(self, user_id: str, roles: List[str] = None, **attrs):
        """Context manager for temporary access context"""
        class ContextManager:
            def __init__(self, security, context):
                self.security = security
                self.context = context
                self.previous = None
            
            def __enter__(self):
                self.previous = self.security.current_context
                self.security.set_context(self.context)
                return self
            
            def __exit__(self, *args):
                self.security.set_context(self.previous)
        
        context = AccessContext(user_id=user_id, roles=roles or [], attributes=attrs)
        return ContextManager(self, context)
    
    def can_read(self, table: str, column: str) -> bool:
        """Check if current user can read column"""
        if not self.current_context:
            return False
        
        allowed, _ = self.policy_engine.can_access_column(
            self.current_context, table, column
        )
        
        self.policy_engine.log_access(self.current_context, table, column, allowed)
        
        return allowed
    
    def can_write(self, table: str, column: str) -> bool:
        """Check if current user can write column"""
        if not self.current_context:
            return False
        
        allowed, _ = self.policy_engine.can_access_column(
            self.current_context, table, column
        )
        
        # Check if access level includes write
        matching = [
            p for p in self.policy_engine.column_policies
            if p.table == table and p.column == column
            and p.role in self.current_context.roles
        ]
        
        if matching:
            for p in matching:
                if p.access_level in (AccessLevel.READ_WRITE, AccessLevel.ADMIN):
                    allowed = True
                else:
                    allowed = False
        
        self.policy_engine.log_access(self.current_context, table, column, allowed)
        
        return allowed
    
    def execute_query(self, query: str, table: str) -> tuple[str, bool]:
        """Execute query with RLS applied"""
        if not self.current_context:
            return query, False
        
        rewritten, success = self.policy_engine.rewrite_query(
            query, self.current_context, table
        )
        
        return rewritten, success
    
    def mask_result(self, data: Dict[str, Any], table: str) -> Dict[str, Any]:
        """Mask sensitive data in result"""
        if not self.current_context:
            return data
        
        return self.policy_engine.mask_sensitive_data(data, self.current_context, table)
    
    def add_column_policy(self, policy: ColumnPolicy):
        """Add column policy"""
        self.policy_engine.add_column_policy(policy)
    
    def add_row_policy(self, policy: RowPolicy):
        """Add row policy"""
        self.policy_engine.add_row_policy(policy)
    
    def add_abac_rule(self, rule_id: str, condition: Callable[[AccessContext], bool]):
        """Add ABAC rule"""
        self.abac.add_rule(rule_id, condition)
    
    def get_audit_log(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit log"""
        if user_id:
            return [log for log in self.policy_engine.access_logs 
                   if log["user_id"] == user_id]
        return self.policy_engine.access_logs
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get security statistics"""
        access_allowed = sum(1 for log in self.policy_engine.access_logs if log["allowed"])
        access_denied = len(self.policy_engine.access_logs) - access_allowed
        
        return {
            "column_policies": len(self.policy_engine.column_policies),
            "row_policies": len(self.policy_engine.row_policies),
            "abac_rules": len(self.abac.rules),
            "access_attempts": len(self.policy_engine.access_logs),
            "access_allowed": access_allowed,
            "access_denied": access_denied,
            "current_context": self.current_context.user_id if self.current_context else None
        }


if __name__ == "__main__":
    print("✓ Column security module loaded successfully")
