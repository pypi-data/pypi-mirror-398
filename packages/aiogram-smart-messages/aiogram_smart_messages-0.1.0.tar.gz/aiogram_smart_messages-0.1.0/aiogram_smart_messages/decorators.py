import logging, inspect
from functools import wraps
from typing import Callable, Any, Optional

def with_error_logging(
    logger: Optional[logging.Logger] = None,
    fallback: Any = None,
    error_label: str = "UNKNOWN_ERROR",
):
    """
    Универсальный декоратор для логирования ошибок функции.
    Подходит как для sync, так и для async функций.
    """

    def decorator(func: Callable):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.exception(f"[{error_label}] Exception in {func.__name__}: {e}")
                    return fallback
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.exception(f"[{error_label}] Exception in {func.__name__}: {e}")
                    return fallback
            return sync_wrapper
    return decorator