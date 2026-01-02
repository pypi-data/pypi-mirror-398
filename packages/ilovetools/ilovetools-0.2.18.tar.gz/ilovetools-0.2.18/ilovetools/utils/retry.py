"""
Retry Mechanism
Automatic retry with exponential backoff and jitter
"""

import time
import random
from typing import Callable, Optional, Tuple, Type, List
from functools import wraps

__all__ = [
    'retry',
    'exponential_backoff',
    'linear_backoff',
    'constant_backoff',
    'RetryStrategy',
    'CircuitBreaker',
    'retry_with_circuit_breaker',
]


class RetryStrategy:
    """
    Base retry strategy.
    
    Examples:
        >>> from ilovetools.utils import RetryStrategy
        
        >>> strategy = RetryStrategy(max_attempts=3)
        >>> for attempt in strategy:
        ...     print(f'Attempt {attempt}')
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True
    ):
        """
        Initialize retry strategy.
        
        Args:
            max_attempts: Maximum retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Add random jitter
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.attempt = 0
    
    def __iter__(self):
        """Iterator for retry attempts."""
        self.attempt = 0
        return self
    
    def __next__(self):
        """Get next retry attempt."""
        if self.attempt >= self.max_attempts:
            raise StopIteration
        
        self.attempt += 1
        return self.attempt
    
    def get_delay(self, attempt: int) -> float:
        """
        Get delay for attempt.
        
        Args:
            attempt: Attempt number
        
        Returns:
            float: Delay in seconds
        """
        delay = self.initial_delay
        
        if self.jitter:
            delay *= (0.5 + random.random())
        
        return min(delay, self.max_delay)
    
    def wait(self, attempt: int):
        """Wait before retry."""
        delay = self.get_delay(attempt)
        time.sleep(delay)


def exponential_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0,
    jitter: bool = True
) -> RetryStrategy:
    """
    Create exponential backoff strategy.
    
    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        multiplier: Delay multiplier
        jitter: Add random jitter
    
    Returns:
        RetryStrategy: Exponential backoff strategy
    
    Examples:
        >>> from ilovetools.utils import exponential_backoff
        
        >>> strategy = exponential_backoff(max_attempts=5, initial_delay=1.0)
        >>> for attempt in strategy:
        ...     print(f'Attempt {attempt}')
        ...     strategy.wait(attempt)
    """
    class ExponentialBackoff(RetryStrategy):
        def get_delay(self, attempt: int) -> float:
            delay = self.initial_delay * (multiplier ** (attempt - 1))
            
            if self.jitter:
                delay *= (0.5 + random.random())
            
            return min(delay, self.max_delay)
    
    return ExponentialBackoff(max_attempts, initial_delay, max_delay, jitter)


def linear_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    increment: float = 1.0,
    jitter: bool = True
) -> RetryStrategy:
    """
    Create linear backoff strategy.
    
    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        increment: Delay increment
        jitter: Add random jitter
    
    Returns:
        RetryStrategy: Linear backoff strategy
    
    Examples:
        >>> from ilovetools.utils import linear_backoff
        
        >>> strategy = linear_backoff(max_attempts=5, increment=2.0)
        >>> for attempt in strategy:
        ...     print(f'Attempt {attempt}')
        ...     strategy.wait(attempt)
    """
    class LinearBackoff(RetryStrategy):
        def get_delay(self, attempt: int) -> float:
            delay = self.initial_delay + (increment * (attempt - 1))
            
            if self.jitter:
                delay *= (0.5 + random.random())
            
            return min(delay, self.max_delay)
    
    return LinearBackoff(max_attempts, initial_delay, max_delay, jitter)


def constant_backoff(
    max_attempts: int = 3,
    delay: float = 1.0,
    jitter: bool = True
) -> RetryStrategy:
    """
    Create constant backoff strategy.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Constant delay in seconds
        jitter: Add random jitter
    
    Returns:
        RetryStrategy: Constant backoff strategy
    
    Examples:
        >>> from ilovetools.utils import constant_backoff
        
        >>> strategy = constant_backoff(max_attempts=5, delay=2.0)
        >>> for attempt in strategy:
        ...     print(f'Attempt {attempt}')
        ...     strategy.wait(attempt)
    """
    class ConstantBackoff(RetryStrategy):
        def get_delay(self, attempt: int) -> float:
            delay_val = delay
            
            if self.jitter:
                delay_val *= (0.5 + random.random())
            
            return delay_val
    
    return ConstantBackoff(max_attempts, delay, delay, jitter)


def retry(
    max_attempts: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff_strategy: Optional[RetryStrategy] = None,
    on_retry: Optional[Callable] = None,
    on_failure: Optional[Callable] = None
):
    """
    Retry decorator with configurable backoff.
    
    Args:
        max_attempts: Maximum retry attempts
        exceptions: Exceptions to catch
        backoff_strategy: Backoff strategy
        on_retry: Callback on retry
        on_failure: Callback on final failure
    
    Examples:
        >>> from ilovetools.utils import retry
        
        >>> @retry(max_attempts=3)
        ... def unstable_function():
        ...     # May fail randomly
        ...     if random.random() < 0.5:
        ...         raise ValueError('Random failure')
        ...     return 'Success'
    """
    if backoff_strategy is None:
        backoff_strategy = exponential_backoff(max_attempts=max_attempts)
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in backoff_strategy:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Call retry callback
                    if on_retry:
                        on_retry(attempt, e)
                    
                    # Wait before retry (except on last attempt)
                    if attempt < backoff_strategy.max_attempts:
                        backoff_strategy.wait(attempt)
            
            # All attempts failed
            if on_failure:
                on_failure(last_exception)
            
            raise last_exception
        
        return wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Examples:
        >>> from ilovetools.utils import CircuitBreaker
        
        >>> breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        >>> 
        >>> @breaker
        ... def api_call():
        ...     # Make API call
        ...     pass
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            timeout: Timeout before trying again (seconds)
            expected_exceptions: Exceptions to count as failures
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exceptions = expected_exceptions
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    def __call__(self, func: Callable):
        """Decorator for circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check circuit state
            if self.state == 'open':
                # Check if timeout has passed
                if time.time() - self.last_failure_time >= self.timeout:
                    self.state = 'half_open'
                else:
                    raise Exception('Circuit breaker is OPEN')
            
            try:
                result = func(*args, **kwargs)
                
                # Success - reset if half_open
                if self.state == 'half_open':
                    self.state = 'closed'
                    self.failure_count = 0
                
                return result
            
            except self.expected_exceptions as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                # Check threshold
                if self.failure_count >= self.failure_threshold:
                    self.state = 'open'
                
                raise
        
        return wrapper
    
    def reset(self):
        """Reset circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'
    
    def get_state(self) -> str:
        """Get current state."""
        return self.state


def retry_with_circuit_breaker(
    max_attempts: int = 3,
    failure_threshold: int = 5,
    timeout: float = 60.0,
    backoff_strategy: Optional[RetryStrategy] = None
):
    """
    Combine retry with circuit breaker.
    
    Args:
        max_attempts: Maximum retry attempts
        failure_threshold: Circuit breaker threshold
        timeout: Circuit breaker timeout
        backoff_strategy: Backoff strategy
    
    Examples:
        >>> from ilovetools.utils import retry_with_circuit_breaker
        
        >>> @retry_with_circuit_breaker(max_attempts=3, failure_threshold=5)
        ... def api_call():
        ...     # Make API call
        ...     pass
    """
    breaker = CircuitBreaker(failure_threshold=failure_threshold, timeout=timeout)
    
    if backoff_strategy is None:
        backoff_strategy = exponential_backoff(max_attempts=max_attempts)
    
    def decorator(func: Callable):
        @breaker
        @retry(max_attempts=max_attempts, backoff_strategy=backoff_strategy)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator
