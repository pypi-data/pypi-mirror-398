class ModelDatabaseProxy:
    """Proxy to bind a specific database to all model operations"""

    def __init__(self, model_class, db):
        self.model_class = model_class
        self.db = db

    def query(self):
        return self.model_class.query(self.db)

    def all(self, **kwargs):
        return self.model_class.all(self.db, **kwargs)

    def filter(self, **kwargs):
        return self.model_class.filter(self.db, **kwargs)

    def get(self, id):
        return self.model_class.get(self.db, id)

    def first(self, **kwargs):
        return self.model_class.first(self.db, **kwargs)

    def count(self, **kwargs):
        return self.model_class.count(self.db, **kwargs)

    def create_table(self):
        return self.model_class.create_table(self.db)

    def raw(self, sql, params=None):
        return self.model_class.raw(self.db, sql, params)
