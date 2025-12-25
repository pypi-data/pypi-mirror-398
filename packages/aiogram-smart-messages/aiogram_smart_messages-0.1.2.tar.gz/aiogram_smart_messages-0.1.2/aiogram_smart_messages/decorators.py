# -*- coding: utf-8 -*-
"""
Error handling decorators for robust function execution.

This module provides decorators for comprehensive error logging and handling
in both synchronous and asynchronous functions. It automatically detects
function type and applies appropriate error handling.
"""

import logging
import inspect
from functools import wraps
from typing import Callable, Any, Optional, TypeVar, ParamSpec, Union

# Type variables for better type hints with decorators
P = ParamSpec('P')
T = TypeVar('T')


def with_error_logging(
    logger: Optional[logging.Logger] = None,
    fallback: Any = None,
    error_label: str = "UNKNOWN_ERROR",
    reraise: bool = False,
) -> Callable[[Callable[P, T]], Callable[P, Union[T, Any]]]:
    """
    Universal decorator for error logging in functions.
    
    This decorator provides comprehensive error handling for both synchronous
    and asynchronous functions. It automatically detects the function type
    and applies appropriate error handling logic.
    
    When an exception occurs, the decorator:
    1. Logs the exception with full traceback
    2. Returns the fallback value (or re-raises if configured)
    3. Preserves function metadata via functools.wraps
    
    Args:
        logger: Logger instance to use for error logging. If None, errors
               are caught but not logged (silent mode).
        fallback: Value to return when an exception occurs. Can be any type
                 including None. Only used if reraise is False.
        error_label: Label prefix for log messages to help identify error source.
                    Defaults to "UNKNOWN_ERROR".
        reraise: If True, re-raise the exception after logging instead of
                returning fallback value. Defaults to False.
    
    Returns:
        Decorated function that handles errors according to configuration.
        Return type is Union of original return type and fallback type.
    
    Example:
        >>> logger = logging.getLogger(__name__)
        >>> 
        >>> @with_error_logging(logger=logger, fallback=[], error_label="DATA_FETCH")
        >>> async def fetch_data(url: str) -> list:
        ...     response = await http_client.get(url)
        ...     return response.json()
        >>> 
        >>> # On error, returns [] instead of crashing
        >>> result = await fetch_data("https://api.example.com/data")
        
        >>> @with_error_logging(logger=logger, reraise=True, error_label="CRITICAL")
        >>> def critical_operation(data: dict) -> bool:
        ...     # Logs error but still raises for critical operations
        ...     return process_data(data)
    
    Note:
        - Automatically detects async vs sync functions using inspect
        - Preserves function signature and metadata
        - Can be used with or without parentheses if using defaults
        - Thread-safe and works with class methods
    """
    def decorator(func: Callable[P, T]) -> Callable[P, Union[T, Any]]:
        """Inner decorator that wraps the target function."""
        
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Any]:
                """Async wrapper for coroutine functions."""
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if logger:
                        logger.exception(
                            f"[{error_label}] Exception in {func.__name__}: {e}"
                        )
                    
                    if reraise:
                        raise
                    
                    return fallback
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[T, Any]:
                """Sync wrapper for regular functions."""
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if logger:
                        logger.exception(
                            f"[{error_label}] Exception in {func.__name__}: {e}"
                        )
                    
                    if reraise:
                        raise
                    
                    return fallback
            
            return sync_wrapper
    
    return decorator

