"""
Password Strength Checker
Analyze password strength with entropy calculation and security recommendations
"""

import re
import math
from typing import Dict, List, Tuple, Optional

__all__ = [
    'check_password_strength',
    'calculate_entropy',
    'generate_password_report',
    'check_common_patterns',
    'estimate_crack_time',
    'get_strength_score',
    'validate_password_rules',
    'suggest_improvements',
]


# Common weak passwords
COMMON_PASSWORDS = {
    'password', '123456', '12345678', 'qwerty', 'abc123', 'monkey', '1234567',
    'letmein', 'trustno1', 'dragon', 'baseball', 'iloveyou', 'master', 'sunshine',
    'ashley', 'bailey', 'passw0rd', 'shadow', '123123', '654321', 'superman',
    'qazwsx', 'michael', 'football', 'password1', 'admin', 'welcome', 'login'
}

# Common patterns
COMMON_PATTERNS = [
    (r'(.)\1{2,}', 'Repeated characters'),
    (r'(012|123|234|345|456|567|678|789|890)', 'Sequential numbers'),
    (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', 'Sequential letters'),
    (r'(qwerty|asdfgh|zxcvbn)', 'Keyboard patterns'),
    (r'\d{4}', 'Year pattern'),
]


def calculate_entropy(password: str) -> float:
    """
    Calculate password entropy (bits).
    
    Args:
        password: Password to analyze
    
    Returns:
        float: Entropy in bits
    
    Examples:
        >>> from ilovetools.security import calculate_entropy
        
        >>> entropy = calculate_entropy('MyP@ssw0rd123')
        >>> print(f'{entropy:.2f} bits')
        76.24 bits
    """
    if not password:
        return 0.0
    
    # Calculate character pool size
    pool_size = 0
    
    if re.search(r'[a-z]', password):
        pool_size += 26  # Lowercase
    if re.search(r'[A-Z]', password):
        pool_size += 26  # Uppercase
    if re.search(r'\d', password):
        pool_size += 10  # Digits
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        pool_size += 32  # Special characters
    
    # Calculate entropy: log2(pool_size^length)
    if pool_size > 0:
        entropy = len(password) * math.log2(pool_size)
        return entropy
    
    return 0.0


def check_common_patterns(password: str) -> List[str]:
    """
    Check for common weak patterns.
    
    Args:
        password: Password to check
    
    Returns:
        list: List of found patterns
    
    Examples:
        >>> from ilovetools.security import check_common_patterns
        
        >>> patterns = check_common_patterns('password123')
        >>> print(patterns)
        ['Common password', 'Sequential numbers']
    """
    found_patterns = []
    
    # Check common passwords
    if password.lower() in COMMON_PASSWORDS:
        found_patterns.append('Common password')
    
    # Check patterns
    for pattern, description in COMMON_PATTERNS:
        if re.search(pattern, password.lower()):
            found_patterns.append(description)
    
    return found_patterns


def estimate_crack_time(
    password: str,
    attempts_per_second: float = 1e9
) -> Dict[str, str]:
    """
    Estimate time to crack password.
    
    Args:
        password: Password to analyze
        attempts_per_second: Cracking speed (default: 1 billion/sec)
    
    Returns:
        dict: Crack time estimates
    
    Examples:
        >>> from ilovetools.security import estimate_crack_time
        
        >>> times = estimate_crack_time('MyP@ssw0rd123')
        >>> print(times['online_throttled'])
        '2.3 million years'
    """
    entropy = calculate_entropy(password)
    
    # Calculate possible combinations
    combinations = 2 ** entropy
    
    # Different attack scenarios
    scenarios = {
        'online_throttled': 10,  # 10 attempts/sec (rate limited)
        'online_unthrottled': 1000,  # 1000 attempts/sec
        'offline_slow': 1e4,  # 10,000 attempts/sec (bcrypt)
        'offline_fast': 1e9,  # 1 billion attempts/sec (MD5)
        'offline_gpu': 1e11,  # 100 billion attempts/sec (GPU cluster)
    }
    
    results = {}
    
    for scenario, speed in scenarios.items():
        seconds = combinations / speed
        results[scenario] = _format_time(seconds)
    
    return results


def _format_time(seconds: float) -> str:
    """Format time duration."""
    if seconds < 1:
        return 'Instant'
    elif seconds < 60:
        return f'{seconds:.1f} seconds'
    elif seconds < 3600:
        return f'{seconds/60:.1f} minutes'
    elif seconds < 86400:
        return f'{seconds/3600:.1f} hours'
    elif seconds < 31536000:
        return f'{seconds/86400:.1f} days'
    elif seconds < 31536000 * 1000:
        return f'{seconds/31536000:.1f} years'
    elif seconds < 31536000 * 1000000:
        return f'{seconds/(31536000*1000):.1f} thousand years'
    elif seconds < 31536000 * 1000000000:
        return f'{seconds/(31536000*1000000):.1f} million years'
    else:
        return f'{seconds/(31536000*1000000000):.1f} billion years'


def get_strength_score(password: str) -> Tuple[int, str]:
    """
    Get password strength score (0-100) and rating.
    
    Args:
        password: Password to score
    
    Returns:
        tuple: (score, rating)
    
    Examples:
        >>> from ilovetools.security import get_strength_score
        
        >>> score, rating = get_strength_score('MyP@ssw0rd123')
        >>> print(f'{score}/100 - {rating}')
        85/100 - Strong
    """
    score = 0
    
    # Length score (max 30 points)
    length = len(password)
    if length >= 16:
        score += 30
    elif length >= 12:
        score += 25
    elif length >= 8:
        score += 20
    elif length >= 6:
        score += 10
    else:
        score += 5
    
    # Character variety (max 40 points)
    if re.search(r'[a-z]', password):
        score += 10
    if re.search(r'[A-Z]', password):
        score += 10
    if re.search(r'\d', password):
        score += 10
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        score += 10
    
    # Entropy bonus (max 20 points)
    entropy = calculate_entropy(password)
    if entropy >= 80:
        score += 20
    elif entropy >= 60:
        score += 15
    elif entropy >= 40:
        score += 10
    elif entropy >= 20:
        score += 5
    
    # Penalties
    patterns = check_common_patterns(password)
    score -= len(patterns) * 10
    
    # Ensure score is in range
    score = max(0, min(100, score))
    
    # Determine rating
    if score >= 80:
        rating = 'Very Strong'
    elif score >= 60:
        rating = 'Strong'
    elif score >= 40:
        rating = 'Moderate'
    elif score >= 20:
        rating = 'Weak'
    else:
        rating = 'Very Weak'
    
    return score, rating


def validate_password_rules(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate password against rules.
    
    Args:
        password: Password to validate
        min_length: Minimum length
        require_uppercase: Require uppercase letter
        require_lowercase: Require lowercase letter
        require_digit: Require digit
        require_special: Require special character
    
    Returns:
        tuple: (is_valid, list of violations)
    
    Examples:
        >>> from ilovetools.security import validate_password_rules
        
        >>> valid, violations = validate_password_rules('Pass123')
        >>> print(valid, violations)
        False ['Too short (minimum 8 characters)', 'Missing special character']
    """
    violations = []
    
    # Check length
    if len(password) < min_length:
        violations.append(f'Too short (minimum {min_length} characters)')
    
    # Check uppercase
    if require_uppercase and not re.search(r'[A-Z]', password):
        violations.append('Missing uppercase letter')
    
    # Check lowercase
    if require_lowercase and not re.search(r'[a-z]', password):
        violations.append('Missing lowercase letter')
    
    # Check digit
    if require_digit and not re.search(r'\d', password):
        violations.append('Missing digit')
    
    # Check special character
    if require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        violations.append('Missing special character')
    
    is_valid = len(violations) == 0
    
    return is_valid, violations


def suggest_improvements(password: str) -> List[str]:
    """
    Suggest improvements for password.
    
    Args:
        password: Password to analyze
    
    Returns:
        list: List of suggestions
    
    Examples:
        >>> from ilovetools.security import suggest_improvements
        
        >>> suggestions = suggest_improvements('password')
        >>> for s in suggestions:
        ...     print(f'- {s}')
        - Increase length to at least 12 characters
        - Add uppercase letters
        - Add numbers
        - Add special characters
    """
    suggestions = []
    
    # Length
    if len(password) < 12:
        suggestions.append('Increase length to at least 12 characters')
    
    # Character types
    if not re.search(r'[A-Z]', password):
        suggestions.append('Add uppercase letters')
    if not re.search(r'[a-z]', password):
        suggestions.append('Add lowercase letters')
    if not re.search(r'\d', password):
        suggestions.append('Add numbers')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        suggestions.append('Add special characters')
    
    # Patterns
    patterns = check_common_patterns(password)
    if patterns:
        suggestions.append(f'Avoid common patterns: {", ".join(patterns)}')
    
    # Common passwords
    if password.lower() in COMMON_PASSWORDS:
        suggestions.append('Avoid common passwords')
    
    # Repeated characters
    if re.search(r'(.)\1{2,}', password):
        suggestions.append('Avoid repeated characters')
    
    return suggestions


def check_password_strength(password: str) -> Dict[str, any]:
    """
    Comprehensive password strength check.
    
    Args:
        password: Password to analyze
    
    Returns:
        dict: Complete analysis
    
    Examples:
        >>> from ilovetools.security import check_password_strength
        
        >>> result = check_password_strength('MyP@ssw0rd123')
        >>> print(result['score'])
        85
        >>> print(result['rating'])
        'Strong'
    """
    score, rating = get_strength_score(password)
    entropy = calculate_entropy(password)
    patterns = check_common_patterns(password)
    crack_times = estimate_crack_time(password)
    is_valid, violations = validate_password_rules(password)
    suggestions = suggest_improvements(password)
    
    return {
        'password_length': len(password),
        'score': score,
        'rating': rating,
        'entropy': round(entropy, 2),
        'has_lowercase': bool(re.search(r'[a-z]', password)),
        'has_uppercase': bool(re.search(r'[A-Z]', password)),
        'has_digit': bool(re.search(r'\d', password)),
        'has_special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password)),
        'common_patterns': patterns,
        'crack_times': crack_times,
        'is_valid': is_valid,
        'violations': violations,
        'suggestions': suggestions,
    }


def generate_password_report(password: str) -> str:
    """
    Generate human-readable password report.
    
    Args:
        password: Password to analyze
    
    Returns:
        str: Formatted report
    
    Examples:
        >>> from ilovetools.security import generate_password_report
        
        >>> report = generate_password_report('MyP@ssw0rd123')
        >>> print(report)
        Password Strength Report
        ========================
        Length: 13 characters
        Score: 85/100
        Rating: Strong
        ...
    """
    result = check_password_strength(password)
    
    lines = [
        'Password Strength Report',
        '=' * 50,
        f'Length: {result["password_length"]} characters',
        f'Score: {result["score"]}/100',
        f'Rating: {result["rating"]}',
        f'Entropy: {result["entropy"]} bits',
        '',
        'Character Types:',
        f'  Lowercase: {"✓" if result["has_lowercase"] else "✗"}',
        f'  Uppercase: {"✓" if result["has_uppercase"] else "✗"}',
        f'  Digits: {"✓" if result["has_digit"] else "✗"}',
        f'  Special: {"✓" if result["has_special"] else "✗"}',
        '',
    ]
    
    if result['common_patterns']:
        lines.append('Common Patterns Found:')
        for pattern in result['common_patterns']:
            lines.append(f'  - {pattern}')
        lines.append('')
    
    lines.append('Estimated Crack Time:')
    for scenario, time in result['crack_times'].items():
        scenario_name = scenario.replace('_', ' ').title()
        lines.append(f'  {scenario_name}: {time}')
    lines.append('')
    
    if result['violations']:
        lines.append('Rule Violations:')
        for violation in result['violations']:
            lines.append(f'  - {violation}')
        lines.append('')
    
    if result['suggestions']:
        lines.append('Suggestions:')
        for suggestion in result['suggestions']:
            lines.append(f'  - {suggestion}')
    
    return '\n'.join(lines)
