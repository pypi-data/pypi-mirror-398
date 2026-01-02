"""
Data Validation Library
Comprehensive input validation and sanitization
"""

import re
from typing import Any, List, Dict, Optional, Callable, Union
from datetime import datetime

__all__ = [
    'validate_email',
    'validate_phone',
    'validate_url',
    'validate_ip_address',
    'validate_credit_card',
    'validate_date',
    'validate_range',
    'validate_length',
    'validate_pattern',
    'validate_type',
    'sanitize_string',
    'sanitize_html',
    'sanitize_sql',
    'validate_schema',
    'create_validator',
    'ValidationError',
]


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_email(email: str, strict: bool = True) -> bool:
    """
    Validate email address.
    
    Args:
        email: Email address to validate
        strict: Use strict RFC 5322 validation
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_email
        
        >>> validate_email('user@example.com')
        True
        >>> validate_email('invalid.email')
        False
    """
    if not email or not isinstance(email, str):
        return False
    
    if strict:
        # RFC 5322 compliant pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    else:
        # Simple pattern
        pattern = r'^.+@.+\..+$'
    
    return bool(re.match(pattern, email))


def validate_phone(
    phone: str,
    country_code: Optional[str] = None,
    allow_extensions: bool = False
) -> bool:
    """
    Validate phone number.
    
    Args:
        phone: Phone number to validate
        country_code: Expected country code (e.g., '+1', '+44')
        allow_extensions: Allow extensions (e.g., 'x123')
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_phone
        
        >>> validate_phone('+1-555-123-4567')
        True
        >>> validate_phone('555-123-4567', country_code='+1')
        True
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check country code
    if country_code:
        if not cleaned.startswith(country_code.replace('+', '')):
            return False
    
    # Check for extensions
    if allow_extensions:
        cleaned = re.sub(r'x\d+$', '', cleaned, flags=re.IGNORECASE)
    
    # Remove + sign
    cleaned = cleaned.replace('+', '')
    
    # Check if all digits and reasonable length
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def validate_url(
    url: str,
    require_protocol: bool = True,
    allowed_protocols: Optional[List[str]] = None
) -> bool:
    """
    Validate URL.
    
    Args:
        url: URL to validate
        require_protocol: Require http:// or https://
        allowed_protocols: List of allowed protocols
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_url
        
        >>> validate_url('https://example.com')
        True
        >>> validate_url('example.com', require_protocol=False)
        True
    """
    if not url or not isinstance(url, str):
        return False
    
    if allowed_protocols is None:
        allowed_protocols = ['http', 'https']
    
    # URL pattern
    if require_protocol:
        protocol_pattern = '|'.join(allowed_protocols)
        pattern = f'^({protocol_pattern})://[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}(/.*)?$'
    else:
        pattern = r'^([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(/.*)?$'
    
    return bool(re.match(pattern, url))


def validate_ip_address(ip: str, version: int = 4) -> bool:
    """
    Validate IP address.
    
    Args:
        ip: IP address to validate
        version: IP version (4 or 6)
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_ip_address
        
        >>> validate_ip_address('192.168.1.1')
        True
        >>> validate_ip_address('2001:0db8:85a3::8a2e:0370:7334', version=6)
        True
    """
    if not ip or not isinstance(ip, str):
        return False
    
    if version == 4:
        # IPv4 pattern
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        # Check each octet
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)
    
    elif version == 6:
        # IPv6 pattern (simplified)
        pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$|^([0-9a-fA-F]{0,4}:){1,7}:$|^::([0-9a-fA-F]{0,4}:){0,6}[0-9a-fA-F]{0,4}$'
        return bool(re.match(pattern, ip))
    
    return False


def validate_credit_card(card_number: str, card_type: Optional[str] = None) -> bool:
    """
    Validate credit card number using Luhn algorithm.
    
    Args:
        card_number: Credit card number
        card_type: Expected card type (visa, mastercard, amex, discover)
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_credit_card
        
        >>> validate_credit_card('4532015112830366')  # Visa test number
        True
        >>> validate_credit_card('4532015112830366', card_type='visa')
        True
    """
    if not card_number or not isinstance(card_number, str):
        return False
    
    # Remove spaces and dashes
    cleaned = re.sub(r'[\s\-]', '', card_number)
    
    # Check if all digits
    if not cleaned.isdigit():
        return False
    
    # Check card type patterns
    if card_type:
        patterns = {
            'visa': r'^4\d{12}(\d{3})?$',
            'mastercard': r'^5[1-5]\d{14}$',
            'amex': r'^3[47]\d{13}$',
            'discover': r'^6(?:011|5\d{2})\d{12}$',
        }
        
        if card_type.lower() not in patterns:
            return False
        
        if not re.match(patterns[card_type.lower()], cleaned):
            return False
    
    # Luhn algorithm
    def luhn_check(number):
        digits = [int(d) for d in number]
        checksum = 0
        
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        
        return sum(digits) % 10 == 0
    
    return luhn_check(cleaned)


def validate_date(
    date_string: str,
    date_format: str = '%Y-%m-%d',
    min_date: Optional[str] = None,
    max_date: Optional[str] = None
) -> bool:
    """
    Validate date string.
    
    Args:
        date_string: Date string to validate
        date_format: Expected date format
        min_date: Minimum allowed date
        max_date: Maximum allowed date
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_date
        
        >>> validate_date('2024-12-03')
        True
        >>> validate_date('2024-12-03', min_date='2024-01-01')
        True
    """
    if not date_string or not isinstance(date_string, str):
        return False
    
    try:
        date_obj = datetime.strptime(date_string, date_format)
        
        # Check min date
        if min_date:
            min_obj = datetime.strptime(min_date, date_format)
            if date_obj < min_obj:
                return False
        
        # Check max date
        if max_date:
            max_obj = datetime.strptime(max_date, date_format)
            if date_obj > max_obj:
                return False
        
        return True
    except ValueError:
        return False


def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    inclusive: bool = True
) -> bool:
    """
    Validate numeric range.
    
    Args:
        value: Value to validate
        min_value: Minimum value
        max_value: Maximum value
        inclusive: Include boundaries
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_range
        
        >>> validate_range(5, min_value=1, max_value=10)
        True
        >>> validate_range(10, min_value=1, max_value=10, inclusive=False)
        False
    """
    if not isinstance(value, (int, float)):
        return False
    
    if min_value is not None:
        if inclusive:
            if value < min_value:
                return False
        else:
            if value <= min_value:
                return False
    
    if max_value is not None:
        if inclusive:
            if value > max_value:
                return False
        else:
            if value >= max_value:
                return False
    
    return True


def validate_length(
    value: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    exact_length: Optional[int] = None
) -> bool:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum length
        max_length: Maximum length
        exact_length: Exact required length
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_length
        
        >>> validate_length('hello', min_length=3, max_length=10)
        True
        >>> validate_length('hello', exact_length=5)
        True
    """
    if not isinstance(value, str):
        return False
    
    length = len(value)
    
    if exact_length is not None:
        return length == exact_length
    
    if min_length is not None and length < min_length:
        return False
    
    if max_length is not None and length > max_length:
        return False
    
    return True


def validate_pattern(value: str, pattern: str, flags: int = 0) -> bool:
    """
    Validate against regex pattern.
    
    Args:
        value: String to validate
        pattern: Regex pattern
        flags: Regex flags
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_pattern
        
        >>> validate_pattern('ABC123', r'^[A-Z]{3}\d{3}$')
        True
        >>> validate_pattern('abc123', r'^[A-Z]{3}\d{3}$', re.IGNORECASE)
        True
    """
    if not isinstance(value, str):
        return False
    
    return bool(re.match(pattern, value, flags))


def validate_type(value: Any, expected_type: type) -> bool:
    """
    Validate value type.
    
    Args:
        value: Value to validate
        expected_type: Expected type
    
    Returns:
        bool: True if valid
    
    Examples:
        >>> from ilovetools.validation import validate_type
        
        >>> validate_type(123, int)
        True
        >>> validate_type('hello', str)
        True
    """
    return isinstance(value, expected_type)


def sanitize_string(
    value: str,
    remove_html: bool = True,
    remove_special: bool = False,
    lowercase: bool = False,
    trim: bool = True
) -> str:
    """
    Sanitize string input.
    
    Args:
        value: String to sanitize
        remove_html: Remove HTML tags
        remove_special: Remove special characters
        lowercase: Convert to lowercase
        trim: Trim whitespace
    
    Returns:
        str: Sanitized string
    
    Examples:
        >>> from ilovetools.validation import sanitize_string
        
        >>> sanitize_string('<b>Hello</b> World!')
        'Hello World!'
        >>> sanitize_string('Hello World!', remove_special=True)
        'Hello World'
    """
    if not isinstance(value, str):
        return str(value)
    
    result = value
    
    # Remove HTML tags
    if remove_html:
        result = re.sub(r'<[^>]+>', '', result)
    
    # Remove special characters
    if remove_special:
        result = re.sub(r'[^a-zA-Z0-9\s]', '', result)
    
    # Convert to lowercase
    if lowercase:
        result = result.lower()
    
    # Trim whitespace
    if trim:
        result = result.strip()
        result = re.sub(r'\s+', ' ', result)
    
    return result


def sanitize_html(html: str, allowed_tags: Optional[List[str]] = None) -> str:
    """
    Sanitize HTML content.
    
    Args:
        html: HTML to sanitize
        allowed_tags: List of allowed tags
    
    Returns:
        str: Sanitized HTML
    
    Examples:
        >>> from ilovetools.validation import sanitize_html
        
        >>> sanitize_html('<script>alert("xss")</script><p>Safe</p>')
        '<p>Safe</p>'
        >>> sanitize_html('<b>Bold</b><i>Italic</i>', allowed_tags=['b'])
        '<b>Bold</b>Italic'
    """
    if not isinstance(html, str):
        return ''
    
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
    
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove event handlers
    html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    
    # Remove disallowed tags
    if allowed_tags:
        # Find all tags
        all_tags = re.findall(r'</?(\w+)[^>]*>', html)
        disallowed = set(all_tags) - set(allowed_tags)
        
        for tag in disallowed:
            html = re.sub(f'<{tag}[^>]*>', '', html, flags=re.IGNORECASE)
            html = re.sub(f'</{tag}>', '', html, flags=re.IGNORECASE)
    
    return html


def sanitize_sql(value: str) -> str:
    """
    Sanitize SQL input (basic protection).
    
    Args:
        value: String to sanitize
    
    Returns:
        str: Sanitized string
    
    Examples:
        >>> from ilovetools.validation import sanitize_sql
        
        >>> sanitize_sql("'; DROP TABLE users; --")
        "'' DROP TABLE users --"
    """
    if not isinstance(value, str):
        return str(value)
    
    # Escape single quotes
    value = value.replace("'", "''")
    
    # Remove SQL comments
    value = re.sub(r'--.*$', '', value, flags=re.MULTILINE)
    value = re.sub(r'/\*.*?\*/', '', value, flags=re.DOTALL)
    
    # Remove dangerous keywords (basic)
    dangerous = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'EXEC', 'EXECUTE']
    for keyword in dangerous:
        value = re.sub(f'\\b{keyword}\\b', '', value, flags=re.IGNORECASE)
    
    return value


def validate_schema(data: Dict[str, Any], schema: Dict[str, Dict]) -> tuple:
    """
    Validate data against schema.
    
    Args:
        data: Data to validate
        schema: Validation schema
    
    Returns:
        tuple: (is_valid, errors)
    
    Examples:
        >>> from ilovetools.validation import validate_schema
        
        >>> schema = {
        ...     'name': {'type': str, 'required': True, 'min_length': 2},
        ...     'age': {'type': int, 'required': True, 'min': 0, 'max': 150},
        ...     'email': {'type': str, 'required': True, 'validator': validate_email}
        ... }
        >>> data = {'name': 'John', 'age': 30, 'email': 'john@example.com'}
        >>> valid, errors = validate_schema(data, schema)
        >>> print(valid)
        True
    """
    errors = []
    
    for field, rules in schema.items():
        # Check required
        if rules.get('required', False) and field not in data:
            errors.append(f'{field} is required')
            continue
        
        if field not in data:
            continue
        
        value = data[field]
        
        # Check type
        if 'type' in rules and not isinstance(value, rules['type']):
            errors.append(f'{field} must be of type {rules["type"].__name__}')
            continue
        
        # Check custom validator
        if 'validator' in rules:
            validator = rules['validator']
            if not validator(value):
                errors.append(f'{field} failed validation')
                continue
        
        # Check min/max for numbers
        if isinstance(value, (int, float)):
            if 'min' in rules and value < rules['min']:
                errors.append(f'{field} must be >= {rules["min"]}')
            if 'max' in rules and value > rules['max']:
                errors.append(f'{field} must be <= {rules["max"]}')
        
        # Check length for strings
        if isinstance(value, str):
            if 'min_length' in rules and len(value) < rules['min_length']:
                errors.append(f'{field} must be at least {rules["min_length"]} characters')
            if 'max_length' in rules and len(value) > rules['max_length']:
                errors.append(f'{field} must be at most {rules["max_length"]} characters')
        
        # Check pattern
        if 'pattern' in rules and isinstance(value, str):
            if not re.match(rules['pattern'], value):
                errors.append(f'{field} does not match required pattern')
    
    return len(errors) == 0, errors


def create_validator(rules: Dict[str, Any]) -> Callable:
    """
    Create custom validator function.
    
    Args:
        rules: Validation rules
    
    Returns:
        Callable: Validator function
    
    Examples:
        >>> from ilovetools.validation import create_validator
        
        >>> validator = create_validator({
        ...     'type': str,
        ...     'min_length': 5,
        ...     'pattern': r'^[A-Z]'
        ... })
        >>> print(validator('Hello'))
        True
        >>> print(validator('hi'))
        False
    """
    def validator(value):
        # Check type
        if 'type' in rules and not isinstance(value, rules['type']):
            return False
        
        # Check length
        if isinstance(value, str):
            if 'min_length' in rules and len(value) < rules['min_length']:
                return False
            if 'max_length' in rules and len(value) > rules['max_length']:
                return False
        
        # Check range
        if isinstance(value, (int, float)):
            if 'min' in rules and value < rules['min']:
                return False
            if 'max' in rules and value > rules['max']:
                return False
        
        # Check pattern
        if 'pattern' in rules and isinstance(value, str):
            if not re.match(rules['pattern'], value):
                return False
        
        return True
    
    return validator
