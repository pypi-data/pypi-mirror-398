from .database import Database
from .model import Model
from .fields import (
    IntegerField,
    TextField,
    FloatField,
    ForeignKey,
    BooleanField,
    DateTimeField,
    JSONField,
    ManyToManyField,
    EncryptedField,
)
from .exceptions import ModelError, ModelSaveError, QueryError, DatabaseHealthError
from .config import ORMConfig, create_database_from_config
from .health import DatabaseHealth, monitor_database, add_health_check_to_database
from .history import HistoryModel
from .search import SearchableModel
from .soft_delete import SoftDeleteModel
from .query_builder import QueryBuilder
from .pagination import Paginator
from .decorators import scope
from .seeder import Seeder, SeederRegistry, seeder
from .multi_db import ModelDatabaseProxy
from .replay import QueryRecorder, ReplayEngine, add_replay_to_database
from .blueprint import Blueprint, blueprint
from .dashboard import Dashboard, add_dashboard_to_database
from .diff import DataDiff, DiffResult, add_diff_to_model
from .contracts import (
    ensure,
    ContractViolation,
    add_contracts_to_model,
    days_ago,
    is_valid_email,
)
from .quantum import QuantumQuery, QuantumResult, add_quantum_to_model
from .optimizer import QueryOptimizer, add_optimizer_to_database
from .nlquery import NaturalLanguageQuery, add_nlq_to_model
from .anomaly import AnomalyDetector, add_anomaly_to_model
from .circuit_breaker import (
    CircuitBreaker,
    circuit_breaker,
    add_circuit_breaker_to_database,
)
from .autoscale import AutoScalingPool, add_autoscaling_to_database
from .quality import DataQualityScorer, add_quality_to_model
from .graphql_gen import GraphQLGenerator, create_graphql_api
from .rest_gen import RESTGenerator, create_rest_api
from .multitenancy import MultiTenantModel, TenantManager, tenant_context, TenantContext
from .rbac import (
    RBACModel,
    Permission,
    FieldPermission,
    set_field_permission,
    get_accessible_fields,
)
from .audit import AuditLog, AuditedModel, audit_context, AuditContext
from .performance import QueryCache, PreparedStatementPool, add_caching_to_database
from .optimized import OptimizedModel, enable_turbo_mode
from .migrations import MigrationManager
from .vector import VectorField, add_vector_search_to_model
from .events import EventBus, add_events_to_model
from .cache_redis import add_redis_caching_to_database
from .cdc import add_cdc_to_model, get_cdc_stream, CDCStream, enable_cdc
from .rules import add_rules_to_model, RuleViolation
from .lazy import add_lazy_loading_to_model

# Advanced Features Imports
from .advanced_features import (
    QueryReplay,
    ModelBlueprint,
    LiveDashboard,
    ModelContract,
    QuantumQuery,
)
from .testing_suites import (
    IntegrationTestSuite,
    PerformanceRegressionTestSuite,
    SecurityPenetrationTestSuite,
    StressLoadTestSuite,
    E2ETestSuite,
)
from .profiling import (
    HotPathProfiler,
    QueryOptimizer as AdvancedQueryOptimizer,
    CacheLayerOptimizer,
    DatabaseOperationOptimizer,
    PerformanceReportGenerator,
)

# Initialize extensions
add_replay_to_database()
add_dashboard_to_database()
add_diff_to_model()
add_contracts_to_model()
add_quantum_to_model()
add_optimizer_to_database()
add_nlq_to_model()
add_anomaly_to_model()
add_circuit_breaker_to_database()
add_autoscaling_to_database()
add_quality_to_model()
add_vector_search_to_model()
add_events_to_model()
add_cdc_to_model()
add_rules_to_model()
add_lazy_loading_to_model()

try:
    from .async_support import AsyncDatabase, AsyncModel
    from .async_optimized import AsyncOptimizedModel
except ImportError:
    AsyncDatabase = None
    AsyncModel = None
    AsyncOptimizedModel = None
