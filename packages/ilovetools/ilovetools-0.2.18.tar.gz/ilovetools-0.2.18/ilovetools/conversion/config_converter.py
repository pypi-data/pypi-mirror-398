"""
Configuration File Converter
Convert between JSON, YAML, TOML, XML, and INI formats
"""

import json
import re
from typing import Any, Dict, List, Union, Optional
from collections import OrderedDict

__all__ = [
    'json_to_yaml',
    'yaml_to_json',
    'json_to_toml',
    'toml_to_json',
    'json_to_xml',
    'xml_to_json',
    'json_to_ini',
    'ini_to_json',
    'dict_to_yaml',
    'yaml_to_dict',
    'dict_to_toml',
    'toml_to_dict',
    'validate_json',
    'validate_yaml',
    'minify_json',
    'prettify_json',
]


def validate_json(json_string: str) -> tuple:
    """
    Validate JSON string.
    
    Args:
        json_string: JSON string to validate
    
    Returns:
        tuple: (is_valid, error_message)
    
    Examples:
        >>> from ilovetools.conversion import validate_json
        
        >>> valid, error = validate_json('{"key": "value"}')
        >>> print(valid)
        True
        
        >>> valid, error = validate_json('{invalid}')
        >>> print(valid, error)
        False 'Expecting property name...'
    """
    try:
        json.loads(json_string)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)


def minify_json(json_string: str) -> str:
    """
    Minify JSON string (remove whitespace).
    
    Args:
        json_string: JSON string to minify
    
    Returns:
        str: Minified JSON
    
    Examples:
        >>> from ilovetools.conversion import minify_json
        
        >>> json_str = '''
        ... {
        ...   "key": "value",
        ...   "number": 123
        ... }
        ... '''
        >>> minified = minify_json(json_str)
        >>> print(minified)
        '{"key":"value","number":123}'
    """
    data = json.loads(json_string)
    return json.dumps(data, separators=(',', ':'))


def prettify_json(
    json_string: str,
    indent: int = 2,
    sort_keys: bool = False
) -> str:
    """
    Prettify JSON string with indentation.
    
    Args:
        json_string: JSON string to prettify
        indent: Indentation spaces
        sort_keys: Sort keys alphabetically
    
    Returns:
        str: Prettified JSON
    
    Examples:
        >>> from ilovetools.conversion import prettify_json
        
        >>> json_str = '{"key":"value","number":123}'
        >>> pretty = prettify_json(json_str)
        >>> print(pretty)
        {
          "key": "value",
          "number": 123
        }
    """
    data = json.loads(json_string)
    return json.dumps(data, indent=indent, sort_keys=sort_keys)


def dict_to_yaml(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Convert Python dict to YAML string.
    
    Args:
        data: Dictionary to convert
        indent: Indentation spaces
    
    Returns:
        str: YAML string
    
    Examples:
        >>> from ilovetools.conversion import dict_to_yaml
        
        >>> data = {'name': 'John', 'age': 30, 'skills': ['Python', 'JS']}
        >>> yaml_str = dict_to_yaml(data)
        >>> print(yaml_str)
        name: John
        age: 30
        skills:
          - Python
          - JS
    """
    def _convert(obj, level=0):
        indent_str = ' ' * (indent * level)
        lines = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{indent_str}{key}:")
                    lines.append(_convert(value, level + 1))
                elif value is None:
                    lines.append(f"{indent_str}{key}: null")
                elif isinstance(value, bool):
                    lines.append(f"{indent_str}{key}: {str(value).lower()}")
                elif isinstance(value, str):
                    # Escape special characters
                    if ':' in value or '#' in value or value.startswith((' ', '-')):
                        value = f'"{value}"'
                    lines.append(f"{indent_str}{key}: {value}")
                else:
                    lines.append(f"{indent_str}{key}: {value}")
        
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent_str}-")
                    lines.append(_convert(item, level + 1))
                elif item is None:
                    lines.append(f"{indent_str}- null")
                elif isinstance(item, bool):
                    lines.append(f"{indent_str}- {str(item).lower()}")
                elif isinstance(item, str):
                    if ':' in item or '#' in item or item.startswith((' ', '-')):
                        item = f'"{item}"'
                    lines.append(f"{indent_str}- {item}")
                else:
                    lines.append(f"{indent_str}- {item}")
        
        return '\n'.join(lines)
    
    return _convert(data)


def yaml_to_dict(yaml_string: str) -> Dict[str, Any]:
    """
    Convert YAML string to Python dict.
    
    Args:
        yaml_string: YAML string to parse
    
    Returns:
        dict: Parsed dictionary
    
    Examples:
        >>> from ilovetools.conversion import yaml_to_dict
        
        >>> yaml_str = '''
        ... name: John
        ... age: 30
        ... skills:
        ...   - Python
        ...   - JS
        ... '''
        >>> data = yaml_to_dict(yaml_str)
        >>> print(data)
        {'name': 'John', 'age': 30, 'skills': ['Python', 'JS']}
    """
    lines = yaml_string.strip().split('\n')
    result = {}
    stack = [(result, -1)]
    current_list = None
    
    for line in lines:
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        # Calculate indentation
        indent = len(line) - len(line.lstrip())
        line = line.strip()
        
        # Handle list items
        if line.startswith('- '):
            value = line[2:].strip()
            
            # Remove quotes
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            # Convert types
            if value == 'null':
                value = None
            elif value == 'true':
                value = True
            elif value == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            elif re.match(r'^-?\d+\.\d+$', value):
                value = float(value)
            
            if current_list is not None:
                current_list.append(value)
            continue
        
        # Handle key-value pairs
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            
            # Pop stack to correct level
            while stack and stack[-1][1] >= indent:
                stack.pop()
            
            parent = stack[-1][0]
            
            if not value or value == '':
                # Empty value - could be dict or list
                new_dict = {}
                parent[key] = new_dict
                stack.append((new_dict, indent))
                current_list = None
            elif value == '[]':
                parent[key] = []
                current_list = None
            elif value == '{}':
                parent[key] = {}
                current_list = None
            else:
                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Convert types
                if value == 'null':
                    value = None
                elif value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif re.match(r'^-?\d+\.\d+$', value):
                    value = float(value)
                
                parent[key] = value
                current_list = None
    
    return result


def json_to_yaml(json_string: str, indent: int = 2) -> str:
    """
    Convert JSON to YAML.
    
    Args:
        json_string: JSON string
        indent: YAML indentation
    
    Returns:
        str: YAML string
    
    Examples:
        >>> from ilovetools.conversion import json_to_yaml
        
        >>> json_str = '{"name": "John", "age": 30}'
        >>> yaml_str = json_to_yaml(json_str)
        >>> print(yaml_str)
        name: John
        age: 30
    """
    data = json.loads(json_string)
    return dict_to_yaml(data, indent)


def yaml_to_json(
    yaml_string: str,
    indent: Optional[int] = 2,
    sort_keys: bool = False
) -> str:
    """
    Convert YAML to JSON.
    
    Args:
        yaml_string: YAML string
        indent: JSON indentation (None for minified)
        sort_keys: Sort keys alphabetically
    
    Returns:
        str: JSON string
    
    Examples:
        >>> from ilovetools.conversion import yaml_to_json
        
        >>> yaml_str = '''
        ... name: John
        ... age: 30
        ... '''
        >>> json_str = yaml_to_json(yaml_str)
        >>> print(json_str)
        {
          "name": "John",
          "age": 30
        }
    """
    data = yaml_to_dict(yaml_string)
    return json.dumps(data, indent=indent, sort_keys=sort_keys)


def dict_to_toml(data: Dict[str, Any]) -> str:
    """
    Convert Python dict to TOML string.
    
    Args:
        data: Dictionary to convert
    
    Returns:
        str: TOML string
    
    Examples:
        >>> from ilovetools.conversion import dict_to_toml
        
        >>> data = {
        ...     'title': 'Config',
        ...     'database': {'host': 'localhost', 'port': 5432}
        ... }
        >>> toml_str = dict_to_toml(data)
        >>> print(toml_str)
        title = "Config"
        
        [database]
        host = "localhost"
        port = 5432
    """
    lines = []
    
    def _format_value(value):
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            items = [_format_value(item) for item in value]
            return f"[{', '.join(items)}]"
        elif value is None:
            return '""'
        return str(value)
    
    # First pass: simple key-value pairs
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f'{key} = {_format_value(value)}')
    
    # Second pass: tables (nested dicts)
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f'\n[{key}]')
            for sub_key, sub_value in value.items():
                if not isinstance(sub_value, dict):
                    lines.append(f'{sub_key} = {_format_value(sub_value)}')
    
    return '\n'.join(lines)


def toml_to_dict(toml_string: str) -> Dict[str, Any]:
    """
    Convert TOML string to Python dict.
    
    Args:
        toml_string: TOML string to parse
    
    Returns:
        dict: Parsed dictionary
    
    Examples:
        >>> from ilovetools.conversion import toml_to_dict
        
        >>> toml_str = '''
        ... title = "Config"
        ... 
        ... [database]
        ... host = "localhost"
        ... port = 5432
        ... '''
        >>> data = toml_to_dict(toml_str)
        >>> print(data)
        {'title': 'Config', 'database': {'host': 'localhost', 'port': 5432}}
    """
    result = {}
    current_section = result
    
    for line in toml_string.strip().split('\n'):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Handle sections
        if line.startswith('[') and line.endswith(']'):
            section_name = line[1:-1].strip()
            current_section = {}
            result[section_name] = current_section
            continue
        
        # Handle key-value pairs
        if '=' in line:
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()
            
            # Remove quotes
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            # Handle arrays
            elif value.startswith('[') and value.endswith(']'):
                array_str = value[1:-1]
                items = [item.strip().strip('"\'') for item in array_str.split(',')]
                value = items
            # Convert types
            elif value == 'true':
                value = True
            elif value == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            elif re.match(r'^-?\d+\.\d+$', value):
                value = float(value)
            
            current_section[key] = value
    
    return result


def json_to_toml(json_string: str) -> str:
    """
    Convert JSON to TOML.
    
    Args:
        json_string: JSON string
    
    Returns:
        str: TOML string
    
    Examples:
        >>> from ilovetools.conversion import json_to_toml
        
        >>> json_str = '{"title": "Config", "database": {"host": "localhost"}}'
        >>> toml_str = json_to_toml(json_str)
        >>> print(toml_str)
        title = "Config"
        
        [database]
        host = "localhost"
    """
    data = json.loads(json_string)
    return dict_to_toml(data)


def toml_to_json(
    toml_string: str,
    indent: Optional[int] = 2,
    sort_keys: bool = False
) -> str:
    """
    Convert TOML to JSON.
    
    Args:
        toml_string: TOML string
        indent: JSON indentation
        sort_keys: Sort keys alphabetically
    
    Returns:
        str: JSON string
    
    Examples:
        >>> from ilovetools.conversion import toml_to_json
        
        >>> toml_str = '''
        ... title = "Config"
        ... [database]
        ... host = "localhost"
        ... '''
        >>> json_str = toml_to_json(toml_str)
        >>> print(json_str)
        {
          "title": "Config",
          "database": {
            "host": "localhost"
          }
        }
    """
    data = toml_to_dict(toml_string)
    return json.dumps(data, indent=indent, sort_keys=sort_keys)


def json_to_xml(json_string: str, root_tag: str = 'root') -> str:
    """
    Convert JSON to XML.
    
    Args:
        json_string: JSON string
        root_tag: Root XML tag name
    
    Returns:
        str: XML string
    
    Examples:
        >>> from ilovetools.conversion import json_to_xml
        
        >>> json_str = '{"name": "John", "age": 30}'
        >>> xml_str = json_to_xml(json_str)
        >>> print(xml_str)
        <root>
          <name>John</name>
          <age>30</age>
        </root>
    """
    data = json.loads(json_string)
    
    def _dict_to_xml(obj, indent=0):
        indent_str = '  ' * indent
        lines = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{indent_str}<{key}>")
                    lines.append(_dict_to_xml(value, indent + 1))
                    lines.append(f"{indent_str}</{key}>")
                else:
                    lines.append(f"{indent_str}<{key}>{value}</{key}>")
        
        elif isinstance(obj, list):
            for item in obj:
                lines.append(f"{indent_str}<item>")
                if isinstance(item, (dict, list)):
                    lines.append(_dict_to_xml(item, indent + 1))
                else:
                    lines.append(f"{'  ' * (indent + 1)}{item}")
                lines.append(f"{indent_str}</item>")
        
        return '\n'.join(lines)
    
    xml_body = _dict_to_xml(data, 1)
    return f"<{root_tag}>\n{xml_body}\n</{root_tag}>"


def xml_to_json(xml_string: str, indent: Optional[int] = 2) -> str:
    """
    Convert XML to JSON (simple implementation).
    
    Args:
        xml_string: XML string
        indent: JSON indentation
    
    Returns:
        str: JSON string
    
    Examples:
        >>> from ilovetools.conversion import xml_to_json
        
        >>> xml_str = '<root><name>John</name><age>30</age></root>'
        >>> json_str = xml_to_json(xml_str)
        >>> print(json_str)
        {
          "name": "John",
          "age": "30"
        }
    """
    # Simple XML parsing
    result = {}
    
    # Remove root tag
    xml_string = re.sub(r'<\?xml[^>]+\?>', '', xml_string)
    xml_string = xml_string.strip()
    
    # Find root tag
    root_match = re.match(r'<([^>]+)>(.*)</\1>', xml_string, re.DOTALL)
    if root_match:
        xml_string = root_match.group(2)
    
    # Extract tags
    pattern = r'<([^/>]+)>([^<]+)</\1>'
    matches = re.findall(pattern, xml_string)
    
    for tag, value in matches:
        tag = tag.strip()
        value = value.strip()
        
        # Try to convert to number
        if value.isdigit():
            value = int(value)
        elif re.match(r'^-?\d+\.\d+$', value):
            value = float(value)
        
        result[tag] = value
    
    return json.dumps(result, indent=indent)


def json_to_ini(json_string: str) -> str:
    """
    Convert JSON to INI format.
    
    Args:
        json_string: JSON string
    
    Returns:
        str: INI string
    
    Examples:
        >>> from ilovetools.conversion import json_to_ini
        
        >>> json_str = '{"database": {"host": "localhost", "port": 5432}}'
        >>> ini_str = json_to_ini(json_str)
        >>> print(ini_str)
        [database]
        host = localhost
        port = 5432
    """
    data = json.loads(json_string)
    lines = []
    
    for section, values in data.items():
        lines.append(f'[{section}]')
        
        if isinstance(values, dict):
            for key, value in values.items():
                lines.append(f'{key} = {value}')
        else:
            lines.append(f'value = {values}')
        
        lines.append('')
    
    return '\n'.join(lines)


def ini_to_json(ini_string: str, indent: Optional[int] = 2) -> str:
    """
    Convert INI to JSON.
    
    Args:
        ini_string: INI string
        indent: JSON indentation
    
    Returns:
        str: JSON string
    
    Examples:
        >>> from ilovetools.conversion import ini_to_json
        
        >>> ini_str = '''
        ... [database]
        ... host = localhost
        ... port = 5432
        ... '''
        >>> json_str = ini_to_json(ini_str)
        >>> print(json_str)
        {
          "database": {
            "host": "localhost",
            "port": "5432"
          }
        }
    """
    result = {}
    current_section = None
    
    for line in ini_string.strip().split('\n'):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith(('#', ';')):
            continue
        
        # Handle sections
        if line.startswith('[') and line.endswith(']'):
            section_name = line[1:-1].strip()
            current_section = {}
            result[section_name] = current_section
            continue
        
        # Handle key-value pairs
        if '=' in line and current_section is not None:
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()
            
            # Try to convert to number
            if value.isdigit():
                value = int(value)
            elif re.match(r'^-?\d+\.\d+$', value):
                value = float(value)
            
            current_section[key] = value
    
    return json.dumps(result, indent=indent)


def validate_yaml(yaml_string: str) -> tuple:
    """
    Validate YAML string.
    
    Args:
        yaml_string: YAML string to validate
    
    Returns:
        tuple: (is_valid, error_message)
    
    Examples:
        >>> from ilovetools.conversion import validate_yaml
        
        >>> valid, error = validate_yaml('name: John\\nage: 30')
        >>> print(valid)
        True
    """
    try:
        yaml_to_dict(yaml_string)
        return True, None
    except Exception as e:
        return False, str(e)
