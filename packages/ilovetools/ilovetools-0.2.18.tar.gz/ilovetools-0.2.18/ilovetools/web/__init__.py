"""
Web scraping and HTTP utilities
"""

from .scraper import (
    extract_links,
    extract_emails,
    extract_phone_numbers,
    extract_images,
    extract_text,
    extract_metadata,
    extract_tables,
    extract_json_ld,
    rate_limiter,
    parse_html_simple,
    clean_text,
    get_domain,
    is_valid_url,
)

from .url_shortener import (
    URLShortener,
    InMemoryStorage,
    ShortURL,
    generate_short_code,
    validate_custom_alias,
)

__all__ = [
    # Scraper
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
    # URL Shortener
    'URLShortener',
    'InMemoryStorage',
    'ShortURL',
    'generate_short_code',
    'validate_custom_alias',
]
