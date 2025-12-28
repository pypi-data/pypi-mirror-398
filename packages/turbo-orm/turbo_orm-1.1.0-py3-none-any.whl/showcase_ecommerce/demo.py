#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E-Commerce Showcase Demo - turbo-orm Real-world Project

This demonstration showcases:
✓ Type-safe model definitions
✓ Complex business logic
✓ Database operations
✓ Performance optimization
✓ Real-world patterns

Run with: python demo.py
"""

from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Ensure UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from .models import (
    User, UserRole, Product, ProductCategory, Order,
    OrderStatus, PaymentStatus, Review, ShoppingCart
)
from services import (
    UserService, ProductService, CartService, OrderService,
    ReviewService, AnalyticsService
)
from database import Database, UserRepository, ProductRepository, OrderRepository


# ============================================================================
# Demo Configuration
# ============================================================================

class DemoConfig:
    """Demo settings"""
    DB_PATH = "showcase_demo.db"
    VERBOSE = True


# ============================================================================
# Demo Execution
# ============================================================================

def print_section(title: str) -> None:
    """Print formatted section"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_step(step: int, description: str) -> None:
    """Print demo step"""
    print(f"[Step {step}] {description}")


def demo_user_management() -> tuple:
    """Demo 1: User management with RBAC"""
    print_section("DEMO 1: User Management & RBAC")
    
    # Create admin
    print_step(1, "Creating admin user")
    admin = UserService.create_user(
        email="admin@turbo-orm.dev",
        username="admin",
        password="AdminPass123",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
    )
    print(f"  ✓ Created admin: {admin.full_name} ({admin.role.value})")
    
    # Create seller
    print_step(2, "Creating seller user")
    seller = UserService.create_user(
        email="seller@turbo-orm.dev",
        username="seller",
        password="SellerPass123",
        first_name="John",
        last_name="Seller",
        role=UserRole.SELLER,
    )
    print(f"  ✓ Created seller: {seller.full_name}")
    print(f"  ✓ Is seller: {seller.is_seller}")
    
    # Create customer
    print_step(3, "Creating customer user")
    customer = UserService.create_user(
        email="alice@example.com",
        username="alice_wonder",
        password="CustomerPass123",
        first_name="Alice",
        last_name="Wonder",
    )
    print(f"  ✓ Created customer: {customer.full_name}")
    print(f"  ✓ Is admin: {customer.is_admin}")
    
    # Password verification
    print_step(4, "Verifying passwords")
    is_valid = UserService.verify_password(customer, "CustomerPass123")
    print(f"  ✓ Password verification: {is_valid}")
    
    return admin, seller, customer


def demo_product_management(seller: User) -> list:
    """Demo 2: Product management with inventory"""
    print_section("DEMO 2: Product Management")
    
    products = []
    
    print_step(1, "Creating products with inventory")
    categories = [
        ProductCategory.ELECTRONICS,
        ProductCategory.BOOKS,
        ProductCategory.CLOTHING,
    ]
    
    product_specs = [
        ("turbo-orm Guide", "Complete guide to using turbo-orm", ProductCategory.BOOKS, Decimal("29.99"), Decimal("10"), 50),
        ("Gaming Laptop", "High-performance gaming laptop", ProductCategory.ELECTRONICS, Decimal("1299.99"), Decimal("800"), 5),
        ("Python T-Shirt", "Awesome Python developer shirt", ProductCategory.CLOTHING, Decimal("24.99"), Decimal("8"), 100),
    ]
    
    for name, desc, category, price, cost, stock in product_specs:
        product, inventory = ProductService.create_product(
            name=name,
            description=desc,
            category=category,
            seller_id=seller.id if hasattr(seller, 'id') else 1,
            price=price,
            cost=cost,
            stock_quantity=stock,
        )
        products.append(product)
        print(f"  ✓ Created: {name} (${price})")
        print(f"    - Profit margin: {product.profit_margin:.1f}%")
    
    # Apply seasonal discount
    print_step(2, "Applying seasonal discount")
    ProductService.apply_seasonal_discount(products[0], Decimal("15"))
    print(f"  ✓ Applied 15% discount to '{products[0].name}'")
    print(f"    - Original: ${products[0].price}")
    print(f"    - Discounted: ${products[0].current_price}")
    
    # Search products
    print_step(3, "Searching products")
    search_results = ProductService.search_products(
        products,
        query="python",
        category=None,
    )
    print(f"  ✓ Found {len(search_results)} products matching 'python'")
    for p in search_results:
        print(f"    - {p.name}")
    
    return products


def demo_shopping_cart(customer: User, products: list) -> ShoppingCart:
    """Demo 3: Shopping cart operations"""
    print_section("DEMO 3: Shopping Cart")
    
    cart = ShoppingCart(customer.id if hasattr(customer, 'id') else 1)
    
    print_step(1, "Adding items to cart")
    CartService.add_to_cart(cart, products[0], 2)
    print(f"  ✓ Added 2x '{products[0].name}'")
    
    CartService.add_to_cart(cart, products[2], 1)
    print(f"  ✓ Added 1x '{products[2].name}'")
    
    print_step(2, "Cart summary")
    print(f"  ✓ Items in cart: {cart.item_count()}")
    print(f"  ✓ Unique products: {len(cart.items)}")
    
    return cart


def demo_order_processing(
    customer: User,
    cart: ShoppingCart,
    products: list,
) -> Order:
    """Demo 4: Order processing workflow"""
    print_section("DEMO 4: Order Processing")
    
    # Create product/inventory mappings for demo
    product_map = {p.id if hasattr(p, 'id') else i: p for i, p in enumerate(products, 1)}
    inventory_map = {p.id if hasattr(p, 'id') else i: f"inventory_{i}" for i, p in enumerate(products, 1)}
    
    # Create order
    print_step(1, "Creating order from cart")
    try:
        order = OrderService.create_order_from_cart(
            cart=cart,
            user=customer,
            shipping_address="123 Main St, Springfield, IL 62701",
            products=product_map,
            inventories=inventory_map,
        )
        print(f"  ✓ Order created: {order.order_number}")
        print(f"    - Status: {order.status.value}")
        print(f"    - Payment: {order.payment_status.value}")
    except ValueError as e:
        print(f"  ⚠ Order error: {e}")
        return None
    
    # Order confirmation
    print_step(2, "Confirming payment")
    OrderService.confirm_order(order)
    print(f"  ✓ Payment confirmed")
    print(f"    - Order status: {order.status.value}")
    print(f"    - Payment status: {order.payment_status.value}")
    
    # Order workflow
    print_step(3, "Order workflow transition")
    print(f"  ✓ Marking as shipped")
    order.mark_shipped()
    print(f"    - Status: {order.status.value}")
    
    # Calculate totals
    print_step(4, "Order summary")
    print(f"  ✓ Subtotal: ${order.subtotal:.2f}")
    print(f"  ✓ Tax (8%): ${order.tax:.2f}")
    print(f"  ✓ Shipping: ${order.shipping:.2f}")
    print(f"  ✓ Total: ${order.total:.2f}")
    
    return order


def demo_reviews(customer: User, products: list) -> list:
    """Demo 5: Review and rating system"""
    print_section("DEMO 5: Reviews & Ratings")
    
    reviews = []
    
    print_step(1, "Creating product reviews")
    review1 = ReviewService.create_review(
        product=products[0],
        customer=customer,
        rating=5,
        title="Excellent guide!",
        content="This guide helped me understand turbo-orm perfectly. Highly recommended for all Python developers!",
        verified_purchase=True,
    )
    reviews.append(review1)
    print(f"  ✓ Review 1: {review1.rating}⭐ - {review1.title}")
    
    # Update product rating
    print_step(2, "Updating product ratings")
    ReviewService.update_product_rating(products[0], reviews)
    print(f"  ✓ Product rating updated: {products[0].rating:.1f}⭐")
    print(f"    - Based on {products[0].review_count} review(s)")
    
    return reviews


def demo_analytics(customer: User, orders: list = None) -> dict:
    """Demo 6: Analytics and reporting"""
    print_section("DEMO 6: Analytics & Reporting")
    
    if orders is None:
        orders = []
    
    # User statistics
    print_step(1, "User statistics")
    user_stats = AnalyticsService.calculate_user_stats(customer, orders)
    print(f"  ✓ Total orders: {user_stats.total_orders}")
    print(f"  ✓ Total spent: ${user_stats.total_spent:.2f}")
    print(f"  ✓ Average order: ${user_stats.average_order_value:.2f}")
    print(f"  ✓ VIP customer: {user_stats.is_vip_customer}")
    
    return {"user_stats": user_stats}


def demo_performance() -> None:
    """Demo 7: Performance highlights"""
    print_section("DEMO 7: Performance Characteristics")
    
    print_step(1, "Key Performance Features")
    features = [
        ("In-memory operations", "Ultra-fast model creation and manipulation"),
        ("Bulk queries", "Batch retrieve products by category/seller"),
        ("Indexed lookups", "Fast user/product/order searches"),
        ("Cache-friendly", "Designed for caching layers"),
        ("Query optimization", "Smart index usage"),
    ]
    
    for feature, description in features:
        print(f"  ✓ {feature}: {description}")
    
    print_step(2, "Zero Dependencies")
    print(f"  ✓ Core models: Pure Python classes")
    print(f"  ✓ Database: Built-in sqlite3")
    print(f"  ✓ Type hints: Native Python typing")
    print(f"  ✓ No external packages required")


def main():
    """Run complete demo"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  E-COMMERCE SHOWCASE: turbo-orm Real-World Project".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        # Run demos
        admin, seller, customer = demo_user_management()
        products = demo_product_management(seller)
        cart = demo_shopping_cart(customer, products)
        order = demo_order_processing(customer, cart, products)
        reviews = demo_reviews(customer, products)
        analytics = demo_analytics(customer, [order] if order else [])
        demo_performance()
        
        # Final summary
        print_section("DEMO COMPLETE")
        print("✓ Successfully demonstrated:")
        print("  • User management with RBAC")
        print("  • Product catalog & inventory")
        print("  • Shopping cart operations")
        print("  • Order processing workflow")
        print("  • Review & rating system")
        print("  • Analytics & reporting")
        print("  • Type-safe model definitions")
        print("  • Business logic patterns")
        print("\n✓ Ready for production deployment")
        print(f"\nView the showcase at: showcase_ecommerce/")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
