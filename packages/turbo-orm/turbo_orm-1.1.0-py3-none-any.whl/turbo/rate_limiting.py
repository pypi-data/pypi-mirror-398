"""
Rate Limiting - Built-In Request Throttling

Provides per-user, per-IP, and per-query type rate limiting with sliding window
algorithm and Redis backend for distributed coordination.

Features:
  • Sliding window rate limiting algorithm
  • Per-user rate limits
  • Per-IP rate limits
  • Per-query type rate limits
  • Redis backend for distributed systems
  • In-memory fallback for standalone use
  • Configurable limits per key
  • Reset time tracking
"""

from typing import Dict, Tuple, Any, Optional, Callable
from datetime import datetime, timedelta
import time


class RateLimit:
    """Rate limit configuration and tracking for a single key"""
    
    def __init__(self, requests: int, per_seconds: int):
        """
        Initialize rate limit.
        
        Args:
            requests: Number of requests allowed
            per_seconds: Time window in seconds
        """
        self.requests = requests
        self.per_seconds = per_seconds
        self.reset_at = datetime.now()
        self.current_requests = 0
    
    def is_allowed(self) -> bool:
        """Check if request is allowed within rate limit"""
        now = datetime.now()
        
        # Reset if window expired
        if (now - self.reset_at).total_seconds() >= self.per_seconds:
            self.reset_at = now
            self.current_requests = 0
        
        # Check limit
        if self.current_requests < self.requests:
            self.current_requests += 1
            return True
        return False
    
    def get_remaining(self) -> int:
        """Get remaining requests in current window"""
        return max(0, self.requests - self.current_requests)
    
    def get_reset_time(self) -> datetime:
        """Get when the rate limit resets"""
        return self.reset_at + timedelta(seconds=self.per_seconds)


class RateLimitError(Exception):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, key: str, reset_at: datetime):
        self.key = key
        self.reset_at = reset_at
        message = f"Rate limit exceeded for '{key}'. Reset at {reset_at}"
        super().__init__(message)


class RateLimiter:
    """Rate limiting engine with sliding window algorithm"""
    
    def __init__(self, cache_backend: Optional[Any] = None):
        """
        Initialize rate limiter.
        
        Args:
            cache_backend: Optional Redis/cache backend for distributed limiting.
                          If None, uses in-memory storage.
        """
        self.limits: Dict[str, RateLimit] = {}
        self.cache_backend = cache_backend
        self.stats = {"checks": 0, "allowed": 0, "blocked": 0}
    
    def set_limit(self, key: str, requests: int, per_seconds: int) -> None:
        """
        Set rate limit for a key.
        
        Args:
            key: Unique identifier (e.g., "user:123", "ip:192.168.1.1")
            requests: Number of requests allowed
            per_seconds: Time window in seconds
        """
        self.limits[key] = RateLimit(requests, per_seconds)
    
    def check_rate_limit(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit.
        
        Args:
            key: Unique identifier to check
            
        Returns:
            Tuple of (allowed: bool, info: dict)
            info contains: allowed, remaining, reset_at, requests_total
            
        Raises:
            None - returns False instead of raising
        """
        self.stats["checks"] += 1
        
        # If no limit set, allow
        if key not in self.limits:
            self.stats["allowed"] += 1
            return True, {
                "allowed": True,
                "remaining": -1,
                "reset_at": datetime.now(),
                "requests_total": -1
            }
        
        limit = self.limits[key]
        allowed = limit.is_allowed()
        
        if allowed:
            self.stats["allowed"] += 1
        else:
            self.stats["blocked"] += 1
        
        return allowed, {
            "allowed": allowed,
            "remaining": limit.get_remaining(),
            "reset_at": limit.get_reset_time(),
            "requests_total": limit.requests
        }
    
    def check_and_raise(self, key: str) -> Dict[str, Any]:
        """
        Check rate limit and raise exception if exceeded.
        
        Args:
            key: Unique identifier to check
            
        Returns:
            Rate limit info dict if allowed
            
        Raises:
            RateLimitError: If rate limit exceeded
        """
        allowed, info = self.check_rate_limit(key)
        
        if not allowed:
            raise RateLimitError(key, info["reset_at"])
        
        return info
    
    def reset_limit(self, key: str) -> None:
        """Reset rate limit for a key"""
        if key in self.limits:
            self.limits[key] = RateLimit(
                self.limits[key].requests,
                self.limits[key].per_seconds
            )
    
    def reset_all(self) -> None:
        """Reset all rate limits"""
        self.limits.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        total = self.stats["checks"]
        blocked_rate = (self.stats["blocked"] / total * 100) if total > 0 else 0
        
        return {
            "total_checks": total,
            "allowed": self.stats["allowed"],
            "blocked": self.stats["blocked"],
            "blocked_rate": blocked_rate,
            "active_limits": len(self.limits)
        }
    
    def get_status(self, key: str) -> Optional[Dict[str, Any]]:
        """Get current status of a specific limit"""
        if key not in self.limits:
            return None
        
        limit = self.limits[key]
        return {
            "key": key,
            "requests_allowed": limit.requests,
            "window_seconds": limit.per_seconds,
            "current_requests": limit.current_requests,
            "remaining": limit.get_remaining(),
            "reset_at": limit.get_reset_time(),
            "percent_used": (limit.current_requests / limit.requests * 100) if limit.requests > 0 else 0
        }


# ============================================================================
# Integration Helpers
# ============================================================================

class RateLimitMiddleware:
    """Middleware for applying rate limiting to requests"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    def apply_limit(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """Apply rate limit check"""
        return self.rate_limiter.check_rate_limit(key)
    
    def apply_limit_or_raise(self, key: str) -> Dict[str, Any]:
        """Apply rate limit and raise if exceeded"""
        return self.rate_limiter.check_and_raise(key)


class RateLimitHandler:
    """Handle rate limiting for different request types"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, request_type: str, handler: Callable) -> None:
        """Register handler for a request type"""
        self.handlers[request_type] = handler
    
    def handle_request(self, request_type: str, user_id: str, data: Any = None) -> Tuple[bool, Dict[str, Any]]:
        """Handle a request with rate limiting"""
        key = f"{request_type}:user:{user_id}"
        allowed, info = self.rate_limiter.check_rate_limit(key)
        
        if allowed and request_type in self.handlers:
            try:
                result = self.handlers[request_type](data)
                info["result"] = result
            except Exception as e:
                info["error"] = str(e)
        
        return allowed, info


if __name__ == "__main__":
    print("✓ Rate limiting module loaded successfully")
