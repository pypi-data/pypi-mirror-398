from .steppable_system import SteppableSystem
from .motors.motors_manager import MotorsManager, Motor
from ..comms import CommsManager
from typing import Optional
from enum import Enum
import canopen
import os
import time
from ..utils import constants
from ..robot.battery_system import PowerEvent, BatterySystem

STEPS_PER_ROTATION = 65536
DEFAULT_RPS = 100  # RPS = rotations per second
DEFAULT_ACCELERATION_RPS2 = 50
DEFAULT_DECELERATION_RPS2 = 12

ROTATIONS_PER_CM_TRAVELED = 2.54  # 1 cm traveled per 2.54 rotation
MM_IN_CM = 10

ZERO_VELOCITY_THRESHOLD = 1000
ZERO_VELOCITY_MIN_SEQUENCE = 10


def overwrite_file(filepath: str, data: list):
    with open(filepath, "w") as file:
        file.write(",".join(data))


def read_array_from_file(filepath: str):
    with open(filepath, "r") as file:
        return file.read().split(",")

class EZMotionControlMode(Enum):
    POSITION = 1
    VELOCITY = 3
    HOMING = 6

class EZMotionCommands(Enum):
    SET_MAX_HOMING_TORQUE = 0x2070
    SET_OPERATION_STATE = 0x6040
    SET_CONTROL_MODE = 0x6060
    SET_POSITION = 0x607A
    SET_VELOCITY = 0x60FF
    SET_MAX_VELOCITY = 0x6081
    SET_MAX_ACCELERATION = 0x6083
    SET_MAX_DECELERATION = 0x6084
    GET_STATUS_WORD = 0x6041
    GET_CURRENT_POSITION = 0x6064
    GET_CURRENT_TORQUE = 0x6077
    GET_CURRENT_VELOCITY = 0x606C
    GET_CURRENT_CURRENT = 0x6078
    GET_TEMPERATURE = 0x2040
    MAX_TORQUE = 0x6072
    HOMING_METHOD = 0x6098
    HOMING_SPEED = 0x6099
    HOMING_OFFSET = 0x607C
    HOMING_ACCELERATION = 0x609A

class EZMotionOperationState(Enum):
    SHUTDOWN = 0x0006
    ENABLED = 0x000F
    TRANSITION_TO_NEW_POSITION = 0x001F

class EZMotionHomingMethod(Enum):
    HOME_USING_MAX_TORQUE_UP = -0x03
    HOME_USING_MAX_TORQUE_DOWN = -0x02


class EZMotionMotor(Motor):
    def __init__(self, motor_id: int, can_interface: str, motor_name: str, config: dict):
        super().__init__(motor_id, motor_name)
        self.target_velocity = config.get("default_target_velocity_rps", DEFAULT_RPS)
        self.target_acceleration = config.get("default_target_acceleration_rps2", DEFAULT_ACCELERATION_RPS2)
        self.target_deceleration = config.get("default_target_deceleration_rps2", DEFAULT_DECELERATION_RPS2)
        self.can_interface = can_interface


class TorsoPlatform(SteppableSystem):

    def __init__(self):
        super().__init__()
        self.operating_frequency = 10

    def set_movement_profile(self, target_velocity, target_acceleration, target_jerk):
        pass

    def go_to(self, height_from_bottom: float):
        pass

    def recalibrate(self):
        pass

    async def get_position(self):
        pass

    async def get_state(self):
        pass

    async def health_check(self):
        pass


class EZMotionTorsoPlatform(TorsoPlatform):

    def __init__(self, motors_manager: MotorsManager, power: BatterySystem, can_interface: Optional[str], config: dict):
        self.cfg = config
        self.motors_map = {}
        self.power = power
        self.top_height_mm = self.cfg.get("top_height_mm", 600)
        self.bottom_height_mm = self.cfg.get("bottom_height_mm", 50)
        self.homing_offset_from_top_num_rotations = self.cfg.get("homing_offset_from_top_num_rotations", 1)
        self.homing_max_torque_percent = self.cfg.get("homing_max_torque_percent", 1000)
        self.homing_acceleration_rps2 = self.cfg.get("homing_acceleration", 50)
        self.print_packet_loss = self.cfg.get("print_packet_loss", False)
        self.last_sent_velocity = 0
        self.last_sent_acceleration = 0
        self.last_sent_deceleration = 0
        self.last_sent_position = 0

        for motor_name, motor_dict in self.cfg["motors"].items():
            self.main_motor_id = int(motor_dict["id"])
            self.main_motor_model = motor_dict["model"]
            self.motors_map[motor_name] = EZMotionMotor(self.main_motor_id, can_interface, motor_name, motor_dict["motor_config"])
        self.calibration_file_path = constants.MOTORS_CALIBRATION_PATH + "/_ezmotion_TvC.json"
        self.motors_manager = motors_manager
        self.motors_manager.add_motors(self.motors_map, family_name="torso")
        self.health_check_future = None
        self.enabled = False
        self.zero_velocity_count = 0

        # self.comms = CommsManager()
        self.network = canopen.Network()

        if can_interface is not None:
            self.network.connect(channel=can_interface, bustype="socketcan", bitrate=1000000)
            eds_file = os.path.join(os.path.dirname(__file__), "motors", self.main_motor_model + ".eds")
            self.node = self.network.add_node(self.main_motor_id, eds_file)
        else:
            self.node = None
        
        self.healthy_state = False
        # assigned_velocity was the last velocity the user requested.
        self.assigned_velocity = 0
        # last_registered_velocity is the velocity that was confirmed received by the motor.
        self.last_registered_velocity = (0, -1)
        self.last_step_time = time.time()

        try:
            last_state = read_array_from_file(self.calibration_file_path)
            if self.power is not None and self.power.last_powered_up_time() > float(last_state[2]):
                raise Exception("Error: Power cycle detected. System must be recalibrated.")
            if last_state[0] == "recalibrated":
                self.current_position = self.get_current_position_with_retry()
                self.curr_height = float(last_state[1])
                self._set_reference_position(self.current_position, self.curr_height)
                self.healthy_state = True
            if last_state[0] == "finished_moving":
                self.current_position = self.get_current_position_with_retry()
                self.curr_height = float(last_state[1])
                self._set_reference_position(self.current_position, self.curr_height)
                self.healthy_state = True
        except Exception as e:
            print("Warning: Torso must be recalibrated.")
            print(e)

        self.init_ezmotion()
        self.moving = False
        self.control_mode = EZMotionControlMode.POSITION
        self.recalibrating = False

        super().__init__()
    
    def _get_node(self):
        if self.node is None:
            raise ValueError("Node is not initialized")
        return self.node

    def init_ezmotion(self):
        if self.node is None:
            print("Warning: Node is not initialized, skipping EZMotion initialization")
            return
        self.shutdown()
        self.set_control_mode(EZMotionControlMode.POSITION)
        # self.enable()
        # self.set_movement_profile("TvC", DEFAULT_RPS, DEFAULT_ACCELERATION_RPS2, DEFAULT_DECELERATION_RPS2)

    def send_movement_profile(self, target_velocity=None, target_acceleration=None, target_deceleration=None):
        if target_velocity is not None:
            if target_velocity != self.last_sent_velocity:
                self._ensure_command(EZMotionCommands.SET_MAX_VELOCITY.value, target_velocity * STEPS_PER_ROTATION)
                self.last_sent_velocity = target_velocity
        if target_acceleration is not None:
            if target_acceleration != self.last_sent_acceleration:
                self._ensure_command(EZMotionCommands.SET_MAX_ACCELERATION.value, target_acceleration * STEPS_PER_ROTATION)
                self.last_sent_acceleration = target_acceleration
        if target_deceleration is not None:
            if target_deceleration != self.last_sent_deceleration:
                self._ensure_command(EZMotionCommands.SET_MAX_DECELERATION.value, target_deceleration * STEPS_PER_ROTATION)
                self.last_sent_acceleration = target_acceleration

    def set_movement_profile(self, target_velocity, target_acceleration, target_deceleration):
        motor = self.motors_map["TvC"]
        if target_velocity is not None:
            motor.target_velocity = target_velocity
        if target_acceleration is not None:
            motor.target_acceleration = target_acceleration
        if target_deceleration is not None:
            motor.target_deceleration = target_deceleration

    def _step(self):
        self.last_step_time = time.time()
        if self.moving:
            status_word = self.get_status_word()
            if status_word & (1 << 10):
                print("target reached")
                if self.recalibrating:
                    self.shutdown()
                    self._on_recalibrated()
                elif self.control_mode == EZMotionControlMode.POSITION:
                    self._on_target_reached()
            else:
                # 3 reads
                current_torque = self.get_current_torque()
                if current_torque > 1000 or current_torque < -1000:
                    print("calibration triggered")
                    self.shutdown()
                    if self.recalibrating:
                        self._on_recalibrated()
                current_velocity = self.get_current_velocity()
                self.current_position = self.get_current_position()
                if abs(current_velocity) < ZERO_VELOCITY_THRESHOLD:
                    self.zero_velocity_count += 1
                else:
                    self.zero_velocity_count = 0
                if self.zero_velocity_count > ZERO_VELOCITY_MIN_SEQUENCE:
                    self.moving = False
                    self._on_target_reached()

    def _ensure_command(self, command: int, value: int, subindex: int | None = None, retries: int = 5):
        for i in range(retries):
            if self._safe_command(command, value, subindex):
                return True
        return False

    def _safe_command(self, command: int, value: int, subindex: int | None = None):
        try:
            if subindex is None:
                self.node.sdo[command].raw = value
            else:
                self.node.sdo[command][subindex].raw = value
            if command == EZMotionCommands.SET_VELOCITY.value:
                self.last_registered_velocity = (value, time.time())
            return True
        except Exception as e:
            if self.print_packet_loss:
                print(
                    "_safe_command() exception - ",
                    type(e).__name__ + ": " + str(e) + ".",
                    "Command: ",
                    command,
                    "Value: ",
                    value,
                )
            return False

    def _safe_read(self, command: int):
        try:
            return self._get_node().sdo[command].raw
        except Exception as e:
            return False

    def _go_to_raw_position(self, position: int, velocity=None):
        if self.control_mode != EZMotionControlMode.POSITION:
            self.set_control_mode(EZMotionControlMode.POSITION)
        self.enable()
        if velocity is not None:
            self.send_movement_profile(velocity)
        else:
            motor = self.motors_map["TvC"]
            self.send_movement_profile(motor.target_velocity, motor.target_acceleration, motor.target_deceleration)
        if position != self.last_sent_position:
            self._ensure_command(EZMotionCommands.SET_POSITION.value, position)
            self.transition_to_new_position()
            self.last_sent_position = position
        
        # if velocity == 0:
        #     self.moving = False

    def _compute_current_height(self):
        current_position = self.get_current_position()
        num_rotations_offset = (
            self.current_position - self.reference_position["associated_position"]
        ) / STEPS_PER_ROTATION
        return (
            self.reference_position["associated_height"] - num_rotations_offset / ROTATIONS_PER_CM_TRAVELED * MM_IN_CM
        )

    def _on_target_reached(self):
        self.current_position = self.get_current_position_with_retry()
        num_rotations_offset = (
            self.current_position - self.reference_position["associated_position"]
        ) / STEPS_PER_ROTATION
        self.curr_height = (
            self.reference_position["associated_height"] - num_rotations_offset / ROTATIONS_PER_CM_TRAVELED * MM_IN_CM
        )
        overwrite_file(self.calibration_file_path, ["finished_moving", str(self.curr_height), str(time.time())])
        self.shutdown()

    def _set_reference_position(self, current_position: int, current_height: float):
        self.reference_position = {"associated_position": current_position, "associated_height": current_height}
        self.max_height_target_position = self.calc_max_height_target_position(current_height, current_position)
        self.min_height_target_position = self.calc_min_height_target_position(current_height, current_position)
        print("max min target positions", self.max_height_target_position, self.min_height_target_position)

    def _on_recalibrated(self):
        self.current_position = self.get_current_position_with_retry()
        # self.min_position = current_position + (NUM_ROTATIONS_OFFSET_FROM_TOP * STEPS_PER_ROTATION)
        self.curr_height = self.top_height_mm
        self._set_reference_position(self.current_position, self.curr_height)
        self.healthy_state = True
        overwrite_file(self.calibration_file_path, ["recalibrated", str(self.curr_height), str(time.time())])
        # Motor's target position should now be the current position.
        self.recalibrating = False

    def wait_for_recalibration(self):
        while self.recalibrating:
            time.sleep(0.1)

    def recalibrate(self):
        self._ensure_command(EZMotionCommands.SET_OPERATION_STATE.value, EZMotionOperationState.SHUTDOWN.value)
        self.set_control_mode(EZMotionControlMode.HOMING)
        self._ensure_command(EZMotionCommands.SET_OPERATION_STATE.value, EZMotionOperationState.SHUTDOWN.value)
        self._ensure_command(EZMotionCommands.SET_OPERATION_STATE.value, EZMotionOperationState.ENABLED.value)

        self._ensure_command(EZMotionCommands.HOMING_METHOD.value, -0x03)

        self._ensure_command(EZMotionCommands.SET_MAX_HOMING_TORQUE.value, self.homing_max_torque_percent, subindex=0x01)
        self._ensure_command(EZMotionCommands.HOMING_METHOD.value, EZMotionHomingMethod.HOME_USING_MAX_TORQUE_UP.value)

        self._ensure_command(EZMotionCommands.HOMING_SPEED.value, STEPS_PER_ROTATION, subindex=0x01) # to switch
        self._ensure_command(EZMotionCommands.HOMING_SPEED.value, STEPS_PER_ROTATION, subindex=0x02) # to zero

        self._ensure_command(EZMotionCommands.HOMING_ACCELERATION.value, self.homing_acceleration_rps2 * STEPS_PER_ROTATION)
        self._ensure_command(EZMotionCommands.HOMING_OFFSET.value, self.homing_offset_from_top_num_rotations * STEPS_PER_ROTATION)
        self.recalibrating = True
        self._safe_command(
            EZMotionCommands.SET_OPERATION_STATE.value, EZMotionOperationState.TRANSITION_TO_NEW_POSITION.value
        )
        self.moving = True

    def _go_to_raw_position_safely(self, position: int):
        if self.control_mode != EZMotionControlMode.POSITION:
            self.set_control_mode(EZMotionControlMode.POSITION)
        self.enable()
        self._safe_command(EZMotionCommands.SET_POSITION.value, position)
        motor = self.motors_map["TvC"]
        self.send_movement_profile(5, 5, 5)
        self.transition_to_new_position()

    def enable_velocity_mode(self):
        self.wait_for_recalibration()
        self.enable()
        self._safe_command(EZMotionCommands.SET_VELOCITY.value, 0 * STEPS_PER_ROTATION)
        motor = self.motors_map["TvC"]
        self.send_movement_profile(motor.target_velocity, motor.target_acceleration, motor.target_deceleration)
        self.transition_to_new_position()

    def _get_max_safe_height(self):
        # The springs pushes the height down. Avoid the springs to minimize cycles on the springs.
        return self.max_height_target_position + (STEPS_PER_ROTATION * 2)

    def _get_min_safe_height(self):
        # The springs pushes the height up. Avoid the springs to minimize cycles on the springs.
        return self.min_height_target_position - (STEPS_PER_ROTATION * 4)

    def _is_at_max_height(self):
        return self.current_position <= self._get_max_safe_height()

    def _is_at_min_height(self):
        return self.current_position >= self._get_min_safe_height()

    def update_velocity(self, mm_per_second: float, skip_overwrite: bool = False):
        if not self.healthy_state:
            raise Exception("Error: System must be recalibrated.")
        if mm_per_second > 200 or mm_per_second < -200:
            raise Exception("Error: Velocity is too high. Maximum velocity is 200 mm/s.")
        self.assigned_velocity = mm_per_second
        if self.current_position is not False:
            if (self._is_at_max_height() and mm_per_second > 0) or (self._is_at_min_height() and mm_per_second < 0):
                return
        rotations_per_second = mm_per_second / MM_IN_CM * ROTATIONS_PER_CM_TRAVELED
        # TODO: Currently, if we overflow the CAN line with too many commands, reading the position feedback will be delayed for the clips.
        target_velocity = -1 * rotations_per_second * STEPS_PER_ROTATION
        self.moving = True
        if self.last_registered_velocity[0] != target_velocity or time.time() - self.last_registered_velocity[1] > 0.1:
            if not skip_overwrite:
                overwrite_file(self.calibration_file_path, ["update_velocity", str(target_velocity), str(time.time())])
            if mm_per_second > 0:
                self._go_to_raw_position(
                    self.max_height_target_position, rotations_per_second
                )
            elif mm_per_second < 0:
                self._go_to_raw_position(
                    self.min_height_target_position, -1 * rotations_per_second
                )
            else:
                self._go_to_raw_position(self.current_position, 0)

            # self._safe_command(EZMotionCommands.SET_VELOCITY.value, target_velocity)

    def go_to(self, height_from_bottom: float):
        # height_from_bottom is in mm
        # TODO: Handle when the emergency stop is triggered, reference position is not updated.
        if not self.healthy_state:
            raise Exception("Error: System must be recalibrated.")
        if height_from_bottom > self.top_height_mm:
            raise Exception(f"Error: Height from bottom {height_from_bottom}mm is greater than maximum supported height {self.top_height_mm}mm.")
        if height_from_bottom < self.bottom_height_mm:
            raise Exception(f"Error: Height from bottom {height_from_bottom}mm is less than minimum supported height {self.bottom_height_mm}mm.")

        height_offset = height_from_bottom - self.reference_position["associated_height"]
        change_in_position = height_offset / MM_IN_CM * ROTATIONS_PER_CM_TRAVELED * STEPS_PER_ROTATION
        target_position = self.reference_position["associated_position"] - change_in_position
        overwrite_file(self.calibration_file_path, ["go_to", str(target_position), str(time.time())])
        self._go_to_raw_position(target_position)

    def calc_max_height_target_position(self, associated_height: float, associated_position: int):
        height_offset = self.top_height_mm - associated_height
        change_in_position = height_offset / MM_IN_CM * ROTATIONS_PER_CM_TRAVELED * STEPS_PER_ROTATION
        return associated_position - change_in_position

    def calc_min_height_target_position(self, associated_height: float, associated_position: int):
        height_offset = self.bottom_height_mm - associated_height
        change_in_position = height_offset / MM_IN_CM * ROTATIONS_PER_CM_TRAVELED * STEPS_PER_ROTATION
        return associated_position - change_in_position

    def shutdown(self):
        self.moving = False
        if self.enabled:
            self.enabled = not self._ensure_command(
                EZMotionCommands.SET_OPERATION_STATE.value, EZMotionOperationState.SHUTDOWN.value
            )

    def enable(self):
        if not self.enabled:
            self.enabled = self._ensure_command(
                EZMotionCommands.SET_OPERATION_STATE.value, EZMotionOperationState.ENABLED.value
            )

    def transition_to_new_position(self):
        # Need to reenable so the system looks for a new position.
        self._ensure_command(EZMotionCommands.SET_OPERATION_STATE.value, EZMotionOperationState.ENABLED.value)
        self._ensure_command(
            EZMotionCommands.SET_OPERATION_STATE.value, EZMotionOperationState.TRANSITION_TO_NEW_POSITION.value
        )
        self.moving = True

    def set_control_mode(self, control_mode: EZMotionControlMode):
        self.control_mode = control_mode
        self._ensure_command(EZMotionCommands.SET_CONTROL_MODE.value, control_mode.value)

    def get_status_word(self):
        return self._safe_read(EZMotionCommands.GET_STATUS_WORD.value)

    def get_current_position(self):
        return self._safe_read(EZMotionCommands.GET_CURRENT_POSITION.value)

    def get_current_velocity(self):
        return self._safe_read(EZMotionCommands.GET_CURRENT_VELOCITY.value)

    def health_check(self):
        return {
            "temperature": self._safe_read(EZMotionCommands.GET_TEMPERATURE.value),
            "current": self._safe_read(EZMotionCommands.GET_CURRENT_CURRENT.value),
            "position": self.get_current_position(),
        }

    def get_state(self):
        return {
            "temperature": self._safe_read(EZMotionCommands.GET_TEMPERATURE.value),
            "velocity": self._safe_read(EZMotionCommands.GET_CURRENT_VELOCITY.value),
            "torque": self.get_current_torque(),
            "position": self.get_current_position(),
            "height": self._compute_current_height(),
        }

    def get_current_position_with_retry(self):
        for i in range(25):
            current_position = self.get_current_position()  # Ensure the position is read
            if current_position is not False:
                return current_position
            time.sleep(0.01)
        raise Exception("Error: Failed to get essential current position.")

    def get_current_torque(self):
        return self._safe_read(EZMotionCommands.GET_CURRENT_TORQUE.value)

    def on_abort(self):
        if not hasattr(self, "current_position"):
            return
        self.update_velocity(0, skip_overwrite=True)
        self.shutdown()
        self.network.disconnect()

    def on_power_event(self, event: PowerEvent):
        if event == PowerEvent.POWER_OFF:
            self.healthy_state = False
        elif event == PowerEvent.POWER_RESTORED:
            self.healthy_state = False
