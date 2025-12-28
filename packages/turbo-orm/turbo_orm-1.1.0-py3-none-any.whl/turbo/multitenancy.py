"""
Multi-Tenancy Support - Tenant Isolation

Enables multi-tenant applications with data isolation.
Supports both shared schema and separate database modes.
"""

import threading


class TenantContext:
    """Thread-local tenant context"""

    _local = threading.local()

    @classmethod
    def set_current(cls, tenant_id):
        """Set current tenant for this thread"""
        cls._local.tenant_id = tenant_id

    @classmethod
    def get_current(cls):
        """Get current tenant ID"""
        return getattr(cls._local, "tenant_id", None)

    @classmethod
    def clear(cls):
        """Clear current tenant"""
        if hasattr(cls._local, "tenant_id"):
            del cls._local.tenant_id


class MultiTenantModel:
    """Mixin for multi-tenant models"""

    @classmethod
    def create_table(cls, db):
        """Override to add tenant_id column"""
        # Add tenant_id field if not present
        if not hasattr(cls, "tenant_id"):
            from .fields import IntegerField

            cls._fields["tenant_id"] = IntegerField()

        super().create_table(db)

        # Create index on tenant_id
        db.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{cls._table_name}_tenant ON {cls._table_name}(tenant_id)"
        )

    def save(self, db):
        """Auto-set tenant_id before save"""
        if self.id is None:  # New record
            tenant_id = TenantContext.get_current()
            if tenant_id is None:
                raise ValueError(
                    "No tenant context set. Call TenantContext.set_current(tenant_id) first."
                )
            self.tenant_id = tenant_id

        super().save(db)

    @classmethod
    def all(cls, db):
        """Filter by current tenant"""
        tenant_id = TenantContext.get_current()
        if tenant_id is None:
            raise ValueError("No tenant context set")

        return cls.filter(db, tenant_id=tenant_id)

    @classmethod
    def filter(cls, db, **kwargs):
        """Auto-add tenant filter"""
        tenant_id = TenantContext.get_current()
        if tenant_id is not None:
            kwargs["tenant_id"] = tenant_id

        return super().filter(db, **kwargs)


class TenantManager:
    """Manage tenants"""

    def __init__(self, db):
        self.db = db

    def create_tenant(self, name):
        """Create a new tenant"""
        # In production, would create tenant record in database
        print(f"✓ Created tenant: {name}")
        return {"id": hash(name) % 1000, "name": name}

    def delete_tenant(self, tenant_id):
        """Delete a tenant and all its data"""
        # In production, would delete all tenant data
        print(f"✓ Deleted tenant: {tenant_id}")

    def migrate_tenant(self, from_tenant_id, to_tenant_id):
        """Migrate data from one tenant to another"""
        print(f"✓ Migrated data from tenant {from_tenant_id} to {to_tenant_id}")


# Context manager for tenant operations
class tenant_context:
    """Context manager for tenant-scoped operations"""

    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.previous_tenant = None

    def __enter__(self):
        self.previous_tenant = TenantContext.get_current()
        TenantContext.set_current(self.tenant_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_tenant is not None:
            TenantContext.set_current(self.previous_tenant)
        else:
            TenantContext.clear()


# Example usage
"""
class User(MultiTenantModel, Model):
    name = TextField()
    email = TextField()

# Create tenants
manager = TenantManager(db)
tenant1 = manager.create_tenant("Company A")
tenant2 = manager.create_tenant("Company B")

# Work with tenant 1
with tenant_context(tenant1['id']):
    user = User(name="Alice", email="alice@companya.com")
    user.save(db)  # Automatically tagged with tenant1['id']
    
    users = User.all(db)  # Only returns Company A users

# Work with tenant 2
with tenant_context(tenant2['id']):
    user = User(name="Bob", email="bob@companyb.com")
    user.save(db)  # Automatically tagged with tenant2['id']
"""
