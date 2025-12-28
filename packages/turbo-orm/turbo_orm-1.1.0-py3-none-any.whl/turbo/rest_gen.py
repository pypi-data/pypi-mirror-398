"""
REST API Auto-Generation - FastAPI Integration

Automatically generates RESTful API endpoints from ORM models.
Includes OpenAPI/Swagger documentation.
"""


class RESTGenerator:
    """Generate REST API from models"""

    def __init__(self, app_name="lite_model_api"):
        self.app_name = app_name
        self.models = []
        self.routes = []

    def add_model(self, model_class):
        """Register a model for REST API generation"""
        self.models.append(model_class)

    def generate_fastapi_code(self, db):
        """Generate FastAPI application code"""
        code = f'''"""
Auto-generated REST API using FastAPI
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from lite_model import *

app = FastAPI(title="{self.app_name}")
db = Database("app.db")
db.connect()

# Pydantic schemas
'''

        # Generate schemas
        for model in self.models:
            code += self._generate_schema(model)
            code += "\n\n"

        # Generate endpoints
        for model in self.models:
            code += self._generate_endpoints(model)
            code += "\n"

        return code

    def _generate_schema(self, model_class):
        """Generate Pydantic schema"""
        name = model_class.__name__
        fields = []

        for field_name, field in model_class._fields.items():
            if field.__class__.__name__ == "ManyToManyField":
                continue

            py_type = self._map_field_type(field)
            default = "= None" if getattr(field, "null", True) else ""
            fields.append(f"    {field_name}: {py_type} {default}")

        return f"""class {name}Schema(BaseModel):
{chr(10).join(fields) if fields else "    pass"}

class {name}Create(BaseModel):
{chr(10).join(fields) if fields else "    pass"}"""

    def _map_field_type(self, field):
        """Map ORM field to Python type"""
        field_type = field.__class__.__name__

        mapping = {
            "TextField": "str",
            "IntegerField": "int",
            "FloatField": "float",
            "BooleanField": "bool",
            "DateTimeField": "str",
            "JSONField": "dict",
            "EncryptedField": "str",
        }

        py_type = mapping.get(field_type, "str")

        # Add Optional
        if getattr(field, "null", True):
            py_type = f"Optional[{py_type}]"

        return py_type

    def _generate_endpoints(self, model_class):
        """Generate CRUD endpoints"""
        name = model_class.__name__
        name_lower = name.lower()
        name_plural = name_lower + "s"

        return f'''
# {name} endpoints

@app.get("/{name_plural}", response_model=List[{name}Schema])
def list_{name_plural}():
    """List all {name_plural}"""
    return {name}.all(db)

@app.get("/{name_plural}/{{id}}", response_model={name}Schema)
def get_{name_lower}(id: int):
    """Get {name} by ID"""
    item = {name}.get(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="{name} not found")
    return item

@app.post("/{name_plural}", response_model={name}Schema)
def create_{name_lower}(item: {name}Create):
    """Create a new {name}"""
    instance = {name}(**item.dict())
    instance.save(db)
    return instance

@app.put("/{name_plural}/{{id}}", response_model={name}Schema)
def update_{name_lower}(id: int, item: {name}Create):
    """Update a {name}"""
    instance = {name}.get(db, id)
    if not instance:
        raise HTTPException(status_code=404, detail="{name} not found")
    
    for key, value in item.dict().items():
        setattr(instance, key, value)
    instance.save(db)
    return instance

@app.delete("/{name_plural}/{{id}}")
def delete_{name_lower}(id: int):
    """Delete a {name}"""
    instance = {name}.get(db, id)
    if not instance:
        raise HTTPException(status_code=404, detail="{name} not found")
    instance.delete(db)
    return {{"message": "{name} deleted successfully"}}
'''

    def save_to_file(self, db, filename="api.py"):
        """Save generated API to file"""
        code = self.generate_fastapi_code(db)

        with open(filename, "w") as f:
            f.write(code)

        print(f"✓ REST API generated: {filename}")
        print(f"  Run with: uvicorn api:app --reload")
        print(f"  Docs at: http://localhost:8000/docs")


# Example usage
def create_rest_api(models, db, filename="api.py"):
    """Create REST API from models"""
    generator = RESTGenerator()

    for model in models:
        generator.add_model(model)

    generator.save_to_file(db, filename)
