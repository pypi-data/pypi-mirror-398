"""Our own custom python logger"""

import os
import sys
import inspect
import logging
import traceback
from datetime import datetime
from .format import strf_obj, _DEFAULT_MAX_STR_LEN
from typing import Optional, Union, Any, TextIO, Type

_LOGGER: Optional[logging.Logger] = None

DEBUG, INFO, WARNING, ERROR, CRITICAL = logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL

_UNKNOWN_MODULE_STR = "unknown_module"


def _init_logging(file_logging_level: int = logging.DEBUG, console_logging_level: int = logging.INFO, 
                  console_out: TextIO = sys.stdout) -> None:
    """Initialize logging to both a log file and to console"""
    global _LOGGER
        
    # Create logs directory if it doesn't exist, and the timestamped log file
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'featheros-%s.log' % datetime.now().strftime('%Y%m%d_%H%M%S'))
    
    # Configure logger
    _LOGGER = logging.getLogger('featheros')
    _LOGGER.setLevel(logging.DEBUG)
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s %(message)s')
    
    # File/console handlers
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_logging_level)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(stream=console_out)
    console_handler.setLevel(console_logging_level)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    #_LOGGER.addHandler(file_handler)
    _LOGGER.addHandler(console_handler)

    info("Logging initialized in file: %s" % log_file)


def _format_message(message: str, *args: Any) -> str:
    """Safely format the args into the message"""
    try:
        formatted_objs = [strf_obj(obj) for obj in args]
        try:
            message = message.format(*formatted_objs)
        except Exception as e:
            args_str = ('[' + ','.join(formatted_objs[:_DEFAULT_MAX_STR_LEN]) + ']')[:_DEFAULT_MAX_STR_LEN]
            message = "[%s] EXCEPTION: could not format message with given args - error when calling message.format()\n\tLog Message: %s\n\tArgs: %s\n\tTraceback: %s" % \
                (_get_message_module_name(1), repr(message[:_DEFAULT_MAX_STR_LEN]), args_str, traceback.format_exc()[:_DEFAULT_MAX_STR_LEN])
    except Exception as e:
        message = "[%s] EXCEPTION: could not format message with given args - error when formatting objects with strf_obj()\n\tLog Message: %s\n\tTraceback: %s" % \
            (_get_message_module_name(1), repr(message[:_DEFAULT_MAX_STR_LEN]), traceback.format_exc()[:_DEFAULT_MAX_STR_LEN])


def log(level: Union[str, int], message: str, *args: Any, _call_chain=2) -> None:
    """Log a message with the specified level
    
    Messages are logged both to a time-stamped file that was created on initialization of this module, and to the
    console. By default, the file logging has DEBUG level, and console has INFO level. Messages will be logged with
    the format:

    "TIME - LEVEL [MODULE_NAME]: MESSAGE"

    Args:
        level (Union[str, int]): the log level. By default, DEBUG and above will be logged to file while INFO and above
            will be logged to console. Can be either integer logging level, or string name of logging level
        message (str): the message to log
        args (Any): additional arguments to be formatted safely and inserted into the string with .format()
    """
    _LOGGER.log(_get_level(level), "[%s]: %s" % (_get_message_module_name(_call_chain), _format_message(message, args)))

def debug(message: str, *args: str) -> None:
    """Log a debug message
    
    Args:
        message (str): the message to log
        args (Any): additional arguments to be formatted safely and inserted into the string with .format()
    """
    log(logging.DEBUG, message, *args, _call_chain=3)

def info(message: str, *args: str) -> None:
    """Log an info message
    
    Args:
        message (str): the message to log
        args (Any): additional arguments to be formatted safely and inserted into the string with .format()
    """
    log(logging.INFO, message, *args, _call_chain=3)

def warning(message: str, *args: str) -> None:
    """Log a warning message
    
    Args:
        message (str): the message to log
        args (Any): additional arguments to be formatted safely and inserted into the string with .format()
    """
    log(logging.WARNING, message, *args, _call_chain=3)

def error(message: str, *args: str) -> None:
    """Log an error message
    
    Args:
        message (str): the message to log
        args (Any): additional arguments to be formatted safely and inserted into the string with .format()
    """
    log(logging.ERROR, message, *args, _call_chain=3)

def critical(message: str, *args: str, exc_type: Optional[Type[Exception]] = None) -> None:
    """Log a critical message
    
    Args:
        message (str): the message to log
        args (Any): additional arguments to be formatted safely and inserted into the string with .format()
        exc_type (Optional[Type[Exception]]): if passed, then an exception will be raised of this type with the formatted
            error message passed in as the only argument in type construction
    """
    log(logging.CRITICAL, message, *args, _call_chain=3)
    if exc_type is not None:
        raise exc_type(_format_message(message, args))

# Don't allow recursion here
_IN_GET_LEVEL_ERROR = False
def _get_level(level: Union[str, int]) -> int:
    """Checks to make sure this is a known level, then returns the log level"""
    global _IN_GET_LEVEL_ERROR

    if isinstance(level, int):
        if level in (DEBUG, INFO, WARNING, ERROR, CRITICAL):
            return level
        if not _IN_GET_LEVEL_ERROR:
            _IN_GET_LEVEL_ERROR = True
            log(ERROR, "Invalid integer logging level value: {0}", level)
            _IN_GET_LEVEL_ERROR = False
            return DEBUG
        else:
            raise ValueError("Invalid integer logging level value: %s" % strf_obj(level))
        
    if isinstance(level, str):
        level = level.upper()
        if level == "DEBUG":
            return DEBUG
        if level == "INFO":
            return INFO
        if level == "WARNING":
            return WARNING
        if level == "ERROR":
            return ERROR
        if level == "CRITICAL":
            return CRITICAL
        if not _IN_GET_LEVEL_ERROR:
            _IN_GET_LEVEL_ERROR = True
            log(ERROR, "Invalid string logging level value: {0}", level)
            _IN_GET_LEVEL_ERROR = False
            return DEBUG
        else:
            raise ValueError("Invalid string logging level value: %s" % repr(level[:300]))
        
    if not _IN_GET_LEVEL_ERROR:
        _IN_GET_LEVEL_ERROR = True
        log(ERROR, "Log level must be string or integer, got: {0}", type(level))
        _IN_GET_LEVEL_ERROR = False
        return DEBUG
    else:
        raise ValueError("Log level must be string or integer, got: %s" % type(level))


def _get_message_module_name(call_chain: int) -> str:
    """Returns the name of the module that the function two upwards on the stack belongs to or 'unknown' if it cannot be determined
    
    Args:
        call_chain (int): the number of frames to go upwards in the call chain to find the calling function. Will likely
            be either 2 if log() was called, or 3 if one of the other log functions was called
    """
    try:
        # Get the current stack frame
        frame = inspect.currentframe()

        # Walk up the call chain to get the frame of the function that called logging
        for _ in range(call_chain):
            frame = frame.f_back
            if frame is None:
                return _UNKNOWN_MODULE_STR
        
        # Get the module name from the frame
        module = inspect.getmodule(frame)
        return _UNKNOWN_MODULE_STR if module is None else module.__name__
    except Exception:
        return _UNKNOWN_MODULE_STR + " EXCEPTION"


# Always leave this at the end of the file
_init_logging()
