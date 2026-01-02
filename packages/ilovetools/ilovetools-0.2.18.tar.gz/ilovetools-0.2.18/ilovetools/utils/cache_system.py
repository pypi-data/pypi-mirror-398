"""
Caching System
Multiple cache backends with TTL support
"""

import time
import json
import hashlib
from typing import Any, Optional, Callable, Dict
from functools import wraps
from collections import OrderedDict
from threading import Lock

__all__ = [
    'MemoryCache',
    'LRUCache',
    'TTLCache',
    'FileCache',
    'cache_decorator',
    'memoize',
    'clear_all_caches',
    'CacheStats',
]


class CacheStats:
    """Cache statistics tracker."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
    
    def hit(self):
        """Record cache hit."""
        self.hits += 1
    
    def miss(self):
        """Record cache miss."""
        self.misses += 1
    
    def set(self):
        """Record cache set."""
        self.sets += 1
    
    def delete(self):
        """Record cache delete."""
        self.deletes += 1
    
    def evict(self):
        """Record cache eviction."""
        self.evictions += 1
    
    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def reset(self):
        """Reset statistics."""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'evictions': self.evictions,
            'hit_rate': self.get_hit_rate()
        }


class MemoryCache:
    """
    Simple in-memory cache.
    
    Examples:
        >>> from ilovetools.utils import MemoryCache
        
        >>> cache = MemoryCache()
        >>> cache.set('key', 'value')
        >>> print(cache.get('key'))
        'value'
    """
    
    def __init__(self):
        """Initialize memory cache."""
        self.cache = {}
        self.stats = CacheStats()
        self.lock = Lock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
        
        Returns:
            Cached value or default
        """
        with self.lock:
            if key in self.cache:
                self.stats.hit()
                return self.cache[key]
            else:
                self.stats.miss()
                return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            self.cache[key] = value
            self.stats.set()
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            bool: True if deleted
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.delete()
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache."""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)
    
    def keys(self) -> list:
        """Get all keys."""
        return list(self.cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.stats.to_dict()


class LRUCache:
    """
    Least Recently Used (LRU) cache.
    
    Examples:
        >>> from ilovetools.utils import LRUCache
        
        >>> cache = LRUCache(max_size=100)
        >>> cache.set('key', 'value')
        >>> print(cache.get('key'))
        'value'
    """
    
    def __init__(self, max_size: int = 128):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum cache size
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self.stats = CacheStats()
        self.lock = Lock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
        
        Returns:
            Cached value or default
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats.hit()
                return self.cache[key]
            else:
                self.stats.miss()
                return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                # Update and move to end
                self.cache.move_to_end(key)
            else:
                # Check size limit
                if len(self.cache) >= self.max_size:
                    # Remove least recently used
                    self.cache.popitem(last=False)
                    self.stats.evict()
            
            self.cache[key] = value
            self.stats.set()
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            bool: True if deleted
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.delete()
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache."""
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.stats.to_dict()


class TTLCache:
    """
    Time-To-Live (TTL) cache with expiration.
    
    Examples:
        >>> from ilovetools.utils import TTLCache
        
        >>> cache = TTLCache(default_ttl=60)
        >>> cache.set('key', 'value', ttl=30)
        >>> print(cache.get('key'))
        'value'
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize TTL cache.
        
        Args:
            default_ttl: Default TTL in seconds
        """
        self.default_ttl = default_ttl
        self.cache = {}
        self.stats = CacheStats()
        self.lock = Lock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
        
        Returns:
            Cached value or default
        """
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                
                # Check expiration
                if time.time() < expiry:
                    self.stats.hit()
                    return value
                else:
                    # Expired
                    del self.cache[key]
                    self.stats.evict()
            
            self.stats.miss()
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        with self.lock:
            if ttl is None:
                ttl = self.default_ttl
            
            expiry = time.time() + ttl
            self.cache[key] = (value, expiry)
            self.stats.set()
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            bool: True if deleted
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.delete()
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache."""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            int: Number of entries removed
        """
        with self.lock:
            now = time.time()
            expired_keys = [
                key for key, (_, expiry) in self.cache.items()
                if now >= expiry
            ]
            
            for key in expired_keys:
                del self.cache[key]
                self.stats.evict()
            
            return len(expired_keys)
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.stats.to_dict()


class FileCache:
    """
    File-based cache for persistence.
    
    Examples:
        >>> from ilovetools.utils import FileCache
        
        >>> cache = FileCache(cache_dir='/tmp/cache')
        >>> cache.set('key', {'data': 'value'})
        >>> print(cache.get('key'))
        {'data': 'value'}
    """
    
    def __init__(self, cache_dir: str = '/tmp/cache', default_ttl: int = 3600):
        """
        Initialize file cache.
        
        Args:
            cache_dir: Cache directory path
            default_ttl: Default TTL in seconds
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.stats = CacheStats()
        self.lock = Lock()
        
        # Create cache directory
        import os
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for key."""
        # Hash key for filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"{self.cache_dir}/{key_hash}.cache"
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
        
        Returns:
            Cached value or default
        """
        with self.lock:
            file_path = self._get_file_path(key)
            
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Check expiration
                if time.time() < data['expiry']:
                    self.stats.hit()
                    return data['value']
                else:
                    # Expired
                    import os
                    os.remove(file_path)
                    self.stats.evict()
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass
            
            self.stats.miss()
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        with self.lock:
            if ttl is None:
                ttl = self.default_ttl
            
            file_path = self._get_file_path(key)
            expiry = time.time() + ttl
            
            data = {
                'value': value,
                'expiry': expiry
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            self.stats.set()
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            bool: True if deleted
        """
        with self.lock:
            file_path = self._get_file_path(key)
            
            try:
                import os
                os.remove(file_path)
                self.stats.delete()
                return True
            except FileNotFoundError:
                return False
    
    def clear(self) -> None:
        """Clear all cache."""
        with self.lock:
            import os
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    os.remove(os.path.join(self.cache_dir, filename))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.stats.to_dict()


def cache_decorator(
    cache: Optional[Any] = None,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        cache: Cache instance (default: MemoryCache)
        ttl: Time to live in seconds
        key_func: Custom key generation function
    
    Examples:
        >>> from ilovetools.utils import cache_decorator, LRUCache
        
        >>> cache = LRUCache(max_size=100)
        >>> @cache_decorator(cache=cache)
        ... def expensive_function(x, y):
        ...     return x + y
    """
    if cache is None:
        cache = MemoryCache()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(key)
            
            if result is None:
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                if isinstance(cache, TTLCache) and ttl:
                    cache.set(key, result, ttl=ttl)
                else:
                    cache.set(key, result)
            
            return result
        
        # Add cache control methods
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        
        return wrapper
    
    return decorator


def memoize(func: Callable) -> Callable:
    """
    Simple memoization decorator.
    
    Args:
        func: Function to memoize
    
    Returns:
        Wrapped function
    
    Examples:
        >>> from ilovetools.utils import memoize
        
        >>> @memoize
        ... def fibonacci(n):
        ...     if n < 2:
        ...         return n
        ...     return fibonacci(n-1) + fibonacci(n-2)
    """
    cache = {}
    
    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    
    wrapper.cache = cache
    wrapper.clear_cache = cache.clear
    
    return wrapper


# Global cache registry
_cache_registry = []


def clear_all_caches():
    """
    Clear all registered caches.
    
    Examples:
        >>> from ilovetools.utils import clear_all_caches
        
        >>> clear_all_caches()
    """
    for cache in _cache_registry:
        cache.clear()
