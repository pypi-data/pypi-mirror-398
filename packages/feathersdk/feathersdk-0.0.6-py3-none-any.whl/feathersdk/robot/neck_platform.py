import math
from .steppable_system import SteppableSystem
from .motors.motors_manager import MotorsManager, Motor
from ..comms import CommsManager, SocketResult
from ..comms.comms_manager import UnknownInterfaceError
from enum import Enum
import asyncio
import time
import struct

class MyActuatorCommands(Enum):
    READ_PID = 0x30
    WRITE_PID_TEMP = 0x31 # writes to RAM
    WRITE_PID_PERM = 0x32 # writes to ROM
    SET_ACCELERATION = 0x43
    SET_POSITION = 0xA4
    SET_INCREMENTAL_POSITION = 0xA8
    ZERO_POSITION = 0x64
    RESET_MOTOR = 0x76
    SHUTDOWN_MOTOR = 0x80
    GET_STATE = 0x9C
    HEALTH_CHECK = 0x9A
    ID_CHECK = 0x79

class MyActuatorPIDParams(Enum):
    CURRENT_KP = 0x01
    CURRENT_KI = 0x02
    SPEED_KP = 0x04
    SPEED_KI = 0x05
    POSITION_KP = 0x07
    POSITION_KI = 0x08
    POSITION_KD = 0x09

class MyActuatorErrorState(Enum):
    NO_ERROR = "0000"
    MOTOR_STALL = "0002"
    LOW_VOLTAGE = "0004"
    OVER_VOLTAGE = "0008"
    OVER_CURRENT = "0010"
    POWER_OVERRUN = "0040"
    CALIBRATION_PARAMETER_WRITING_ERROR = "0080"
    SPEEDING = "0100"
    MOTOR_TEMPERATURE_OVER_TEMPERATURE = "1000"
    ENCODER_CALIBRATION_ERROR = "2000"


class NeckPlatform(SteppableSystem):

    def __init__(self):
        super().__init__()
        self.operating_frequency = 100
    
    def set_movement_profile(self, motor_name, max_velocity, max_acceleration, max_jerk):
        pass
    
    def move(self, pitch_in_degrees=None, yaw_in_degrees=None):
        pass

    def recalibrate(self):
        pass
    
    async def get_position(self):
        pass
    
    async def get_state(self, motor_name, property):
        pass

    async def health_check(self):
        pass

class MyActuatorMotor(Motor):
    def __init__(self, motor_id: int, can_interface: str, motor_name: str):
        '''
        Deprecated: Use RobstrideNeckPlatform instead. This was for an older version of hardware.
        '''
        super().__init__(motor_id, motor_name)
        self.target_velocity = 360 # degrees/s
        self.target_acceleration = 1440 # degrees/s^2
        self.can_id = motor_id + 140
        self.rec_can_id = motor_id + 240

        self.error_state = (MyActuatorErrorState.NO_ERROR, -1)
        self.break_release = (0, -1)
        self.voltage = (0, -1)
        self.can_interface = can_interface

    def health_check_update(self, temp, break_release, voltage, error_state):
        update_time = time.time()
        self.temp = (temp, update_time)
        self.break_release = (break_release, update_time)
        self.voltage = (voltage, update_time)
        self.error_state = (error_state, update_time)


class MyActuatorNeckPlatform(NeckPlatform):

    MIN_PITCH_ANGLE = -145
    MAX_PITCH_ANGLE = 0
    MIN_YAW_ANGLE = -180
    MAX_YAW_ANGLE = 0

    def __init__(self, motors_manager: MotorsManager, can_interface: str):
        '''
        Deprecated: Use RobstrideNeckPlatform instead. This was for an older version of hardware.
        '''
        self.default_can_interface = can_interface
        self.motors_map = {
            "NwC": MyActuatorMotor(1, can_interface, "NwC"),
            "NpC": MyActuatorMotor(2, can_interface, "NpC")
        }
        self.motors_manager = motors_manager
        self.motors_manager.add_motors(self.motors_map, family_name="neck")
        self.health_check_future = None
        
        self.comms = CommsManager()
        self.comms.add_callback(lambda result: self.on_motor_message(result))
        self.event_loop = asyncio.get_event_loop()

        # get_state
        self.get_state_lock = asyncio.Lock()
        self.get_state_futures = []
        self.get_state_pending_motors = None

        # health_check
        self.health_check_lock = asyncio.Lock()
        self.health_check_futures = []
        self.health_check_pending_motors = None

        try:
            self._enabled = True
            for motor in self.motors_map.keys():
                self._update_motor_acceleration(motor)
        except UnknownInterfaceError as e:
            print(f"Could not find interface for motors: {e}, neck platform will be disabled")
            self._enabled = False

        super().__init__()
    
    def _get_motor_manager(self):
        if not self._enabled:
            raise ValueError("Neck platform is disabled")
        return self.motors_manager
    
    def _get_motor(self, motor_name):
        if not self._enabled:
            raise ValueError("Neck platform is disabled")
        return self.motors_map[motor_name]
        
    def _step(self):
        pass

    def set_movement_profile(self, motor_name, target_velocity, target_acceleration):
        motor = self._get_motor(motor_name)
        motor.target_velocity = target_velocity
        if target_acceleration != motor.target_acceleration:
            motor.target_acceleration = target_acceleration # dp/s^2
            self._update_motor_acceleration(motor_name)

    def _update_motor_acceleration(self, motor_name):
        # Convert motor name to ID number
        motor = self._get_motor(motor_name)
        # Set acceleration to 100 dps^2 for position control
        acceleration_bytes = motor.target_acceleration.to_bytes(4, 'little')
        data = bytes([MyActuatorCommands.SET_ACCELERATION.value] + [0] * 3) + acceleration_bytes
        self.comms.cansend(motor.can_interface, False, motor.can_id, data)

    def _zero_position(self, motor_name):
        motor = self._get_motor(motor_name)
        data = bytes([MyActuatorCommands.ZERO_POSITION.value] + [0] * 7)
        self.comms.cansend(motor.can_interface, False, motor.can_id, data)
        time.sleep(0.2)
        self._reset_motor(motor_name)

    def _reset_motor(self, motor_name):
        motor = self._get_motor(motor_name)
        data = bytes([MyActuatorCommands.RESET_MOTOR.value] + [0] * 7)
        self.comms.cansend(motor.can_interface, False, motor.can_id, data)
        time.sleep(2) # Needs time to reset

    def _shutdown_motor(self, motor_name):
        motor = self._get_motor(motor_name)
        data = bytes([MyActuatorCommands.SHUTDOWN_MOTOR.value] + [0] * 7)
        self.comms.cansend(motor.can_interface, False, motor.can_id, data)

    def _move(self,  pitch_in_degrees=None, yaw_in_degrees=None, command=MyActuatorCommands.SET_POSITION):
        if not pitch_in_degrees is None:
            pitch_motor = self._get_motor("NpC")
            pitch_motor.target_position = pitch_in_degrees
            pitch_speed_2_bytes = pitch_motor.target_velocity.to_bytes(2, 'little')
            pitch_position_4_bytes = (int(pitch_in_degrees * 100)).to_bytes(4, 'little')
            data = bytes([command.value] + [0] * 1) + pitch_speed_2_bytes + pitch_position_4_bytes
            self.comms.cansend(pitch_motor.can_interface, False, pitch_motor.can_id, data)

        if not yaw_in_degrees is None:
            yaw_motor = self._get_motor("NwC")
            yaw_motor.target_position = yaw_in_degrees
            yaw_speed_2_bytes = yaw_motor.target_velocity.to_bytes(2, 'little')
            yaw_position_4_bytes = (int(yaw_in_degrees * 100)).to_bytes(4, 'little')
            data = bytes([command.value] + [0] * 1) + yaw_speed_2_bytes + yaw_position_4_bytes
            self.comms.cansend(yaw_motor.can_interface, False, yaw_motor.can_id, data)

    def move(self, pitch_in_degrees=None, yaw_in_degrees=None):
        if not pitch_in_degrees is None and (pitch_in_degrees < self.MIN_PITCH_ANGLE or pitch_in_degrees > self.MAX_PITCH_ANGLE):
            raise ValueError(f"Pitch angle must be between {self.MIN_PITCH_ANGLE} and {self.MAX_PITCH_ANGLE} degrees")
        if not yaw_in_degrees is None and (yaw_in_degrees < self.MIN_YAW_ANGLE or yaw_in_degrees > self.MAX_YAW_ANGLE):
            raise ValueError(f"Yaw angle must be between {self.MIN_YAW_ANGLE} and {self.MAX_YAW_ANGLE} degrees")
        self._move(pitch_in_degrees, yaw_in_degrees, MyActuatorCommands.SET_POSITION)

    def move_incremental(self, pitch_in_degrees=None, yaw_in_degrees=None):
        self._move(pitch_in_degrees, yaw_in_degrees, MyActuatorCommands.SET_INCREMENTAL_POSITION)

    def request_state(self, motor_name):
        motor = self._get_motor(motor_name)
        data = bytes([MyActuatorCommands.GET_STATE.value] + [0] * 7)
        self.comms.cansend(motor.can_interface, False, motor.can_id, data)
    
    def request_health_check(self, motor_name):
        motor = self._get_motor(motor_name)
        data = bytes([MyActuatorCommands.HEALTH_CHECK.value] + [0] * 7)
        self.comms.cansend(motor.can_interface, False, motor.can_id, data)

    def request_pid_values(self, motor_name, pid_param: MyActuatorPIDParams):
        motor = self._get_motor(motor_name)
        data = bytes([MyActuatorCommands.READ_PID.value, pid_param.value] + [0] * 6)
        self.comms.cansend(motor.can_interface, False, motor.can_id, data)

    def write_pid_values(self, motor_name, pid_param: MyActuatorPIDParams, value: float, permanent=False):
        command = MyActuatorCommands.WRITE_PID_PERM if permanent else MyActuatorCommands.WRITE_PID_TEMP
        write_value = struct.pack('<f', value)
        motor = self._get_motor(motor_name)
        data = bytes([command.value, pid_param.value] + [0] * 2) + write_value
        self.comms.cansend(motor.can_interface, False, motor.can_id, data)

    async def get_position(self):
        await self.get_state(["NpC", "NwC"])
        return {
            "NpC": self._get_motor("NpC").angle,
            "NwC": self._get_motor("NwC").angle
        }

    async def request_info_helper(self, motors_names, request_method, lock, pending_motors, futures, timeout=0.1):
        for motor_name in motors_names:
            request_method(motor_name)
        
        await getattr(self, lock).acquire()
        future = self.event_loop.create_future()
        if getattr(self, pending_motors) is None:
            setattr(self, pending_motors, {})
            setattr(self, futures, [future])
        else:
            getattr(self, futures).append(future)
        for motor_name in motors_names:
            if not motor_name in getattr(self, pending_motors):
                getattr(self, pending_motors)[motor_name] = False
        getattr(self, lock).release()
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            return None

        return result

    async def get_state(self, motors_names):
        result = await self.request_info_helper(
            motors_names, self.request_state, "get_state_lock", "get_state_pending_motors", "get_state_futures")
        resp = []
        for motor_name in motors_names:
            motor = self._get_motor(motor_name)
            resp.append({
                "temp": motor.temp,
                "current": motor.torque,
                "speed": motor.velocity,
                "angle": motor.angle,
            })
        return resp

    async def id_check(self):
        data = bytes([MyActuatorCommands.ID_CHECK.value] + [0, 1, 0, 0, 0, 0, 0])   
        self.comms.cansend(self.default_can_interface, False, 300, data)

    async def health_check(self, motors_names):
        """
        Checks if the system is receiving and responding.
        Method can block up to 0.1 seconds to receive responses from all motors.
        """
        result = await self.request_info_helper(motors_names, self.request_health_check, "health_check_lock", "health_check_pending_motors", "health_check_futures")
        resp = []
        for motor_name in motors_names:
            motor = self._get_motor(motor_name)
            resp.append({
                "temp": motor.temp,
                "break_release": motor.break_release,
                "voltage": motor.voltage,
                "error_state": motor.error_state,
            })
        return resp

    def recalibrate(self, motor_name):
        return # TODO: Fix wires.
        old_velocity = self._get_motor(motor_name).target_velocity
        old_acceleration = self._get_motor(motor_name).target_acceleration
        self.set_movement_profile(motor_name, 60, 60)
        for i in range(40):
            if motor_name == "NpC":
                self.move_incremental(pitch_in_degrees=5, yaw_in_degrees=None)
            else:
                self.move_incremental(pitch_in_degrees=None, yaw_in_degrees=5)
            time.sleep(0.2)
            self.request_state(motor_name)
            time.sleep(0.2)
            print(self._get_motor(motor_name).torque[0], self._get_motor(motor_name).angle[0])
            if self._get_motor(motor_name).torque[0] > 100 or self._get_motor(motor_name).torque[0] < -100:
                break
        self._shutdown_motor(motor_name)
        self._zero_position(motor_name)
        if motor_name == "NpC":
            self.move(-90)
        else:
            self.move(pitch_in_degrees=None, yaw_in_degrees=-90)
        time.sleep(1)
        self.set_movement_profile(motor_name, old_velocity, old_acceleration)

    def on_motor_message(self, result: SocketResult):
        for motor in self.motors_map.keys():
            if result.can_id == self._get_motor(motor).rec_can_id:
                self.handle_motor_reply(motor, result.data)
        
        if result.can_id == 300:
            if result.data[0] == MyActuatorCommands.ID_CHECK.value:
                print("ID check received", result.data)

    async def notify_futures(self, motor_name, lock, pending_motors, futures):
        await getattr(self, lock).acquire()
        getattr(self, pending_motors)[motor_name] = True
        if all(getattr(self, pending_motors).values()):
            for future in getattr(self, futures):
                self.event_loop.call_soon_threadsafe(future.set_result, True)
        setattr(self, futures, [])
        setattr(self, pending_motors, None)
        getattr(self, lock).release()

    def handle_motor_reply(self, motor_name, data):
        motor = self.motors_map[motor_name]  # Assume motor is enabled
        if data[0] == MyActuatorCommands.READ_PID.value:
            pid_val = struct.unpack('<f', data[4:8])[0]  # Comment said little endian, but code showed big endian
            print(data, pid_val)
        if data[0] in [MyActuatorCommands.GET_STATE.value, MyActuatorCommands.SET_POSITION.value, MyActuatorCommands.SET_INCREMENTAL_POSITION.value]:
            temp = int.from_bytes(data[1:2], 'little', signed=True)
            current = int.from_bytes(data[2:4], 'little', signed=True)
            speed = int.from_bytes(data[4:6], 'little', signed=True)
            angle = int.from_bytes(data[6:8], 'little', signed=True)
            motor.update_feedback(angle, speed, current, temp, [], motor.mode[0])
            if not self.get_state_pending_motors is None:
                asyncio.run_coroutine_threadsafe(self.notify_futures(motor_name, "get_state_lock", "get_state_pending_motors", "get_state_futures"), self.event_loop)
        if data[0] == MyActuatorCommands.HEALTH_CHECK.value:
            temp = int.from_bytes(data[1:2], 'little', signed=True)
            break_release = int.from_bytes(data[3:4], 'little', signed=True)
            voltage = int.from_bytes(data[4:6], 'little', signed=True)
            error_state = data[-4:]
            error_state_enum = MyActuatorErrorState(error_state)
            motor.health_check_update(temp, break_release, voltage, error_state_enum)
            if not self.health_check_pending_motors is None:
                asyncio.run_coroutine_threadsafe(self.notify_futures(motor_name, "health_check_lock", "health_check_pending_motors", "health_check_futures"), self.event_loop)
