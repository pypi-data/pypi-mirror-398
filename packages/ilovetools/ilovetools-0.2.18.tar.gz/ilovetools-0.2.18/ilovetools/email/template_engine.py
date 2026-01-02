"""
Email Template Engine
Dynamic email generation with variable substitution and HTML support
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

__all__ = [
    'EmailTemplate',
    'TemplateEngine',
    'render_template',
    'create_html_email',
    'create_text_email',
    'validate_template',
    'extract_variables',
]


class EmailTemplate:
    """
    Email template with variable substitution.
    
    Examples:
        >>> from ilovetools.email import EmailTemplate
        
        >>> template = EmailTemplate(
        ...     subject='Hello {{name}}',
        ...     body='Welcome {{name}}! Your code is {{code}}.'
        ... )
        >>> email = template.render({'name': 'John', 'code': '12345'})
    """
    
    def __init__(
        self,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None
    ):
        """
        Initialize email template.
        
        Args:
            subject: Email subject with variables
            body: Plain text body with variables
            html_body: HTML body with variables
            from_email: From email address
            reply_to: Reply-to email address
        """
        self.subject = subject
        self.body = body
        self.html_body = html_body
        self.from_email = from_email
        self.reply_to = reply_to
    
    def render(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """
        Render template with variables.
        
        Args:
            variables: Variable values
        
        Returns:
            dict: Rendered email
        
        Examples:
            >>> template = EmailTemplate('Hello {{name}}', 'Welcome {{name}}!')
            >>> email = template.render({'name': 'John'})
            >>> print(email['subject'])
            'Hello John'
        """
        # Add default variables
        default_vars = {
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_time': datetime.now().strftime('%H:%M:%S'),
            'current_year': datetime.now().year,
        }
        
        # Merge variables
        all_vars = {**default_vars, **variables}
        
        # Render subject
        subject = self._substitute(self.subject, all_vars)
        
        # Render body
        body = self._substitute(self.body, all_vars)
        
        # Render HTML body
        html_body = None
        if self.html_body:
            html_body = self._substitute(self.html_body, all_vars)
        
        return {
            'subject': subject,
            'body': body,
            'html_body': html_body,
            'from_email': self.from_email,
            'reply_to': self.reply_to
        }
    
    def _substitute(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in text."""
        result = text
        
        # Find all variables {{var}}
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, text)
        
        for var in matches:
            if var in variables:
                value = str(variables[var])
                result = result.replace(f'{{{{{var}}}}}', value)
        
        return result
    
    def get_variables(self) -> List[str]:
        """
        Get all variables in template.
        
        Returns:
            list: Variable names
        """
        variables = set()
        
        # Extract from subject
        variables.update(self._extract_vars(self.subject))
        
        # Extract from body
        variables.update(self._extract_vars(self.body))
        
        # Extract from HTML body
        if self.html_body:
            variables.update(self._extract_vars(self.html_body))
        
        return list(variables)
    
    def _extract_vars(self, text: str) -> List[str]:
        """Extract variables from text."""
        pattern = r'\{\{(\w+)\}\}'
        return re.findall(pattern, text)


class TemplateEngine:
    """
    Email template engine with template management.
    
    Examples:
        >>> from ilovetools.email import TemplateEngine
        
        >>> engine = TemplateEngine()
        >>> engine.add_template('welcome', subject='Welcome {{name}}', body='Hello {{name}}!')
        >>> email = engine.render('welcome', {'name': 'John'})
    """
    
    def __init__(self):
        """Initialize template engine."""
        self.templates = {}
    
    def add_template(
        self,
        name: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None
    ):
        """
        Add template to engine.
        
        Args:
            name: Template name
            subject: Email subject
            body: Email body
            html_body: HTML body
            from_email: From email
            reply_to: Reply-to email
        
        Examples:
            >>> engine = TemplateEngine()
            >>> engine.add_template('welcome', 'Welcome!', 'Hello {{name}}!')
        """
        template = EmailTemplate(
            subject=subject,
            body=body,
            html_body=html_body,
            from_email=from_email,
            reply_to=reply_to
        )
        self.templates[name] = template
    
    def render(self, name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """
        Render template by name.
        
        Args:
            name: Template name
            variables: Variable values
        
        Returns:
            dict: Rendered email
        
        Examples:
            >>> engine = TemplateEngine()
            >>> engine.add_template('welcome', 'Welcome!', 'Hello {{name}}!')
            >>> email = engine.render('welcome', {'name': 'John'})
        """
        if name not in self.templates:
            raise ValueError(f'Template "{name}" not found')
        
        return self.templates[name].render(variables)
    
    def get_template(self, name: str) -> EmailTemplate:
        """
        Get template by name.
        
        Args:
            name: Template name
        
        Returns:
            EmailTemplate: Template
        """
        if name not in self.templates:
            raise ValueError(f'Template "{name}" not found')
        
        return self.templates[name]
    
    def list_templates(self) -> List[str]:
        """
        List all template names.
        
        Returns:
            list: Template names
        """
        return list(self.templates.keys())
    
    def delete_template(self, name: str) -> bool:
        """
        Delete template.
        
        Args:
            name: Template name
        
        Returns:
            bool: True if deleted
        """
        if name in self.templates:
            del self.templates[name]
            return True
        return False


def render_template(template: str, variables: Dict[str, Any]) -> str:
    """
    Render template string with variables.
    
    Args:
        template: Template string
        variables: Variable values
    
    Returns:
        str: Rendered string
    
    Examples:
        >>> from ilovetools.email import render_template
        
        >>> result = render_template('Hello {{name}}!', {'name': 'John'})
        >>> print(result)
        'Hello John!'
    """
    result = template
    
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, template)
    
    for var in matches:
        if var in variables:
            value = str(variables[var])
            result = result.replace(f'{{{{{var}}}}}', value)
    
    return result


def create_html_email(
    subject: str,
    heading: str,
    content: str,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None,
    footer: Optional[str] = None
) -> str:
    """
    Create HTML email with standard layout.
    
    Args:
        subject: Email subject
        heading: Main heading
        content: Email content
        button_text: Button text
        button_url: Button URL
        footer: Footer text
    
    Returns:
        str: HTML email
    
    Examples:
        >>> from ilovetools.email import create_html_email
        
        >>> html = create_html_email(
        ...     subject='Welcome',
        ...     heading='Welcome to our service!',
        ...     content='Thank you for signing up.',
        ...     button_text='Get Started',
        ...     button_url='https://example.com'
        ... )
    """
    button_html = ''
    if button_text and button_url:
        button_html = f'''
        <table border="0" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
            <tr>
                <td style="background-color: #007bff; border-radius: 4px; padding: 12px 24px;">
                    <a href="{button_url}" style="color: #ffffff; text-decoration: none; font-weight: bold;">
                        {button_text}
                    </a>
                </td>
            </tr>
        </table>
        '''
    
    footer_html = ''
    if footer:
        footer_html = f'''
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 12px;">
            {footer}
        </div>
        '''
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #333; margin-bottom: 20px;">{heading}</h1>
        <div style="margin-bottom: 20px;">
            {content}
        </div>
        {button_html}
        {footer_html}
    </body>
    </html>
    '''
    
    return html


def create_text_email(
    subject: str,
    greeting: str,
    content: str,
    signature: Optional[str] = None
) -> str:
    """
    Create plain text email.
    
    Args:
        subject: Email subject
        greeting: Greeting text
        content: Email content
        signature: Signature
    
    Returns:
        str: Plain text email
    
    Examples:
        >>> from ilovetools.email import create_text_email
        
        >>> text = create_text_email(
        ...     subject='Welcome',
        ...     greeting='Hello John,',
        ...     content='Thank you for signing up!',
        ...     signature='Best regards,\\nThe Team'
        ... )
    """
    parts = [greeting, '', content]
    
    if signature:
        parts.extend(['', signature])
    
    return '\n'.join(parts)


def validate_template(template: str) -> tuple:
    """
    Validate template syntax.
    
    Args:
        template: Template string
    
    Returns:
        tuple: (is_valid, errors)
    
    Examples:
        >>> from ilovetools.email import validate_template
        
        >>> valid, errors = validate_template('Hello {{name}}!')
        >>> print(valid)
        True
    """
    errors = []
    
    # Check for unclosed variables
    open_count = template.count('{{')
    close_count = template.count('}}')
    
    if open_count != close_count:
        errors.append('Unclosed variable brackets')
    
    # Check for invalid variable names
    pattern = r'\{\{(\w+)\}\}'
    matches = re.findall(pattern, template)
    
    # Check for nested variables
    if '{{' in template.replace('{{', '', 1):
        nested_pattern = r'\{\{[^}]*\{\{'
        if re.search(nested_pattern, template):
            errors.append('Nested variables not allowed')
    
    return len(errors) == 0, errors


def extract_variables(template: str) -> List[str]:
    """
    Extract all variables from template.
    
    Args:
        template: Template string
    
    Returns:
        list: Variable names
    
    Examples:
        >>> from ilovetools.email import extract_variables
        
        >>> vars = extract_variables('Hello {{name}}, your code is {{code}}')
        >>> print(vars)
        ['name', 'code']
    """
    pattern = r'\{\{(\w+)\}\}'
    return re.findall(pattern, template)
