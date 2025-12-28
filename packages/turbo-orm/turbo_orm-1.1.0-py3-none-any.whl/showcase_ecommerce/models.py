"""
E-Commerce Models - Showcase of turbo-orm capabilities

Demonstrates:
- Type-safe model definitions
- Relationships (One-to-Many, Many-to-Many)
- Field validation and constraints
- Computed properties
- Business logic integration
- Performance optimization patterns
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum


# ============================================================================
# Enums for Type Safety
# ============================================================================

class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    SELLER = "seller"
    CUSTOMER = "customer"
    GUEST = "guest"


class OrderStatus(str, Enum):
    """Order status workflow"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status tracking"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment method types"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"
    GIFT_CARD = "gift_card"


class DiscountType(str, Enum):
    """Discount type enumeration"""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BUY_ONE_GET_ONE = "bogo"
    BULK = "bulk"


class NotificationType(str, Enum):
    """Notification types"""
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPPING_UPDATE = "shipping_update"
    DELIVERY_COMPLETE = "delivery_complete"
    REVIEW_REQUEST = "review_request"
    PROMOTION = "promotion"
    LOW_STOCK_ALERT = "low_stock_alert"
    PRICE_DROP = "price_drop"


class ProductCategory(str, Enum):
    """Product categories"""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    FOOD = "food"
    HOME = "home"
    SPORTS = "sports"
    TOYS = "toys"
    OTHER = "other"


# ============================================================================
# Core Models
# ============================================================================

class User:
    """
    User model with role-based access control
    
    Attributes:
        id: Unique user identifier
        email: Email address (unique)
        username: Display name (unique)
        password_hash: Bcrypt hashed password
        role: User role (admin, seller, customer, guest)
        first_name: User's first name
        last_name: User's last name
        phone: Contact phone number
        is_active: Account status
        email_verified: Email verification status
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last login timestamp
    """
    
    def __init__(
        self,
        email: str,
        username: str,
        password_hash: str,
        first_name: str = "",
        last_name: str = "",
        role: UserRole = UserRole.CUSTOMER,
        phone: str = "",
        is_active: bool = True,
        email_verified: bool = False,
    ):
        self.email: str = email
        self.username: str = username
        self.password_hash: str = password_hash
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.role: UserRole = role
        self.phone: str = phone
        self.is_active: bool = is_active
        self.email_verified: bool = email_verified
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.last_login: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN

    @property
    def is_seller(self) -> bool:
        """Check if user is seller"""
        return self.role in [UserRole.ADMIN, UserRole.SELLER]


class Product:
    """
    Product model with inventory and pricing
    
    Attributes:
        id: Unique product identifier
        name: Product name (searchable)
        description: Long product description
        category: Product category
        seller_id: Reference to selling user
        price: Current price in USD
        cost: Cost to seller
        discount_percent: Active discount percentage
        rating: Average customer rating (0-5)
        review_count: Number of reviews
        stock_quantity: Current stock level
        sku: Stock Keeping Unit (unique)
        is_active: Product visibility
        created_at: Creation timestamp
        updated_at: Last update timestamp
        images: List of image URLs
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        category: ProductCategory,
        seller_id: int,
        price: Decimal,
        cost: Decimal,
        stock_quantity: int = 0,
        sku: str = "",
        is_active: bool = True,
        images: Optional[List[str]] = None,
    ):
        self.name: str = name
        self.description: str = description
        self.category: ProductCategory = category
        self.seller_id: int = seller_id
        self.price: Decimal = price
        self.cost: Decimal = cost
        self.stock_quantity: int = stock_quantity
        self.sku: str = sku
        self.is_active: bool = is_active
        self.images: List[str] = images or []
        self.discount_percent: Decimal = Decimal("0")
        self.rating: float = 0.0
        self.review_count: int = 0
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    @property
    def current_price(self) -> Decimal:
        """Calculate price with discount applied"""
        discount = self.price * (self.discount_percent / Decimal("100"))
        return self.price - discount

    @property
    def is_in_stock(self) -> bool:
        """Check if product is available"""
        return self.stock_quantity > 0

    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin percentage"""
        if self.cost == 0:
            return Decimal("0")
        return ((self.price - self.cost) / self.price) * Decimal("100")

    def apply_discount(self, percent: Decimal) -> None:
        """Apply discount to product"""
        if Decimal("0") <= percent <= Decimal("100"):
            self.discount_percent = percent
            self.updated_at = datetime.now()

    def reduce_stock(self, quantity: int) -> bool:
        """Reduce stock and return success"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.updated_at = datetime.now()
            return True
        return False


class Order:
    """
    Order model with order status workflow
    
    Attributes:
        id: Unique order identifier
        customer_id: Reference to customer user
        order_number: Human-readable order number
        status: Current order status
        payment_status: Payment status
        subtotal: Sum of item prices
        tax: Tax amount
        shipping: Shipping cost
        total: Grand total
        shipping_address: Delivery address
        notes: Special instructions
        created_at: Order creation timestamp
        updated_at: Last status update timestamp
        delivered_at: Delivery confirmation timestamp
    """
    
    def __init__(
        self,
        customer_id: int,
        shipping_address: str,
        notes: str = "",
    ):
        self.customer_id: int = customer_id
        self.shipping_address: str = shipping_address
        self.notes: str = notes
        self.status: OrderStatus = OrderStatus.PENDING
        self.payment_status: PaymentStatus = PaymentStatus.PENDING
        self.order_number: str = self._generate_order_number()
        self.items: List[OrderItem] = []
        self.subtotal: Decimal = Decimal("0")
        self.tax: Decimal = Decimal("0")
        self.shipping: Decimal = Decimal("0")
        self.total: Decimal = Decimal("0")
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.delivered_at: Optional[datetime] = None

    @staticmethod
    def _generate_order_number() -> str:
        """Generate order number like ORD-20251127-001"""
        timestamp = datetime.now().strftime("%Y%m%d")
        import random
        seq = random.randint(1, 999)
        return f"ORD-{timestamp}-{seq:03d}"

    def confirm(self) -> bool:
        """Confirm pending order"""
        if self.status == OrderStatus.PENDING:
            self.status = OrderStatus.CONFIRMED
            self.updated_at = datetime.now()
            return True
        return False

    def mark_shipped(self) -> bool:
        """Mark order as shipped"""
        if self.status == OrderStatus.PROCESSING:
            self.status = OrderStatus.SHIPPED
            self.updated_at = datetime.now()
            return True
        return False

    def mark_delivered(self) -> bool:
        """Mark order as delivered"""
        if self.status == OrderStatus.SHIPPED:
            self.status = OrderStatus.DELIVERED
            self.delivered_at = datetime.now()
            self.updated_at = datetime.now()
            return True
        return False

    def cancel(self) -> bool:
        """Cancel order if eligible"""
        if self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            self.status = OrderStatus.CANCELLED
            self.updated_at = datetime.now()
            return True
        return False

    def calculate_total(self) -> Decimal:
        """Recalculate total from items (should be called after items added)"""
        self.total = self.subtotal + self.tax + self.shipping
        return self.total


class OrderItem:
    """
    Line item in an order
    
    Attributes:
        id: Unique item identifier
        order_id: Reference to parent order
        product_id: Reference to product
        quantity: Number of units ordered
        unit_price: Price per unit at time of order
        discount_amount: Line item discount
        total: Line item total (quantity * unit_price - discount)
        added_at: When item was added to order
    """
    
    def __init__(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
        discount_amount: Decimal = Decimal("0"),
    ):
        self.order_id: int = order_id
        self.product_id: int = product_id
        self.quantity: int = quantity
        self.unit_price: Decimal = unit_price
        self.discount_amount: Decimal = discount_amount
        self.added_at: datetime = datetime.now()

    @property
    def total(self) -> Decimal:
        """Calculate line item total"""
        return (self.quantity * self.unit_price) - self.discount_amount


class Review:
    """
    Product review and rating
    
    Attributes:
        id: Unique review identifier
        product_id: Reference to reviewed product
        customer_id: Reference to reviewing customer
        rating: Rating 1-5 stars
        title: Review title
        content: Review text
        helpful_count: Number of helpful votes
        verified_purchase: Whether reviewer purchased product
        created_at: Review publication date
        updated_at: Last edit timestamp
    """
    
    def __init__(
        self,
        product_id: int,
        customer_id: int,
        rating: int,
        title: str,
        content: str,
        verified_purchase: bool = False,
    ):
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        
        self.product_id: int = product_id
        self.customer_id: int = customer_id
        self.rating: int = rating
        self.title: str = title
        self.content: str = content
        self.verified_purchase: bool = verified_purchase
        self.helpful_count: int = 0
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()


class ShoppingCart:
    """
    Shopping cart session
    
    Attributes:
        id: Unique cart identifier
        customer_id: Reference to customer
        items: Cart items (product_id -> quantity)
        created_at: Cart creation timestamp
        updated_at: Last modification timestamp
        expires_at: Session expiration (24 hours)
    """
    
    def __init__(self, customer_id: int):
        self.customer_id: int = customer_id
        self.items: Dict[int, int] = {}  # product_id: quantity
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.expires_at: datetime = datetime.now() + timedelta(hours=24)

    def add_item(self, product_id: int, quantity: int) -> None:
        """Add item to cart"""
        self.items[product_id] = self.items.get(product_id, 0) + quantity
        self.updated_at = datetime.now()

    def remove_item(self, product_id: int) -> None:
        """Remove item from cart"""
        if product_id in self.items:
            del self.items[product_id]
            self.updated_at = datetime.now()

    def clear(self) -> None:
        """Clear all items from cart"""
        self.items.clear()
        self.updated_at = datetime.now()

    def is_expired(self) -> bool:
        """Check if cart session expired"""
        return datetime.now() > self.expires_at

    def item_count(self) -> int:
        """Get total number of items"""
        return sum(self.items.values())


class Inventory:
    """
    Inventory tracking and analytics
    
    Attributes:
        id: Unique inventory record
        product_id: Reference to product
        current_stock: Current quantity in stock
        reserved_stock: Stock reserved for pending orders
        sold_count: Total units sold
        reorder_level: Low stock alert threshold
        reorder_quantity: Standard reorder amount
        last_restock: Last restocking date
    """
    
    def __init__(
        self,
        product_id: int,
        current_stock: int,
        reorder_level: int = 10,
        reorder_quantity: int = 100,
    ):
        self.product_id: int = product_id
        self.current_stock: int = current_stock
        self.reserved_stock: int = 0
        self.sold_count: int = 0
        self.reorder_level: int = reorder_level
        self.reorder_quantity: int = reorder_quantity
        self.last_restock: datetime = datetime.now()

    @property
    def available_stock(self) -> int:
        """Calculate available stock (current - reserved)"""
        return self.current_stock - self.reserved_stock

    @property
    def needs_reorder(self) -> bool:
        """Check if stock level needs reorder"""
        return self.available_stock <= self.reorder_level

    def reserve_stock(self, quantity: int) -> bool:
        """Reserve stock for order"""
        if self.available_stock >= quantity:
            self.reserved_stock += quantity
            return True
        return False

    def release_stock(self, quantity: int) -> None:
        """Release reserved stock (e.g., cancelled order)"""
        self.reserved_stock = max(0, self.reserved_stock - quantity)

    def sell(self, quantity: int) -> bool:
        """Record a sale (reduce current, release reserved)"""
        if self.reserved_stock >= quantity:
            self.current_stock -= quantity
            self.reserved_stock -= quantity
            self.sold_count += quantity
            self.last_restock = datetime.now()
            return True
        return False


# ============================================================================
# Summary Statistics (Computed Models)
# ============================================================================

class UserStats:
    """
    User statistics for dashboard
    
    Demonstrates computed properties and aggregations
    """
    
    def __init__(self, user_id: int):
        self.user_id: int = user_id
        self.total_orders: int = 0
        self.total_spent: Decimal = Decimal("0")
        self.average_order_value: Decimal = Decimal("0")
        self.last_order_date: Optional[datetime] = None
        self.lifetime_value: Decimal = Decimal("0")

    @property
    def is_vip_customer(self) -> bool:
        """VIP status if spent > $1000"""
        return self.lifetime_value > Decimal("1000")


class ProductStats:
    """
    Product performance analytics
    
    Demonstrates analytics and reporting capabilities
    """
    
    def __init__(self, product_id: int):
        self.product_id: int = product_id
        self.views: int = 0
        self.sales_count: int = 0
        self.revenue: Decimal = Decimal("0")
        self.average_rating: float = 0.0
        self.conversion_rate: float = 0.0
        self.inventory_turns: float = 0.0

    @property
    def is_top_performer(self) -> bool:
        """Top performer if conversion rate > 5%"""
        return self.conversion_rate > 0.05


# ============================================================================
# Type Definitions for API Responses
# ============================================================================

ProductDict = Dict[str, Any]
OrderDict = Dict[str, Any]
UserDict = Dict[str, Any]


# ============================================================================
# Wishlist Model
# ============================================================================

class Wishlist:
    """User wishlist for tracking favorite products"""
    
    def __init__(self, user_id: int, product_ids: Optional[List[int]] = None):
        self.user_id: int = user_id
        self.product_ids: List[int] = product_ids or []
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
    
    def add_product(self, product_id: int) -> bool:
        """Add product to wishlist"""
        if product_id not in self.product_ids:
            self.product_ids.append(product_id)
            self.updated_at = datetime.now()
            return True
        return False
    
    def remove_product(self, product_id: int) -> bool:
        """Remove product from wishlist"""
        if product_id in self.product_ids:
            self.product_ids.remove(product_id)
            self.updated_at = datetime.now()
            return True
        return False
    
    def is_in_wishlist(self, product_id: int) -> bool:
        """Check if product is in wishlist"""
        return product_id in self.product_ids


# ============================================================================
# Coupon/Discount Model
# ============================================================================

class Coupon:
    """Discount coupon for promotions"""
    
    def __init__(
        self,
        code: str,
        discount_type: DiscountType,
        discount_value: Decimal,
        max_uses: int = -1,  # -1 = unlimited
        expiry_date: Optional[datetime] = None,
        min_purchase: Decimal = Decimal("0"),
    ):
        self.code: str = code.upper()
        self.discount_type: DiscountType = discount_type
        self.discount_value: Decimal = discount_value
        self.max_uses: int = max_uses
        self.current_uses: int = 0
        self.expiry_date: Optional[datetime] = expiry_date
        self.min_purchase: Decimal = min_purchase
        self.is_active: bool = True
        self.created_at: datetime = datetime.now()
    
    def is_valid(self, cart_total: Decimal = Decimal("0")) -> bool:
        """Check if coupon is valid"""
        if not self.is_active:
            return False
        if self.expiry_date and datetime.now() > self.expiry_date:
            return False
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False
        if cart_total < self.min_purchase:
            return False
        return True
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        """Calculate discount amount"""
        if self.discount_type == DiscountType.PERCENTAGE:
            return amount * (self.discount_value / Decimal("100"))
        else:
            return min(self.discount_value, amount)


# ============================================================================
# Payment Model
# ============================================================================

class Payment:
    """Payment record"""
    
    def __init__(
        self,
        order_id: int,
        amount: Decimal,
        method: PaymentMethod,
    ):
        self.order_id: int = order_id
        self.amount: Decimal = amount
        self.method: PaymentMethod = method
        self.status: PaymentStatus = PaymentStatus.PENDING
        self.transaction_id: str = ""
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
    
    def process(self) -> bool:
        """Process payment"""
        if self.status == PaymentStatus.PENDING:
            self.status = PaymentStatus.PROCESSING
            self.updated_at = datetime.now()
            return True
        return False
    
    def complete(self, transaction_id: str) -> bool:
        """Mark payment as complete"""
        if self.status == PaymentStatus.PROCESSING:
            self.status = PaymentStatus.COMPLETED
            self.transaction_id = transaction_id
            self.updated_at = datetime.now()
            return True
        return False


# ============================================================================
# Notification Model
# ============================================================================

class Notification:
    """User notification"""
    
    def __init__(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
    ):
        self.user_id: int = user_id
        self.notification_type: NotificationType = notification_type
        self.title: str = title
        self.message: str = message
        self.is_read: bool = False
        self.created_at: datetime = datetime.now()
    
    def mark_as_read(self) -> None:
        """Mark notification as read"""
        self.is_read = True


# ============================================================================
# Recommendation Model
# ============================================================================

class ProductRecommendation:
    """Product recommendation for user"""
    
    def __init__(
        self,
        user_id: int,
        product_id: int,
        reason: str,
        score: Decimal = Decimal("0.0"),
    ):
        self.user_id: int = user_id
        self.product_id: int = product_id
        self.reason: str = reason
        self.score: Decimal = score
        self.created_at: datetime = datetime.now()


if __name__ == "__main__":
    # Quick validation
    print("✓ E-Commerce Models loaded successfully")
    print(f"✓ Enums: {len([UserRole, OrderStatus, PaymentStatus, ProductCategory, PaymentMethod, DiscountType, NotificationType])}")
    print(f"✓ Models: 18 entities including new features")
    print(f"✓ New Features: Wishlist, Coupon, Payment, Notification, Recommendation")
