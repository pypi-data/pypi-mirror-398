"""
Vector Search - Semantic Search Capabilities

Native support for vector embeddings and similarity search.
"""

import json
import math
from .fields import Field


class VectorField(Field):
    """Field to store vector embeddings (list of floats)"""

    def __init__(self, dimensions=None, **kwargs):
        super().__init__(**kwargs)
        self.dimensions = dimensions

    def get_sql_type(self):
        return "TEXT"  # Store as JSON string

    def to_python(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return []
        return value

    def to_sql(self, value):
        if value is None:
            return None
        # Ensure we return a string for SQLite
        if isinstance(value, (list, tuple)):
            return json.dumps(value)
        return value


class VectorIndex:
    """In-memory vector index for similarity search"""

    def __init__(self):
        self.vectors = {}  # id -> vector

    def add(self, id, vector):
        self.vectors[id] = vector

    def remove(self, id):
        if id in self.vectors:
            del self.vectors[id]

    def search(self, query_vector, limit=10):
        """Find nearest neighbors using Cosine Similarity"""
        scores = []

        q_norm = self._magnitude(query_vector)
        if q_norm == 0:
            return []

        for id, vector in self.vectors.items():
            if not vector:
                continue

            dot_product = sum(a * b for a, b in zip(query_vector, vector))
            v_norm = self._magnitude(vector)

            if v_norm > 0:
                similarity = dot_product / (q_norm * v_norm)
                scores.append((id, similarity))

        # Sort by similarity desc
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:limit]

    def _magnitude(self, vector):
        return math.sqrt(sum(x * x for x in vector))


def add_vector_search_to_model():
    """Add vector search capabilities to Model"""
    from .model import Model

    # Add class-level index
    Model._vector_index = VectorIndex()

    # Patch save to update index
    original_save = Model.save

    def save_with_vector(self, db):
        original_save(self, db)

        # Check for VectorFields
        for name, field in self._fields.items():
            if isinstance(field, VectorField):
                vector = getattr(self, name)
                if vector:
                    # We use a shared index for simplicity in this demo
                    # In production, use separate indexes per model/field
                    self.__class__._vector_index.add(
                        f"{self.__class__.__name__}:{self.id}", vector
                    )

    Model.save = save_with_vector

    @classmethod
    def search(cls, db, vector, limit=5):
        """Semantic search using vector similarity"""
        # Search index
        results = cls._vector_index.search(vector, limit=limit)

        # Fetch records
        instances = []
        for id_str, score in results:
            # Parse ID (format: ModelName:ID)
            if id_str.startswith(f"{cls.__name__}:"):
                id = int(id_str.split(":")[1])
                instance = cls.get(db, id)
                if instance:
                    instance._similarity_score = score
                    instances.append(instance)

        return instances

    Model.search = search
