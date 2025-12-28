"""
E-Commerce Business Logic - Core operations

Demonstrates:
- Transaction handling
- Business rule enforcement
- Inventory management
- Order processing workflow
- Performance optimization with batching
- Error handling and validation
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime
import hashlib

from .models import (
    User, UserRole, Product, ProductCategory, Order, OrderStatus,
    OrderItem, Review, ShoppingCart, Inventory, PaymentStatus,
    UserStats, ProductStats, Wishlist, Coupon, DiscountType,
    Payment, PaymentMethod, Notification, NotificationType,
    ProductRecommendation
)


# ============================================================================
# Constants
# ============================================================================

TAX_RATE = Decimal("0.08")  # 8% tax
STANDARD_SHIPPING = Decimal("9.99")
FREE_SHIPPING_THRESHOLD = Decimal("100.00")  # Free shipping over $100


# ============================================================================
# User Management
# ============================================================================

class UserService:
    """Manage user accounts and authentication"""
    
    @staticmethod
    def create_user(
        email: str,
        username: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        role: UserRole = UserRole.CUSTOMER,
    ) -> User:
        """Create new user account"""
        # Validate inputs
        if not email or "@" not in email:
            raise ValueError("Invalid email address")
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Hash password (simple demonstration - use bcrypt in production)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )
        
        return user

    @staticmethod
    def verify_password(user: User, password: str) -> bool:
        """Verify password matches user's hash"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == user.password_hash

    @staticmethod
    def promote_to_seller(user: User) -> bool:
        """Promote customer to seller"""
        if user.role == UserRole.CUSTOMER:
            user.role = UserRole.SELLER
            user.updated_at = datetime.now()
            return True
        return False


# ============================================================================
# Product Management
# ============================================================================

class ProductService:
    """Manage product catalog and inventory"""
    
    @staticmethod
    def create_product(
        name: str,
        description: str,
        category: ProductCategory,
        seller_id: int,
        price: Decimal,
        cost: Decimal,
        stock_quantity: int = 0,
    ) -> Tuple[Product, Inventory]:
        """Create product with inventory"""
        # Validation
        if price <= Decimal("0"):
            raise ValueError("Price must be positive")
        if cost < Decimal("0"):
            raise ValueError("Cost cannot be negative")
        if cost >= price:
            raise ValueError("Cost must be less than price")
        
        # Create product
        product = Product(
            name=name,
            description=description,
            category=category,
            seller_id=seller_id,
            price=price,
            cost=cost,
            stock_quantity=stock_quantity,
            sku=ProductService._generate_sku(),
        )
        
        # Create inventory record
        inventory = Inventory(
            product_id=product.id if hasattr(product, 'id') else 0,
            current_stock=stock_quantity,
        )
        
        return product, inventory

    @staticmethod
    def _generate_sku() -> str:
        """Generate unique SKU"""
        import random
        return f"SKU-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"

    @staticmethod
    def apply_seasonal_discount(product: Product, percent: Decimal) -> None:
        """Apply seasonal discount"""
        if not (Decimal("0") <= percent <= Decimal("100")):
            raise ValueError("Discount must be between 0-100%")
        product.apply_discount(percent)

    @staticmethod
    def get_trending_products(
        products: List[Product],
        limit: int = 10
    ) -> List[Product]:
        """Get top trending products by rating"""
        return sorted(
            products,
            key=lambda p: (p.rating, p.review_count),
            reverse=True
        )[:limit]

    @staticmethod
    def search_products(
        products: List[Product],
        query: str,
        category: Optional[ProductCategory] = None,
    ) -> List[Product]:
        """Full-text search on products"""
        results = products
        
        # Filter by category
        if category:
            results = [p for p in results if p.category == category]
        
        # Search by query
        query_lower = query.lower()
        results = [
            p for p in results
            if query_lower in p.name.lower() or
               query_lower in p.description.lower()
        ]
        
        return results


# ============================================================================
# Shopping Cart & Order Processing
# ============================================================================

class CartService:
    """Manage shopping carts"""
    
    @staticmethod
    def add_to_cart(
        cart: ShoppingCart,
        product: Product,
        quantity: int,
    ) -> bool:
        """Add product to cart with validation"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if not product.is_in_stock:
            raise ValueError(f"Product '{product.name}' is out of stock")
        if product.stock_quantity < quantity:
            raise ValueError(
                f"Only {product.stock_quantity} units available"
            )
        
        cart.add_item(product.id if hasattr(product, 'id') else 0, quantity)
        return True

    @staticmethod
    def calculate_cart_total(
        cart: ShoppingCart,
        products: dict,  # product_id -> Product mapping
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Calculate cart totals: (subtotal, tax, shipping)"""
        subtotal = Decimal("0")
        
        for product_id, quantity in cart.items.items():
            product = products.get(product_id)
            if product:
                subtotal += product.current_price * quantity
        
        # Calculate tax
        tax = subtotal * TAX_RATE
        
        # Calculate shipping
        shipping = (
            Decimal("0") if subtotal >= FREE_SHIPPING_THRESHOLD
            else STANDARD_SHIPPING
        )
        
        return subtotal, tax, shipping


class OrderService:
    """Manage order lifecycle"""
    
    @staticmethod
    def create_order_from_cart(
        cart: ShoppingCart,
        user: User,
        shipping_address: str,
        products: dict,
        inventories: dict,
    ) -> Optional[Order]:
        """Convert cart to order with inventory reservation"""
        if not cart.items:
            raise ValueError("Cannot create order from empty cart")
        
        # Create order
        order = Order(
            customer_id=user.id if hasattr(user, 'id') else 0,
            shipping_address=shipping_address,
        )
        
        # Calculate totals
        subtotal = Decimal("0")
        
        for product_id, quantity in cart.items.items():
            product = products.get(product_id)
            inventory = inventories.get(product_id)
            
            if not product or not inventory:
                raise ValueError(f"Product {product_id} not found")
            
            # Check availability
            if not inventory.reserve_stock(quantity):
                raise ValueError(
                    f"Insufficient stock for {product.name}"
                )
            
            # Create order item
            item = OrderItem(
                order_id=order.id if hasattr(order, 'id') else 0,
                product_id=product_id,
                quantity=quantity,
                unit_price=product.current_price,
            )
            
            subtotal += item.total
        
        # Calculate final totals
        order.subtotal = subtotal
        order.tax = subtotal * TAX_RATE
        order.shipping = (
            Decimal("0") if subtotal >= FREE_SHIPPING_THRESHOLD
            else STANDARD_SHIPPING
        )
        order.total = order.calculate_total()
        order.payment_status = PaymentStatus.PENDING
        
        return order

    @staticmethod
    def confirm_order(order: Order) -> bool:
        """Confirm payment and transition order status"""
        if order.payment_status != PaymentStatus.PENDING:
            raise ValueError("Order payment already processed")
        
        order.payment_status = PaymentStatus.COMPLETED
        order.confirm()
        order.status = OrderStatus.PROCESSING
        return True

    @staticmethod
    def cancel_order(
        order: Order,
        inventories: dict,
        order_items: List[OrderItem],
    ) -> bool:
        """Cancel order and release inventory"""
        if not order.cancel():
            return False
        
        # Release reserved inventory
        for item in order_items:
            inventory = inventories.get(item.product_id)
            if inventory:
                inventory.release_stock(item.quantity)
        
        return True


# ============================================================================
# Review & Rating System
# ============================================================================

class ReviewService:
    """Manage product reviews and ratings"""
    
    @staticmethod
    def create_review(
        product: Product,
        customer: User,
        rating: int,
        title: str,
        content: str,
        verified_purchase: bool = False,
    ) -> Review:
        """Create product review"""
        if len(content) < 10:
            raise ValueError("Review content must be at least 10 characters")
        
        review = Review(
            product_id=product.id if hasattr(product, 'id') else 0,
            customer_id=customer.id if hasattr(customer, 'id') else 0,
            rating=rating,
            title=title,
            content=content,
            verified_purchase=verified_purchase,
        )
        
        return review

    @staticmethod
    def update_product_rating(
        product: Product,
        reviews: List[Review],
    ) -> None:
        """Recalculate product rating from reviews"""
        if not reviews:
            product.rating = 0.0
            product.review_count = 0
            return
        
        total_rating = sum(r.rating for r in reviews)
        product.rating = total_rating / len(reviews)
        product.review_count = len(reviews)
        product.updated_at = datetime.now()


# ============================================================================
# Analytics & Reporting
# ============================================================================

class AnalyticsService:
    """Generate analytics and statistics"""
    
    @staticmethod
    def calculate_user_stats(
        user: User,
        orders: List[Order],
    ) -> UserStats:
        """Calculate user statistics"""
        stats = UserStats(user.id if hasattr(user, 'id') else 0)
        stats.total_orders = len(orders)
        stats.total_spent = sum(o.total for o in orders)
        
        if stats.total_orders > 0:
            stats.average_order_value = stats.total_spent / stats.total_orders
            stats.lifetime_value = stats.total_spent
            # Find last order
            delivered_orders = [
                o for o in orders if o.status == OrderStatus.DELIVERED
            ]
            if delivered_orders:
                stats.last_order_date = max(
                    o.delivered_at for o in delivered_orders
                    if o.delivered_at
                )
        
        return stats

    @staticmethod
    def calculate_product_stats(
        product: Product,
        sales: List[OrderItem],
        views: int = 0,
    ) -> ProductStats:
        """Calculate product performance metrics"""
        stats = ProductStats(product.id if hasattr(product, 'id') else 0)
        stats.views = views
        stats.sales_count = sum(s.quantity for s in sales)
        stats.revenue = sum(
            s.quantity * s.unit_price - s.discount_amount
            for s in sales
        )
        stats.average_rating = product.rating
        
        if stats.views > 0:
            stats.conversion_rate = stats.sales_count / stats.views
        
        return stats

    @staticmethod
    def get_sales_summary(orders: List[Order]) -> dict:
        """Get sales summary for dashboard"""
        total_revenue = sum(o.total for o in orders if o.status != OrderStatus.CANCELLED)
        total_orders = len([o for o in orders if o.status != OrderStatus.CANCELLED])
        avg_order_value = (
            total_revenue / total_orders if total_orders > 0 else Decimal("0")
        )
        
        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": avg_order_value,
            "pending_orders": len([o for o in orders if o.status == OrderStatus.PENDING]),
            "shipped_orders": len([o for o in orders if o.status == OrderStatus.SHIPPED]),
        }


# ============================================================================
# Wishlist Service
# ============================================================================

class WishlistService:
    """Manage user wishlists"""
    
    @staticmethod
    def create_wishlist(user_id: int) -> Wishlist:
        """Create user wishlist"""
        return Wishlist(user_id=user_id)
    
    @staticmethod
    def add_to_wishlist(wishlist: Wishlist, product_id: int) -> bool:
        """Add product to wishlist"""
        return wishlist.add_product(product_id)
    
    @staticmethod
    def remove_from_wishlist(wishlist: Wishlist, product_id: int) -> bool:
        """Remove product from wishlist"""
        return wishlist.remove_product(product_id)
    
    @staticmethod
    def get_wishlist_count(wishlist: Wishlist) -> int:
        """Get wishlist item count"""
        return len(wishlist.product_ids)


# ============================================================================
# Coupon/Discount Service
# ============================================================================

class CouponService:
    """Manage coupons and discounts"""
    
    @staticmethod
    def create_coupon(
        code: str,
        discount_type: DiscountType,
        discount_value: Decimal,
        max_uses: int = -1,
        expiry_date = None,
        min_purchase: Decimal = Decimal("0"),
    ) -> Coupon:
        """Create new coupon"""
        return Coupon(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
            expiry_date=expiry_date,
            min_purchase=min_purchase,
        )
    
    @staticmethod
    def apply_coupon(coupon: Coupon, cart_total: Decimal) -> Tuple[bool, Decimal]:
        """Apply coupon to cart"""
        if not coupon.is_valid(cart_total):
            return False, Decimal("0")
        
        discount = coupon.calculate_discount(cart_total)
        coupon.current_uses += 1
        return True, discount
    
    @staticmethod
    def get_active_coupons(coupons: List[Coupon]) -> List[Coupon]:
        """Get all active coupons"""
        return [c for c in coupons if c.is_active]


# ============================================================================
# Payment Service
# ============================================================================

class PaymentService:
    """Handle payment processing"""
    
    @staticmethod
    def create_payment(
        order_id: int,
        amount: Decimal,
        method: PaymentMethod,
    ) -> Payment:
        """Create payment record"""
        return Payment(order_id=order_id, amount=amount, method=method)
    
    @staticmethod
    def process_payment(payment: Payment) -> bool:
        """Process payment"""
        return payment.process()
    
    @staticmethod
    def complete_payment(payment: Payment, transaction_id: str) -> bool:
        """Complete payment"""
        return payment.complete(transaction_id)
    
    @staticmethod
    def refund_payment(payment: Payment) -> bool:
        """Refund payment"""
        if payment.status == PaymentStatus.COMPLETED:
            payment.status = PaymentStatus.REFUNDED
            payment.updated_at = datetime.now()
            return True
        return False


# ============================================================================
# Notification Service
# ============================================================================

class NotificationService:
    """Send and manage notifications"""
    
    @staticmethod
    def create_notification(
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
    ) -> Notification:
        """Create notification"""
        return Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
        )
    
    @staticmethod
    def send_order_confirmation(user: User, order: Order) -> Notification:
        """Send order confirmation notification"""
        return NotificationService.create_notification(
            user_id=user.id if hasattr(user, 'id') else 1,
            notification_type=NotificationType.ORDER_CONFIRMATION,
            title=f"Order #{order.order_number} Confirmed",
            message=f"Your order of {len(order.items)} items has been confirmed.",
        )
    
    @staticmethod
    def send_shipping_update(user: User, order: Order) -> Notification:
        """Send shipping update notification"""
        return NotificationService.create_notification(
            user_id=user.id if hasattr(user, 'id') else 1,
            notification_type=NotificationType.SHIPPING_UPDATE,
            title=f"Order #{order.order_number} Shipped",
            message=f"Your order is on the way!",
        )
    
    @staticmethod
    def get_unread_notifications(notifications: List[Notification], user_id: int) -> List[Notification]:
        """Get unread notifications for user"""
        return [n for n in notifications if n.user_id == user_id and not n.is_read]


# ============================================================================
# Recommendation Service
# ============================================================================

class RecommendationService:
    """Generate product recommendations"""
    
    @staticmethod
    def recommend_by_category(
        user_id: int,
        products: List[Product],
        category: ProductCategory,
        limit: int = 5,
    ) -> List[ProductRecommendation]:
        """Recommend products in same category"""
        recommendations = []
        for product in products:
            if product.category == category and len(recommendations) < limit:
                rec = ProductRecommendation(
                    user_id=user_id,
                    product_id=product.id if hasattr(product, 'id') else 1,
                    reason="Similar category",
                    score=Decimal(product.rating if hasattr(product, 'rating') else 0),
                )
                recommendations.append(rec)
        return recommendations
    
    @staticmethod
    def recommend_bestsellers(
        user_id: int,
        products: List[Product],
        limit: int = 5,
    ) -> List[ProductRecommendation]:
        """Recommend bestselling products"""
        sorted_products = sorted(
            products,
            key=lambda p: (p.review_count if hasattr(p, 'review_count') else 0, p.rating if hasattr(p, 'rating') else 0),
            reverse=True
        )
        
        recommendations = []
        for product in sorted_products[:limit]:
            rec = ProductRecommendation(
                user_id=user_id,
                product_id=product.id if hasattr(product, 'id') else 1,
                reason="Bestseller",
                score=Decimal(product.rating if hasattr(product, 'rating') else 0),
            )
            recommendations.append(rec)
        return recommendations


if __name__ == "__main__":
    print("✓ E-Commerce Business Logic loaded successfully")
    print("✓ Services: UserService, ProductService, CartService, OrderService")
    print("✓ Services: ReviewService, AnalyticsService")
    print("✓ New Services: WishlistService, CouponService, PaymentService")
    print("✓ New Services: NotificationService, RecommendationService")
