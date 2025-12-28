import re
from typing import Set, FrozenSet

# Valid characters for identifiers (alphanumeric and underscore only)
VALID_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

# Reserved SQL keywords that could cause issues if used as identifiers
SQL_RESERVED_WORDS: FrozenSet[str] = frozenset([
    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'AND', 'OR', 'NOT',
    'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'ON', 'JOIN',
    'INNER', 'LEFT', 'RIGHT', 'OUTER', 'FULL', 'CREATE', 'DROP', 'ALTER',
    'TABLE', 'INDEX', 'VIEW', 'TRIGGER', 'PROCEDURE', 'FUNCTION', 'DATABASE',
    'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT', 'UNIQUE', 'CHECK',
    'DEFAULT', 'NULL', 'IS', 'LIKE', 'IN', 'BETWEEN', 'EXISTS', 'CAST',
    'CONVERT', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT',
    'UNION', 'INTERSECT', 'EXCEPT', 'ALL', 'TOP', 'INTO', 'VALUES', 'SET',
    'ADD', 'REMOVE', 'MODIFY', 'COLUMN', 'TO', 'WITH', 'CASE', 'WHEN', 'THEN',
    'ELSE', 'END', 'IF', 'BEGIN', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'SAVEPOINT'
])

def validate_identifier(identifier: str) -> bool:
    """
    Validate that an identifier (table name, column name) is safe to use in SQL.
    
    Args:
        identifier: The identifier to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check if identifier matches valid pattern
    if not VALID_IDENTIFIER_PATTERN.match(identifier):
        return False
    
    # Check if identifier is a reserved word (case insensitive)
    if identifier.upper() in SQL_RESERVED_WORDS:
        return False
    
    # Check length (most databases have limits, typically 64+ characters)
    if len(identifier) > 64:
        return False
    
    return True

def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize an identifier by validating it and raising an exception if invalid.
    
    Args:
        identifier: The identifier to sanitize
        
    Returns:
        The identifier if valid
        
    Raises:
        ValueError: If the identifier is invalid
    """
    if not validate_identifier(identifier):
        raise ValueError(f"Invalid identifier: {identifier}")
    return identifier

def sanitize_order_by_field(field: str) -> str:
    """
    Sanitize an order by field specification (may include - for DESC).
    
    Args:
        field: The field specification (e.g., "name" or "-created_at")
        
    Returns:
        The sanitized field specification
        
    Raises:
        ValueError: If the field specification is invalid
    """
    # Strip leading/trailing whitespace
    field = field.strip()
    
    # Check for DESC prefix
    is_desc = field.startswith('-')
    if is_desc:
        field = field[1:]
    
    # Validate the field name
    sanitize_identifier(field)
    
    # Reconstruct with DESC prefix if needed
    return f"-{field}" if is_desc else field

def quote_identifier(identifier: str) -> str:
    """
    Quote an identifier with double quotes for SQLite.
    
    Args:
        identifier: The identifier to quote
        
    Returns:
        The quoted identifier
    """
    return f'"{identifier}"'