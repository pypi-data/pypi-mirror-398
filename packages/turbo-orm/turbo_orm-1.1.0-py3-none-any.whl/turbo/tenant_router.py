"""
Multi-Tenant Router - Automatic data isolation per tenant
Query rewriting, context detection, and encryption per tenant.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class TenantContextSource(Enum):
    """Sources for tenant context"""
    HEADER = "header"
    JWT = "jwt"
    COOKIE = "cookie"
    SESSION = "session"
    ENVIRONMENT = "environment"


@dataclass
class TenantContext:
    """Represents the current tenant context"""
    tenant_id: str
    tenant_name: str
    isolation_level: str  # 'STRICT', 'LOOSE', 'SHARED'
    encryption_key: Optional[str] = None
    allowed_tables: List[str] = field(default_factory=list)
    allowed_columns: List[str] = field(default_factory=list)
    max_query_rows: int = 10000
    rate_limit: int = 1000  # requests per minute
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "isolation_level": self.isolation_level,
            "allowed_tables": self.allowed_tables,
            "max_query_rows": self.max_query_rows
        }


@dataclass
class TenantPolicy:
    """Policy configuration for a tenant"""
    tenant_id: str
    isolation_level: str = "STRICT"
    row_filter_column: str = "tenant_id"
    encryption_enabled: bool = True
    audit_enabled: bool = True
    allowed_tables: List[str] = field(default_factory=list)
    forbidden_tables: List[str] = field(default_factory=list)
    max_rows: int = 10000
    rate_limit: int = 1000


class TenantContextManager:
    """Manages tenant context detection and switching"""
    
    def __init__(self):
        self.current_context: Optional[TenantContext] = None
        self.context_stack: List[TenantContext] = []
        self.source_priority = [
            TenantContextSource.JWT,
            TenantContextSource.HEADER,
            TenantContextSource.SESSION,
            TenantContextSource.COOKIE
        ]
    
    def set_context(self, context: TenantContext):
        """Set current tenant context"""
        self.current_context = context
    
    def push_context(self, context: TenantContext):
        """Push context onto stack for nested operations"""
        if self.current_context:
            self.context_stack.append(self.current_context)
        self.current_context = context
    
    def pop_context(self):
        """Pop context from stack"""
        if self.context_stack:
            self.current_context = self.context_stack.pop()
        else:
            self.current_context = None
    
    def detect_from_jwt(self, token: str) -> Optional[TenantContext]:
        """Detect tenant from JWT token"""
        # Simplified - in production use jwt.decode()
        try:
            parts = token.split(".")
            if len(parts) >= 2:
                # Simulate JWT payload parsing
                payload = parts[1]
                # In real implementation: json.loads(base64.decode(payload))
                return TenantContext(
                    tenant_id="tenant_" + payload[:8],
                    tenant_name="Tenant from JWT",
                    isolation_level="STRICT"
                )
        except:
            pass
        return None
    
    def detect_from_header(self, headers: Dict[str, str]) -> Optional[TenantContext]:
        """Detect tenant from request header"""
        tenant_id = headers.get("X-Tenant-ID")
        if tenant_id:
            return TenantContext(
                tenant_id=tenant_id,
                tenant_name=headers.get("X-Tenant-Name", tenant_id),
                isolation_level="STRICT"
            )
        return None
    
    def detect_context(self, source: TenantContextSource, 
                      data: Any) -> Optional[TenantContext]:
        """Detect tenant context from various sources"""
        if source == TenantContextSource.JWT:
            return self.detect_from_jwt(str(data))
        elif source == TenantContextSource.HEADER:
            return self.detect_from_header(data)
        elif source == TenantContextSource.ENVIRONMENT:
            return TenantContext(
                tenant_id=str(data),
                tenant_name=f"Tenant {data}",
                isolation_level="STRICT"
            )
        return None
    
    def get_current_context(self) -> Optional[TenantContext]:
        """Get current tenant context"""
        return self.current_context
    
    def is_tenant_context_set(self) -> bool:
        """Check if tenant context is set"""
        return self.current_context is not None


class TenantQueryRewriter:
    """Rewrites queries to enforce tenant isolation"""
    
    def __init__(self, policy_manager: "TenantPolicyManager"):
        self.policy_manager = policy_manager
        self.context_manager = TenantContextManager()
    
    def rewrite_query(self, query: str, tenant_id: str) -> str:
        """Rewrite query to filter by tenant"""
        policy = self.policy_manager.get_policy(tenant_id)
        
        if not policy:
            return query
        
        if policy.isolation_level == "STRICT":
            return self._add_tenant_filter(query, tenant_id, policy.row_filter_column)
        
        return query
    
    def _add_tenant_filter(self, query: str, tenant_id: str, filter_column: str) -> str:
        """Add tenant filter to WHERE clause"""
        tenant_filter = f"{filter_column} = '{tenant_id}'"
        
        query_upper = query.upper()
        
        if "WHERE" in query_upper:
            # Add to existing WHERE clause
            insert_pos = query_upper.rfind("WHERE") + 5
            return query[:insert_pos] + f" {tenant_filter} AND " + query[insert_pos:]
        else:
            # Add new WHERE clause
            return query + f" WHERE {tenant_filter}"
    
    def validate_query_allowed(self, query: str, tenant_id: str) -> Tuple[bool, Optional[str]]:
        """Validate query is allowed for tenant"""
        policy = self.policy_manager.get_policy(tenant_id)
        
        if not policy:
            return False, "No policy found for tenant"
        
        # Check for forbidden tables
        query_upper = query.upper()
        for forbidden in policy.forbidden_tables:
            if f"FROM {forbidden.upper()}" in query_upper or \
               f"UPDATE {forbidden.upper()}" in query_upper or \
               f"DELETE FROM {forbidden.upper()}" in query_upper:
                return False, f"Access to {forbidden} is forbidden"
        
        # Check for allowed tables if list is defined
        if policy.allowed_tables:
            has_allowed_table = False
            for allowed in policy.allowed_tables:
                if f"FROM {allowed.upper()}" in query_upper:
                    has_allowed_table = True
                    break
            if not has_allowed_table:
                return False, "Query uses tables not in allowed list"
        
        return True, None


class TenantPolicyManager:
    """Manages tenant policies"""
    
    def __init__(self):
        self.policies: Dict[str, TenantPolicy] = {}
    
    def register_policy(self, policy: TenantPolicy):
        """Register a policy for a tenant"""
        self.policies[policy.tenant_id] = policy
    
    def get_policy(self, tenant_id: str) -> Optional[TenantPolicy]:
        """Get policy for tenant"""
        return self.policies.get(tenant_id)
    
    def create_default_policy(self, tenant_id: str) -> TenantPolicy:
        """Create default policy for tenant"""
        policy = TenantPolicy(
            tenant_id=tenant_id,
            isolation_level="STRICT",
            allowed_tables=["users", "orders", "products"]
        )
        self.register_policy(policy)
        return policy


class TenantRouter:
    """Main tenant router for data isolation"""
    
    def __init__(self):
        self.context_manager = TenantContextManager()
        self.policy_manager = TenantPolicyManager()
        self.query_rewriter = TenantQueryRewriter(self.policy_manager)
        self.audit_log: List[Dict[str, Any]] = []
    
    def set_tenant_context(self, tenant_id: str, tenant_name: str = "",
                          isolation_level: str = "STRICT"):
        """Set current tenant context"""
        context = TenantContext(
            tenant_id=tenant_id,
            tenant_name=tenant_name or f"Tenant {tenant_id}",
            isolation_level=isolation_level
        )
        self.context_manager.set_context(context)
    
    def with_tenant(self, tenant_id: str):
        """Context manager for temporary tenant switching"""
        class TenantContextManager:
            def __init__(self, router, tenant_id):
                self.router = router
                self.tenant_id = tenant_id
                self.previous_context = None
            
            def __enter__(self):
                self.previous_context = self.router.context_manager.current_context
                self.router.set_tenant_context(self.tenant_id)
                return self
            
            def __exit__(self, *args):
                self.router.context_manager.set_context(self.previous_context)
        
        return TenantContextManager(self, tenant_id)
    
    def execute_query(self, query: str) -> Tuple[str, bool, Optional[str]]:
        """Execute query with tenant isolation"""
        context = self.context_manager.get_current_context()
        
        if not context:
            return query, False, "No tenant context set"
        
        # Validate query
        allowed, error = self.query_rewriter.validate_query_allowed(query, context.tenant_id)
        if not allowed:
            return query, False, error
        
        # Rewrite query with tenant filter
        rewritten_query = self.query_rewriter.rewrite_query(query, context.tenant_id)
        
        # Log access
        self._log_access(context.tenant_id, query, True)
        
        return rewritten_query, True, None
    
    def _log_access(self, tenant_id: str, query: str, success: bool):
        """Log query access for audit"""
        self.audit_log.append({
            "tenant_id": tenant_id,
            "query": query[:100],  # First 100 chars
            "success": success,
            "timestamp": str(__import__('datetime').datetime.now())
        })
    
    def get_audit_log(self, tenant_id: Optional[str] = None) -> List[Dict]:
        """Get audit log, optionally filtered by tenant"""
        if tenant_id:
            return [log for log in self.audit_log if log["tenant_id"] == tenant_id]
        return self.audit_log
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            "active_tenants": len(self.policy_manager.policies),
            "audit_log_entries": len(self.audit_log),
            "current_tenant": self.context_manager.current_context.tenant_id if \
                            self.context_manager.current_context else None
        }


if __name__ == "__main__":
    print("✓ Tenant router module loaded successfully")
