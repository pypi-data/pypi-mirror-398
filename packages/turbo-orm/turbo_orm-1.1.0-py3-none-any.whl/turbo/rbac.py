"""
RBAC - Role-Based Access Control

Comprehensive permission system for model and field-level access control.
"""

from enum import Enum


class Permission(Enum):
    """Permission types"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class RBACModel:
    """Mixin for RBAC-enabled models"""

    # Class-level permissions
    _permissions = {}

    @classmethod
    def set_permissions(cls, role, permissions):
        """Set permissions for a role"""
        cls._permissions[role] = permissions

    @classmethod
    def check_permission(cls, role, permission):
        """Check if role has permission"""
        role_perms = cls._permissions.get(role, [])
        return permission in role_perms

    def can_create(self, user_role):
        """Check create permission"""
        return self.check_permission(user_role, Permission.CREATE)

    def can_read(self, user_role):
        """Check read permission"""
        return self.check_permission(user_role, Permission.READ)

    def can_update(self, user_role):
        """Check update permission"""
        return self.check_permission(user_role, Permission.UPDATE)

    def can_delete(self, user_role):
        """Check delete permission"""
        return self.check_permission(user_role, Permission.DELETE)

    def save(self, db, user_role=None):
        """Save with permission check"""
        if user_role:
            perm = Permission.CREATE if self.id is None else Permission.UPDATE
            if not self.check_permission(user_role, perm):
                raise PermissionError(
                    f"Role '{user_role}' does not have {perm.value} permission"
                )

        super().save(db)

    def delete(self, db, user_role=None):
        """Delete with permission check"""
        if user_role and not self.check_permission(user_role, Permission.DELETE):
            raise PermissionError(f"Role '{user_role}' does not have delete permission")

        super().delete(db)


class FieldPermission:
    """Field-level permissions"""

    def __init__(self):
        self.field_permissions = {}

    def set_field_permission(self, model_class, field_name, roles):
        """Set which roles can access a field"""
        key = f"{model_class.__name__}.{field_name}"
        self.field_permissions[key] = roles

    def can_access_field(self, model_class, field_name, user_role):
        """Check if role can access field"""
        key = f"{model_class.__name__}.{field_name}"
        allowed_roles = self.field_permissions.get(key, None)

        if allowed_roles is None:
            return True  # No restrictions

        return user_role in allowed_roles

    def filter_fields(self, model_class, instance, user_role):
        """Filter out fields user cannot access"""
        accessible_data = {}

        for field_name in model_class._fields.keys():
            if self.can_access_field(model_class, field_name, user_role):
                accessible_data[field_name] = getattr(instance, field_name, None)

        return accessible_data


# Global permission manager
_permission_manager = FieldPermission()


def set_field_permission(model_class, field_name, roles):
    """Set field-level permissions"""
    _permission_manager.set_field_permission(model_class, field_name, roles)


def get_accessible_fields(model_class, instance, user_role):
    """Get fields accessible to role"""
    return _permission_manager.filter_fields(model_class, instance, user_role)


# Example usage
"""
class User(RBACModel, Model):
    name = TextField()
    email = TextField()
    salary = FloatField()  # Sensitive field

# Set model-level permissions
User.set_permissions('admin', [Permission.CREATE, Permission.READ, Permission.UPDATE, Permission.DELETE])
User.set_permissions('user', [Permission.READ])
User.set_permissions('guest', [])

# Set field-level permissions
set_field_permission(User, 'salary', ['admin'])  # Only admins can see salary

# Use with permissions
user = User(name="Alice", email="alice@example.com", salary=100000)

try:
    user.save(db, user_role='admin')  # ✓ Allowed
    user.save(db, user_role='guest')  # ✗ PermissionError
except PermissionError as e:
    print(e)

# Field filtering
accessible = get_accessible_fields(User, user, user_role='user')
# Returns: {'name': 'Alice', 'email': 'alice@example.com'}
# Excludes: 'salary' (not accessible to 'user' role)
"""
