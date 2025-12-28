from .model import Model, ModelMeta
from .fields import DateTimeField
import datetime


# Define SoftDeleteModel with deleted_at field
class SoftDeleteMeta(ModelMeta):
    def __new__(cls, name, bases, attrs):
        # Add deleted_at field if this is a SoftDeleteModel subclass
        if name != "SoftDeleteModel" and any(
            isinstance(b, SoftDeleteMeta) or b.__name__ == "SoftDeleteModel"
            for b in bases
        ):
            attrs["deleted_at"] = DateTimeField()
        elif name == "SoftDeleteModel":
            attrs["deleted_at"] = DateTimeField()
        return super().__new__(cls, name, bases, attrs)


class SoftDeleteModel(Model, metaclass=SoftDeleteMeta):
    """Model with soft delete support"""

    def delete(self, db):
        """Soft delete - mark as deleted instead of removing"""
        self.deleted_at = datetime.datetime.now()
        self.save(db)

    def hard_delete(self, db):
        """Permanently delete from database"""
        super().delete(db)

    def restore(self, db):
        """Restore a soft-deleted record"""
        self.deleted_at = None
        self.save(db)

    @classmethod
    def all(cls, db, order_by=None, limit=None):
        """Override to exclude soft-deleted records"""
        results = super().all(db, order_by=order_by, limit=limit)
        # Filter out records where deleted_at is not None and not empty
        return [r for r in results if not r.deleted_at]

    @classmethod
    def filter(cls, db, order_by=None, limit=None, offset=None, **kwargs):
        """Override to exclude soft-deleted records"""
        results = super().filter(
            db, order_by=order_by, limit=limit, offset=offset, **kwargs
        )
        return [r for r in results if not r.deleted_at]

    @classmethod
    def with_trashed(cls, db, order_by=None, limit=None):
        """Get all records including soft-deleted"""
        return super().all(db, order_by=order_by, limit=limit)

    @classmethod
    def only_trashed(cls, db, order_by=None, limit=None):
        """Get only soft-deleted records"""
        results = super().all(db, order_by=order_by, limit=limit)
        return [r for r in results if r.deleted_at]
