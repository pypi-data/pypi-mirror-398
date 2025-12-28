"""
Audit Logging - Track All Data Changes

Comprehensive audit trail for compliance and security.
Tracks who changed what, when, and from where.
"""

import datetime
import json
from .model import Model
from .fields import IntegerField, TextField, JSONField, DateTimeField


class AuditLog(Model):
    """Audit log model"""

    user_id = IntegerField()
    user_name = TextField()
    model_name = TextField()
    record_id = IntegerField()
    action = TextField()  # CREATE, UPDATE, DELETE
    changes = JSONField()  # What changed
    ip_address = TextField()
    timestamp = DateTimeField()

    class Meta:
        indexes = [
            ("model_name", "record_id"),
            ("user_id",),
            ("timestamp",),
        ]


class AuditContext:
    """Thread-local audit context"""

    import threading

    _local = threading.local()

    @classmethod
    def set_user(cls, user_id, user_name, ip_address=None):
        """Set current user for audit trail"""
        cls._local.user_id = user_id
        cls._local.user_name = user_name
        cls._local.ip_address = ip_address or "0.0.0.0"

    @classmethod
    def get_user(cls):
        """Get current user info"""
        return {
            "user_id": getattr(cls._local, "user_id", None),
            "user_name": getattr(cls._local, "user_name", "anonymous"),
            "ip_address": getattr(cls._local, "ip_address", "0.0.0.0"),
        }

    @classmethod
    def clear(cls):
        """Clear audit context"""
        for attr in ["user_id", "user_name", "ip_address"]:
            if hasattr(cls._local, attr):
                delattr(cls._local, attr)


class AuditedModel:
    """Mixin for audited models"""

    def save(self, db):
        """Save with audit logging"""
        is_new = self.id is None
        old_data = None

        # Capture old state for updates
        if not is_new:
            old_instance = self.__class__.get(db, self.id)
            if old_instance:
                old_data = {k: getattr(old_instance, k) for k in self._fields.keys()}

        # Perform save
        super().save(db)

        # Log the change
        user_info = AuditContext.get_user()
        changes = {}

        if is_new:
            action = "CREATE"
            changes = {k: getattr(self, k) for k in self._fields.keys()}
        else:
            action = "UPDATE"
            for key in self._fields.keys():
                new_val = getattr(self, key)
                old_val = old_data.get(key) if old_data else None
                if new_val != old_val:
                    changes[key] = {"from": old_val, "to": new_val}

        # Create audit log entry
        audit_entry = AuditLog(
            user_id=user_info["user_id"],
            user_name=user_info["user_name"],
            model_name=self.__class__.__name__,
            record_id=self.id,
            action=action,
            changes=changes,
            ip_address=user_info["ip_address"],
            timestamp=datetime.datetime.now(),
        )
        audit_entry.save(db)

    def delete(self, db):
        """Delete with audit logging"""
        user_info = AuditContext.get_user()

        # Capture state before deletion
        data_snapshot = {k: getattr(self, k) for k in self._fields.keys()}

        # Perform deletion
        record_id = self.id
        super().delete(db)

        # Log the deletion
        audit_entry = AuditLog(
            user_id=user_info["user_id"],
            user_name=user_info["user_name"],
            model_name=self.__class__.__name__,
            record_id=record_id,
            action="DELETE",
            changes=data_snapshot,
            ip_address=user_info["ip_address"],
            timestamp=datetime.datetime.now(),
        )
        audit_entry.save(db)

    @classmethod
    def get_audit_trail(cls, db, record_id=None):
        """Get audit trail for model or specific record"""
        query = {"model_name": cls.__name__}
        if record_id:
            query["record_id"] = record_id

        return AuditLog.filter(db, **query)


# Context manager for audit operations
class audit_context:
    """Context manager for audited operations"""

    def __init__(self, user_id, user_name, ip_address=None):
        self.user_id = user_id
        self.user_name = user_name
        self.ip_address = ip_address

    def __enter__(self):
        AuditContext.set_user(self.user_id, self.user_name, self.ip_address)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        AuditContext.clear()


# Example usage
"""
class Product(AuditedModel, Model):
    name = TextField()
    price = FloatField()

# Create audit log table
AuditLog.create_table(db)
Product.create_table(db)

# Perform audited operations
with audit_context(user_id=1, user_name="alice", ip_address="192.168.1.100"):
    product = Product(name="Laptop", price=999.99)
    product.save(db)  # Automatically logged
    
    product.price = 899.99
    product.save(db)  # Update logged
    
    product.delete(db)  # Deletion logged

# View audit trail
trail = Product.get_audit_trail(db, record_id=product.id)
for entry in trail:
    print(f"{entry.timestamp}: {entry.user_name} performed {entry.action}")
    print(f"  Changes: {entry.changes}")
"""
