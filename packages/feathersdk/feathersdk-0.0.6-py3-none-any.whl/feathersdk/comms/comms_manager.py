# gcc -fPIC -shared -o libsocketcantcp.so socketcan_tcp.c -lpthread && python3 test_app.py
import threading
import time
from typing import Optional, Callable, Any
from typing_extensions import Self
from .system import is_can_interface, enable_can_interface, is_can_enabled
from .socketcan_tcp import _subscribe_multi, _cansend, _tcpsend_modbus, SocketResult, _stop_polling, \
    _clear_all_sockets, _POLL_TIMEOUT_MS
import math
from collections import namedtuple


class SocketCANLibError(Exception):
    """Error raised when the socketcan library returns a non-zero error code."""
    pass

class CanOverloadError(Exception):
    """Error raised when the CAN bus is overloaded."""
    pass

class UnknownInterfaceError(Exception):
    """Error raised when the interface is not an interface, or is not being tracked by CommsManager."""
    def __init__(self, interface: str):
        super().__init__(f"Interface {interface} is not an interface, or is not being tracked by CommsManager")

class CommsManagerNotRunningError(Exception):
    """Error raised when the comms manager is not running."""
    def __init__(self):
        super().__init__("CommsManager is not running")

class CanNotEnabledError(Exception):
    """Error raised when a CAN interface is not enabled."""
    def __init__(self, interface: str):
        super().__init__(f"CAN interface \"{interface}\" is not enabled")


# We calculate the maximum number of messages that can be sent over a CAN bus per second using math similar to:
# https://electronics.stackexchange.com/questions/121329/whats-the-maximum-can-bus-frame-message-rate-at-125-kbit-s
# 
# Including all the extra overhead, CRC, bit stuffing, etc, we get a theoretical 144 bits per frame. At 1Mbs, this
# would be a theoretical max of 6944 frames per second. Since most all messages we send will have 1 reply from the
# device, we divide by 2 to get 3472 messages-sent per second. To give us ~10% leeway, we limit to 3000 messages-sent
# per second on average.
# 
# Using our exponential decay formula of N_{x+1} = N_x * e^(-t * decay_rate) + decay_scale, and a decay rate of 0.01,
# experiments (see /playground/justin_exp_decay_math.py) show that at a rate of 3000 messages-sent per second, the
# decayed-count maxes out at ~300. So, we use this limit here.
CAN_BUS_DECAY_LIMIT: float = 300.0;
CAN_BUS_DECAY_RATE: float = 0.01;
CAN_BUS_DECAY_SCALE: float = 10.0;  # Controls how quickly we reach our limit. Higher=more quicker.
                                    # Value of 10.0 = ~30 messages before limit at full speed, ~50 at 100us/message


LoadAndTime = namedtuple("LoadAndTime", ["load", "last_message_time"])


class CommsManager:
    """Handles sending and receiving messages over CAN and TCP.

    Provides a single point of entry for sending and receiving messages over CAN and TCP. Any new instances of this
    class will point to the same instance.

    The manager also checks for message overload on the CAN bus and will raise an error if the message rate is too high.
    """

    _instance: Optional[Self] = None
    """The singleton instance of the CommsManager. Do not modify at runtime!!!"""

    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> Self:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CommsManager, cls).__new__(cls)
                cls._instance.__reset()
            return cls._instance
    
    def __reset(self) -> None:
        """Reset the comms manager to a clean state. Assumes you have the lock already."""
        if hasattr(self, "thread") and self.is_running():
            raise ValueError("Cannot reset CommsManager while it is running")
        
        self.thread = None
        self.is_dry = False
        self._callbacks: list[Callable[[SocketResult], None]] = []
        self.endpoints: list[str] = []
        self._can_loads: dict[str, LoadAndTime] = {}
        self.__overload_check = True
    
    def _DANGEROUS_disable_overload_check(self) -> None:
        """WARNING: Only use this for testing!"""
        with self._lock:
            self.__overload_check = False

    def set_is_dry(self, is_dry: bool) -> None:
        """Enable/disable 'dry run' mode.

        In dry run mode, the comms manager will not send any messages, and instead just print info about them
        """
        with self._lock:
            self.is_dry = is_dry

    def start(self, endpoints: list[str], enable_cans: bool = True, allow_no_enable_can: bool = False) -> None:
        """Start the comms manager
        
        This will start a background thread that will poll all the endpoints and call the callback for each message.

        Will call `enable_can_interface` for each endpoint that is a CAN interface with default bitrate of 1Mbs. Will
        create vCAN interfaces for each endpoint that is a vCAN interface.

        Args:
            endpoints: list of endpoints to subscribe to, eg: ["can0", "vcan1", "192.168.11.210"], etc.
            enable_cans: If True, will attempt to enable any CAN interface that is not already enabled.
            allow_no_enable_can: If True, will not raise an error if any of the CAN interfaces are not enabled.
        """
        with self._lock:
            if self.is_running():
                raise ValueError("CommsManager is already running")
            
            for ep in endpoints:
                if is_can_interface(ep):
                    try:
                        if not is_can_enabled(ep, bitrate=1_000_000):
                            if not enable_cans:
                                raise CanNotEnabledError(ep)
                            enable_can_interface(ep, bitrate=1_000_000)
                    except Exception as e:
                        if not allow_no_enable_can:
                            raise e
                        else:
                            print(f"Warning: Could not enable CAN interface {ep}: {e}, for the robot to work properly, run `sudo ip link set {ep} up`")
            
            self.endpoints = endpoints
            self._can_loads = {ep: LoadAndTime(0.0, 0.0) for ep in endpoints if is_can_interface(ep)}
            self.thread = threading.Thread(target=_subscribe_multi, args=(endpoints, self.__main_callback), daemon=True)
            self.thread.start()
    
    def add_callback(self, callback: Callable[[SocketResult], None]) -> None:
        """Add a callback to be called for each message."""
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[SocketResult], None]) -> None:
        """Remove a callback from being called for each message."""
        with self._lock:
            self._callbacks.remove(callback)
    
    def close(self) -> None:
        """Close the comms manager.
        
        This will stop the background thread and close all the endpoints.
        """
        with self._lock:
            if not self.is_running():
                raise CommsManagerNotRunningError()
        
            _stop_polling()
            time.sleep((_POLL_TIMEOUT_MS / 1000.0) * 1.5)  # Give it a bit of extra time to stop polling

            if self.is_running():
                raise SystemError("CommsManager is still running after closing")
            
            _clear_all_sockets()
            self.__reset()
    
    def __main_callback(self, result: SocketResult) -> None:
        """Called by libsocketcantcp library to notify us of a new message."""
        if result.is_error():
            print(f"Error in comms manager callback: {result.err_type} - {result.err_msg}")
            return
        
        for callback in self._callbacks:
            callback(result)
    
    def is_running(self) -> bool:
        """Check if the background polling thread is currently running."""
        return self.thread is not None and self.thread.is_alive()

    def cansend(self, interface: str, extended: bool, can_id: int, data: bytes) -> None:
        """Send a CAN message.
        
        Args:
            interface: The interface to send the message on.
            extended: Whether the message is an extended (29-bit) CAN message, or a standard (11-bit) CAN message.
            can_id: The CAN ID of the message. Must be in the range [0-0x1FFFFFFF] for extended messages, or 
                [0-0x7FF] for standard messages.
            data: The data to send in the message. Must be 8 bytes long.
        """
        if self.is_dry:
            print("Dry cansend: ", interface, can_id, data)
            return
        
        with self._lock:
            # Make sure we are not overloading the CAN bus
            if interface not in self._can_loads:
                raise UnknownInterfaceError(interface)
            
            if self.__overload_check:
                dt_ms = (time.monotonic() - self._can_loads[interface].last_message_time) * 1000.0 * CAN_BUS_DECAY_SCALE
                new_load = self._can_loads[interface].load * math.exp(-dt_ms * CAN_BUS_DECAY_RATE) + CAN_BUS_DECAY_SCALE
                if new_load > CAN_BUS_DECAY_LIMIT:
                    raise CanOverloadError(f"CAN bus {interface} is overloaded")
            
                self._can_loads[interface] = LoadAndTime(load=new_load, last_message_time=time.monotonic()) 
            
        self._run_and_check(_cansend, interface, extended, can_id, data)

    def tcpsend_modbus(self, ip: str, tid: int, uid: int, fcode: int, reg_addr: int, reg_val: int) -> None:
        """Send a Modbus TCP message."""
        if self.is_dry:
            print("dry tcpsend", ip, tid, uid, fcode, reg_addr, reg_val)
            return
        
        self._run_and_check(_tcpsend_modbus, ip, tid, uid, fcode, reg_addr, reg_val)
    
    def _run_and_check(self, func: Callable[[Any], None], *args: Any) -> None:
        """Run a library function and check the result. If the result is non-zero, print a warning."""
        if not self.is_running():
            raise CommsManagerNotRunningError()
        func(*args)
