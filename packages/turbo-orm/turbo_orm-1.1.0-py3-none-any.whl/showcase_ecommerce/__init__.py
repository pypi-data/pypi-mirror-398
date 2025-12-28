"""
E-Commerce Showcase Module

This module demonstrates advanced turbo-orm capabilities with a complete
e-commerce application including models, database layer, services, and
business logic.
"""

# Import and export all models
from .models import (
    User, UserRole, Product, ProductCategory, Order, OrderStatus,
    OrderItem, Review, ShoppingCart, Inventory, PaymentStatus,
    UserStats, ProductStats, Wishlist, Coupon, DiscountType,
    Payment, PaymentMethod, Notification, NotificationType,
    ProductRecommendation
)

# Import and export database components
from .database import (
    Database, UserRepository, ProductRepository, OrderRepository
)

# Import and export service components
from .services import (
    UserService, ProductService, CartService, OrderService,
    ReviewService, AnalyticsService, WishlistService, CouponService,
    PaymentService, NotificationService, RecommendationService
)

# Define what gets imported with "from showcase_ecommerce import *"
__all__ = [
    # Models
    'User', 'UserRole', 'Product', 'ProductCategory', 'Order', 'OrderStatus',
    'OrderItem', 'Review', 'ShoppingCart', 'Inventory', 'PaymentStatus',
    'UserStats', 'ProductStats', 'Wishlist', 'Coupon', 'DiscountType',
    'Payment', 'PaymentMethod', 'Notification', 'NotificationType',
    'ProductRecommendation',

    # Database
    'Database', 'UserRepository', 'ProductRepository', 'OrderRepository',

    # Services
    'UserService', 'ProductService', 'CartService', 'OrderService',
    'ReviewService', 'AnalyticsService', 'WishlistService', 'CouponService',
    'PaymentService', 'NotificationService', 'RecommendationService'
]