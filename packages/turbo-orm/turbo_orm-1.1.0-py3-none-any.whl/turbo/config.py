"""
Type-safe configuration system for Turbo ORM

Provides environment-aware configuration with validation.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
import os


class ORMConfig(BaseModel):
    """Type-safe configuration for Turbo ORM"""
    
    # Database
    database_path: str = Field(..., description="Path to SQLite database")
    pool_size: int = Field(default=5, ge=0, le=50, description="Connection pool size")
    
    # Performance
    cache_ttl: int = Field(default=300, ge=60, le=86400, description="Cache TTL in seconds")
    slow_query_threshold: float = Field(default=1.0, gt=0, description="Slow query threshold in seconds")
    
    # Features
    enable_query_logging: bool = Field(default=True, description="Enable query logging")
    connection_timeout: int = Field(default=30, ge=5, le=300, description="Connection timeout")
    
    # Security
    encryption_key: Optional[str] = Field(default=None, description="Encryption key for EncryptedField")
    
    class Config:
        env_prefix = "TURBO_ORM_"
    
    @classmethod
    def from_env(cls):
        """Load from environment variables"""
        return cls(
            database_path=os.getenv("TURBO_ORM_DATABASE_PATH", "app.db"),
            pool_size=int(os.getenv("TURBO_ORM_POOL_SIZE", "5")),
            cache_ttl=int(os.getenv("TURBO_ORM_CACHE_TTL", "300")),
            slow_query_threshold=float(os.getenv("TURBO_ORM_SLOW_QUERY_THRESHOLD", "1.0")),
            enable_query_logging=os.getenv("TURBO_ORM_ENABLE_QUERY_LOGGING", "true").lower() == "true",
            connection_timeout=int(os.getenv("TURBO_ORM_CONNECTION_TIMEOUT", "30")),
            encryption_key=os.getenv("TURBO_ORM_ENCRYPTION_KEY")
        )
    
    @classmethod
    def from_file(cls, path: str):
        """Load from JSON file"""
        import json
        with open(path) as f:
            data = json.load(f)
        return cls(**data)
    
    def to_env(self) -> None:
        """Export current config to environment variables"""
        os.environ["TURBO_ORM_DATABASE_PATH"] = self.database_path
        os.environ["TURBO_ORM_POOL_SIZE"] = str(self.pool_size)
        os.environ["TURBO_ORM_CACHE_TTL"] = str(self.cache_ttl)
        os.environ["TURBO_ORM_SLOW_QUERY_THRESHOLD"] = str(self.slow_query_threshold)
        os.environ["TURBO_ORM_ENABLE_QUERY_LOGGING"] = str(self.enable_query_logging).lower()
        os.environ["TURBO_ORM_CONNECTION_TIMEOUT"] = str(self.connection_timeout)
        if self.encryption_key:
            os.environ["TURBO_ORM_ENCRYPTION_KEY"] = self.encryption_key
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return self.dict()


def create_database_from_config(config):
    """Create database instance from config"""
    from turbo.database import Database
    
    return Database(
        path=config.database_path,
        pool_size=config.pool_size,
        slow_query_threshold=config.slow_query_threshold
    )