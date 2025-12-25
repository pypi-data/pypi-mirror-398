import warnings
from functools import wraps
from typing import Any, Callable


def deprecated(reason: str = "") -> Callable:
    """
    标记函数为已弃用的装饰器

    Example:
        @deprecated("use CtrlConnection.screenshot instead")
        def old_screenshot():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(f"{func.__name__} is deprecated. {reason}", category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator
