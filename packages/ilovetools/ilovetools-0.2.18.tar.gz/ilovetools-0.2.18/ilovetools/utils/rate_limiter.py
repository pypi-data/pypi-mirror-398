"""
Advanced Rate Limiter
Multiple rate limiting algorithms for API throttling
"""

import time
from typing import Optional, Dict, List, Callable
from collections import deque
from threading import Lock

__all__ = [
    'TokenBucketLimiter',
    'LeakyBucketLimiter',
    'FixedWindowLimiter',
    'SlidingWindowLimiter',
    'create_rate_limiter',
    'RateLimitDecorator',
    'MultiTierLimiter',
    'AdaptiveRateLimiter',
]


class TokenBucketLimiter:
    """
    Token Bucket Rate Limiter.
    
    Allows bursts while maintaining average rate.
    
    Examples:
        >>> from ilovetools.utils import TokenBucketLimiter
        
        >>> limiter = TokenBucketLimiter(rate=10, capacity=20)
        >>> if limiter.allow():
        ...     # Make API call
        ...     pass
    """
    
    def __init__(
        self,
        rate: float,
        capacity: int,
        initial_tokens: Optional[int] = None
    ):
        """
        Initialize token bucket limiter.
        
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
            initial_tokens: Starting tokens (default: capacity)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_update = time.time()
        self.lock = Lock()
    
    def allow(self, tokens: int = 1) -> bool:
        """
        Check if request is allowed.
        
        Args:
            tokens: Tokens required for request
        
        Returns:
            bool: True if allowed
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            # Check if enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def wait(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait until request is allowed.
        
        Args:
            tokens: Tokens required
            timeout: Maximum wait time (None = infinite)
        
        Returns:
            bool: True if allowed, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.allow(tokens):
                return True
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            # Sleep briefly
            time.sleep(0.01)
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get estimated wait time for tokens.
        
        Args:
            tokens: Tokens required
        
        Returns:
            float: Wait time in seconds
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Calculate current tokens
            current_tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            
            # Calculate wait time
            if current_tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - current_tokens
            return tokens_needed / self.rate
    
    def reset(self):
        """Reset limiter to initial state."""
        with self.lock:
            self.tokens = self.capacity
            self.last_update = time.time()


class LeakyBucketLimiter:
    """
    Leaky Bucket Rate Limiter.
    
    Smooths out bursts by processing at constant rate.
    
    Examples:
        >>> from ilovetools.utils import LeakyBucketLimiter
        
        >>> limiter = LeakyBucketLimiter(rate=5, capacity=10)
        >>> if limiter.allow():
        ...     # Make API call
        ...     pass
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize leaky bucket limiter.
        
        Args:
            rate: Leak rate (requests per second)
            capacity: Bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.queue = deque()
        self.lock = Lock()
    
    def allow(self) -> bool:
        """
        Check if request is allowed.
        
        Returns:
            bool: True if allowed
        """
        with self.lock:
            now = time.time()
            
            # Remove leaked requests
            while self.queue and now - self.queue[0] >= 1.0 / self.rate:
                self.queue.popleft()
            
            # Check capacity
            if len(self.queue) < self.capacity:
                self.queue.append(now)
                return True
            
            return False
    
    def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until request is allowed.
        
        Args:
            timeout: Maximum wait time
        
        Returns:
            bool: True if allowed, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.allow():
                return True
            
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            time.sleep(0.01)
    
    def reset(self):
        """Reset limiter."""
        with self.lock:
            self.queue.clear()


class FixedWindowLimiter:
    """
    Fixed Window Rate Limiter.
    
    Limits requests per fixed time window.
    
    Examples:
        >>> from ilovetools.utils import FixedWindowLimiter
        
        >>> limiter = FixedWindowLimiter(max_requests=100, window_size=60)
        >>> if limiter.allow():
        ...     # Make API call
        ...     pass
    """
    
    def __init__(self, max_requests: int, window_size: float):
        """
        Initialize fixed window limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_size: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.window_start = time.time()
        self.request_count = 0
        self.lock = Lock()
    
    def allow(self) -> bool:
        """
        Check if request is allowed.
        
        Returns:
            bool: True if allowed
        """
        with self.lock:
            now = time.time()
            
            # Check if new window
            if now - self.window_start >= self.window_size:
                self.window_start = now
                self.request_count = 0
            
            # Check limit
            if self.request_count < self.max_requests:
                self.request_count += 1
                return True
            
            return False
    
    def get_remaining(self) -> int:
        """
        Get remaining requests in current window.
        
        Returns:
            int: Remaining requests
        """
        with self.lock:
            now = time.time()
            
            if now - self.window_start >= self.window_size:
                return self.max_requests
            
            return max(0, self.max_requests - self.request_count)
    
    def reset(self):
        """Reset limiter."""
        with self.lock:
            self.window_start = time.time()
            self.request_count = 0


class SlidingWindowLimiter:
    """
    Sliding Window Rate Limiter.
    
    More accurate than fixed window, prevents boundary issues.
    
    Examples:
        >>> from ilovetools.utils import SlidingWindowLimiter
        
        >>> limiter = SlidingWindowLimiter(max_requests=100, window_size=60)
        >>> if limiter.allow():
        ...     # Make API call
        ...     pass
    """
    
    def __init__(self, max_requests: int, window_size: float):
        """
        Initialize sliding window limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_size: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()
        self.lock = Lock()
    
    def allow(self) -> bool:
        """
        Check if request is allowed.
        
        Returns:
            bool: True if allowed
        """
        with self.lock:
            now = time.time()
            
            # Remove old requests
            while self.requests and now - self.requests[0] >= self.window_size:
                self.requests.popleft()
            
            # Check limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    def get_remaining(self) -> int:
        """
        Get remaining requests in current window.
        
        Returns:
            int: Remaining requests
        """
        with self.lock:
            now = time.time()
            
            # Remove old requests
            while self.requests and now - self.requests[0] >= self.window_size:
                self.requests.popleft()
            
            return max(0, self.max_requests - len(self.requests))
    
    def reset(self):
        """Reset limiter."""
        with self.lock:
            self.requests.clear()


class MultiTierLimiter:
    """
    Multi-tier rate limiter with different limits.
    
    Examples:
        >>> from ilovetools.utils import MultiTierLimiter
        
        >>> limiter = MultiTierLimiter({
        ...     'second': (10, 1),
        ...     'minute': (100, 60),
        ...     'hour': (1000, 3600)
        ... })
        >>> if limiter.allow():
        ...     # Make API call
        ...     pass
    """
    
    def __init__(self, tiers: Dict[str, tuple]):
        """
        Initialize multi-tier limiter.
        
        Args:
            tiers: Dict of tier_name -> (max_requests, window_size)
        """
        self.limiters = {}
        for name, (max_requests, window_size) in tiers.items():
            self.limiters[name] = SlidingWindowLimiter(max_requests, window_size)
    
    def allow(self) -> bool:
        """
        Check if request is allowed in all tiers.
        
        Returns:
            bool: True if allowed
        """
        # Check all tiers
        for limiter in self.limiters.values():
            if not limiter.allow():
                return False
        return True
    
    def get_remaining(self) -> Dict[str, int]:
        """
        Get remaining requests for each tier.
        
        Returns:
            dict: Remaining requests per tier
        """
        return {
            name: limiter.get_remaining()
            for name, limiter in self.limiters.items()
        }
    
    def reset(self):
        """Reset all tiers."""
        for limiter in self.limiters.values():
            limiter.reset()


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on success/failure.
    
    Examples:
        >>> from ilovetools.utils import AdaptiveRateLimiter
        
        >>> limiter = AdaptiveRateLimiter(initial_rate=10)
        >>> if limiter.allow():
        ...     try:
        ...         # Make API call
        ...         limiter.record_success()
        ...     except:
        ...         limiter.record_failure()
    """
    
    def __init__(
        self,
        initial_rate: float,
        min_rate: float = 1.0,
        max_rate: float = 100.0,
        increase_factor: float = 1.1,
        decrease_factor: float = 0.5
    ):
        """
        Initialize adaptive limiter.
        
        Args:
            initial_rate: Starting rate
            min_rate: Minimum rate
            max_rate: Maximum rate
            increase_factor: Rate increase on success
            decrease_factor: Rate decrease on failure
        """
        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.increase_factor = increase_factor
        self.decrease_factor = decrease_factor
        self.limiter = TokenBucketLimiter(initial_rate, int(initial_rate * 2))
        self.lock = Lock()
    
    def allow(self) -> bool:
        """Check if request is allowed."""
        return self.limiter.allow()
    
    def record_success(self):
        """Record successful request."""
        with self.lock:
            # Increase rate
            new_rate = min(self.max_rate, self.current_rate * self.increase_factor)
            if new_rate != self.current_rate:
                self.current_rate = new_rate
                self.limiter = TokenBucketLimiter(new_rate, int(new_rate * 2))
    
    def record_failure(self):
        """Record failed request."""
        with self.lock:
            # Decrease rate
            new_rate = max(self.min_rate, self.current_rate * self.decrease_factor)
            if new_rate != self.current_rate:
                self.current_rate = new_rate
                self.limiter = TokenBucketLimiter(new_rate, int(new_rate * 2))
    
    def get_current_rate(self) -> float:
        """Get current rate."""
        return self.current_rate


def create_rate_limiter(
    algorithm: str = 'token_bucket',
    **kwargs
):
    """
    Create rate limiter with specified algorithm.
    
    Args:
        algorithm: Algorithm type (token_bucket, leaky_bucket, fixed_window, sliding_window)
        **kwargs: Algorithm-specific parameters
    
    Returns:
        Rate limiter instance
    
    Examples:
        >>> from ilovetools.utils import create_rate_limiter
        
        >>> limiter = create_rate_limiter('token_bucket', rate=10, capacity=20)
        >>> if limiter.allow():
        ...     # Make API call
        ...     pass
    """
    algorithms = {
        'token_bucket': TokenBucketLimiter,
        'leaky_bucket': LeakyBucketLimiter,
        'fixed_window': FixedWindowLimiter,
        'sliding_window': SlidingWindowLimiter,
    }
    
    if algorithm not in algorithms:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    return algorithms[algorithm](**kwargs)


class RateLimitDecorator:
    """
    Decorator for rate limiting functions.
    
    Examples:
        >>> from ilovetools.utils import RateLimitDecorator
        
        >>> @RateLimitDecorator(rate=5, capacity=10)
        ... def api_call():
        ...     # Make API call
        ...     pass
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize decorator.
        
        Args:
            rate: Requests per second
            capacity: Burst capacity
        """
        self.limiter = TokenBucketLimiter(rate, capacity)
    
    def __call__(self, func: Callable):
        """Wrap function with rate limiting."""
        def wrapper(*args, **kwargs):
            self.limiter.wait()
            return func(*args, **kwargs)
        return wrapper
