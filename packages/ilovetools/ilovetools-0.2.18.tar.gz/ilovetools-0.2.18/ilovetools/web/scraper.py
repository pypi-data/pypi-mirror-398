"""
Web Scraping Utility
Extract data from websites with rate limiting and error handling
"""

import re
import time
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urljoin, urlparse
import json

__all__ = [
    'extract_links',
    'extract_emails',
    'extract_phone_numbers',
    'extract_images',
    'extract_text',
    'extract_metadata',
    'extract_tables',
    'extract_json_ld',
    'rate_limiter',
    'parse_html_simple',
    'clean_text',
    'get_domain',
    'is_valid_url',
]


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL to validate
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.web import is_valid_url
        
        >>> is_valid_url('https://example.com')
        True
        >>> is_valid_url('not-a-url')
        False
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to parse
    
    Returns:
        str: Domain name
    
    Examples:
        >>> from ilovetools.web import get_domain
        
        >>> get_domain('https://www.example.com/page')
        'www.example.com'
    """
    parsed = urlparse(url)
    return parsed.netloc


def clean_text(text: str, remove_extra_spaces: bool = True) -> str:
    """
    Clean extracted text.
    
    Args:
        text: Text to clean
        remove_extra_spaces: Remove extra whitespace
    
    Returns:
        str: Cleaned text
    
    Examples:
        >>> from ilovetools.web import clean_text
        
        >>> clean_text('  Hello   World  \\n\\n  ')
        'Hello World'
    """
    # Remove extra whitespace
    if remove_extra_spaces:
        text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def parse_html_simple(html: str) -> Dict[str, Any]:
    """
    Simple HTML parsing without external libraries.
    
    Args:
        html: HTML content
    
    Returns:
        dict: Parsed data
    
    Examples:
        >>> from ilovetools.web import parse_html_simple
        
        >>> html = '<html><title>Test</title><body>Content</body></html>'
        >>> data = parse_html_simple(html)
        >>> print(data['title'])
        'Test'
    """
    result = {
        'title': '',
        'body': '',
        'links': [],
        'images': [],
    }
    
    # Extract title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_match:
        result['title'] = clean_text(title_match.group(1))
    
    # Extract body
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.IGNORECASE | re.DOTALL)
    if body_match:
        body_html = body_match.group(1)
        # Remove script and style tags
        body_html = re.sub(r'<script[^>]*>.*?</script>', '', body_html, flags=re.IGNORECASE | re.DOTALL)
        body_html = re.sub(r'<style[^>]*>.*?</style>', '', body_html, flags=re.IGNORECASE | re.DOTALL)
        # Remove HTML tags
        body_text = re.sub(r'<[^>]+>', ' ', body_html)
        result['body'] = clean_text(body_text)
    
    return result


def extract_links(
    html: str,
    base_url: Optional[str] = None,
    absolute_only: bool = False
) -> List[str]:
    """
    Extract all links from HTML.
    
    Args:
        html: HTML content
        base_url: Base URL for relative links
        absolute_only: Return only absolute URLs
    
    Returns:
        list: Extracted links
    
    Examples:
        >>> from ilovetools.web import extract_links
        
        >>> html = '<a href="/page">Link</a><a href="https://example.com">External</a>'
        >>> links = extract_links(html, base_url='https://site.com')
        >>> print(links)
        ['https://site.com/page', 'https://example.com']
    """
    # Find all href attributes
    pattern = r'<a[^>]+href=["\']([^"\']+)["\']'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    links = []
    for link in matches:
        # Skip anchors and javascript
        if link.startswith('#') or link.startswith('javascript:'):
            continue
        
        # Convert relative to absolute
        if base_url and not link.startswith(('http://', 'https://', '//')):
            link = urljoin(base_url, link)
        
        # Filter absolute only
        if absolute_only and not link.startswith(('http://', 'https://')):
            continue
        
        links.append(link)
    
    return list(set(links))  # Remove duplicates


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to search
    
    Returns:
        list: Extracted emails
    
    Examples:
        >>> from ilovetools.web import extract_emails
        
        >>> text = 'Contact us at info@example.com or support@example.com'
        >>> emails = extract_emails(text)
        >>> print(emails)
        ['info@example.com', 'support@example.com']
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    return list(set(emails))


def extract_phone_numbers(
    text: str,
    country_code: Optional[str] = None
) -> List[str]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Text to search
        country_code: Filter by country code (e.g., '+1', '+44')
    
    Returns:
        list: Extracted phone numbers
    
    Examples:
        >>> from ilovetools.web import extract_phone_numbers
        
        >>> text = 'Call us at +1-555-123-4567 or (555) 987-6543'
        >>> phones = extract_phone_numbers(text)
        >>> print(phones)
        ['+1-555-123-4567', '(555) 987-6543']
    """
    # Multiple phone patterns
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-555-123-4567
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (555) 123-4567
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 555-123-4567
    ]
    
    phones = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phones.extend(matches)
    
    # Filter by country code
    if country_code:
        phones = [p for p in phones if p.startswith(country_code)]
    
    return list(set(phones))


def extract_images(
    html: str,
    base_url: Optional[str] = None,
    absolute_only: bool = False
) -> List[Dict[str, str]]:
    """
    Extract images from HTML.
    
    Args:
        html: HTML content
        base_url: Base URL for relative links
        absolute_only: Return only absolute URLs
    
    Returns:
        list: Image data (src, alt)
    
    Examples:
        >>> from ilovetools.web import extract_images
        
        >>> html = '<img src="/logo.png" alt="Logo"><img src="https://cdn.com/pic.jpg">'
        >>> images = extract_images(html, base_url='https://site.com')
        >>> print(images[0])
        {'src': 'https://site.com/logo.png', 'alt': 'Logo'}
    """
    # Find all img tags
    pattern = r'<img[^>]+src=["\']([^"\']+)["\'](?:[^>]+alt=["\']([^"\']*)["\'])?'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    images = []
    for src, alt in matches:
        # Convert relative to absolute
        if base_url and not src.startswith(('http://', 'https://', '//')):
            src = urljoin(base_url, src)
        
        # Filter absolute only
        if absolute_only and not src.startswith(('http://', 'https://')):
            continue
        
        images.append({
            'src': src,
            'alt': alt or ''
        })
    
    return images


def extract_text(
    html: str,
    remove_scripts: bool = True,
    remove_styles: bool = True
) -> str:
    """
    Extract plain text from HTML.
    
    Args:
        html: HTML content
        remove_scripts: Remove script tags
        remove_styles: Remove style tags
    
    Returns:
        str: Extracted text
    
    Examples:
        >>> from ilovetools.web import extract_text
        
        >>> html = '<html><body><h1>Title</h1><p>Content</p></body></html>'
        >>> text = extract_text(html)
        >>> print(text)
        'Title Content'
    """
    # Remove script tags
    if remove_scripts:
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove style tags
    if remove_styles:
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    
    # Clean text
    text = clean_text(text)
    
    return text


def extract_metadata(html: str) -> Dict[str, str]:
    """
    Extract meta tags from HTML.
    
    Args:
        html: HTML content
    
    Returns:
        dict: Meta tag data
    
    Examples:
        >>> from ilovetools.web import extract_metadata
        
        >>> html = '<meta name="description" content="Page description">'
        >>> meta = extract_metadata(html)
        >>> print(meta['description'])
        'Page description'
    """
    metadata = {}
    
    # Find all meta tags
    pattern = r'<meta[^>]+(?:name|property)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    for name, content in matches:
        metadata[name] = content
    
    # Also check reverse order (content before name)
    pattern = r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']([^"\']+)["\']'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    for content, name in matches:
        if name not in metadata:
            metadata[name] = content
    
    return metadata


def extract_tables(html: str) -> List[List[List[str]]]:
    """
    Extract tables from HTML.
    
    Args:
        html: HTML content
    
    Returns:
        list: List of tables (each table is list of rows)
    
    Examples:
        >>> from ilovetools.web import extract_tables
        
        >>> html = '<table><tr><td>A</td><td>B</td></tr></table>'
        >>> tables = extract_tables(html)
        >>> print(tables[0])
        [['A', 'B']]
    """
    tables = []
    
    # Find all table tags
    table_pattern = r'<table[^>]*>(.*?)</table>'
    table_matches = re.findall(table_pattern, html, re.IGNORECASE | re.DOTALL)
    
    for table_html in table_matches:
        rows = []
        
        # Find all tr tags
        row_pattern = r'<tr[^>]*>(.*?)</tr>'
        row_matches = re.findall(row_pattern, table_html, re.IGNORECASE | re.DOTALL)
        
        for row_html in row_matches:
            cells = []
            
            # Find all td/th tags
            cell_pattern = r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>'
            cell_matches = re.findall(cell_pattern, row_html, re.IGNORECASE | re.DOTALL)
            
            for cell_html in cell_matches:
                # Remove HTML tags and clean
                cell_text = re.sub(r'<[^>]+>', ' ', cell_html)
                cell_text = clean_text(cell_text)
                cells.append(cell_text)
            
            if cells:
                rows.append(cells)
        
        if rows:
            tables.append(rows)
    
    return tables


def extract_json_ld(html: str) -> List[Dict[str, Any]]:
    """
    Extract JSON-LD structured data from HTML.
    
    Args:
        html: HTML content
    
    Returns:
        list: JSON-LD objects
    
    Examples:
        >>> from ilovetools.web import extract_json_ld
        
        >>> html = '<script type="application/ld+json">{"@type": "Article"}</script>'
        >>> data = extract_json_ld(html)
        >>> print(data[0]['@type'])
        'Article'
    """
    json_ld_data = []
    
    # Find all JSON-LD script tags
    pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
    
    for match in matches:
        try:
            data = json.loads(match)
            json_ld_data.append(data)
        except json.JSONDecodeError:
            continue
    
    return json_ld_data


class RateLimiter:
    """
    Rate limiter for web scraping.
    
    Examples:
        >>> from ilovetools.web import rate_limiter
        
        >>> limiter = rate_limiter(requests_per_second=2)
        >>> for url in urls:
        ...     limiter.wait()
        ...     # Make request
    """
    
    def __init__(
        self,
        requests_per_second: float = 1.0,
        burst_size: int = 1
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
            burst_size: Allow burst of requests
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.tokens = burst_size
        self.last_token_update = time.time()
    
    def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        
        # Refill tokens
        time_passed = current_time - self.last_token_update
        self.tokens = min(
            self.burst_size,
            self.tokens + time_passed * self.requests_per_second
        )
        self.last_token_update = current_time
        
        # Wait if no tokens available
        if self.tokens < 1:
            sleep_time = (1 - self.tokens) / self.requests_per_second
            time.sleep(sleep_time)
            self.tokens = 0
            self.last_token_update = time.time()
        else:
            self.tokens -= 1
        
        # Ensure minimum interval
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def reset(self):
        """Reset rate limiter."""
        self.tokens = self.burst_size
        self.last_request_time = 0
        self.last_token_update = time.time()


def rate_limiter(
    requests_per_second: float = 1.0,
    burst_size: int = 1
) -> RateLimiter:
    """
    Create a rate limiter instance.
    
    Args:
        requests_per_second: Maximum requests per second
        burst_size: Allow burst of requests
    
    Returns:
        RateLimiter: Rate limiter instance
    
    Examples:
        >>> from ilovetools.web import rate_limiter
        
        >>> limiter = rate_limiter(requests_per_second=2)
        >>> for i in range(10):
        ...     limiter.wait()
        ...     print(f"Request {i}")
    """
    return RateLimiter(requests_per_second, burst_size)
