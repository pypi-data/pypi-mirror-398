class Paginator:
    """Pagination helper"""

    def __init__(self, model_class, db, page=1, per_page=20, **filters):
        self.model_class = model_class
        self.db = db
        self.page = max(1, page)
        self.per_page = per_page
        self.filters = filters

        # Calculate total
        self.total = model_class.count(db, **filters)

        # Calculate offset
        offset = (self.page - 1) * per_page

        # Get items
        self.items = model_class.filter(db, limit=per_page, offset=offset, **filters)

    @property
    def pages(self):
        """Total number of pages"""
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_prev(self):
        """Whether there's a previous page"""
        return self.page > 1

    @property
    def has_next(self):
        """Whether there's a next page"""
        return self.page < self.pages

    @property
    def prev_page(self):
        """Previous page number"""
        return self.page - 1 if self.has_prev else None

    @property
    def next_page(self):
        """Next page number"""
        return self.page + 1 if self.has_next else None
