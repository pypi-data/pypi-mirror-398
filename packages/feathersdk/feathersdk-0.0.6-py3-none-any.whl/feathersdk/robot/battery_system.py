import asyncio
import threading
import time
from .steppable_system import SteppableSystem
from .motors.motors_manager import MotorsManager
from ..utils import constants
from ..utils.files import read_json_file
from abc import ABC, abstractmethod
from enum import Enum
from smbus2 import SMBus, i2c_msg

def i2c_write(bus, addr, data):
    msg = i2c_msg.write(addr, data)
    bus.i2c_rdwr(msg)

def i2c_read(bus, addr, reg, length):
    write = i2c_msg.write(addr, [reg])
    read = i2c_msg.read(addr, length)
    bus.i2c_rdwr(write, read)
    return list(read)

class PowerEvent(Enum):
    POWER_OFF = 1
    POWER_RESTORED = 2

class PowerEventListener(ABC):
    @abstractmethod
    def on_power_event(self, event: PowerEvent):
        pass

class BatterySystem(SteppableSystem):

    def __init__(self):
        super().__init__()
        self.operating_frequency = 4
        self.power_event_listeners = []

    def add_power_event_listener(self, listener):
        self.power_event_listeners.append(listener)

    def remove_power_event_listener(self, listener):
        self.power_event_listeners.remove(listener)

    def notify_power_event_listeners(self, event: PowerEvent):
        for listener in self.power_event_listeners:
            listener.on_power_event(event)

    def get_battery_voltage(self):
        pass

    def last_powered_up_time(self):
        pass


class DualBatterySystem(BatterySystem):

    I2C_DEV_BUS = 1
    ADS1115_ADDR = 0x48
    CONFIG_REG = 0x01
    CONV_REG = 0x00

    ESTOP_VOLTAGE_THRESHOLD = 45
    
    def __init__(self, config: dict = {}):
        super().__init__()
        self.battery_voltage = 0
        self.update_power_state()
        self.cfg = config
        self.rated_voltage = config.get("rated_voltage", 48)
        self.capacity_amp_hours = config.get("capacity_amp_hours", 50)
        self.num_batteries = config.get("num_batteries", 2)
        try:
            self.get_battery_voltage()
        except Exception:
            raise Exception("Warning: Battery monitoring is not healthy.")

    def _step(self):
        last_estop_pressed_time = self.last_estop_pressed_time
        last_estop_released_time = self.last_estop_released_time
        self.update_power_state()
        if self.last_estop_pressed_time != last_estop_pressed_time:
            self.notify_power_event_listeners(PowerEvent.POWER_OFF)
        if self.last_estop_released_time != last_estop_released_time:
            self.notify_power_event_listeners(PowerEvent.POWER_RESTORED)

    def update_power_state(self):
        state = read_json_file(constants.POWER_STATE_PATH)
        self.battery_monitoring_healthy = state.get("battery_monitoring_healthy")
        self.current_boot_time = state.get("boot_time")
        self.last_estop_pressed_time = state.get("last_estop_pressed_time")
        self.last_estop_released_time = state.get("last_estop_released_time")
        self.last_reliable_seen_voltage = state.get("last_reliable_seen_voltage")
        self.state_update_time = state.get("state_update_time")


        if not self.battery_monitoring_healthy:
            raise Exception("Battery monitoring is not healthy.")

    def is_estop_pressed(self):
        return self.get_battery_voltage() < self.ESTOP_VOLTAGE_THRESHOLD

    def last_powered_up_time(self):
        return max(self.current_boot_time or 0, self.last_estop_released_time or 0)

    def get_battery_voltage(self):
        with SMBus(self.I2C_DEV_BUS) as bus:
            # Configure ADS1115
            config = [
                self.CONFIG_REG,
                0xC0,  # AIN0, single-shot, PGA bits
                0x83   # 128 SPS, comparator disabled
            ]
            i2c_write(bus, self.ADS1115_ADDR, config)

            # Wait for conversion (~8 ms at 128 SPS)
            time.sleep(0.009)

            # Read conversion register
            data = i2c_read(bus, self.ADS1115_ADDR, self.CONV_REG, 2)

            # Combine bytes (signed 16-bit)
            raw_adc = (data[0] << 8) | data[1]
            if raw_adc & 0x8000:
                raw_adc -= 0x10000

            # Convert to voltage (ADS1115 input)
            voltage = (raw_adc * 6.114) / 32768.0

            # Apply resistor divider scaling (same as C code)
            return voltage * 11
