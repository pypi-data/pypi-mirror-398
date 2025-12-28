"""
Lazy Loading - Efficient Relationship Loading

Defers relationship loading until accessed, preventing N+1 queries.
"""


class LazyProxy:
    """Proxy object for lazy-loaded relationships"""

    __slots__ = ("_loader", "_loaded", "_value")

    def __init__(self, loader):
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_loaded", False)
        object.__setattr__(self, "_value", None)

    def _load(self):
        """Load the actual value"""
        if not self._loaded:
            object.__setattr__(self, "_value", self._loader())
            object.__setattr__(self, "_loaded", True)
        return self._value

    def __getattr__(self, name):
        return getattr(self._load(), name)

    def __setattr__(self, name, value):
        setattr(self._load(), name, value)

    def __repr__(self):
        if self._loaded:
            return repr(self._value)
        return f"<LazyProxy: not loaded>"

    def __bool__(self):
        return bool(self._load())


def add_lazy_loading_to_model():
    """Add lazy loading to Model relationships"""
    from .model import Model

    # Store original related method
    original_related = Model.related

    def lazy_related(self, db, field_name):
        """Return lazy proxy for relationship"""

        def loader():
            return original_related(self, db, field_name)

        return LazyProxy(loader)

    # Optionally replace related() with lazy version
    # For now, keep original and add lazy_related() as new method
    Model.lazy_related = lazy_related

    # Add prefetch capability
    @classmethod
    def with_related(cls, db, *field_names, **filters):
        """
        Prefetch related fields to avoid N+1.

        Usage:
            users = User.with_related(db, 'posts', 'comments')
        """
        instances = cls.filter(db, **filters)

        # For each field, batch load
        for field_name in field_names:
            if field_name not in cls._fields:
                continue

            field = cls._fields[field_name]
            if field.__class__.__name__ != "ForeignKey":
                continue

            # Get all foreign IDs
            foreign_ids = set()
            for inst in instances:
                fk_id = getattr(inst, field_name)
                if fk_id:
                    foreign_ids.add(fk_id)

            # Batch load related objects
            # This would need the related model class which we don't have easily
            # For now, this is a placeholder for the architecture

        return instances

    Model.with_related = with_related
