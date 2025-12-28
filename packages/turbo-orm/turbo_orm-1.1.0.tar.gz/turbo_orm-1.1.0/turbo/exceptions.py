"""
Enhanced exception handling for Turbo ORM

Provides detailed error messages with context and suggestions for debugging.
"""

class ModelError(Exception):
    """Base exception for all model operations"""
    pass


class ModelSaveError(ModelError):
    """Detailed error for save operations with context and suggestions"""
    
    def __init__(self, model, operation: str, cause: Exception, context: dict):
        self.model = model
        self.operation = operation
        self.cause = cause
        self.context = context
        
        # Generate suggestions based on error type
        cause_str = str(cause).lower()
        suggestions = []
        
        if "unique" in cause_str or "duplicate" in cause_str:
            suggestions.append("  • Check for duplicate values in unique fields")
            suggestions.append("  • Query existing: Model.filter(db, field=value)")
            suggestions.append("  • Use update() for existing records")
        elif "not null" in cause_str or "null" in cause_str:
            suggestions.append("  • All required fields must have values")
            suggestions.append("  • Check field.required = True")
            suggestions.append("  • Provide default values")
        elif "foreign key" in cause_str:
            suggestions.append("  • Verify referenced record exists")
            suggestions.append("  • Create parent record first")
        elif "no such table" in cause_str:
            suggestions.append("  • Run Model.create_table(db) first")
            suggestions.append("  • Check db.path and table name")
        elif "database is locked" in cause_str:
            suggestions.append("  • Use connection pooling")
            suggestions.append("  • Check for unclosed connections")
        else:
            suggestions.append("  • Check schema matches model")
            suggestions.append("  • Verify field types and constraints")
            suggestions.append("  • Enable query logging")
        
        suggestions.append("  • Use DatabaseHealth(db).full_report() for diagnostics")
        
        message = f"""
{'='*70}
❌ TURBO ORM SAVE ERROR
{'='*70}
Model: {model.__class__.__name__}
Operation: {operation}
Table: {context.get('table', 'unknown')}
{'='*70}
DATA:
  Fields: {context.get('fields', [])}
  Values: {context.get('values', [])}
  SQL: {context.get('sql', 'N/A')}
{'='*70}
ROOT CAUSE:
  {cause}
{'='*70}
SUGGESTIONS:
{chr(10).join(suggestions)}
{'='*70}
"""
        super().__init__(message)


class QueryError(ModelError):
    """Error for query execution failures"""
    
    def __init__(self, sql: str, params: tuple, cause: Exception):
        self.sql = sql
        self.params = params
        self.cause = cause
        super().__init__(
            f"Query failed: {sql}\nParams: {params}\nError: {cause}"
        )


class DatabaseHealthError(ModelError):
    """Error for database health check failures"""
    
    def __init__(self, check_type: str, details: dict):
        self.check_type = check_type
        self.details = details
        super().__init__(
            f"Health check failed ({check_type}): {details}"
        )