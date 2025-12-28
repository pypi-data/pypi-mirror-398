"""
Circuit Breaker - Prevent Cascading Failures

Automatically breaks circuit when error threshold is exceeded.
Prevents cascading failures in production systems.
"""

import time
import functools
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit breaker tripped
    HALF_OPEN = "half_open"  # Testing if system recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open"""

    pass


class CircuitBreaker:
    """Circuit breaker implementation"""

    def __init__(self, threshold=5, timeout=60):
        self.threshold = threshold  # Failures before opening
        self.timeout = timeout  # Seconds before trying half-open
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        # Check if we should try recovery
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                print(f"   🔄 Circuit half-open - testing recovery...")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError(f"Circuit breaker OPEN - too many failures")

        try:
            result = func(*args, **kwargs)

            # Success - reset if we were testing
            if self.state == CircuitState.HALF_OPEN:
                print(f"   ✓ Circuit recovered - closing")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            # Trip breaker if threshold exceeded
            if self.failure_count >= self.threshold:
                self.state = CircuitState.OPEN
                print(f"   ⚠️ Circuit breaker OPENED - {self.failure_count} failures")

            raise


def circuit_breaker(threshold=5, timeout=60):
    """Decorator for circuit breaker protection"""
    breaker = CircuitBreaker(threshold, timeout)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        wrapper._circuit_breaker = breaker
        return wrapper

    return decorator


# Example usage in database operations
def add_circuit_breaker_to_database():
    """Add circuit breaker protection to critical DB operations"""
    from .database import Database

    original_execute = Database.execute

    def execute_with_breaker(self, sql, params=None):
        """Execute with circuit breaker protection"""
        if not hasattr(self, "_circuit_breaker"):
            self._circuit_breaker = CircuitBreaker(threshold=10, timeout=30)

        return self._circuit_breaker.call(original_execute, self, sql, params)

    # Optionally enable
    Database.enable_circuit_breaker = lambda self: setattr(
        self.__class__, "execute", execute_with_breaker
    )
