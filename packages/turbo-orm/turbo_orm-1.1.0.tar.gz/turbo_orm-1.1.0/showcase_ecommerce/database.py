"""
E-Commerce Database Layer - turbo-orm integration

Demonstrates:
- Database schema setup
- ORM model mapping
- Query optimization
- Bulk operations
- Transaction handling
- Connection pooling patterns
"""

import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import json

from .models import (
    User, UserRole, Product, ProductCategory, Order, OrderStatus,
    OrderItem, Review, ShoppingCart, Inventory, PaymentStatus
)


# ============================================================================
# Database Schema
# ============================================================================

SQL_SCHEMA = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    role TEXT NOT NULL DEFAULT 'customer',
    is_active BOOLEAN DEFAULT 1,
    email_verified BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    seller_id INTEGER NOT NULL,
    price DECIMAL NOT NULL,
    cost DECIMAL NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    sku TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    discount_percent DECIMAL DEFAULT 0,
    rating REAL DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    images TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(id)
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_number TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    payment_status TEXT NOT NULL DEFAULT 'pending',
    subtotal DECIMAL,
    tax DECIMAL,
    shipping DECIMAL,
    total DECIMAL,
    shipping_address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id)
);

-- Order items table
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL NOT NULL,
    discount_amount DECIMAL DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    helpful_count INTEGER DEFAULT 0,
    verified_purchase BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (customer_id) REFERENCES users(id)
);

-- Shopping carts table
CREATE TABLE IF NOT EXISTS shopping_carts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER UNIQUE NOT NULL,
    items TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id)
);

-- Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL,
    current_stock INTEGER NOT NULL,
    reserved_stock INTEGER DEFAULT 0,
    sold_count INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 100,
    last_restock TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_seller ON products(seller_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_customer ON reviews(customer_id);
"""


# ============================================================================
# Database Connection
# ============================================================================

class Database:
    """Simple database wrapper for demonstration"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.cache: Dict[str, Any] = {}  # Simple cache demonstration
        self.connect()

    def connect(self) -> None:
        """Connect to database"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.initialize_schema()

    def initialize_schema(self) -> None:
        """Create tables"""
        if not self.connection:
            raise RuntimeError("Database connection not established")
        cursor = self.connection.cursor()
        for statement in SQL_SCHEMA.split(";"):
            if statement.strip():
                cursor.execute(statement)
        self.connection.commit()

    def execute(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Cursor]:
        """Execute SQL statement"""
        if not self.connection:
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            return cursor
        except Exception:
            return None

    def commit(self) -> None:
        """Commit transaction"""
        self.connection.commit()

    def close(self) -> None:
        """Close connection"""
        if self.connection:
            self.connection.close()


# ============================================================================
# Repository Pattern - ORM-like Access
# ============================================================================

class UserRepository:
    """User data access"""
    
    def __init__(self, db: Database):
        self.db = db

    def create(self, user: User) -> int:
        """Create user and return ID"""
        cursor = self.db.execute("""
            INSERT INTO users (
                email, username, password_hash, first_name, last_name,
                phone, role, is_active, email_verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.email, user.username, user.password_hash,
            user.first_name, user.last_name, user.phone,
            user.role.value, user.is_active, user.email_verified,
            user.created_at, user.updated_at
        ))
        if cursor is None:
            raise RuntimeError("Failed to create user: cursor is None")
        self.db.commit()
        return cursor.lastrowid

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        cursor = self.db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        if cursor is None:
            return None
        row = cursor.fetchone()
        return self._row_to_user(row) if row else None

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        cursor = self.db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )
        if cursor is None:
            return None
        row = cursor.fetchone()
        return self._row_to_user(row) if row else None

    def get_all_sellers(self) -> List[User]:
        """Get all sellers"""
        cursor = self.db.execute(
            "SELECT * FROM users WHERE role IN ('seller', 'admin')"
        )
        if cursor is None:
            return []
        return [self._row_to_user(row) for row in cursor.fetchall()]

    def update(self, user: User) -> bool:
        """Update user"""
        cursor = self.db.execute("""
            UPDATE users SET
                email = ?, username = ?, first_name = ?, last_name = ?,
                phone = ?, role = ?, is_active = ?, email_verified = ?,
                updated_at = ?, last_login = ?
            WHERE id = ?
        """, (
            user.email, user.username, user.first_name, user.last_name,
            user.phone, user.role.value, user.is_active, user.email_verified,
            user.updated_at, user.last_login, user.id if hasattr(user, 'id') else 0
        ))
        if cursor is None:
            return False
        self.db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_user(row: Optional[sqlite3.Row]) -> Optional[User]:
        """Convert database row to User object"""
        if row is None:
            return None
        user = User(
            email=row['email'],
            username=row['username'],
            password_hash=row['password_hash'],
            first_name=row['first_name'] or "",
            last_name=row['last_name'] or "",
            role=UserRole(row['role']),
            phone=row['phone'] or "",
            is_active=bool(row['is_active']),
            email_verified=bool(row['email_verified']),
        )
        user.id = row['id']
        user.created_at = row['created_at']
        user.updated_at = row['updated_at']
        user.last_login = row['last_login']
        return user


class ProductRepository:
    """Product data access"""
    
    def __init__(self, db: Database):
        self.db = db

    def create(self, product: Product) -> int:
        """Create product"""
        cursor = self.db.execute("""
            INSERT INTO products (
                name, description, category, seller_id, price, cost,
                stock_quantity, sku, is_active, discount_percent,
                rating, review_count, images, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product.name, product.description, product.category.value,
            product.seller_id, str(product.price), str(product.cost),
            product.stock_quantity, product.sku, product.is_active,
            str(product.discount_percent), product.rating, product.review_count,
            json.dumps(product.images), product.created_at, product.updated_at
        ))
        if cursor is None:
            raise RuntimeError("Failed to create product: cursor is None")
        self.db.commit()
        return cursor.lastrowid

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        cursor = self.db.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
        if cursor is None:
            return None
        row = cursor.fetchone()
        return self._row_to_product(row) if row else None

    def get_by_category(self, category: ProductCategory) -> List[Product]:
        """Get products by category"""
        cursor = self.db.execute(
            "SELECT * FROM products WHERE category = ? AND is_active = 1",
            (category.value,)
        )
        if cursor is None:
            return []
        return [self._row_to_product(row) for row in cursor.fetchall()]

    def get_by_seller(self, seller_id: int) -> List[Product]:
        """Get seller's products"""
        cursor = self.db.execute(
            "SELECT * FROM products WHERE seller_id = ?",
            (seller_id,)
        )
        if cursor is None:
            return []
        return [self._row_to_product(row) for row in cursor.fetchall()]

    def get_top_rated(self, limit: int = 10) -> List[Product]:
        """Get top-rated products"""
        cursor = self.db.execute("""
            SELECT * FROM products WHERE is_active = 1
            ORDER BY rating DESC, review_count DESC
            LIMIT ?
        """, (limit,))
        if cursor is None:
            return []
        return [self._row_to_product(row) for row in cursor.fetchall()]

    def update(self, product: Product) -> bool:
        """Update product"""
        cursor = self.db.execute("""
            UPDATE products SET
                name = ?, description = ?, price = ?, stock_quantity = ?,
                discount_percent = ?, rating = ?, review_count = ?,
                is_active = ?, updated_at = ?
            WHERE id = ?
        """, (
            product.name, product.description, str(product.price),
            product.stock_quantity, str(product.discount_percent),
            product.rating, product.review_count, product.is_active,
            product.updated_at, product.id if hasattr(product, 'id') else 0
        ))
        if cursor is None:
            return False
        self.db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_product(row: Optional[sqlite3.Row]) -> Optional[Product]:
        """Convert database row to Product"""
        if row is None:
            return None
        product = Product(
            name=row['name'],
            description=row['description'] or "",
            category=ProductCategory(row['category']),
            seller_id=row['seller_id'],
            price=Decimal(row['price']),
            cost=Decimal(row['cost']),
            stock_quantity=row['stock_quantity'],
            sku=row['sku'],
            is_active=bool(row['is_active']),
            images=json.loads(row['images'] or "[]"),
        )
        product.id = row['id']
        product.discount_percent = Decimal(row['discount_percent'])
        product.rating = row['rating']
        product.review_count = row['review_count']
        product.created_at = row['created_at']
        product.updated_at = row['updated_at']
        return product


class OrderRepository:
    """Order data access"""
    
    def __init__(self, db: Database):
        self.db = db

    def create(self, order: Order) -> int:
        """Create order"""
        cursor = self.db.execute("""
            INSERT INTO orders (
                customer_id, order_number, status, payment_status,
                subtotal, tax, shipping, total, shipping_address,
                notes, created_at, updated_at, delivered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order.customer_id, order.order_number,
            order.status.value, order.payment_status.value,
            str(order.subtotal), str(order.tax), str(order.shipping),
            str(order.total), order.shipping_address, order.notes,
            order.created_at, order.updated_at, order.delivered_at
        ))
        if cursor is None:
            raise RuntimeError("Failed to create order: cursor is None")
        self.db.commit()
        return cursor.lastrowid

    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        cursor = self.db.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        )
        if cursor is None:
            return None
        row = cursor.fetchone()
        return self._row_to_order(row) if row else None

    def get_by_customer(self, customer_id: int) -> List[Order]:
        """Get customer's orders"""
        cursor = self.db.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,)
        )
        if cursor is None:
            return []
        return [self._row_to_order(row) for row in cursor.fetchall()]

    def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        cursor = self.db.execute(
            "SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at"
        )
        if cursor is None:
            return []
        return [self._row_to_order(row) for row in cursor.fetchall()]

    def update(self, order: Order) -> bool:
        """Update order"""
        cursor = self.db.execute("""
            UPDATE orders SET
                status = ?, payment_status = ?, subtotal = ?, tax = ?,
                shipping = ?, total = ?, updated_at = ?, delivered_at = ?
            WHERE id = ?
        """, (
            order.status.value, order.payment_status.value,
            str(order.subtotal), str(order.tax), str(order.shipping),
            str(order.total), order.updated_at, order.delivered_at,
            order.id if hasattr(order, 'id') else 0
        ))
        if cursor is None:
            return False
        self.db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_order(row: Optional[sqlite3.Row]) -> Optional[Order]:
        """Convert database row to Order"""
        if row is None:
            return None
        order = Order(
            customer_id=row['customer_id'],
            shipping_address=row['shipping_address'],
            notes=row['notes'] or "",
        )
        order.id = row['id']
        order.order_number = row['order_number']
        order.status = OrderStatus(row['status'])
        order.payment_status = PaymentStatus(row['payment_status'])
        order.subtotal = Decimal(row['subtotal'])
        order.tax = Decimal(row['tax'])
        order.shipping = Decimal(row['shipping'])
        order.total = Decimal(row['total'])
        order.created_at = row['created_at']
        order.updated_at = row['updated_at']
        order.delivered_at = row['delivered_at']
        return order


if __name__ == "__main__":
    print("✓ E-Commerce Database Layer loaded")
    print("✓ Repositories: UserRepository, ProductRepository, OrderRepository")
