"""
GraphQL Auto-Generation - Schema from Models

Automatically generates GraphQL schema, queries, and mutations from ORM models.
Integrates with popular GraphQL libraries.
"""


class GraphQLGenerator:
    """Generate GraphQL schema from models"""

    def __init__(self):
        self.models = []
        self.schema_parts = []

    def add_model(self, model_class):
        """Register a model for GraphQL generation"""
        self.models.append(model_class)

    def generate_schema(self):
        """Generate complete GraphQL schema"""
        types = []
        queries = []
        mutations = []

        for model in self.models:
            # Generate type
            types.append(self._generate_type(model))

            # Generate queries
            queries.extend(self._generate_queries(model))

            # Generate mutations
            mutations.extend(self._generate_mutations(model))

        schema = f"""
type Query {{
{chr(10).join(queries)}
}}

type Mutation {{
{chr(10).join(mutations)}
}}

{chr(10).join(types)}
"""

        return schema.strip()

    def _generate_type(self, model_class):
        """Generate GraphQL type for model"""
        fields = ["  id: ID!"]

        for field_name, field in model_class._fields.items():
            if field.__class__.__name__ == "ManyToManyField":
                continue  # Handle separately

            gql_type = self._map_field_type(field)
            fields.append(f"  {field_name}: {gql_type}")

        type_def = f"""type {model_class.__name__} {{
{chr(10).join(fields)}
}}"""

        return type_def

    def _map_field_type(self, field):
        """Map ORM field to GraphQL type"""
        field_type = field.__class__.__name__

        mapping = {
            "TextField": "String",
            "IntegerField": "Int",
            "FloatField": "Float",
            "BooleanField": "Boolean",
            "DateTimeField": "String",  # ISO format
            "JSONField": "String",  # JSON string
            "EncryptedField": "String",
        }

        gql_type = mapping.get(field_type, "String")

        # Add nullability
        if not getattr(field, "null", True):
            gql_type += "!"

        return gql_type

    def _generate_queries(self, model_class):
        """Generate query resolvers"""
        name = model_class.__name__
        name_lower = name.lower()

        return [
            f"  {name_lower}(id: ID!): {name}",
            f"  {name_lower}s: [{name}!]!",
        ]

    def _generate_mutations(self, model_class):
        """Generate mutation resolvers"""
        name = model_class.__name__
        name_lower = name.lower()

        return [
            f"  create{name}(input: {name}Input!): {name}!",
            f"  update{name}(id: ID!, input: {name}Input!): {name}!",
            f"  delete{name}(id: ID!): Boolean!",
        ]

    def generate_resolvers(self, db):
        """Generate Python resolver functions"""
        resolvers = {}

        for model in self.models:
            name = model.__name__
            name_lower = name.lower()

            # Query resolvers
            resolvers[name_lower] = lambda parent, info, id, model=model: model.get(
                db, id
            )
            resolvers[f"{name_lower}s"] = lambda parent, info, model=model: model.all(
                db
            )

            # Mutation resolvers
            resolvers[f"create{name}"] = (
                lambda parent, info, input, model=model: self._create(db, model, input)
            )
            resolvers[f"update{name}"] = (
                lambda parent, info, id, input, model=model: self._update(
                    db, model, id, input
                )
            )
            resolvers[f"delete{name}"] = (
                lambda parent, info, id, model=model: self._delete(db, model, id)
            )

        return resolvers

    def _create(self, db, model, input_data):
        """Create resolver"""
        instance = model(**input_data)
        instance.save(db)
        return instance

    def _update(self, db, model, id, input_data):
        """Update resolver"""
        instance = model.get(db, id)
        for key, value in input_data.items():
            setattr(instance, key, value)
        instance.save(db)
        return instance

    def _delete(self, db, model, id):
        """Delete resolver"""
        instance = model.get(db, id)
        instance.delete(db)
        return True


# Example usage
def create_graphql_api(models, db):
    """Create GraphQL API from models"""
    generator = GraphQLGenerator()

    for model in models:
        generator.add_model(model)

    schema = generator.generate_schema()
    resolvers = generator.generate_resolvers(db)

    return schema, resolvers
