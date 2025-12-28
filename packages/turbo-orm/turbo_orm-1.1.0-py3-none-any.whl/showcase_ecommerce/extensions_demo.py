#!/usr/bin/env python3
"""
ORM Extensions Demonstration
Showcases all advanced ORM features with realistic examples
"""

import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Fix UTF-8 encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path for importing orm_extensions from turbo
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'turbo'))

from orm_extensions import (
    QueryBuilder, QueryFilter, FilterOperator, SortOrder,
    QueryCache, ValidatedField, Validator, RequiredValidator,
    LengthValidator, RangeValidator, PatternValidator,
    EventManager, EventType, BulkOperation, DataExporter,
    AuditLog, ORMExtensions
)


# Mock Model Classes
class User:
    def __init__(self, id: int, name: str, email: str, age: int, balance: Decimal):
        self.id = id
        self.name = name
        self.email = email
        self.age = age
        self.balance = balance
    
    def __repr__(self):
        return f"User(id={self.id}, name='{self.name}', email='{self.email}', age={self.age}, balance={self.balance})"


class Product:
    def __init__(self, id: int, name: str, price: Decimal, stock: int, rating: float):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
        self.rating = rating
    
    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price}, stock={self.stock}, rating={self.rating})"


def demo_query_builder():
    """Demo 1: Advanced Query Filtering & Sorting"""
    print("\n" + "="*80)
    print("DEMO 1: Advanced Query Filtering & Sorting")
    print("="*80)
    
    # Create sample users
    users = [
        User(1, "Alice Johnson", "alice@example.com", 28, Decimal("5000.00")),
        User(2, "Bob Smith", "bob@example.com", 35, Decimal("8500.00")),
        User(3, "Carol White", "carol@example.com", 28, Decimal("3200.00")),
        User(4, "David Brown", "david@example.com", 42, Decimal("12000.00")),
        User(5, "Eve Davis", "eve@example.com", 30, Decimal("6800.00")),
    ]
    
    print(f"\n1. All Users ({len(users)} total):")
    for user in users:
        print(f"   {user}")
    
    # Query 1: Filter by age
    print(f"\n2. Users aged 28:")
    query = QueryBuilder(users)
    results = query.where("age", FilterOperator.EQ, 28).execute()
    for user in results:
        print(f"   {user}")
    
    # Query 2: Filter and sort
    print(f"\n3. Users with balance > 5000, sorted by name:")
    query = QueryBuilder(users)
    results = query.where("balance", FilterOperator.GT, Decimal("5000")).order_by("name").execute()
    for user in results:
        print(f"   {user}")
    
    # Query 3: Complex query with pagination
    print(f"\n4. Top 2 users by balance:")
    query = QueryBuilder(users)
    results = query.order_by("balance", SortOrder.DESC).take(2).execute()
    for user in results:
        print(f"   {user}")
    
    # Query 4: Multiple filters
    print(f"\n5. Users aged 28-35 with balance >= 3000:")
    query = QueryBuilder(users)
    results = query.where("age", FilterOperator.GTE, 28).where("age", FilterOperator.LTE, 35).where("balance", FilterOperator.GTE, Decimal("3000")).execute()
    for user in results:
        print(f"   {user}")
    
    # Query 5: Like search
    print(f"\n6. Users with email containing 'example':")
    query = QueryBuilder(users)
    results = query.where("email", FilterOperator.LIKE, "example").execute()
    print(f"   Found {len(results)} matching users")
    
    print(f"\n✓ Query Builder Demo Complete")


def demo_caching():
    """Demo 2: Result Caching with TTL"""
    print("\n" + "="*80)
    print("DEMO 2: Result Caching with TTL")
    print("="*80)
    
    products = [
        Product(1, "Laptop", Decimal("999.99"), 5, 4.5),
        Product(2, "Mouse", Decimal("29.99"), 50, 4.2),
        Product(3, "Keyboard", Decimal("79.99"), 30, 4.3),
        Product(4, "Monitor", Decimal("299.99"), 10, 4.4),
        Product(5, "Headphones", Decimal("149.99"), 20, 4.6),
    ]
    
    cache = QueryCache()
    
    print(f"\n1. Initial cache stats:")
    print(f"   {cache.stats()}")
    
    # Query 1: Cache miss
    print(f"\n2. Execute query (CACHE MISS):")
    query = QueryBuilder(products)
    results = query.where("price", FilterOperator.LT, Decimal("100")).execute()
    cache_key = cache.get_key(query.filters, query.sorts)
    cache.set(cache_key, results)
    print(f"   Found {len(results)} products < $100")
    
    # Query 2: Cache hit
    print(f"\n3. Execute same query (CACHE HIT):")
    cached = cache.get(cache_key)
    print(f"   Got {len(cached)} products from cache")
    
    print(f"\n4. Cache stats after queries:")
    stats = cache.stats()
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
    print(f"   Cached Entries: {stats['cached_entries']}")
    
    print(f"\n✓ Caching Demo Complete")


def demo_validation():
    """Demo 3: Field Validation Framework"""
    print("\n" + "="*80)
    print("DEMO 3: Field Validation Framework")
    print("="*80)
    
    # Create validators
    email_validator = PatternValidator(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    name_validator = LengthValidator(min_length=2, max_length=50)
    age_validator = RangeValidator(min_value=18, max_value=120)
    
    test_cases = [
        ("Email", email_validator, "user@example.com", "invalid-email", "user@domain"),
        ("Name", name_validator, "John Smith", "J", "A" * 51),
        ("Age", age_validator, 25, 15, 150),
    ]
    
    print(f"\n1. Validation Tests:")
    for field_name, validator, valid_val, invalid_val1, invalid_val2 in test_cases:
        print(f"\n   {field_name} Validator:")
        
        is_valid, error = validator.validate(valid_val)
        print(f"   ✓ '{valid_val}' -> Valid: {is_valid}")
        
        is_valid, error = validator.validate(invalid_val1)
        print(f"   ✗ '{invalid_val1}' -> Valid: {is_valid}, Error: {error}")
        
        is_valid, error = validator.validate(invalid_val2)
        print(f"   ✗ '{invalid_val2}' -> Valid: {is_valid}, Error: {error}")
    
    print(f"\n✓ Validation Demo Complete")


def demo_events():
    """Demo 4: Event/Hook System"""
    print("\n" + "="*80)
    print("DEMO 4: Event/Hook System")
    print("="*80)
    
    events = EventManager()
    event_log = []
    
    # Register event listeners
    events.on(EventType.BEFORE_CREATE, lambda data: event_log.append(f"[BEFORE_CREATE] Preparing to create: {data}"))
    events.on(EventType.AFTER_CREATE, lambda data: event_log.append(f"[AFTER_CREATE] Created successfully: {data}"))
    events.on(EventType.BEFORE_UPDATE, lambda data: event_log.append(f"[BEFORE_UPDATE] Preparing to update: {data}"))
    events.on(EventType.AFTER_UPDATE, lambda data: event_log.append(f"[AFTER_UPDATE] Updated successfully: {data}"))
    
    print(f"\n1. Simulating user lifecycle:")
    
    # Create event
    print(f"\n   Creating user...")
    events.emit(EventType.BEFORE_CREATE, "User(name='Alice')")
    events.emit(EventType.AFTER_CREATE, "User(name='Alice', id=1)")
    
    # Update event
    print(f"\n   Updating user...")
    events.emit(EventType.BEFORE_UPDATE, "User(id=1, name='Alice')")
    events.emit(EventType.AFTER_UPDATE, "User(id=1, name='Alice Johnson')")
    
    print(f"\n2. Event log:")
    for entry in event_log:
        print(f"   {entry}")
    
    print(f"\n✓ Event System Demo Complete")


def demo_bulk_operations():
    """Demo 5: Bulk Operations"""
    print("\n" + "="*80)
    print("DEMO 5: Bulk Operations")
    print("="*80)
    
    bulk = BulkOperation()
    
    print(f"\n1. Building bulk operation:")
    
    # Add operations
    for i in range(1, 6):
        bulk.insert(User(i, f"User{i}", f"user{i}@example.com", 25 + i, Decimal("5000")))
    
    for i in range(1, 4):
        bulk.update(User(i, f"Updated{i}", f"updated{i}@example.com", 26 + i, Decimal("6000")))
    
    bulk.delete(User(5, "User5", "user5@example.com", 30, Decimal("5000")))
    
    print(f"   Queued {len(bulk.operations)} operations")
    for i, (op_type, obj) in enumerate(bulk.operations, 1):
        print(f"   {i}. {op_type.upper()}: {obj.name}")
    
    # Execute
    print(f"\n2. Executing bulk operation:")
    results = bulk.execute()
    print(f"   Inserted: {results['inserted']}")
    print(f"   Updated: {results['updated']}")
    print(f"   Deleted: {results['deleted']}")
    
    print(f"\n✓ Bulk Operations Demo Complete")


def demo_export_import():
    """Demo 6: Export/Import"""
    print("\n" + "="*80)
    print("DEMO 6: Export/Import")
    print("="*80)
    
    users = [
        User(1, "Alice Johnson", "alice@example.com", 28, Decimal("5000.00")),
        User(2, "Bob Smith", "bob@example.com", 35, Decimal("8500.00")),
        User(3, "Carol White", "carol@example.com", 28, Decimal("3200.00")),
    ]
    
    # Export to JSON
    print(f"\n1. Export to JSON:")
    json_data = DataExporter.to_json(users)
    print(json_data)
    
    # Export to CSV
    print(f"\n2. Export to CSV:")
    csv_data = DataExporter.to_csv(users)
    print(csv_data)
    
    print(f"✓ Export/Import Demo Complete")


def demo_audit_logging():
    """Demo 7: Audit Logging"""
    print("\n" + "="*80)
    print("DEMO 7: Audit Logging")
    print("="*80)
    
    audit = AuditLog()
    
    print(f"\n1. Recording changes:")
    
    # Record create
    audit.record(
        object_id=1,
        object_type="User",
        action="CREATE",
        new_values={"name": "Alice", "email": "alice@example.com"},
        user_id=None
    )
    print(f"   Recorded: User 1 created")
    
    # Record update
    audit.record(
        object_id=1,
        object_type="User",
        action="UPDATE",
        old_values={"email": "alice@example.com"},
        new_values={"email": "alice.johnson@example.com"},
        user_id=2
    )
    print(f"   Recorded: User 1 updated by User 2")
    
    # Record delete
    audit.record(
        object_id=1,
        object_type="User",
        action="DELETE",
        old_values={"name": "Alice", "email": "alice.johnson@example.com"},
        user_id=3
    )
    print(f"   Recorded: User 1 deleted by User 3")
    
    # Get history
    print(f"\n2. Audit history for User 1:")
    history = audit.get_history(1, "User")
    for entry in history:
        print(f"\n   [{entry['timestamp'].strftime('%H:%M:%S')}] {entry['action']}")
        if entry['old_values']:
            print(f"   Old: {entry['old_values']}")
        if entry['new_values']:
            print(f"   New: {entry['new_values']}")
        if entry['user_id']:
            print(f"   By User: {entry['user_id']}")
    
    print(f"\n✓ Audit Logging Demo Complete")


def demo_integrated_workflow():
    """Demo 8: Integrated Workflow"""
    print("\n" + "="*80)
    print("DEMO 8: Integrated ORM Extensions Workflow")
    print("="*80)
    
    # Initialize ORM extensions
    orm = ORMExtensions()
    
    # Create sample data
    products = [
        Product(1, "Laptop", Decimal("999.99"), 5, 4.5),
        Product(2, "Mouse", Decimal("29.99"), 50, 4.2),
        Product(3, "Keyboard", Decimal("79.99"), 30, 4.3),
        Product(4, "Monitor", Decimal("299.99"), 10, 4.4),
        Product(5, "Headphones", Decimal("149.99"), 20, 4.6),
    ]
    
    # Register events
    orm.event_manager.on(EventType.BEFORE_CREATE, lambda d: print(f"   [EVENT] Before create: {d}"))
    orm.event_manager.on(EventType.AFTER_CREATE, lambda d: print(f"   [EVENT] After create: {d}"))
    
    print(f"\n1. Query with caching:")
    query = orm.create_query(products)
    results = query.where("stock", "gte", 20).order_by("price").execute()
    print(f"   Found {len(results)} products with stock >= 20")
    for p in results:
        print(f"   - {p.name}: ${p.price}")
    
    print(f"\n2. Bulk operations:")
    bulk = orm.bulk_operation()
    for i in range(3):
        bulk.insert(Product(100+i, f"New Product {i}", Decimal("199.99"), 10, 4.0))
    results = bulk.execute()
    print(f"   Inserted: {results['inserted']} products")
    
    print(f"\n3. Audit logging:")
    orm.audit_log.record(1, "Product", "UPDATE", {"stock": 5}, {"stock": 3}, user_id=1)
    print(f"   Recorded product update")
    
    print(f"\n4. Export data:")
    sample_data = products[:2]
    json_export = orm.export_json(sample_data)
    print(f"   Exported {len(json_export)} bytes of JSON data")
    
    print(f"\n✓ Integrated Workflow Demo Complete")


def main():
    """Run all demonstrations"""
    print("\n╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + " ORM EXTENSIONS COMPREHENSIVE DEMONSTRATION ".center(78) + "║")
    print("║" + " Query Builder • Caching • Validation • Events • Bulk Ops • Export/Import • Audit Logs ".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    try:
        demo_query_builder()
        demo_caching()
        demo_validation()
        demo_events()
        demo_bulk_operations()
        demo_export_import()
        demo_audit_logging()
        demo_integrated_workflow()
        
        print("\n" + "="*80)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY ✓")
        print("="*80)
        print("\nFeature Coverage:")
        print("  ✓ Query Filtering & Sorting (8 operators, pagination)")
        print("  ✓ Caching Layer (TTL, hit rate tracking)")
        print("  ✓ Validation Framework (6 validators, composable)")
        print("  ✓ Event/Hook System (6 lifecycle events)")
        print("  ✓ Bulk Operations (batch insert/update/delete)")
        print("  ✓ Export/Import (JSON, CSV formats)")
        print("  ✓ Audit Logging (change tracking, history)")
        print("  ✓ Integrated Workflow (all features working together)")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
