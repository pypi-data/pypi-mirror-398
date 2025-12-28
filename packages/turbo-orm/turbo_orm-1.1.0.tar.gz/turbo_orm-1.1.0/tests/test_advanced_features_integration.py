"""
Integration Tests - Advanced Features with Core ORM

Tests the integration of advanced features with the core Turbo ORM functionality.
Ensures that new features work seamlessly with existing models and operations.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from turbo.database import Database
from turbo.model import Model
from turbo.fields import IntegerField, TextField, FloatField
from turbo.advanced_features import QueryReplay, ModelBlueprint, LiveDashboard, ModelContract
from turbo.profiling import HotPathProfiler, QueryOptimizer, CacheLayerOptimizer


# ============================================================================
# TEST MODELS
# ============================================================================

class User(Model):
    """Test User model"""
    name = TextField()
    email = TextField()
    age = IntegerField()


class Product(Model):
    """Test Product model"""
    name = TextField()
    description = TextField()
    price = FloatField()
    stock = IntegerField()


class OrderRecord(Model):
    """Test Order model"""
    user_id = IntegerField()
    product_id = IntegerField()
    quantity = IntegerField()
    total = FloatField()


# ============================================================================
# QUERY REPLAY INTEGRATION TESTS
# ============================================================================

class QueryReplayIntegrationTests(unittest.TestCase):
    """Test QueryReplay integration with core ORM"""

    def setUp(self):
        self.db = Database(":memory:")
        self.db.connect()
        User.create_table(self.db)
        Product.create_table(self.db)
        self.replay = QueryReplay()

    def tearDown(self):
        self.db.close()

    def test_replay_user_creation_workflow(self):
        """Test replay of user creation workflow"""
        self.replay.start_recording("user_workflow")
        
        # Create users
        user1 = User(name="Alice", email="alice@example.com", age=25)
        user1.save(self.db)
        
        user2 = User(name="Bob", email="bob@example.com", age=30)
        user2.save(self.db)
        
        self.replay.record_operation("CREATE_USER", {"name": "Alice"})
        self.replay.record_operation("CREATE_USER", {"name": "Bob"})
        
        self.replay.stop_recording()
        
        # Verify recording
        stats = self.replay.get_session_stats("user_workflow")
        self.assertGreater(stats["total_operations"], 0)
        
        # Verify users exist
        users = User.all(self.db)
        self.assertEqual(len(users), 2)

    def test_replay_product_operations(self):
        """Test replay of product operations"""
        self.replay.start_recording("product_ops")
        
        # Create products
        prod1 = Product(name="Laptop", description="High-end laptop", price=999.99, stock=5)
        prod1.save(self.db)
        
        prod2 = Product(name="Mouse", description="Wireless mouse", price=29.99, stock=50)
        prod2.save(self.db)
        
        self.replay.stop_recording()
        
        # Verify
        products = Product.all(self.db)
        self.assertEqual(len(products), 2)


# ============================================================================
# MODEL BLUEPRINT INTEGRATION TESTS
# ============================================================================

class ModelBlueprintIntegrationTests(unittest.TestCase):
    """Test ModelBlueprint integration with core ORM"""

    def setUp(self):
        self.db = Database(":memory:")
        self.db.connect()
        User.create_table(self.db)
        Product.create_table(self.db)

    def tearDown(self):
        self.db.close()

    def test_blueprint_generate_ecommerce_products(self):
        """Test generating e-commerce product data"""
        blueprint = ModelBlueprint(Product, style="e-commerce")
        records = blueprint.generate_bulk(5)
        
        # Verify generation
        self.assertEqual(len(records), 5)
        
        # Verify record structure
        for record in records:
            self.assertIn("name", record)
            self.assertIn("price", record)

    def test_blueprint_bulk_insert_integration(self):
        """Test inserting blueprint-generated data"""
        blueprint = ModelBlueprint(Product, style="e-commerce")
        records = blueprint.generate_bulk(3)
        
        # Insert records
        for record in records:
            product = Product(**record)
            product.save(self.db)
        
        # Verify inserted
        products = Product.all(self.db)
        self.assertEqual(len(products), 3)

    def test_blueprint_social_style(self):
        """Test social network style data generation"""
        blueprint = ModelBlueprint(User, style="social")
        records = blueprint.generate_bulk(3)
        
        self.assertEqual(len(records), 3)


# ============================================================================
# LIVE DASHBOARD INTEGRATION TESTS
# ============================================================================

class LiveDashboardIntegrationTests(unittest.TestCase):
    """Test LiveDashboard integration with core ORM"""

    def setUp(self):
        self.db = Database(":memory:")
        self.db.connect()
        User.create_table(self.db)
        self.dashboard = LiveDashboard()

    def tearDown(self):
        self.db.close()

    def test_dashboard_tracks_queries(self):
        """Test dashboard tracks query operations"""
        self.dashboard.record_query("SELECT", 0.050)
        self.dashboard.record_query("SELECT", 0.045)
        self.dashboard.record_save()
        
        # Get status
        status = self.dashboard.get_status()
        
        self.assertEqual(status["total_queries"], 2)
        self.assertEqual(status["total_saves"], 1)

    def test_dashboard_cache_tracking(self):
        """Test dashboard tracks cache metrics"""
        self.dashboard.record_cache_hit()
        self.dashboard.record_cache_hit()
        self.dashboard.record_cache_miss()
        
        status = self.dashboard.get_status()
        
        self.assertEqual(status["cache_hits"], 2)
        self.assertEqual(status["cache_misses"], 1)


# ============================================================================
# MODEL CONTRACT INTEGRATION TESTS
# ============================================================================

class ModelContractIntegrationTests(unittest.TestCase):
    """Test ModelContract integration with core ORM"""

    def setUp(self):
        self.db = Database(":memory:")
        self.db.connect()
        User.create_table(self.db)

    def tearDown(self):
        self.db.close()

    def test_contract_validation(self):
        """Test contract validation"""
        contract = ModelContract()
        contract.add_rule("name_valid", lambda obj: len(obj.name.strip()) > 0)
        
        # Valid user
        valid_user = User(name="David", email="david@example.com", age=28)
        self.assertTrue(contract.validate(valid_user))
        valid_user.save(self.db)
        
        # Invalid user
        invalid_user = User(name="", email="invalid@example.com", age=200)
        self.assertFalse(contract.validate(invalid_user))


# ============================================================================
# PROFILING INTEGRATION TESTS
# ============================================================================

class ProfilingIntegrationTests(unittest.TestCase):
    """Test profiling tools integration with core ORM"""

    def setUp(self):
        self.db = Database(":memory:")
        self.db.connect()
        User.create_table(self.db)
        Product.create_table(self.db)

    def tearDown(self):
        self.db.close()

    def test_profiler_with_user_operations(self):
        """Test profiler with user creation"""
        profiler = HotPathProfiler()
        
        def create_users():
            for i in range(5):
                user = User(name=f"User{i}", email=f"user{i}@example.com", age=20+i)
                user.save(self.db)
        
        time_ms = profiler.measure_execution_time("create_users", create_users)
        
        # Should complete in reasonable time
        self.assertGreater(time_ms, 0)

    def test_query_optimizer_analysis(self):
        """Test query optimizer"""
        optimizer = QueryOptimizer()
        optimizer.analyze_query_pattern("SELECT * FROM users")
        recommendations = optimizer.recommend_optimizations("SELECT * FROM users")
        self.assertIsNotNone(recommendations)

    def test_cache_layer_optimizer(self):
        """Test cache layer analysis"""
        from turbo.profiling import CacheLayerOptimizer as CacheOpt
        
        optimizer = CacheOpt()
        
        for _ in range(7):
            optimizer.record_hit()
        for _ in range(3):
            optimizer.record_miss()
        
        hit_rate = optimizer.get_hit_rate()
        self.assertEqual(hit_rate, 70.0)


# ============================================================================
# END-TO-END INTEGRATION TESTS
# ============================================================================

class EndToEndIntegrationTests(unittest.TestCase):
    """Test advanced features working together in realistic scenarios"""

    def setUp(self):
        self.db = Database(":memory:")
        self.db.connect()
        User.create_table(self.db)
        Product.create_table(self.db)
        OrderRecord.create_table(self.db)

    def tearDown(self):
        self.db.close()

    def test_full_ecommerce_workflow(self):
        """Test complete e-commerce workflow"""
        blueprint_users = ModelBlueprint(User, style="social")
        blueprint_products = ModelBlueprint(Product, style="e-commerce")
        dashboard = LiveDashboard()
        
        # Generate and create users
        user_records = blueprint_users.generate_bulk(2)
        for record in user_records:
            try:
                user = User(**{k: v for k, v in record.items() if k in ["name", "email", "age"]})
                user.save(self.db)
                dashboard.record_save()
            except:
                pass
        
        # Generate and create products
        product_records = blueprint_products.generate_bulk(3)
        for record in product_records:
            try:
                product = Product(**{k: v for k, v in record.items() if k in ["name", "description", "price", "stock"]})
                product.save(self.db)
                dashboard.record_save()
            except:
                pass
        
        # Verify
        users = User.all(self.db)
        products = Product.all(self.db)
        
        self.assertGreater(len(users), 0)
        self.assertGreater(len(products), 0)
        
        status = dashboard.get_status()
        self.assertGreater(status["total_saves"], 0)

    def test_data_validation_workflow(self):
        """Test workflow with validation"""
        contract = ModelContract()
        contract.add_rule("valid", lambda obj: len(obj.name.strip()) > 0)
        
        # Create valid users
        valid_users = [
            User(name="User1", email="user1@example.com", age=25),
            User(name="User2", email="user2@example.com", age=30),
        ]
        
        for user in valid_users:
            if contract.validate(user):
                user.save(self.db)
        
        # Verify
        saved_users = User.all(self.db)
        self.assertEqual(len(saved_users), 2)


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    if result.testsRun > 0:
        print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70)
    
    sys.exit(0 if result.wasSuccessful() else 1)
