"""
Email template and utilities
"""

from .template_engine import (
    EmailTemplate,
    TemplateEngine,
    render_template,
    create_html_email,
    create_text_email,
    validate_template,
    extract_variables,
)

__all__ = [
    'EmailTemplate',
    'TemplateEngine',
    'render_template',
    'create_html_email',
    'create_text_email',
    'validate_template',
    'extract_variables',
]
