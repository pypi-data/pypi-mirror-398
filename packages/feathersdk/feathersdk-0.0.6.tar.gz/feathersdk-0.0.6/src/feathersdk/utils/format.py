"""Functions to nicely format objects into strings"""

import sys
import math
from typing import Any, Callable, Union
from .timeout import timeout_wrapper


_TOO_LARGE_CONCAT = '...'
_DEFAULT_MAX_STR_LEN = 5_000
_TIMEOUT_STRING = "[String conversion timeout]"


def strf_obj(obj: Any, str_limit: int = _DEFAULT_MAX_STR_LEN, format_func: Callable[[Any], str] = repr, timeout: float = 5.0) -> str:
    """Attempts to convert the given object to a string in a way that can never crash/hang
    
    If obj is a known type and wont break to be formatted with a known format_func (either str() or repr()), then it 
    will be directly formatted. Otherwise it will be formatted in a separate thread with a timeout applied.

    Args:
        obj (Any): the object to format
        str_limit (int): max size of the string to return in characters
        format_func (Callable[[Any], str]): function to format the string. Recommended to use either str or repr, but
            you can implement your own here if you wish
        timeout (float): timeout in seconds to convert the object to a string. If it cannot be converted, then a string
            saying so will be returned instead
    """
    #from .logger import logger as logging  # Here because of circular import
    import logging

    def _limit_size(string: str) -> str:
        return (string[:str_limit] + _TOO_LARGE_CONCAT) if len(string) > str_limit else string
    
    # Check if we have known format functions and object types
    if format_func in [str, repr]:
        # Integers can be arbitrarily long, so make sure they wont be converted unless it's a good size.
        # This will throw an error if not, so handle it nicely
        if type(obj) in [int]:
            n_digits = int(math.log10(abs(obj)))
            if n_digits < sys.get_int_max_str_digits() - 3:  # Just to make sure it is always smaller
                return _limit_size(format_func(obj))
            else:
                return _limit_size("[Integer with %d digits]" % n_digits)
        
        elif type(obj) in [str]:
            return format_func(_limit_size(obj))
        
        elif type(obj) in [bytes]:
            # Make sure the extra _TOO_LARGE_CONCAT string is there if needed
            return _limit_size(format_func(obj[:str_limit + len(_TOO_LARGE_CONCAT)]))
        
        # Types that don't need anything special applied to them
        elif type(obj) in [float, complex, bool] or obj in [None, Ellipsis]:
            return _limit_size(format_func(obj))
    
        logging.debug("Unknown strf_obj type: %s" % repr(type(obj).__name__))
    
    # Otherwise we don't know how to safely convert it, so run in a separate thread and timeout if needed
    result: Union[None, str] = timeout_wrapper(timeout, default=None, raise_error=False)(format_func)(obj)
    if result is None:
        logging.error("strf_obj() formatting timed out after %f seconds" % timeout)
        return _TIMEOUT_STRING
    return result
