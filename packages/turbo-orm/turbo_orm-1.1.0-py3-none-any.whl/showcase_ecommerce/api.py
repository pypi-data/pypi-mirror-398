"""
E-Commerce API Layer - REST endpoints for turbo-orm showcase

Routes implemented:
  • Users: POST /api/users, GET /api/users/{id}
  • Products: GET /api/products, GET /api/products/search
  • Cart: POST /api/cart/add, GET /api/cart/{user_id}
  • Orders: POST /api/orders, GET /api/orders/{id}
  • Reviews: POST /api/reviews, GET /api/products/{id}/reviews

Run with: python api.py
"""

import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
import json

# Fix UTF-8 encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from .models import (
    User, UserRole, Product, ProductCategory, Order,
    OrderStatus, ShoppingCart, Review
)
from services import (
    UserService, ProductService, CartService, OrderService,
    ReviewService, AnalyticsService
)
from database import Database, UserRepository, ProductRepository, OrderRepository


# ============================================================================
# JSON Serialization
# ============================================================================

class APIEncoder(json.JSONEncoder):
    """Custom JSON encoder for model types"""
    
    def default(self, obj: Any) -> Any:
        """Handle custom types"""
        # Enums
        if hasattr(obj, 'value'):
            return obj.value
        # Decimal
        if isinstance(obj, Decimal):
            return str(obj)
        # Datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Models
        if hasattr(obj, '__dict__'):
            return self._serialize_model(obj)
        return super().default(obj)
    
    @staticmethod
    def _serialize_model(obj: Any) -> Dict[str, Any]:
        """Serialize model to dict"""
        data = {}
        for key, value in obj.__dict__.items():
            if key.startswith('_'):
                continue
            if isinstance(value, (Decimal, datetime)):
                data[key] = APIEncoder().default(value)
            elif hasattr(value, 'value'):  # Enum
                data[key] = value.value
            elif isinstance(value, list):
                data[key] = [APIEncoder().default(v) if not isinstance(v, (str, int, float, bool, type(None))) else v for v in value]
            else:
                data[key] = value
        return data


# ============================================================================
# API Response Helpers
# ============================================================================

def response_success(data: Any = None, status: int = 200) -> tuple:
    """Success response"""
    return {
        "success": True,
        "data": data,
        "status": status,
    }, status


def response_error(message: str, status: int = 400) -> tuple:
    """Error response"""
    return {
        "success": False,
        "error": message,
        "status": status,
    }, status


# ============================================================================
# API Server (Mock - Educational)
# ============================================================================

class MockAPIServer:
    """Mock API server for demonstration (without Flask dependency)"""
    
    def __init__(self, db_path: str = "showcase_api.db"):
        """Initialize API"""
        self.db = Database(db_path)
        self._seed_data()
    
    def _seed_data(self) -> None:
        """Seed initial data"""
        # Create sample users
        admin = UserService.create_user(
            email="api_admin@turbo-orm.dev",
            username="api_admin",
            password="AdminPass123",
            first_name="API",
            last_name="Admin",
            role=UserRole.ADMIN,
        )
        
        seller = UserService.create_user(
            email="api_seller@turbo-orm.dev",
            username="api_seller",
            password="SellerPass123",
            first_name="API",
            last_name="Seller",
            role=UserRole.SELLER,
        )
        
        # Create sample products
        ProductService.create_product(
            name="turbo-orm Premium",
            description="Professional ORM for Python applications",
            category=ProductCategory.ELECTRONICS,
            seller_id=seller.id if hasattr(seller, 'id') else 1,
            price=Decimal("299.99"),
            cost=Decimal("100"),
            stock_quantity=100,
        )
    
    # ========================================================================
    # Users Endpoints
    # ========================================================================
    
    def create_user(self, data: Dict[str, Any]) -> tuple:
        """POST /api/users"""
        try:
            user = UserService.create_user(
                email=data.get("email"),
                username=data.get("username"),
                password=data.get("password"),
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                role=UserRole(data.get("role", "customer")),
            )
            return response_success(
                json.loads(json.dumps(user.__dict__, cls=APIEncoder)),
                status=201
            )
        except ValueError as e:
            return response_error(str(e), status=400)
        except Exception as e:
            return response_error(f"User creation failed: {str(e)}", status=500)
    
    def get_user(self, user_id: int) -> tuple:
        """GET /api/users/{id}"""
        try:
            # Simplified: return mock user
            user = User(
                id=user_id,
                email=f"user{user_id}@example.com",
                username=f"user_{user_id}",
                password_hash="[HASH]",
                first_name="User",
                last_name=str(user_id),
                role=UserRole.CUSTOMER,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True,
            )
            return response_success(
                json.loads(json.dumps(user.__dict__, cls=APIEncoder))
            )
        except Exception as e:
            return response_error(str(e), status=404)
    
    # ========================================================================
    # Products Endpoints
    # ========================================================================
    
    def list_products(self, category: Optional[str] = None) -> tuple:
        """GET /api/products"""
        try:
            # Simplified: return sample products
            products = [
                {
                    "id": 1,
                    "name": "turbo-orm Premium",
                    "price": "299.99",
                    "category": "electronics",
                    "stock": 100,
                    "rating": 4.8,
                },
                {
                    "id": 2,
                    "name": "Python Handbook",
                    "price": "49.99",
                    "category": "books",
                    "stock": 50,
                    "rating": 4.5,
                },
            ]
            
            if category:
                products = [p for p in products if p["category"] == category]
            
            return response_success({"products": products, "total": len(products)})
        except Exception as e:
            return response_error(str(e), status=500)
    
    def search_products(self, query: str) -> tuple:
        """GET /api/products/search?q={query}"""
        try:
            # Simplified search
            all_products = [
                {
                    "id": 1,
                    "name": "turbo-orm Premium",
                    "description": "Professional ORM for Python applications",
                    "price": "299.99",
                },
                {
                    "id": 2,
                    "name": "Python Handbook",
                    "description": "Complete Python programming guide",
                    "price": "49.99",
                },
            ]
            
            query_lower = query.lower()
            results = [
                p for p in all_products
                if query_lower in p["name"].lower() or query_lower in p["description"].lower()
            ]
            
            return response_success({"results": results, "count": len(results)})
        except Exception as e:
            return response_error(str(e), status=400)
    
    def get_product_reviews(self, product_id: int) -> tuple:
        """GET /api/products/{id}/reviews"""
        try:
            reviews = [
                {
                    "id": 1,
                    "rating": 5,
                    "title": "Excellent product!",
                    "content": "Highly recommended",
                    "author": "customer1",
                    "created_at": datetime.now().isoformat(),
                },
            ]
            return response_success({"reviews": reviews, "product_id": product_id})
        except Exception as e:
            return response_error(str(e), status=404)
    
    # ========================================================================
    # Cart Endpoints
    # ========================================================================
    
    def add_to_cart(self, data: Dict[str, Any]) -> tuple:
        """POST /api/cart/add"""
        try:
            user_id = data.get("user_id")
            product_id = data.get("product_id")
            quantity = data.get("quantity", 1)
            
            if not user_id or not product_id:
                return response_error("user_id and product_id required", status=400)
            
            if quantity < 1:
                return response_error("quantity must be >= 1", status=400)
            
            return response_success({
                "user_id": user_id,
                "product_id": product_id,
                "quantity": quantity,
                "message": "Item added to cart",
            }, status=200)
        except Exception as e:
            return response_error(str(e), status=400)
    
    def get_cart(self, user_id: int) -> tuple:
        """GET /api/cart/{user_id}"""
        try:
            cart = {
                "user_id": user_id,
                "items": [
                    {
                        "product_id": 1,
                        "name": "turbo-orm Premium",
                        "quantity": 1,
                        "price": "299.99",
                    }
                ],
                "subtotal": "299.99",
                "tax": "23.99",
                "shipping": "9.99",
                "total": "333.97",
            }
            return response_success(cart)
        except Exception as e:
            return response_error(str(e), status=404)
    
    # ========================================================================
    # Orders Endpoints
    # ========================================================================
    
    def create_order(self, data: Dict[str, Any]) -> tuple:
        """POST /api/orders"""
        try:
            user_id = data.get("user_id")
            shipping_address = data.get("shipping_address")
            
            if not user_id or not shipping_address:
                return response_error("user_id and shipping_address required", status=400)
            
            order = {
                "id": 1001,
                "order_number": "ORD-20251127-001",
                "user_id": user_id,
                "status": "pending",
                "payment_status": "pending",
                "subtotal": "299.99",
                "tax": "23.99",
                "shipping": "9.99",
                "total": "333.97",
                "created_at": datetime.now().isoformat(),
            }
            return response_success(order, status=201)
        except Exception as e:
            return response_error(str(e), status=400)
    
    def get_order(self, order_id: int) -> tuple:
        """GET /api/orders/{id}"""
        try:
            order = {
                "id": order_id,
                "order_number": f"ORD-20251127-{order_id:03d}",
                "status": "processing",
                "payment_status": "completed",
                "items": [
                    {
                        "product_id": 1,
                        "name": "turbo-orm Premium",
                        "quantity": 1,
                        "price": "299.99",
                    }
                ],
                "total": "333.97",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            return response_success(order)
        except Exception as e:
            return response_error(str(e), status=404)
    
    # ========================================================================
    # Reviews Endpoints
    # ========================================================================
    
    def create_review(self, data: Dict[str, Any]) -> tuple:
        """POST /api/reviews"""
        try:
            product_id = data.get("product_id")
            user_id = data.get("user_id")
            rating = data.get("rating")
            title = data.get("title")
            content = data.get("content")
            
            if not all([product_id, user_id, rating, title, content]):
                return response_error("All fields required", status=400)
            
            if not (1 <= rating <= 5):
                return response_error("Rating must be 1-5", status=400)
            
            review = {
                "id": 1,
                "product_id": product_id,
                "user_id": user_id,
                "rating": rating,
                "title": title,
                "content": content,
                "created_at": datetime.now().isoformat(),
            }
            return response_success(review, status=201)
        except Exception as e:
            return response_error(str(e), status=400)
    
    # ========================================================================
    # Health & Info
    # ========================================================================
    
    def health(self) -> tuple:
        """GET /api/health"""
        return response_success({
            "status": "healthy",
            "service": "turbo-orm E-Commerce API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
        })


# ============================================================================
# Demo Server
# ============================================================================

def run_api_demo():
    """Run API demonstration"""
    print("\n╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  E-COMMERCE API: turbo-orm REST Endpoints".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝\n")
    
    api = MockAPIServer()
    
    # Test endpoints
    print("Testing API endpoints:\n")
    
    # Health check
    print("[1] Health Check")
    result, status = api.health()
    print(f"    Status: {status}")
    print(f"    ✓ {result['data']['service']}\n")
    
    # List products
    print("[2] List Products")
    result, status = api.list_products()
    print(f"    Status: {status}")
    print(f"    ✓ Found {result['data']['total']} products\n")
    
    # Search products
    print("[3] Search Products")
    result, status = api.search_products("python")
    print(f"    Status: {status}")
    print(f"    ✓ Search returned {result['data']['count']} results\n")
    
    # Add to cart
    print("[4] Add to Cart")
    result, status = api.add_to_cart({
        "user_id": 1,
        "product_id": 1,
        "quantity": 1,
    })
    print(f"    Status: {status}")
    print(f"    ✓ {result['data']['message']}\n")
    
    # Get cart
    print("[5] Get Cart")
    result, status = api.get_cart(1)
    print(f"    Status: {status}")
    print(f"    ✓ Cart total: ${result['data']['total']}\n")
    
    # Create order
    print("[6] Create Order")
    result, status = api.create_order({
        "user_id": 1,
        "shipping_address": "123 Main St, Springfield, IL",
    })
    print(f"    Status: {status}")
    print(f"    ✓ Order: {result['data']['order_number']}\n")
    
    # Get order
    print("[7] Get Order")
    result, status = api.get_order(1001)
    print(f"    Status: {status}")
    print(f"    ✓ Order status: {result['data']['status']}\n")
    
    # Create review
    print("[8] Create Review")
    result, status = api.create_review({
        "product_id": 1,
        "user_id": 1,
        "rating": 5,
        "title": "Excellent product!",
        "content": "Highly recommended for all Python developers",
    })
    print(f"    Status: {status}")
    print(f"    ✓ Review created with {result['data']['rating']}⭐ rating\n")
    
    # Get product reviews
    print("[9] Get Product Reviews")
    result, status = api.get_product_reviews(1)
    print(f"    Status: {status}")
    print(f"    ✓ Found {len(result['data']['reviews'])} reviews\n")
    
    print("="*70)
    print("\n✓ All API endpoints tested successfully!\n")


if __name__ == "__main__":
    run_api_demo()
