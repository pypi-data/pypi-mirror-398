import warnings
import functools

def deprecated(reason: str = None):
    def decorator(func):
        message = f"The function {func.__name__} is DEPRECATED."
        if reason:
            message += f" Reason: {reason}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
