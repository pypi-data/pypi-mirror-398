"""A wrapper to wrap functions and timeout if they don't return in a certain amount of time"""

import threading
from typing import Optional, TypeVar, Callable, Any, Union, ParamSpec


T = TypeVar('T')
U = TypeVar('U')
P = ParamSpec('P')


class TimeoutError(Exception):
    """Raised when a function times out"""
    pass


def timeout_wrapper(seconds: float, default: U = None, raise_error: bool = True) -> Callable[[Callable[P, T]], Callable[P, Union[T, U]]]:
    """Decorator that applies a timeout to a function

    WARNING: this will NOT kill the thread that the wrapped function is in. That function will continue to run and
    eat up resources until it finishes itself.
    
    Args:
        seconds (float): Number of seconds to wait before timing out
        default (Any, optional): Value to return if function times out and raise_error is False
        raise_error (bool, optional): Whether to raise TimeoutError on timeout. If False, returns default value
        
    Returns:
        Callable: Decorated function that will timeout after specified seconds
    """
    def decorator(func: Callable[P, T]) -> Callable[P, Union[T, U]]:
        def wrapper(*args: Any, **kwargs: Any) -> Union[T, U]:
            # Make sure timeouts aren't negative. Do it here so the error is raised on call and possible to be caught
            if seconds < 0:
                raise ValueError("`seconds` parameter in timeout_wrapper() cannot be negative: %f" % seconds)
            
            result: Optional[T] = None
            error: Optional[Exception] = None
            done = threading.Event()
            
            def target() -> None:
                nonlocal result, error
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    error = e
                finally:
                    done.set()
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            
            if not done.wait(seconds):
                if raise_error:
                    raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
                return default
                
            if error is not None:
                raise error
                
            return result
            
        return wrapper
    return decorator