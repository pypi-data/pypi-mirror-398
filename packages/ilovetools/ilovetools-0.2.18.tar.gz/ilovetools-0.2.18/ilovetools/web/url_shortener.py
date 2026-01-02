"""
URL Shortener Utility
Create and manage short URLs with custom aliases
"""

import hashlib
import string
import random
from typing import Dict, Optional, List
from datetime import datetime, timedelta

__all__ = [
    'URLShortener',
    'InMemoryStorage',
    'ShortURL',
    'generate_short_code',
    'validate_custom_alias',
]


def generate_short_code(length: int = 6) -> str:
    """
    Generate random short code.
    
    Args:
        length: Code length
    
    Returns:
        str: Short code
    
    Examples:
        >>> from ilovetools.web import generate_short_code
        
        >>> code = generate_short_code(6)
        >>> print(len(code))
        6
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def validate_custom_alias(alias: str) -> bool:
    """
    Validate custom alias.
    
    Args:
        alias: Custom alias
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.web import validate_custom_alias
        
        >>> validate_custom_alias('my-link')
        True
        >>> validate_custom_alias('invalid alias!')
        False
    """
    if not alias:
        return False
    
    # Check length
    if len(alias) < 3 or len(alias) > 50:
        return False
    
    # Check characters (alphanumeric, dash, underscore)
    allowed = set(string.ascii_letters + string.digits + '-_')
    return all(c in allowed for c in alias)


class ShortURL:
    """
    Short URL data model.
    
    Examples:
        >>> from ilovetools.web import ShortURL
        
        >>> short_url = ShortURL(
        ...     code='abc123',
        ...     original_url='https://example.com',
        ...     created_at=datetime.now()
        ... )
    """
    
    def __init__(
        self,
        code: str,
        original_url: str,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        clicks: int = 0,
        metadata: Optional[Dict] = None
    ):
        """
        Initialize short URL.
        
        Args:
            code: Short code
            original_url: Original URL
            created_at: Creation timestamp
            expires_at: Expiration timestamp
            clicks: Click count
            metadata: Additional metadata
        """
        self.code = code
        self.original_url = original_url
        self.created_at = created_at
        self.expires_at = expires_at
        self.clicks = clicks
        self.metadata = metadata or {}
    
    def is_expired(self) -> bool:
        """Check if URL is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def increment_clicks(self):
        """Increment click count."""
        self.clicks += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'code': self.code,
            'original_url': self.original_url,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'clicks': self.clicks,
            'metadata': self.metadata
        }


class InMemoryStorage:
    """
    In-memory storage for short URLs.
    
    Examples:
        >>> from ilovetools.web import InMemoryStorage
        
        >>> storage = InMemoryStorage()
        >>> storage.save(short_url)
        >>> retrieved = storage.get('abc123')
    """
    
    def __init__(self):
        """Initialize storage."""
        self.urls = {}
    
    def save(self, short_url: ShortURL) -> bool:
        """
        Save short URL.
        
        Args:
            short_url: ShortURL instance
        
        Returns:
            bool: True if saved
        """
        self.urls[short_url.code] = short_url
        return True
    
    def get(self, code: str) -> Optional[ShortURL]:
        """
        Get short URL by code.
        
        Args:
            code: Short code
        
        Returns:
            ShortURL or None
        """
        return self.urls.get(code)
    
    def delete(self, code: str) -> bool:
        """
        Delete short URL.
        
        Args:
            code: Short code
        
        Returns:
            bool: True if deleted
        """
        if code in self.urls:
            del self.urls[code]
            return True
        return False
    
    def exists(self, code: str) -> bool:
        """
        Check if code exists.
        
        Args:
            code: Short code
        
        Returns:
            bool: True if exists
        """
        return code in self.urls
    
    def list_all(self) -> List[ShortURL]:
        """
        List all short URLs.
        
        Returns:
            list: All short URLs
        """
        return list(self.urls.values())
    
    def cleanup_expired(self) -> int:
        """
        Remove expired URLs.
        
        Returns:
            int: Number of URLs removed
        """
        expired = [
            code for code, url in self.urls.items()
            if url.is_expired()
        ]
        
        for code in expired:
            del self.urls[code]
        
        return len(expired)


class URLShortener:
    """
    URL shortener with custom aliases and analytics.
    
    Examples:
        >>> from ilovetools.web import URLShortener
        
        >>> shortener = URLShortener()
        >>> short_url = shortener.shorten('https://example.com')
        >>> print(short_url.code)
        'abc123'
        >>> 
        >>> original = shortener.expand('abc123')
        >>> print(original)
        'https://example.com'
    """
    
    def __init__(
        self,
        storage: Optional[InMemoryStorage] = None,
        base_url: str = 'http://short.url/',
        code_length: int = 6
    ):
        """
        Initialize URL shortener.
        
        Args:
            storage: Storage backend
            base_url: Base URL for short links
            code_length: Short code length
        """
        self.storage = storage or InMemoryStorage()
        self.base_url = base_url.rstrip('/')
        self.code_length = code_length
    
    def shorten(
        self,
        url: str,
        custom_alias: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> ShortURL:
        """
        Shorten URL.
        
        Args:
            url: URL to shorten
            custom_alias: Custom alias
            expires_in_days: Expiration in days
            metadata: Additional metadata
        
        Returns:
            ShortURL: Short URL object
        
        Examples:
            >>> from ilovetools.web import URLShortener
            
            >>> shortener = URLShortener()
            >>> short_url = shortener.shorten(
            ...     'https://example.com',
            ...     custom_alias='my-link',
            ...     expires_in_days=30
            ... )
        """
        # Generate or validate code
        if custom_alias:
            if not validate_custom_alias(custom_alias):
                raise ValueError('Invalid custom alias')
            
            if self.storage.exists(custom_alias):
                raise ValueError('Custom alias already exists')
            
            code = custom_alias
        else:
            # Generate unique code
            code = self._generate_unique_code(url)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        # Create short URL
        short_url = ShortURL(
            code=code,
            original_url=url,
            created_at=datetime.now(),
            expires_at=expires_at,
            metadata=metadata
        )
        
        # Save
        self.storage.save(short_url)
        
        return short_url
    
    def expand(self, code: str, track_click: bool = True) -> Optional[str]:
        """
        Expand short URL.
        
        Args:
            code: Short code
            track_click: Track click
        
        Returns:
            str or None: Original URL
        
        Examples:
            >>> from ilovetools.web import URLShortener
            
            >>> shortener = URLShortener()
            >>> original = shortener.expand('abc123')
        """
        short_url = self.storage.get(code)
        
        if not short_url:
            return None
        
        # Check expiration
        if short_url.is_expired():
            return None
        
        # Track click
        if track_click:
            short_url.increment_clicks()
            self.storage.save(short_url)
        
        return short_url.original_url
    
    def get_stats(self, code: str) -> Optional[Dict]:
        """
        Get URL statistics.
        
        Args:
            code: Short code
        
        Returns:
            dict or None: Statistics
        
        Examples:
            >>> from ilovetools.web import URLShortener
            
            >>> shortener = URLShortener()
            >>> stats = shortener.get_stats('abc123')
            >>> print(stats['clicks'])
            42
        """
        short_url = self.storage.get(code)
        
        if not short_url:
            return None
        
        return {
            'code': short_url.code,
            'original_url': short_url.original_url,
            'clicks': short_url.clicks,
            'created_at': short_url.created_at.isoformat(),
            'expires_at': short_url.expires_at.isoformat() if short_url.expires_at else None,
            'is_expired': short_url.is_expired(),
            'metadata': short_url.metadata
        }
    
    def delete(self, code: str) -> bool:
        """
        Delete short URL.
        
        Args:
            code: Short code
        
        Returns:
            bool: True if deleted
        
        Examples:
            >>> from ilovetools.web import URLShortener
            
            >>> shortener = URLShortener()
            >>> shortener.delete('abc123')
        """
        return self.storage.delete(code)
    
    def list_all(self) -> List[Dict]:
        """
        List all short URLs.
        
        Returns:
            list: All short URLs
        
        Examples:
            >>> from ilovetools.web import URLShortener
            
            >>> shortener = URLShortener()
            >>> urls = shortener.list_all()
        """
        return [url.to_dict() for url in self.storage.list_all()]
    
    def cleanup_expired(self) -> int:
        """
        Remove expired URLs.
        
        Returns:
            int: Number removed
        
        Examples:
            >>> from ilovetools.web import URLShortener
            
            >>> shortener = URLShortener()
            >>> removed = shortener.cleanup_expired()
        """
        return self.storage.cleanup_expired()
    
    def get_full_url(self, code: str) -> str:
        """
        Get full short URL.
        
        Args:
            code: Short code
        
        Returns:
            str: Full short URL
        
        Examples:
            >>> from ilovetools.web import URLShortener
            
            >>> shortener = URLShortener()
            >>> full_url = shortener.get_full_url('abc123')
            >>> print(full_url)
            'http://short.url/abc123'
        """
        return f"{self.base_url}/{code}"
    
    def _generate_unique_code(self, url: str) -> str:
        """Generate unique short code."""
        # Try hash-based first
        hash_code = hashlib.md5(url.encode()).hexdigest()[:self.code_length]
        
        if not self.storage.exists(hash_code):
            return hash_code
        
        # Generate random codes
        max_attempts = 10
        for _ in range(max_attempts):
            code = generate_short_code(self.code_length)
            if not self.storage.exists(code):
                return code
        
        # Increase length if needed
        return generate_short_code(self.code_length + 2)
