from ctypes import *
from typing import List, Callable, Any
import os
import copy
import subprocess
import time
from enum import Enum
from filelock import FileLock, Timeout as FileLockTimeout

# Info for loading the library
_LIB = None
_LIB_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_SRC = os.path.join(_LIB_DIR, "socketcan_tcp.c")
_LIB_SO = os.path.join(_LIB_DIR, "libsocketcantcp.so")
_LIB_LOCK = os.path.join(_LIB_DIR, ".libsocketcantcp.so.lock")
_LIB_COMPILE_TIMEOUT_SECONDS = float(os.getenv("SOCKETCAN_COMPILE_TIMEOUT", "3.0"))


# C lib structure info
_SOCKET_NAME_MAX_LEN = 32
_CAN_DATA_SIZE = 8
_TCP_BUF_SIZE = 512
_MAX_ERR_STR_LEN = 1024
_POLL_TIMEOUT_MS = 1

class SocketType(Enum):
    UNINITIALIZED = 0
    CAN = 1
    TCP = 2
    ERROR = 3

class SocketResult(Structure):
    """Result of a socket operation. Can be a CAN message, a TCP message, or an error."""

    _fields_ = [
        ("result_type", c_uint8),
        ("socket_name", c_uint8 * _SOCKET_NAME_MAX_LEN),

        ("can_id", c_uint32),
        ("data", c_uint8 * _CAN_DATA_SIZE),
        ("dlc", c_uint8),

        ("tcp_buffer", c_uint8 * _TCP_BUF_SIZE),
        ("tcp_buf_len", c_uint32),

        ("err_type", c_int32),
        ("err_msg", c_uint8 * _MAX_ERR_STR_LEN),
    ]

    # Custom getter for uint8_t array fields to return bytes instead of ctypes array objects.
    def __getattribute__(self, name: str):
        ret = super().__getattribute__(name)

        if name == "socket_name" or name == "err_msg":
            return bytes(ret).partition(b"\0")[0].decode("ascii")
        elif type(type(ret)) is _C_ARRAY_TYPE:
            if ret._type_ is c_ubyte:
                return bytes(ret)
            else:
                raise TypeError(f"Unhandled array type: {type(ret).__name__}")
            
        return ret

    def __repr__(self) -> str:
        if self.result_type == SocketType.UNINITIALIZED.value:
            return "SocketResult(result_type=SocketType.UNINITIALIZED)"
        elif self.result_type == SocketType.CAN.value:
            return f"SocketResult(result_type=SocketType.CAN, socket_name={self.socket_name}, " \
                f"can_id={self.can_id}, data={self.data}, dlc={self.dlc})"
        elif self.result_type == SocketType.TCP.value:
            return f"SocketResult(result_type=SocketType.TCP, socket_name={self.socket_name}, " \
                f"tcp_buffer={self.tcp_buffer}, tcp_buf_len={self.tcp_buf_len})"
        elif self.result_type == SocketType.ERROR.value:
            return f"SocketResult(result_type=SocketType.ERROR, err_type={self.err_type}, " \
                f"err_msg={self.err_msg})"
        else:
            raise ValueError(f"Unhandled result type: {self.result_type}")
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def is_error(self) -> bool:
        """Check if the result is an error."""
        return self.result_type == SocketType.ERROR.value

class SCTSystemError(Exception):
    pass

class SCTOverflowError(Exception):
    pass

class SCTUserError(Exception):
    pass

class SCTTimeoutError(Exception):
    pass

class SCTErrorType(Enum):
    NO_OVERRIDE = -1
    NONE = 0
    SYSTEM = 1
    OVERFLOW = 2
    USER = 3
    TIMEOUT = 4

    @classmethod
    def raise_error(cls, err_type: int, err_msg: str) -> None:
        if err_type == cls.NO_OVERRIDE.value:
            raise ValueError("Should not be able to get NO_OVERRIDE error type!")
        elif err_type == cls.NONE.value:
            raise ValueError("No error occurred! Error message: " + err_msg)
        elif err_type == cls.SYSTEM.value:
            raise SCTSystemError(err_msg)
        elif err_type == cls.OVERFLOW.value:
            raise SCTOverflowError(err_msg)
        elif err_type == cls.USER.value:
            raise SCTUserError(err_msg)
        elif err_type == cls.TIMEOUT.value:
            raise SCTTimeoutError(err_msg)
        else:
            raise ValueError(f"Unhandled error type: {err_type}")


_MAIN_CALLBACK_TYPE = CFUNCTYPE(None, POINTER(SocketResult))


def __compile_load_lib() -> None:
    """Load the shared library, attempting to compile it if it doesn't exist. Should only be called in this file."""
    global _LIB
    
    try:
        with FileLock(_LIB_LOCK, timeout=_LIB_COMPILE_TIMEOUT_SECONDS, mode=0o666):
            # Check again if library exists (another process may have compiled it while we waited for the lock)
            if not os.path.exists(_LIB_SO):
                # Allow environment variable to override compile flags (useful for CI)
                compile_flags = os.getenv("SOCKETCAN_COMPILE_FLAGS", "-O3 -march=native -flto")
                cmd = ["gcc", "-fvisibility=hidden", "-shared"] + compile_flags.split() + ["-fPIC", "-o", _LIB_SO, _LIB_SRC]
                print(f"Compiling library {_LIB_SO} with command: ", " ".join(cmd))
                try:
                    subprocess.run(cmd, check=True, timeout=_LIB_COMPILE_TIMEOUT_SECONDS)
                    if not os.path.exists(_LIB_SO):
                        raise Exception(f"Library {_LIB_SO} didn't exist after compilation")
                except Exception as e:
                    print(f"Error compiling library {_LIB_SO}: {e}")
                    raise e
                print(f"Library {_LIB_SO} compiled successfully")
            
    except FileLockTimeout:
        # If we couldn't acquire the lock, another process is compiling. Wait for the library to appear and be complete
        start_time = time.time()
        while time.time() - start_time < _LIB_COMPILE_TIMEOUT_SECONDS:
            if os.path.exists(_LIB_SO):
                # Check if file size is stable (not being written)
                size1 = os.path.getsize(_LIB_SO)
                time.sleep(0.01)
                size2 = os.path.getsize(_LIB_SO)
                if size1 == size2 and size1 > 0:
                    break
            time.sleep(0.1)
        else:
            raise Exception(f"Library {_LIB_SO} was not compiled within {_LIB_COMPILE_TIMEOUT_SECONDS} seconds")
    
    # Load the library, and set up prototypes.
    _LIB = CDLL(_LIB_SO)

    _LIB.stop_polling.argtypes = None
    _LIB.stop_polling.restype = None

    _LIB.get_err_str.argtypes = [c_char_p]
    _LIB.get_err_str.restype = None

    _LIB.get_err_type.argtypes = None
    _LIB.get_err_type.restype = c_int32

    _LIB.clear_err_str.argtypes = None
    _LIB.clear_err_str.restype = None

    _LIB.cansend.argtypes = [c_char_p, c_bool, c_uint32, c_uint8 * _CAN_DATA_SIZE, c_uint8]
    _LIB.cansend.restype = c_int

    _LIB.tcpsend_modbus.argtypes = [c_char_p, c_uint16, c_uint16, c_uint8, c_uint16, c_uint16]
    _LIB.tcpsend_modbus.restype = c_int

    _LIB.comms_subscribe_multi.argtypes = [POINTER(c_char_p), c_int, _MAIN_CALLBACK_TYPE]
    _LIB.comms_subscribe_multi.restype = c_int

    _LIB.clear_all_sockets.argtypes = None
    _LIB.clear_all_sockets.restype = c_int


def _unload_socketcan_library(delete_lib: bool = False) -> None:
    """Unload the socketcan library, deleting the library .so file if requested.
    
    Mostly just used for testing purposes.

    Args:
        delete_lib: If True, will delete the library .so file after unloading it.
    """
    global _LIB
    _LIB = None
    if delete_lib and os.path.exists(_LIB_SO):
        os.remove(_LIB_SO)
    
    # Force the gc to run. Will unload the library so long as it has no more references.
    import gc
    gc.collect()


# All of the main super-types for C types. All c-types are derivatives of these.
_C_SIMPLE_TYPE = type(c_uint8)
_C_ARRAY_TYPE = type(c_uint8 * 2)
_C_POINTER_TYPE = type(POINTER(c_uint8))
_C_STRUCT_TYPE = type(Structure)
_C_FUNC_TYPE = type(CFUNCTYPE(None, c_uint8))
_C_SUPER_TYPES = set([_C_SIMPLE_TYPE, _C_ARRAY_TYPE, _C_POINTER_TYPE, _C_STRUCT_TYPE, _C_FUNC_TYPE])

# Bounds for the integer types in the library (since python doesn't have native integer bounds). Inclusive on both ends.
_SINT_TS = [c_int, c_int16, c_int32, c_int64, c_int8, c_long, c_longdouble, c_longlong, c_short, c_byte, c_char]
_UINT_TS = [c_size_t, c_ssize_t, c_ubyte, c_uint, c_uint16, c_uint32, c_uint64, c_uint8, c_ulong, c_ulonglong, c_ushort]
_INT_BOUNDS = {
    **{t: (-2**(8*sizeof(t)-1), 2**(8*sizeof(t)-1)-1) for t in _SINT_TS},
    **{t: (0, 2**(8*sizeof(t))-1) for t in _UINT_TS},
}

# Types that don't need validation.
_UNVALIDATED_SUPER_TYPES = set([_C_POINTER_TYPE, _C_STRUCT_TYPE, _C_FUNC_TYPE])
_UNVALIDATED_TYPES = set([c_void_p, c_char_p, c_wchar_p])


def __get_lib() -> CDLL:
    """Get the shared library, loading it if it isn't already loaded. Should only be called in this file."""
    global _LIB
    if _LIB is None:
        __compile_load_lib()
    return _LIB

def __check_for_error(result: int) -> None:
    """Check for an error in the result and raise the appropriate error."""
    if result != 0:
        err_type, err_str = _get_err_type(), _get_err_str()
        _clear_err_str()
        SCTErrorType.raise_error(err_type, err_str)

def __validate_simple_arg(arg: Any, arg_type: type) -> None:
    """Validate a simple argument."""
    if arg_type in _INT_BOUNDS:
        min_val, max_val = _INT_BOUNDS[arg_type]
        if not (min_val <= arg <= max_val):
            raise OverflowError(f"Argument {arg} out of bounds for type {arg_type.__name__}: [{min_val}, {max_val}]")
    elif arg_type is c_bool:
        if arg is not True and arg is not False:
            raise TypeError(f"Expected boolean, got {arg}")
    elif arg_type is c_float or arg_type is c_double:
        if arg_type(arg).value == float("inf"):
            raise OverflowError(f"Argument {arg} is infinity or too large to store in a {arg_type.__name__}")
    elif arg_type not in _UNVALIDATED_TYPES:
        raise ValueError(f"Unhandled simple C type: {arg_type.__name__}")

def __validate_and_call(func: Callable[[Any], Any], *args: Any) -> Any:
    """Validate the arguments and call the library function, returning the result
    
    Does some validation to make sure the arguments will work with the library function. Currently:
    - Ensures integer overflow/underflow will raise an error.
    - Ensured floats/doubles are not infinity or too large to store in a C type (unless they are already C types).
    - Ensures boolean args are exact booleans like True or False.
    """
    args = list(args)
    if func.argtypes is None and len(args) > 0:
        raise ValueError(f"Expected no arguments, got {len(args)}")
    elif func.argtypes is not None and len(args) != len(func.argtypes):
        raise ValueError(f"Expected {len(func.argtypes)} lib arguments, got {len(args)}")

    for i, (arg, arg_type) in enumerate(zip(args, func.argtypes or [])):
        # If the arg is already a C type, don't validate it.
        if type(type(arg)) in _C_SUPER_TYPES:
            continue
        
        # Simple and array types can be handled
        elif type(arg_type) is _C_SIMPLE_TYPE:
            __validate_simple_arg(arg, arg_type)
        elif type(arg_type) is _C_ARRAY_TYPE:
            if len(arg) != arg_type._length_:
                raise ValueError(f"Invalid length for array {arg_type.__name__}: {len(arg)} != {arg_type._length_}")
            for item in arg:
                __validate_simple_arg(item, arg_type._type_)
            args[i] = arg_type(*arg)  # Convert the iterable of items to a ctypes array.

        # Other types like structures and functions are assumed to be validated already.
        elif type(arg_type) not in _UNVALIDATED_SUPER_TYPES:
            raise ValueError(f"Unhandled argument super-type: {type(arg_type).__name__}")
    
    return __check_for_error(func(*args))


def _stop_polling() -> None:
    """Stop the infinite polling loop."""
    if _LIB is None:
        return
    __get_lib().stop_polling()

def _clear_all_sockets() -> None:
    """Clear all sockets."""
    if _LIB is None:
        return
    __validate_and_call(__get_lib().clear_all_sockets)

def _get_err_str() -> str:
    """Get the current error string from the library."""
    err_str = create_string_buffer(_MAX_ERR_STR_LEN)
    __get_lib().get_err_str(err_str)
    return err_str.value.decode("ascii")

def _get_err_type() -> int:
    """Get the current error type from the library."""
    return __get_lib().get_err_type()

def _clear_err_str() -> None:
    """Clear the current error string from the library."""
    __get_lib().clear_err_str()

def _cansend(interface: str, extended: bool, can_id: int, data: bytes) -> None:
    """Send a CAN message to the given interface."""
    __validate_and_call(__get_lib().cansend, interface.encode("ascii"), extended, can_id, data, len(data))

def _tcpsend_modbus(ip: str, tid: int, uid: int, fcode: int, reg_addr: int, reg_val: int) -> None:
    """Send a Modbus TCP message to the given IP address."""
    __validate_and_call(__get_lib().tcpsend_modbus, ip.encode("ascii"), tid, uid, fcode, reg_addr, reg_val)

def _subscribe_multi(endpoints: List[str], callback: Callable[[SocketResult], None]) -> None:
    """Subscribe to multiple endpoints and run infinite polling loop to call the callback for each message."""
    if len(endpoints) == 0:
        print("No endpoints to subscribe to, returning")
        return
    
    # Convert the ctypes LP_SocketResult to a Python SocketResult, and create a copy of the object
    _cb = lambda result: callback(copy.deepcopy(result.contents))  
    arr = (c_char_p * len(endpoints))(*[ep.encode("utf-8") for ep in endpoints])
    __validate_and_call(__get_lib().comms_subscribe_multi, arr, len(endpoints), _MAIN_CALLBACK_TYPE(_cb))


__all__ = ["SocketType", "SocketResult", "SCTSystemError", "SCTOverflowError", "SCTUserError", "SCTTimeoutError", 
           "SCTErrorType"]