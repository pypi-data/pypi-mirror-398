#!/usr/bin/env python3
"""
Advanced Features Demonstration

Showcases new capabilities:
- Wishlist management
- Coupon & discount system
- Payment processing
- Notifications
- Product recommendations
"""

import sys
from decimal import Decimal
from datetime import datetime, timedelta

# Fix UTF-8 encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from .models import (
    User, UserRole, Product, ProductCategory, DiscountType, PaymentMethod,
    NotificationType, Wishlist, Coupon, Payment, Notification
)
from .services import (
    UserService, ProductService, WishlistService, CouponService,
    PaymentService, NotificationService, RecommendationService
)


def print_header(text: str) -> None:
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def demo_wishlist() -> None:
    """Demonstrate wishlist features"""
    print_header("1. WISHLIST MANAGEMENT")
    
    # Create user and wishlist
    user = UserService.create_user(
        email="wishlist@example.com",
        username="wishlist_user",
        password="SecurePass123",
        first_name="Wishlist",
        last_name="Demo",
    )
    print(f"✓ Created user: {user.username}")
    
    # Create wishlist
    wishlist = WishlistService.create_wishlist(user.id if hasattr(user, 'id') else 1)
    print(f"✓ Created wishlist for user")
    
    # Create products
    products = [
        ProductService.create_product(
            name="Wireless Headphones",
            description="Premium noise-canceling headphones",
            category=ProductCategory.ELECTRONICS,
            seller_id=1,
            price=Decimal("149.99"),
            cost=Decimal("75.00"),
            stock_quantity=50,
        )[0],
        ProductService.create_product(
            name="USB-C Cable",
            description="Fast charging cable",
            category=ProductCategory.ELECTRONICS,
            seller_id=1,
            price=Decimal("19.99"),
            cost=Decimal("5.00"),
            stock_quantity=200,
        )[0],
    ]
    
    # Add to wishlist
    for product in products:
        pid = product.id if hasattr(product, 'id') else 1
        WishlistService.add_to_wishlist(wishlist, pid)
        print(f"✓ Added '{product.name}' to wishlist")
    
    print(f"✓ Wishlist contains {WishlistService.get_wishlist_count(wishlist)} items")


def demo_coupons() -> None:
    """Demonstrate coupon system"""
    print_header("2. COUPON & DISCOUNT SYSTEM")
    
    # Create coupons
    coupons = [
        CouponService.create_coupon(
            code="WELCOME10",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("10"),
            max_uses=100,
        ),
        CouponService.create_coupon(
            code="SAVE20",
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("20"),
            max_uses=50,
            min_purchase=Decimal("100"),
        ),
        CouponService.create_coupon(
            code="HOLIDAY50",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=Decimal("50"),
            max_uses=10,
            expiry_date=datetime.now() + timedelta(days=30),
        ),
    ]
    
    print(f"✓ Created {len(coupons)} coupons:")
    for coupon in coupons:
        print(f"  - {coupon.code}: {coupon.discount_value} ({coupon.discount_type.value})")
    
    # Test coupon validity
    cart_total = Decimal("150.00")
    print(f"\nTesting coupons on cart total: ${cart_total}")
    
    for coupon in coupons:
        is_valid = coupon.is_valid(cart_total)
        if is_valid:
            discount = coupon.calculate_discount(cart_total)
            print(f"✓ {coupon.code} valid: Discount = ${discount:.2f}")
        else:
            print(f"✗ {coupon.code} invalid")
    
    print(f"\n✓ Active coupons: {len(CouponService.get_active_coupons(coupons))}")


def demo_payments() -> None:
    """Demonstrate payment processing"""
    print_header("3. PAYMENT PROCESSING")
    
    payment_methods = [
        PaymentMethod.CREDIT_CARD,
        PaymentMethod.PAYPAL,
        PaymentMethod.BANK_TRANSFER,
    ]
    
    print("Processing multiple payment methods:\n")
    
    for i, method in enumerate(payment_methods, 1):
        payment = PaymentService.create_payment(
            order_id=i,
            amount=Decimal("199.99"),
            method=method,
        )
        print(f"✓ Created payment for {method.value}")
        
        # Process payment
        if PaymentService.process_payment(payment):
            print(f"  → Payment status: {payment.status.value}")
        
        # Complete payment
        if PaymentService.complete_payment(payment, f"TXN-{i:05d}"):
            print(f"  → Completed with transaction ID: {payment.transaction_id}")
    
    print()


def demo_notifications() -> None:
    """Demonstrate notification system"""
    print_header("4. NOTIFICATION SYSTEM")
    
    # Create user
    user = UserService.create_user(
        email="notify@example.com",
        username="notify_user",
        password="SecurePass123",
        first_name="Notify",
        last_name="Demo",
    )
    print(f"✓ Created user: {user.username}\n")
    
    # Create fake order for notifications
    from models import Order
    order = Order(
        customer_id=user.id if hasattr(user, 'id') else 1,
        shipping_address="123 Main St",
        notes="Demo order",
    )
    
    # Generate notifications
    notifications = [
        NotificationService.send_order_confirmation(user, order),
        NotificationService.send_shipping_update(user, order),
        NotificationService.create_notification(
            user_id=user.id if hasattr(user, 'id') else 1,
            notification_type=NotificationType.REVIEW_REQUEST,
            title="How did you like your order?",
            message="Please leave a review!",
        ),
        NotificationService.create_notification(
            user_id=user.id if hasattr(user, 'id') else 1,
            notification_type=NotificationType.PROMOTION,
            title="Special Sale Today!",
            message="Get 20% off electronics",
        ),
    ]
    
    print("Generated notifications:\n")
    for notif in notifications:
        print(f"✓ [{notif.notification_type.value}]")
        print(f"  Title: {notif.title}")
        print(f"  Message: {notif.message}\n")
    
    # Mark as read
    notifications[0].mark_as_read()
    
    unread_count = len(NotificationService.get_unread_notifications(
        notifications,
        user.id if hasattr(user, 'id') else 1
    ))
    print(f"✓ Unread notifications: {unread_count}/{len(notifications)}")


def demo_recommendations() -> None:
    """Demonstrate recommendation engine"""
    print_header("5. PRODUCT RECOMMENDATIONS")
    
    # Create user
    user = UserService.create_user(
        email="recommend@example.com",
        username="recommend_user",
        password="SecurePass123",
        first_name="Recommend",
        last_name="Demo",
    )
    
    # Create products
    products = []
    for i in range(1, 11):
        product = ProductService.create_product(
            name=f"Product {i}",
            description=f"Premium product {i}",
            category=ProductCategory.ELECTRONICS if i % 2 == 0 else ProductCategory.BOOKS,
            seller_id=1,
            price=Decimal(str(50 + i * 10)),
            cost=Decimal(str(25 + i * 5)),
            stock_quantity=100 - i * 5,
        )[0]
        # Simulate some ratings
        if hasattr(product, 'rating'):
            product.rating = 4.0 + (i % 5) * 0.2
        if hasattr(product, 'review_count'):
            product.review_count = (i * 10) % 100
        products.append(product)
    
    print(f"✓ Created {len(products)} products for recommendation\n")
    
    # Get recommendations by category
    category_recs = RecommendationService.recommend_by_category(
        user_id=user.id if hasattr(user, 'id') else 1,
        products=products,
        category=ProductCategory.ELECTRONICS,
        limit=3,
    )
    print(f"✓ Category-based recommendations: {len(category_recs)}")
    for rec in category_recs:
        print(f"  - Product {rec.product_id}: {rec.reason} (score: {rec.score})")
    
    # Get bestseller recommendations
    bestseller_recs = RecommendationService.recommend_bestsellers(
        user_id=user.id if hasattr(user, 'id') else 1,
        products=products,
        limit=3,
    )
    print(f"\n✓ Bestseller recommendations: {len(bestseller_recs)}")
    for rec in bestseller_recs:
        print(f"  - Product {rec.product_id}: {rec.reason} (score: {rec.score})")


def demo_integrated_workflow() -> None:
    """Demonstrate integrated advanced features workflow"""
    print_header("6. INTEGRATED WORKFLOW")
    
    # Create customer
    customer = UserService.create_user(
        email="premium@example.com",
        username="premium_customer",
        password="SecurePass123",
        first_name="Premium",
        last_name="Customer",
    )
    print(f"✓ Created customer: {customer.username}")
    
    # Create wishlist and add items
    wishlist = WishlistService.create_wishlist(
        customer.id if hasattr(customer, 'id') else 1
    )
    print(f"✓ Created wishlist")
    
    # Create product
    product = ProductService.create_product(
        name="Premium Laptop",
        description="High-performance laptop",
        category=ProductCategory.ELECTRONICS,
        seller_id=1,
        price=Decimal("1299.99"),
        cost=Decimal("600.00"),
        stock_quantity=10,
    )[0]
    print(f"✓ Created product: {product.name}")
    
    # Add to wishlist
    pid = product.id if hasattr(product, 'id') else 1
    WishlistService.add_to_wishlist(wishlist, pid)
    print(f"✓ Added to wishlist")
    
    # Apply coupon
    coupon = CouponService.create_coupon(
        code="SAVE100",
        discount_type=DiscountType.FIXED_AMOUNT,
        discount_value=Decimal("100"),
    )
    cart_total = product.price
    success, discount = CouponService.apply_coupon(coupon, cart_total)
    print(f"✓ Applied coupon: {coupon.code} (discount: ${discount})")
    
    # Create and process payment
    payment = PaymentService.create_payment(
        order_id=1,
        amount=cart_total - discount,
        method=PaymentMethod.CREDIT_CARD,
    )
    PaymentService.process_payment(payment)
    PaymentService.complete_payment(payment, "TXN-00001")
    print(f"✓ Payment processed and completed")
    
    # Send notifications
    from models import Order
    order = Order(
        customer_id=customer.id if hasattr(customer, 'id') else 1,
        shipping_address="123 Premium St",
    )
    notif = NotificationService.send_order_confirmation(customer, order)
    print(f"✓ Sent notification: {notif.title}")
    
    print("\n✓ Complete workflow executed successfully!")


def main() -> None:
    """Run all advanced features demos"""
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║   turbo-orm Advanced Features Demonstration                        ║
    ║                                                                    ║
    ║   New Capabilities:                                               ║
    ║   • Wishlist Management                                           ║
    ║   • Coupon & Discount System                                      ║
    ║   • Payment Processing                                            ║
    ║   • Notifications                                                 ║
    ║   • Product Recommendations                                       ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        demo_wishlist()
        demo_coupons()
        demo_payments()
        demo_notifications()
        demo_recommendations()
        demo_integrated_workflow()
        
        print_header("ALL ADVANCED FEATURES DEMONSTRATED")
        print("""
        ✓ Wishlist system fully functional
        ✓ Coupon validation and application working
        ✓ Payment processing and tracking operational
        ✓ Notification generation and management active
        ✓ Recommendation engine providing suggestions
        ✓ Integrated workflows executed successfully
        """)
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
