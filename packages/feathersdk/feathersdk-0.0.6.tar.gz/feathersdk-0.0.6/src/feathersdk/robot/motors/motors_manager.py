import os
import time
import enum
from ...comms import CommsManager, SocketResult, CanOverloadError
from ...comms.system import get_all_physical_can_interfaces
import math
import struct
from typing import List, Tuple, Union, TypedDict, NamedTuple, Any, Optional
from ...utils.files import write_json_file, read_json_file
import threading
import asyncio
from ...utils import constants

DRY_RUN = True
DISABLE_HANDS = True

class TimestampedValue(NamedTuple):
    value: float
    timestamp: float


class RunMode(enum.Enum):
    Operation = 0
    Position = 1
    Speed = 2
    Current = 3


param_ids_by_name = {
    "run_mode": 0x7005,
    "iq_ref": 0x7006,
    "spd_ref": 0x700A,
    "limit_torque": 0x700B,
    "cur_kp": 0x7010,
    "cur_ki": 0x7011,
    "cur_fit_gain": 0x7014,
    "loc_ref": 0x7016,
    "limit_spd": 0x7017,
    "limit_cur": 0x7018,
    "mechpos": 0x7019,
    "iqf": 0x701A,
    "mechvel": 0x701B,
    "vbus": 0x701C,
    "loc_kp": 0x701E,
    "spd_kp": 0x701F,
    "spd_ki": 0x7020,
    "spd_filt_gain": 0x7021,
    "vel_max": 0x7024,  # default is 10rad/s
    "acc_set": 0x7025,  # default is 10rad/s^2
}


class MotorError(enum.Enum):
    Undervoltage = 1
    Overcurrent = 2
    Overtemp = 4
    MagneticEncodingFault = 8
    HallEncodingFault = 16
    Uncalibrated = 32


class MotorMode(enum.Enum):
    Reset = 0
    Calibration = 1
    Run = 2


params_names_by_id = {v: k for k, v in param_ids_by_name.items()}

INSPIRE_PROPERTIES_OFFSETS = {"force_set": 12}

INSPIRE_RIGHT_FINGERS = {
    "Gr00R": {
        "motor_id": 1496,
        "ip_address": "192.168.11.210",
        "motor_name": "Gp00R",
        "description": "Right thumb rotation finger",
    },
    "Gp01R": {
        "motor_id": 1494,
        "ip_address": "192.168.11.210",
        "motor_name": "Gp01R",
        "description": "Right thumb bending finger",
    },
    "Gp10R": {
        "motor_id": 1492,
        "ip_address": "192.168.11.210",
        "motor_name": "Gp10R",
        "description": "Right index finger",
    },
    "Gp20R": {
        "motor_id": 1490,
        "ip_address": "192.168.11.210",
        "motor_name": "Gp20R",
        "description": "Right middle finger",
    },
    "Gp30R": {
        "motor_id": 1488,
        "ip_address": "192.168.11.210",
        "motor_name": "Gp30R",
        "description": "Right ring finger",
    },
    "Gp40R": {
        "motor_id": 1486,    
        "ip_address": "192.168.11.210",
        "motor_name": "Gp40R",
        "description": "Right pinky finger",
    },
}

INSPIRE_LEFT_FINGERS = {
    "Gr00L": {
        "motor_id": 1496,
        "ip_address": "192.168.12.210",
        "motor_name": "Gp00L", 
        "description": "Left thumb rotation finger",
    },
    "Gp01L": {
        "motor_id": 1494,
        "ip_address": "192.168.12.210",
        "motor_name": "Gp01L",
        "description": "Left thumb bending finger",
    },
    "Gp10L": {
        "motor_id": 1492,
        "ip_address": "192.168.12.210",
        "motor_name": "Gp10L",
        "description": "Left index finger",
    },
    "Gp20L": {
        "motor_id": 1490,
        "ip_address": "192.168.12.210",
        "motor_name": "Gp20L",
        "description": "Left middle finger",
    },
    "Gp30L": {
        "motor_id": 1488,
        "ip_address": "192.168.12.210",
        "motor_name": "Gp30L",
        "description": "Left ring finger",
    },
    "Gp40L": {
        "motor_id": 1486,
        "ip_address": "192.168.12.210",
        "motor_name": "Gp40L",
        "description": "Left pinky finger",
    },
}

DEFAULT_MAX_FORCE = 500  # for safety purposes.

class InspireFingerJoint:

    def __init__(self, motor_id: int, ip_address: str, motor_name: str):
        self.motor_id = motor_id
        self.motor_name = motor_name
        self.ip_address = ip_address
        self.properties = {}
        self.comms = CommsManager()
        if not DISABLE_HANDS:
            self.set_max_force(DEFAULT_MAX_FORCE)

    def move_percentage(self, percentage: float):
        """
        Move the finger joint. 0% is fully closed, 100% is fully open.
        """
        # Record start time
        # start_time = time.time()
        self.comms.tcpsend_modbus(self.ip_address, 1, 255, 6, self.motor_id, int(percentage * 1000))
        time.sleep(0.01)
        # end_time = time.time()
        # print(f"Move {self.motor_name} to {percentage * 100}% in {end_time - start_time} seconds")

    def set_max_force(self, force: int):
        """
        Set the max force for the finger joint.
        """
        # Convert motor_id from bytes to int, add offset, then convert back to bytes
        force_set_id = int(self.motor_id) + INSPIRE_PROPERTIES_OFFSETS["force_set"]
        self.comms.tcpsend_modbus(self.ip_address, 1, 255, 6, force_set_id, force)
        time.sleep(0.005)


INSPIRE_RIGHT_FINGER_JOINTS_MAP = {}
INSPIRE_LEFT_FINGER_JOINTS_MAP = {}

if not DISABLE_HANDS:
    for motor_name, motor_info in INSPIRE_RIGHT_FINGERS.items():
        INSPIRE_RIGHT_FINGER_JOINTS_MAP[motor_name] = InspireFingerJoint(
            motor_info["motor_id"], motor_info["ip_address"], motor_info["motor_name"]
        )

    for motor_name, motor_info in INSPIRE_LEFT_FINGERS.items():
        INSPIRE_LEFT_FINGER_JOINTS_MAP[motor_name] = InspireFingerJoint(
            motor_info["motor_id"], motor_info["ip_address"], motor_info["motor_name"]
        )


class UnsafeCommandError(Exception):
    """Raised when attempting to execute an unsafe command."""
    def __init__(self, message: str, motor: 'Motor'):
        super().__init__(message)
        self.motor = motor
        self.motor_name = motor.motor_name


class MotorDisabledError(Exception):
    """Raised when attempting to command a motor that is disabled (in Reset mode)."""
    def __init__(self, message: str, motor: 'Motor'):
        super().__init__(message)
        self.motor = motor
        self.motor_name = motor.motor_name


class MotorModeInconsistentError(Exception):
    """Raised when attempting to command a motor with an incompatible run mode."""
    def __init__(self, message: str, motor: 'Motor', current_mode: RunMode, expected_mode: RunMode):
        super().__init__(message)
        self.motor = motor
        self.motor_name = motor.motor_name
        self.current_mode = current_mode
        self.expected_mode = expected_mode


class MotorNotFoundError(Exception):
    """Raised when attempting to access a motor that does not exist in the motors map."""
    def __init__(self, message: str, motor_name_or_id: Union[str, int]):
        super().__init__(message)
        self.motor_name_or_id = motor_name_or_id
        # For consistency with other exceptions, also provide motor_name (as string representation)
        self.motor_name = str(motor_name_or_id)


class MotorCalibrationError(Exception):
    """Raised when motor calibration fails or motor doesn't respond as expected during calibration."""
    def __init__(self, message: str, motor: 'Motor'):
        super().__init__(message)
        self.motor = motor
        self.motor_name = motor.motor_name


class MotorConfig(TypedDict, total=False):
    max_torque: float  # Max torque in N
    max_position_dx: float  # positional difference in radians
    joint_limits: Tuple[float, float]  # joint limits in radians
    max_velocity: float  # Max velocity in radians / seconds


class SafeStopPolicy(enum.Enum):
    DISABLE_MOTORS = 1
    COMPLIANCE_MODE = 2


class FamilyConfig(TypedDict, total=False):
    safe_stop_policy: SafeStopPolicy


_MOTOR_NO_DEFAULT = object()


class Motor:
    def __init__(self, motor_id: int, motor_name: str, motor_config: MotorConfig = {}, can_interface: str = None):
        self.motor_id: int = motor_id
        self.motor_name: str = motor_name

        self.calibration_time = None
        self._homing_pos = motor_config.get("homing_pos", 0)
        self.direction = motor_config.get("direction", 1)

        self.range = motor_config.get("range", {
            "min": -math.pi / 2,
            "max": math.pi / 2,
        })

        self.upper_limit = None
        self.lower_limit = None
        self.middle_pos = None
        self.total_range = None
        
        self.calibrated_angle = (0, -1)
        self.dual_encoder = True

        self.family_name: Union[str, None] = None
        self.can_interface: Union[str, None] = can_interface
        self.properties: dict[str, TimestampedValue] = {}
        self.joint_limits = motor_config.get("joint_limits", None)

        if self.joint_limits is not None:
            if (
                self.joint_limits[0] < -math.pi
                or self.joint_limits[1] > math.pi
                and self.joint_limits[0] <= self.joint_limits[1]
            ):
                print("Warning: Joint limits must be from -pi to pi for ", motor_name)
        self.max_torque = motor_config.get("max_torque", None)
        self.max_position_dx = motor_config.get("max_position_dx", None)
        self.max_velocity = motor_config.get("max_velocity", None)
        self.run_mode = RunMode.Operation
        self.compliance_mode: bool = False
        self.target_position = 0
        self.last_compliance_pos = 0
        self.compliance_mode_torque_threshold = motor_config.get("compliance_mode_torque_threshold", 1.0)
        self.compliance_mode_dx = motor_config.get("compliance_mode_dx", 0.01)

        # TODO: properly initialize
        self.mode = (MotorMode.Reset, -1)
        self.angle = (0, -1)
        self.calibrated_angle = (0, -1)
        self.velocity = (0, -1)
        self.torque = (0, -1)
        self.temp = (0, -1)

        self.load_calibration_state()

    @property
    def expected_range(self) -> float:
        return self.range["max"] - self.range["min"]

    # make a getter for homing_pos
    @property
    def homing_pos(self) -> float:
        if self.middle_pos is not None:
            return self.middle_pos + self._homing_pos
        return self._homing_pos

    def update_feedback(
        self, angle: float, velocity: float, torque: float, temp: float, errors: List[MotorError], mode: MotorMode
    ):
        last_update = time.time()
        # Raw angle coming from the encoder.
        self.angle: TimestampedValue = TimestampedValue(angle, last_update)
        if self.middle_pos is not None:
            # Calibrated angle useful for control the robot between different machines to account for encoder differences.
            # Calibrated angle is a better indicator of the angle set by the user.
            self.calibrated_angle = TimestampedValue(angle - self.middle_pos, last_update)
        else:
            self.calibrated_angle = TimestampedValue(angle, last_update)
        self.velocity: TimestampedValue = TimestampedValue(velocity, last_update)
        self.torque: TimestampedValue = TimestampedValue(torque, last_update)
        self.temp: TimestampedValue = TimestampedValue(temp, last_update)
        self.errors: tuple[List[MotorError], float] = (errors, last_update)
        self.mode: TimestampedValue = TimestampedValue(mode, last_update)  # Update mode from feedback

    def update_property(self, property_name: str, value: Union[float, int]):
        self.properties[property_name] = TimestampedValue(value, time.time())
    
    def get_property_value(self, property_name: str, default: Any = _MOTOR_NO_DEFAULT) -> Any:
        """Get the currently stored value for a property in this motor. 
        
        If the property is not found, return the default value. If the default value is not provided, raise a KeyError.
        """
        if property_name in self.properties:
            return self.properties[property_name].value
        if default is not _MOTOR_NO_DEFAULT:
            return default
        raise KeyError(f"Property {property_name} not found in motor {self.motor_name}")

    def get_property_timestamp(self, property_name: str, default: Any = _MOTOR_NO_DEFAULT) -> Any:
        """Get the timestamp of the currently stored value for a property in this motor. 
        
        If the property is not found, return the default value. If the default value is not provided, raise a KeyError.
        """
        if property_name in self.properties:
            return self.properties[property_name].timestamp
        if default is not _MOTOR_NO_DEFAULT:
            return default
        raise KeyError(f"Property {property_name} not found in motor {self.motor_name}")

    def is_safe_position_update(self, target_position: float) -> bool:
        if self.max_position_dx is not None:
            return abs(target_position - self.angle[0]) <= self.max_position_dx
        return True

    def update_target_position(self, target_position: float) -> None:
        """
        Used for safety purposes.
        If max_position_dx is set, the motor will be stopped if the position is outside the max_position_dx.
        """
        if self.compliance_mode:
            raise UnsafeCommandError("Commands are currently blocked because compliance mode is activated.", motor=self)

        self.target_position = target_position

    def should_trigger_compliance_mode(self):
        if self.compliance_mode or self.mode[0] == MotorMode.Reset:
            return False

        if self.max_position_dx is not None:
            if abs(self.angle[0] - self.target_position) > self.max_position_dx:
                print(
                    f"Compliance mode triggered: Motor {self.motor_name} Position {self.angle[0]} is outside max position dx {self.max_position_dx} Target position {self.target_position}"
                )
                return True

        if self.max_torque is not None:
            if abs(self.torque[0]) > self.max_torque:
                print(
                    f"Compliance mode triggered: Motor {self.motor_name} Torque {self.torque[0]} is greater than max torque {self.max_torque}"
                )
                return True

        if self.joint_limits is not None:
            if self.angle[0] > self.joint_limits[1] or self.angle[0] < self.joint_limits[0]:
                print(
                    f"Compliance mode triggered: Motor {self.motor_name} Angle {self.angle[0]} is outside joint limits {self.joint_limits}"
                )
                return True

        if self.max_velocity is not None:
            if abs(self.velocity[0]) > self.max_velocity:
                print(
                    f"Compliance mode triggered: Motor {self.motor_name} Velocity {self.velocity[0]} is greater than max velocity {self.max_velocity}"
                )
                return True

        return False

    def set_calibration(self, lower_limit: float, upper_limit: float, middle_pos: float, total_range: float):
        self.calibration_time = time.time()
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.middle_pos = middle_pos
        self.total_range = total_range
        self.save_calibration_state()

    def save_calibration_state(self):
        data = {
            "calibration_time": self.calibration_time,
            "lower_limit": self.lower_limit,
            "upper_limit": self.upper_limit,
            "middle_pos": self.middle_pos,
            "total_range": self.total_range,
        }
        write_json_file(data, constants.MOTORS_CALIBRATION_PATH + "/" + self.motor_name + ".json")

    def load_calibration_state(self) -> bool:
        """Load the calibration state from the file.
        
        Returns True if the calibration state was loaded successfully, False otherwise.
        """
        file_path = constants.MOTORS_CALIBRATION_PATH + "/" + self.motor_name + ".json"
        if not os.path.exists(file_path):
            return False
        data = read_json_file(file_path)
        self.calibration_time = data["calibration_time"]
        self.lower_limit = data["lower_limit"]
        self.upper_limit = data["upper_limit"]
        self.middle_pos = data["middle_pos"]
        self.total_range = data["total_range"]
        return True


MotorMap = dict[str, Motor]

class RobstrideMotorMsg(enum.Enum):
    Info = 0x00
    Control = 0x01
    Feedback = 0x02
    Enable = 0x03
    Disable = 0x04
    ZeroPos = 0x06
    SetID = 0x07
    ReadParam = 0x11
    WriteParam = 0x12
    SetMotorActiveReporting = 0x18


class OperationCommand:
    def __init__(self, motor_name_or_id: Union[str, int], target_torque, target_angle, target_velocity, kp, kd):
        self.motor_name_or_id = motor_name_or_id
        self.target_torque = target_torque
        self.target_angle = target_angle
        self.target_velocity = target_velocity
        self.kp = kp
        self.kd = kd


class MotorsManager:
    """
    Handles sending commands to and receiving feedback from motors.
    Handles caching the state of the motors.
    Abstractions to make it easy to work with motors.
    """

    def __init__(self) -> None:
        self.motors: MotorMap = {}
        # Create a map of motor IDs to motors for faster lookup
        self.motors_by_id: dict[int, Motor] = {}
        self.motor_families: dict[str, MotorMap] = {}
        self.motor_families_config: dict[str, FamilyConfig] = {}
        self.motor_families_compliance_threads: dict[str, threading.Thread] = {}
        self.comms = CommsManager()
        self.host_id = 0xFD
        self.comms.add_callback(lambda result: self.on_motor_message(result))

    def add_motors(self, motors_map: MotorMap, family_name: str, family_config: FamilyConfig = {}) -> None:
        self.motor_families[family_name] = motors_map
        self.motor_families_config[family_name] = family_config
        for motor_name, motor in motors_map.items():
            self.motors_by_id[motor.motor_id] = motor
            self.motors[motor_name] = motor
            motor.family_name = family_name
    
    def find_motors(self, motor_names: Optional[List[str]] = None) -> None:
        """Find the motors on the physical CAN interfaces.

        If motor_names is not provided, find all motors in the motors map.
        """
        if motor_names is None:
            motor_names = list(self.motors.keys())

        for motor_name in motor_names:
            motor = self.motors[motor_name]
            if motor.can_interface is not None:
                continue

            found = False
            for attempt in range(3):
                for can_interface in get_all_physical_can_interfaces():
                    try:
                        motor.can_interface = can_interface
                        motor.update_property("loc_ref", None)
                        self.read_param(motor_name, "loc_ref")
                        time.sleep(0.01)

                        if motor.properties["loc_ref"].value is not None:
                            found = True
                            break
                    except Exception:
                        motor.can_interface = None

                if found:
                    break
                time.sleep(0.5)

            if not found:
                motor.can_interface = None
                raise MotorNotFoundError(
                    f"Warning: Could not find motor {motor_name} on any physical CAN interface [New]",
                    motor_name_or_id=motor_name,
                )

    def stop_compliance_mode(self, family_name: str) -> None:
        family_motors = self.motor_families[family_name]
        for m in family_motors.values():
            m.compliance_mode = False
            self.disable(m.motor_name)
        # by setting it to None, trigger_compliance_mode will be called again from handle_msg from m.motor_name.
        del self.motor_families_compliance_threads[family_name]

    def compliance_mode_main(self, family_name: str) -> None:
        family_motors = self.motor_families[family_name]
        while True:
            for m in family_motors.values():
                if m.compliance_mode == False:
                    return  # exit.

                if abs(m.torque[0]) > m.compliance_mode_torque_threshold:
                    proposed_new_pos = m.last_compliance_pos + m.torque[0] * -m.compliance_mode_dx
                    if m.joint_limits is None:
                        m.last_compliance_pos = proposed_new_pos
                    elif m.joint_limits[0] <= proposed_new_pos and m.joint_limits[1] >= proposed_new_pos:
                        m.last_compliance_pos = proposed_new_pos
                # self.write does a time.sleep(0.0002) for each motor.
                self._set_target_position_in_compliance_mode(m.motor_name, m.last_compliance_pos)
                # time.sleep(0.01)

    def trigger_compliance_mode(self, family_name: str) -> None:
        # disable all motors
        family_motors = self.motor_families[family_name]
        safe_stop_policy = self.motor_families_config[family_name].get(
            "safe_stop_policy", SafeStopPolicy.COMPLIANCE_MODE
        )
        for m in family_motors.values():
            m.compliance_mode = True
            self.disable(m.motor_name)
            if safe_stop_policy == SafeStopPolicy.COMPLIANCE_MODE:
                self.set_run_mode(m.motor_name, RunMode.Position)
                self.enable(m.motor_name)
                self._set_target_position_in_compliance_mode(m.motor_name, m.angle[0] - m.velocity[0] * 0.01)
                m.last_compliance_pos = m.angle[0] - m.velocity[0] * 0.01

        if family_name not in self.motor_families_compliance_threads:
            thread = threading.Thread(target=self.compliance_mode_main, args=(family_name,), daemon=True)
            self.motor_families_compliance_threads[family_name] = thread
            thread.start()

    def on_feedback_message(self, can_id: int, motor_id: int, data: bytes):
        # Find the corresponding motor
        target_motor: Motor = None
        for motor in self.motors.values():
            if motor.motor_id == motor_id:
                target_motor = motor
                break
        else:
            return
        
        # Parse error bits and mode from arbitration ID
        error_bits = (can_id & (0x1F0000 << 2)) >> 16
        errors = []
        for i in range(6):
            value = 1 << i
            if value & error_bits:
                errors.append(MotorError(value))

        mode = MotorMode((can_id & (0x300000 << 2)) >> 22)
        
        # Convert values using same scaling as robstride_client
        angle_raw = int.from_bytes(data[0:2], "big")
        angle = (float(angle_raw) / 65535 * 8 * math.pi) - 4 * math.pi

        velocity_raw = int.from_bytes(data[2:4], "big")
        velocity_range = 88  # Assuming motor_model 1
        velocity = (float(velocity_raw) / 65535 * velocity_range) - velocity_range / 2

        torque_raw = int.from_bytes(data[4:6], "big")
        torque_range = 34  # Assuming motor_model 1
        torque = (float(torque_raw) / 65535 * torque_range) - torque_range / 2

        temp_raw = int.from_bytes(data[6:8], "big")
        temp = float(temp_raw) / 10

        # Update the motor's feedback values
        old_mode = target_motor.mode[0]
        target_motor.update_feedback(angle, velocity, torque, temp, errors, mode)
        if target_motor.should_trigger_compliance_mode() and old_mode != MotorMode.Reset:
            self.trigger_compliance_mode(target_motor.family_name)
        
    def on_read_message(self, can_id: int, motor_id: int, data: bytes):
        # Extract parameter ID and value
        param_id = int.from_bytes(data[:2], 'little', signed=False)  # First 2 bytes are param ID
        # Special handling for run_mode parameter (0x7005)
        if param_id == 0x7005:
            value = int(data[4])  # Run mode is a single byte value
        else:
            value = struct.unpack("<f", data[4:8])[0]  # Float value in last 4 bytes
        
        # Skip if motor is not in our map (might be from an unknown motor)
        if motor_id not in self.motors_by_id:
            return
        
        self.motors_by_id[motor_id].update_property(params_names_by_id[param_id], value)

    def on_motor_message(self, result: SocketResult) -> None:
        # Parse the arbitration ID to get message type and motor ID
        # CAN ID format in hex string: "0280FD73"
        #   msg[0:2] = message type (bits 24-31)
        #   msg[2:4] = error bits + mode (bits 16-23)
        #   msg[4:6] = sender id (bits 8-15)
        #   msg[6:8] = receiver id (bits 0-7)
        msg_type = (result.can_id & 0x1F00_0000) >> 24
        motor_id = (result.can_id & 0x0000_FF00) >> 8

        # Only process feedback messages (type 2)
        if msg_type == RobstrideMotorMsg.Feedback.value:
            self.on_feedback_message(result.can_id, motor_id, result.data)
        elif msg_type == RobstrideMotorMsg.ReadParam.value and motor_id != self.host_id:
            self.on_read_message(result.can_id, motor_id, result.data)

    def get_motor(self, motor_name_or_id: Union[str, int]) -> Motor:
        if isinstance(motor_name_or_id, str):
            if motor_name_or_id not in self.motors:
                raise MotorNotFoundError(f"Motor '{motor_name_or_id}' not found in motors map", motor_name_or_id=motor_name_or_id)
            return self.motors[motor_name_or_id]
        else:
            if motor_name_or_id not in self.motors_by_id:
                raise MotorNotFoundError(f"Motor with ID {motor_name_or_id} not found in motors map", motor_name_or_id=motor_name_or_id)
            return self.motors_by_id[motor_name_or_id]
    
    def _default_can_id(self, op: RobstrideMotorMsg, motor_id: int) -> int:
        return (op.value << 24) | (self.host_id << 8) | motor_id

    def enable(self, motor_name_or_id: Union[str, int]):
        try:
            motor = self.get_motor(motor_name_or_id)
            can_id = self._default_can_id(RobstrideMotorMsg.Enable, motor.motor_id)
            self.comms.cansend(motor.can_interface, True, can_id, bytes([0] * 8))
        except Exception as e:
            print(f"[ERROR MotorsManager.enable]: Exception occurred: {e}")
            import traceback

            traceback.print_exc()
            raise

    def disable(self, motor_name_or_id: Union[str, int]):
        motor = self.get_motor(motor_name_or_id)
        can_id = self._default_can_id(RobstrideMotorMsg.Disable, motor.motor_id)
        self.comms.cansend(motor.can_interface, True, can_id, bytes([0] * 8))

    def _disable_active_reporting(self, motor_name_or_id: Union[str, int]):
        """
        Send a command to disable active reporting, which triggers a feedback frame.
        
        This method sends a SetMotorActiveReporting command with active_flag=0 to the motor.
        While the intended purpose is to disable active reporting, this command also triggers
        the motor to send a feedback frame, which is the primary use case for this method.
        
        Note: Active reporting enable functionality was found to not work as
        documented in testing (TODO for later). This method is primarily used as a side-effect to trigger
        feedback frames rather than to actually control active reporting state.
        
        Args:
            motor_name_or_id: Motor name or ID
        """
        motor = self.get_motor(motor_name_or_id)
        can_id = self._default_can_id(RobstrideMotorMsg.SetMotorActiveReporting, motor.motor_id)
        # Data format: [0, 1, 2, 3, 4, 5, 6, active_flag] where active_flag is 1 for active, 0 for inactive
        data = bytes([0, 1, 2, 3, 4, 5, 6, 0])
        self.comms.cansend(motor.can_interface, True, can_id, data)

    async def read_current_state_async(self, motor_name_or_id: Union[str, int]):
        """
        Asynchronously trigger a feedback frame from the motor and wait for fresh motor data.
        
        This method sends a command to the motor (via _disable_active_reporting) that triggers
        a feedback response. It then waits for the feedback frame to arrive and be processed,
        retrying the command if necessary.
        
        The method will retry sending the command every 100ms (10 iterations) if no feedback is
        received. After 300ms (30 iterations) with no feedback, a TimeoutError is raised to
        indicate that the motor is not responding. This ensures that stale feedback data is not
        used, as the method guarantees fresh feedback or an error.
        
        Args:
            motor_name_or_id: Name or ID of the motor
            
        Raises:
            TimeoutError: If no feedback frame is received within 300ms (after up to 3 retries)

        Note:
            This method has a side-effect of disabling active reporting, which is not the true purpose.
            Since we are not using active reporting, this is not a problem for now.
            But if we start using active reporting, we need to revisit this. There was a Motor Data
            Save command in the Robstride manual for the motor, however, that did not work as expected.
        """
        motor = self.get_motor(motor_name_or_id)
        
        # Record timestamp before triggering feedback
        update_time = time.time()
        
        # Disable active reporting to trigger a feedback frame
        self._disable_active_reporting(motor_name_or_id)
        
        # Wait for feedback frame to arrive and be processed
        # Check if temp timestamp has been updated (indicating fresh feedback received)
        await asyncio.sleep(0.001)  # Initial pause
        retry_cnt = 10  # Retry command every 10 iterations (10 * 10ms = 100ms)
        max_retry_cnt = 0
        
        # Wait for feedback to be updated (check temp timestamp as indicator)
        # temp[1] is the timestamp; -1 means no feedback received yet
        while motor.temp[1] < update_time:
            await asyncio.sleep(0.01)  # Wait 10ms between checks
            retry_cnt -= 1
            if retry_cnt <= 0:
                # Retry disabling active reporting if no feedback received
                self._disable_active_reporting(motor_name_or_id)
                retry_cnt = 10  # Reset retry counter
            max_retry_cnt += 1
            if max_retry_cnt > 30:  # Timeout after ~0.3 seconds (30 * 0.01s), allows 3 retries
                raise TimeoutError(
                    f"Failed to receive feedback from motor {motor.motor_name} within timeout (300ms). "
                    f"Motor may be disconnected or not responding."
                )

    def zero_position(self, motor_name_or_id: Union[str, int]):
        motor = self.get_motor(motor_name_or_id)
        can_id = self._default_can_id(RobstrideMotorMsg.ZeroPos, motor.motor_id)
        self.comms.cansend(motor.can_interface, True, can_id, bytes([0x01] + [0] * 7))

    def read_param_sync(self, motor_name_or_id: Union[str, bytes], param_id: Union[int, str]) -> float:
        motor = self.get_motor(motor_name_or_id)
        update_time = time.time()

        self.read_param(motor_name_or_id, param_id)
        time.sleep(0.001)
        retry_cnt = 50
        max_retry_cnt = 0
        while motor.get_property_timestamp(param_id, default=-1) < update_time:
            time.sleep(0.001)
            retry_cnt -= 1
            if retry_cnt <= 0:
                self.read_param(motor_name_or_id, param_id)    
                retry_cnt = 50
            max_retry_cnt += 1
            if max_retry_cnt > 25:
                raise TimeoutError(f"Failed to read parameter {param_id} within timeout")
        return motor.get_property_value(param_id)

    async def read_param_async(self, motor_name_or_id: Union[str, bytes], param_id: Union[int, str]) -> float:
        """
        Asynchronously reads a motor parameter, waiting for the value to be updated.
        Replaces blocking time.sleep with non-blocking asyncio.sleep.
        """

        # 1. Initial setup and parameter read
        motor = self.get_motor(motor_name_or_id)

        # Use time.monotonic() for sleep/timeout checks, as it's not affected by system clock changes.
        start_time = time.monotonic()
        # The 'update_time' from the original code: get the current time before requesting the update.
        update_time = time.time()

        # Initiate the read request (assuming self.read_param is already non-blocking or schedules a background action)
        self.read_param(motor_name_or_id, param_id)

        # Initial pause and setup
        await asyncio.sleep(0.001)  # Replace the first time.sleep(0.01) with non-blocking asyncio.sleep
        retry_cnt = 5
        max_retry_cnt = 0

        # Define the maximum total time to wait for the parameter to update (e.g., 0.5 seconds, as 25 * 0.02 is 0.5s total wait)
        # The original logic used 25 iterations of the main loop. With an inner sleep of 0.01s and an outer sleep/read sequence,
        # it's best to rely on a total timeout based on time.monotonic() rather than a fixed retry count.
        # We will stick close to the original retry/max_retry logic, but use a more explicit maximum duration for robustness.

        # 2. Asynchronous Polling Loop
        while motor.get_property_timestamp(param_id, default=-1) < update_time:

            # Replace time.sleep(0.01) with non-blocking asyncio.sleep
            await asyncio.sleep(0.001)

            retry_cnt -= 1

            if retry_cnt <= 0:
                # Re-request the parameter read
                self.read_param(motor_name_or_id, param_id)
                retry_cnt = 5

            max_retry_cnt += 1

            # Original maximum loop count check (25 * 0.02s delay approx = 0.5s total wait)
            if max_retry_cnt > 25:
                # If a TimeoutError is raised, it's better to use the time-based check below,
                # but for a direct reimplementation, we keep the original logic.
                raise TimeoutError(f"Failed to read parameter {param_id} within timeout")

        # 3. Return the updated parameter value
        return motor.get_property_value(param_id, default=-1)

    def read_param(self, motor_name_or_id: Union[str, int], param_id: Union[int, str]) -> float:
        """Read a parameter from the specified motor."""
        motor = self.get_motor(motor_name_or_id)

        # Convert string param_id to int if needed
        if isinstance(param_id, str):
            param_id = param_ids_by_name[param_id]
        
        can_id = self._default_can_id(RobstrideMotorMsg.ReadParam, motor.motor_id)
        self.comms.cansend(motor.can_interface, True, can_id, param_id.to_bytes(2, 'little') + bytes([0] * 6))
        # Note: Response handling will be done by on_motor_message callback
        
    def set_run_mode(self, motor_name_or_id: Union[str, int], run_mode: RunMode):
        motor = self.get_motor(motor_name_or_id)
        self.write_param(motor_name_or_id, "run_mode", run_mode.value)
        motor.run_mode = run_mode

    def _set_target_position_in_compliance_mode(self, motor_name_or_id: Union[str, int], target_position: float) -> None:
        """Set the target position (loc_ref) for the specified motor, bypassing safety checks.
        
        This is an internal method used only by compliance mode to set target positions
        without triggering safety checks. It bypasses motor state validation and position
        safety checks that would normally prevent commands during unsafe conditions.
        
        Args:
            motor_name_or_id: Name or ID of the motor
            target_position: Target position in radians
        """
        self._write_param_private(motor_name_or_id, "loc_ref", target_position, force_run=True)

    def set_target_position(self, motor_name_or_id: Union[str, int], target_position: float) -> None:
        """Set the target position (loc_ref) for the specified motor.
        
        This is a convenience method that wraps write_param for setting loc_ref.
        It provides a clearer API for position control.
        
        Args:
            motor_name_or_id: Name or ID of the motor
            target_position: Target position in radians
        
        Raises:
            MotorDisabledError: If the motor is in Reset mode (disabled)
            MotorModeInconsistentError: If the motor is not in Position run mode
        """
        motor = self.get_motor(motor_name_or_id)
        
        # Check if motor is disabled (in Reset mode)
        if motor.mode[0] == MotorMode.Reset:
            raise MotorDisabledError(
                f"Cannot set target position for motor {motor.motor_name}: "
                f"Motor is disabled (in Reset mode). Enable the motor first.",
                motor=motor
            )
        
        # Check if motor is in the correct run mode for position control
        if motor.run_mode != RunMode.Position:
            raise MotorModeInconsistentError(
                f"Cannot set target position for motor {motor.motor_name}: "
                f"Motor is in {motor.run_mode.name} mode, but Position mode is required. "
                f"Use set_run_mode() to switch to Position mode first.",
                motor=motor,
                current_mode=motor.run_mode,
                expected_mode=RunMode.Position
            )
        
        self.write_param(motor_name_or_id, "loc_ref", target_position)

    def set_target_velocity(self, motor_name_or_id: Union[str, int], target_velocity: float) -> None:
        """Set the target velocity (spd_ref) for the specified motor.
        
        This is a convenience method that wraps write_param for setting spd_ref.
        It provides a clearer API for velocity control.
        
        Args:
            motor_name_or_id: Name or ID of the motor
            target_velocity: Target velocity in radians per second
        
        Raises:
            MotorDisabledError: If the motor is in Reset mode (disabled)
            MotorModeInconsistentError: If the motor is not in Speed run mode
        """
        motor = self.get_motor(motor_name_or_id)
        
        # Check if motor is disabled (in Reset mode)
        if motor.mode[0] == MotorMode.Reset:
            raise MotorDisabledError(
                f"Cannot set target velocity for motor {motor.motor_name}: "
                f"Motor is disabled (in Reset mode). Enable the motor first.",
                motor=motor
            )
        
        # Check if motor is in the correct run mode for velocity control
        if motor.run_mode != RunMode.Speed:
            raise MotorModeInconsistentError(
                f"Cannot set target velocity for motor {motor.motor_name}: "
                f"Motor is in {motor.run_mode.name} mode, but Speed mode is required. "
                f"Use set_run_mode() to switch to Speed mode first.",
                motor=motor,
                current_mode=motor.run_mode,
                expected_mode=RunMode.Speed
            )
        
        self.write_param(motor_name_or_id, "spd_ref", target_velocity)

    def write_param(self, motor_name_or_id: Union[str, int], param_id: Union[int, str], param_value: Union[float, int]) -> None:
        """Write a parameter value to the specified motor.

        Args:
            motor_name_or_id: Name or ID of the motor
            param_id: Parameter ID
            param_value: Parameter value
        """
        self._write_param_private(motor_name_or_id, param_id, param_value, force_run=False)

    def _write_param_private(self, motor_name_or_id: Union[str, int], param_id: Union[int, str], param_value: Union[float, int], force_run=False) -> None:
        """Write a parameter value to the specified motor.
        force_run: should only be set to true when running commands from compliance mode. Otherwise, it defeats the safety purposes of compliance mode.
        """
        motor = self.get_motor(motor_name_or_id)

        # Convert string param_id to int if needed
        if isinstance(param_id, str):
            param_id = param_ids_by_name[param_id]

        # Prepare the parameter data
        param_bytes = param_id.to_bytes(2, 'little') + bytes([0] * 2)

        # Handle special case for run_mode (0x7005)
        if param_id == 0x7005:
            value_bytes = bytes([int(param_value), 0, 0, 0])
            motor.run_mode = RunMode(param_value)
        else:
            value_bytes = struct.pack("<f", param_value)
            
        data = param_bytes + value_bytes
        if not force_run and param_id == param_ids_by_name["loc_ref"]:
            if motor.is_safe_position_update(param_value):
                motor.update_target_position(param_value)  # can raise an exception to cancel the run.
            else:
                self.trigger_compliance_mode(motor.family_name)
                raise UnsafeCommandError(
                    f"Safety Error: Target position {param_value} is too far from current position {motor.angle[0]} (max dx: {motor.max_position_dx})",
                    motor=motor
                ) # stop the program safely.

        can_id = self._default_can_id(RobstrideMotorMsg.WriteParam, motor.motor_id)

        try:
            self.comms.cansend(motor.can_interface, True, can_id, data)
        except CanOverloadError:
            time.sleep(0.01)
            self.comms.cansend(motor.can_interface, True, can_id, data)
        
    def operation_command(self, motor_name_or_id: Union[str, int], target_torque: float, target_angle: float, target_velocity: float, kp: float, kd: float):
        """ target_torque range (-60Nm to 60Nm)"""
        can_id, data, can_interface = self.operation_batch_command(motor_name_or_id, target_torque, target_angle, target_velocity, kp, kd, apply_target_position=True)
        self.comms.cansend(can_interface, True, can_id, data)

    def operation_batch_command(self, motor_name_or_id: Union[str, int], target_torque: float, target_angle: float, target_velocity: float, kp: float, kd: float, apply_target_position: bool = True):
        """
        apply_target_position: if True, the target position will be applied to the motor.
        """
        motor = self.get_motor(motor_name_or_id)

        torque_in_65535 = int(((target_torque + 60) / 120) * 65535)

        angle_in_65535 = int(((target_angle + 4 * math.pi) / (8 * math.pi)) * 65535)
        velocity_in_65535 = int(((target_velocity + 15) / 30) * 65535)
        kp_in_65535 = int(((kp) / 5000) * 65535)
        kd_in_65535 = int(((kd) / 100) * 65535)

        target_angle_bytes = angle_in_65535.to_bytes(2, 'big')
        target_velocity_bytes = velocity_in_65535.to_bytes(2, 'big')
        target_kp_bytes = kp_in_65535.to_bytes(2, 'big')
        target_kd_bytes = kd_in_65535.to_bytes(2, 'big')

        data = target_angle_bytes + target_velocity_bytes + target_kp_bytes + target_kd_bytes
        if apply_target_position:
            if motor.is_safe_position_update(target_angle):
                motor.update_target_position(target_angle)  # can raise an exception to cancel the run.
            else:
                self.trigger_compliance_mode(motor.family_name)
                raise UnsafeCommandError(
                    f"Safety Error: Target position {target_angle} is too far from current position {motor.angle[0]} (max dx: {motor.max_position_dx})",
                    motor=motor
                ) # stop the program safely.

        can_id = self._default_can_id(RobstrideMotorMsg.Control, motor.motor_id)
        return ((can_id & 0xFF00_00FF) | (torque_in_65535 << 8), data, motor.can_interface)

    def send_operation_commands(self, operation_commands: List[OperationCommand]):
        for operation_command in operation_commands:
            can_id, data, can_interface = self.operation_batch_command(
                operation_command.motor_name_or_id,
                operation_command.target_torque,
                operation_command.target_angle,
                operation_command.target_velocity,
                operation_command.kp,
                operation_command.kd,
                apply_target_position=True,
            )
            self.comms.cansend(can_interface, True, can_id, data)

    def _find_limit(
        self,
        motor_name: str,
        initial_pos: float,
        step_size: float,
        step_time: float,
        max_torque: float,
        threshold_target_distance: float,
        direction: int,  # 1 for forward, -1 for backward
        verbose: bool,
    ) -> float:
        """Helper method to find a limit (upper or lower) by moving the motor until torque limit is reached.
        
        Returns the limit position found.
        """
        motor = self.get_motor(motor_name)
        target_pos = initial_pos
        while True:
            target_pos += direction * step_size
            self.set_target_position(motor_name, target_pos)
            time.sleep(step_time)
            if verbose:
                print("torque, angle", motor.torque[0], motor.angle[0], target_pos)
            if abs(motor.torque[0]) > max_torque:
                limit = motor.angle[0]
                if verbose:
                    print(f"final_mech_pos (direction={direction})", motor.angle[0], target_pos)
                break
            # To avoid an infinite loop!
            target_distance = abs(target_pos - initial_pos)
            if target_distance > threshold_target_distance:
                curr_pos_from_motor = self.read_param_sync(motor_name, "mechpos")
                if abs(curr_pos_from_motor - initial_pos) < 0.0175:  # 0.0175 in radians is 1 degree
                    help_string = f"Motor {motor_name} has not moved during calibration (current position: {curr_pos_from_motor}, initial position: {initial_pos})."
                else:
                    help_string = f"Motor {motor_name} has moved to {curr_pos_from_motor} after attempting to reach {target_pos}, but did not hit the limit. Calibration may be faulty."
                raise MotorCalibrationError(help_string, motor=motor)
        return limit

    def get_range(
        self,
        motor_name,
        step_size=0.01,
        step_time=0.01,
        max_torque=4.5,
        verbose=False,
    ):
        if step_size < 0.001:
            raise ValueError(f"Step size is too low or negative, got {step_size}, recommended value is 0.01")
        if step_time < 0.001:
            raise ValueError(f"Step time is too low or negative, got {step_time}, recommended value is 0.01")
        if max_torque < 0:
            raise ValueError(f"Max torque cannot be negative, got {max_torque}, recommended value depends on the motor's max torque")

        motor = self.get_motor(motor_name)
        expected_range = motor.expected_range
        self.set_run_mode(motor_name, RunMode.Position)
        self.enable(motor_name)
        start_pos = self.read_param_sync(motor_name, "mechpos")

        print(f"Moving the motor {motor_name} to one end to get the range of motion, starting from {start_pos}")
        # Find upper limit (moving forward)
        upper_limit = self._find_limit(
            motor_name=motor_name,
            initial_pos=start_pos,
            step_size=step_size,
            step_time=step_time,
            max_torque=max_torque,
            threshold_target_distance=expected_range * 2.0,
            direction=1,  # forward
            verbose=verbose,
        )
        
        print(f"Reached one end at upper_limit {upper_limit}, trying to go to the other end by setting intial target to {upper_limit - (expected_range * 0.8)} and exploring the other end")
        self.set_target_position(motor_name, upper_limit - (expected_range * 0.8))
        time.sleep(1.0)
        
        lower_limit_initial_pos = upper_limit - (expected_range * 0.8)
        # Find lower limit (moving backward)
        lower_limit = self._find_limit(
            motor_name=motor_name,
            initial_pos=lower_limit_initial_pos,
            step_size=step_size,
            step_time=step_time,
            max_torque=max_torque,
            threshold_target_distance=expected_range * 2.5,
            direction=-1,  # backward
            verbose=verbose,
        )

        middle_pos = lower_limit + ((upper_limit - lower_limit) / 2)

        print(f"Reached the other end at lower_limit {lower_limit}, trying to go to the middle position by setting target position to {middle_pos}")
        self.set_target_position(motor_name, middle_pos)
        time.sleep(2.5)

        return lower_limit, upper_limit, middle_pos, abs(upper_limit - lower_limit)


    def recover_from_power_cycle(self, motor_name: str):
        motor = self.get_motor(motor_name)
        # recovers the motor from a power cycle where the encoder is reset.
        if not motor.dual_encoder:
            raise UnsafeCommandError("Only dual encoder motors can recover from power cycle.", motor=motor)
        if motor.calibration_time is None:
            raise UnsafeCommandError("Motor does not have a calibration to recover from.", motor=motor)
        
        mechpos = self.read_param_sync(motor_name, "mechpos")
        if mechpos > motor.upper_limit:
            # too high by 2 pi
            motor.upper_limit += 2 * math.pi
            motor.lower_limit += 2 * math.pi
            motor.middle_pos += 2 * math.pi
            
        if mechpos < motor.lower_limit:
            # too low by 2 pi
            motor.upper_limit -= 2 * math.pi
            motor.lower_limit -= 2 * math.pi
            motor.middle_pos -= 2 * math.pi

    def check_motors_in_range(self, motor_names: list[str], target_angle: float = None, raise_error: bool = True) -> bool:
        """Check if motors are within valid range.
        
        Validates that motors' current positions and optionally a target angle are within
        their calibrated limits (upper_limit and lower_limit).
        
        Args:
            motor_names: List of motor names to check
            target_angle: Optional target angle to validate against limits
            raise_error: If True, raise exceptions on violations; if False, return False
            
        Returns:
            True if all motors are in range, False otherwise
            
        Raises:
            ValueError: If target_angle is out of range and raise_error is True
            Exception: If current motor position is out of range and raise_error is True
        """
        for motor_name in motor_names:
            motor = self.get_motor(motor_name)
            
            # Check target angle if provided
            if target_angle is not None:
                if target_angle > motor.upper_limit or target_angle < motor.lower_limit:
                    if raise_error:
                        raise ValueError(
                            f"{target_angle} is out of range for {motor_name}. "
                            f"Range: {motor.lower_limit} to {motor.upper_limit}"
                        )
                    return False
            
            # Check motor current angle. if not in range even with +-2*pi difference, raise error, tell user to recalibrate
            try:
                mechpos = self.read_param_sync(motor_name, "mechpos")
            except Exception as e:
                if raise_error:
                    raise
                print(f"Error reading mechpos for {motor_name}: {e} in check_motors_in_range")
                return False
            if mechpos is not None and (mechpos > motor.upper_limit or mechpos < motor.lower_limit):
                if raise_error:
                    raise Exception(f"{motor_name} position {mechpos} is outside of valid range. Please recalibrate.")
                return False
        
        return True

    def motors_in_mode(self, motor_names: list[str], mode: MotorMode) -> bool:
        for motor_name in motor_names:
            motor = self.get_motor(motor_name)
            if motor.run_mode != mode:
                return False
        return True
        
