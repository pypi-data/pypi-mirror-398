"""
Advanced Logging Utility
Structured logging with multiple formatters and handlers
"""

import sys
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

__all__ = [
    'Logger',
    'LogLevel',
    'JSONFormatter',
    'ColoredFormatter',
    'StructuredLogger',
    'create_logger',
    'log_execution_time',
    'log_errors',
]


class LogLevel(Enum):
    """Log levels."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class JSONFormatter:
    """
    JSON log formatter.
    
    Examples:
        >>> from ilovetools.utils import JSONFormatter
        
        >>> formatter = JSONFormatter()
        >>> formatted = formatter.format('INFO', 'Test message', {'key': 'value'})
    """
    
    def format(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format log entry as JSON.
        
        Args:
            level: Log level
            message: Log message
            context: Additional context
        
        Returns:
            str: JSON formatted log
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message
        }
        
        if context:
            log_entry['context'] = context
        
        return json.dumps(log_entry)


class ColoredFormatter:
    """
    Colored console log formatter.
    
    Examples:
        >>> from ilovetools.utils import ColoredFormatter
        
        >>> formatter = ColoredFormatter()
        >>> formatted = formatter.format('INFO', 'Test message')
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format log entry with colors.
        
        Args:
            level: Log level
            message: Log message
            context: Additional context
        
        Returns:
            str: Colored formatted log
        """
        color = self.COLORS.get(level, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted = f"{color}[{timestamp}] {level}{reset}: {message}"
        
        if context:
            formatted += f" {context}"
        
        return formatted


class Logger:
    """
    Advanced logger with multiple formatters.
    
    Examples:
        >>> from ilovetools.utils import Logger
        
        >>> logger = Logger(name='myapp')
        >>> logger.info('Application started')
        >>> logger.error('Error occurred', {'error_code': 500})
    """
    
    def __init__(
        self,
        name: str = 'app',
        level: LogLevel = LogLevel.INFO,
        formatter: Optional[Any] = None,
        output: Optional[Any] = None
    ):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            level: Minimum log level
            formatter: Log formatter
            output: Output stream (default: stdout)
        """
        self.name = name
        self.level = level
        self.formatter = formatter or ColoredFormatter()
        self.output = output or sys.stdout
        self.handlers = []
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Internal log method."""
        if level.value < self.level.value:
            return
        
        # Add logger name to context
        if context is None:
            context = {}
        context['logger'] = self.name
        
        # Format message
        formatted = self.formatter.format(level.name, message, context)
        
        # Write to output
        self.output.write(formatted + '\n')
        self.output.flush()
        
        # Call handlers
        for handler in self.handlers:
            handler(level, message, context)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, context)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log(LogLevel.INFO, message, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log(LogLevel.ERROR, message, context)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, context)
    
    def add_handler(self, handler):
        """Add custom handler."""
        self.handlers.append(handler)
    
    def set_level(self, level: LogLevel):
        """Set log level."""
        self.level = level


class StructuredLogger:
    """
    Structured logger with field support.
    
    Examples:
        >>> from ilovetools.utils import StructuredLogger
        
        >>> logger = StructuredLogger(name='api')
        >>> logger.with_fields({'user_id': 123}).info('User logged in')
    """
    
    def __init__(
        self,
        name: str = 'app',
        level: LogLevel = LogLevel.INFO,
        base_fields: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            level: Minimum log level
            base_fields: Base fields for all logs
        """
        self.name = name
        self.level = level
        self.base_fields = base_fields or {}
        self.formatter = JSONFormatter()
        self.output = sys.stdout
    
    def with_fields(self, fields: Dict[str, Any]) -> 'StructuredLogger':
        """
        Create logger with additional fields.
        
        Args:
            fields: Additional fields
        
        Returns:
            StructuredLogger: New logger instance
        """
        new_logger = StructuredLogger(
            name=self.name,
            level=self.level,
            base_fields={**self.base_fields, **fields}
        )
        new_logger.formatter = self.formatter
        new_logger.output = self.output
        return new_logger
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        fields: Optional[Dict[str, Any]] = None
    ):
        """Internal log method."""
        if level.value < self.level.value:
            return
        
        # Merge fields
        context = {**self.base_fields}
        if fields:
            context.update(fields)
        
        # Format and write
        formatted = self.formatter.format(level.name, message, context)
        self.output.write(formatted + '\n')
        self.output.flush()
    
    def debug(self, message: str, fields: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, fields)
    
    def info(self, message: str, fields: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log(LogLevel.INFO, message, fields)
    
    def warning(self, message: str, fields: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, fields)
    
    def error(self, message: str, fields: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log(LogLevel.ERROR, message, fields)
    
    def critical(self, message: str, fields: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, fields)


def create_logger(
    name: str = 'app',
    level: str = 'INFO',
    format_type: str = 'colored',
    output_file: Optional[str] = None
) -> Logger:
    """
    Create logger with configuration.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Formatter type (colored, json)
        output_file: Output file path
    
    Returns:
        Logger: Configured logger
    
    Examples:
        >>> from ilovetools.utils import create_logger
        
        >>> logger = create_logger('myapp', level='DEBUG', format_type='json')
        >>> logger.info('Application started')
    """
    # Parse level
    log_level = LogLevel[level.upper()]
    
    # Create formatter
    if format_type == 'json':
        formatter = JSONFormatter()
    else:
        formatter = ColoredFormatter()
    
    # Create output
    if output_file:
        output = open(output_file, 'a')
    else:
        output = sys.stdout
    
    return Logger(
        name=name,
        level=log_level,
        formatter=formatter,
        output=output
    )


def log_execution_time(logger: Optional[Logger] = None):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger instance
    
    Examples:
        >>> from ilovetools.utils import log_execution_time, create_logger
        
        >>> logger = create_logger('myapp')
        >>> @log_execution_time(logger)
        ... def slow_function():
        ...     time.sleep(1)
    """
    if logger is None:
        logger = create_logger()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"Function '{func.__name__}' executed",
                    {'execution_time': f'{execution_time:.4f}s'}
                )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(
                    f"Function '{func.__name__}' failed",
                    {
                        'execution_time': f'{execution_time:.4f}s',
                        'error': str(e)
                    }
                )
                raise
        
        return wrapper
    
    return decorator


def log_errors(logger: Optional[Logger] = None, reraise: bool = True):
    """
    Decorator to log function errors.
    
    Args:
        logger: Logger instance
        reraise: Re-raise exception after logging
    
    Examples:
        >>> from ilovetools.utils import log_errors, create_logger
        
        >>> logger = create_logger('myapp')
        >>> @log_errors(logger)
        ... def risky_function():
        ...     raise ValueError('Something went wrong')
    """
    if logger is None:
        logger = create_logger()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Error in '{func.__name__}'",
                    {
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                )
                
                if reraise:
                    raise
        
        return wrapper
    
    return decorator
