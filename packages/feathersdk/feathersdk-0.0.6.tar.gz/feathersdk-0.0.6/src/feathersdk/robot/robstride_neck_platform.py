import math
from .steppable_system import SteppableSystem

from .neck_platform import NeckPlatform
from .motors.motors_manager import MotorsManager, Motor, RunMode, MotorMode, OperationCommand, TimestampedValue
import time
import asyncio
from ..comms.comms_manager import UnknownInterfaceError
from .battery_system import BatterySystem
from .battery_system import PowerEvent

SAFETY_MARGIN = 0.5 * math.pi / 180  # .5 degree safety margin
PITCH_OFFSET = -5 * math.pi / 180  # 2 degrees offset for pitch motor
MAX_POSITION_VELOCITY = 20  # 0 - 20 rad/s (default is 10 rad/s)
MAX_POSITION_ACCELERATION = 30  # 0 - 1000 rad/s^2 (default is 10 rad/s^2) (50 stays within rated torque limits)


class RobstrideNeckPlatform(NeckPlatform):
    YAW_MOTOR_NAME = "NwC"
    PITCH_MOTOR_NAME = "NpC"

    def __init__(self, motors_manager: MotorsManager, power: BatterySystem = None, config: dict = {}):
        super().__init__()
        self.motors_manager = motors_manager
        self.power = power
        self.cfg = config
        self.enabled = False
        self.healthy_state = False
        self.recalibrating = False
        self.control_mode = RunMode.Position
        self.operation_frequency = 50

        self.target_pitch_in_degrees = None
        self.target_yaw_in_degrees = None
        self.last_sent_pitch_in_degrees = None
        self.last_sent_yaw_in_degrees = None

        # vel_max and acc_set are write only parameters, so we need to store them
        self.motor_vel_max = {}
        self.motor_acc_set = {}
        self.default_loc_kp = {}
        self.default_vel_max = {}
        self.default_acc_set = {}
        self.motors = {}

        for motor_name, motor_dict in self.cfg["motors"].items():
            self.motors[motor_name] = Motor(
                int(motor_dict["id"], 16),
                motor_name,
                motor_dict["motor_config"],
            )
            self.default_vel_max[motor_name] = motor_dict["default_velocity_max"]
            self.default_acc_set[motor_name] = motor_dict["default_acceleration_max"]
            self.default_loc_kp[motor_name] = motor_dict["default_loc_kp"]
        self.motors_manager.add_motors(
            self.motors,
            "neck",
        )

        self.motors_manager.find_motors(list(self.motors.keys()))

        for motor_name in self.motors.keys():
            self.set_movement_profile(motor_name, self.default_vel_max[motor_name], self.default_acc_set[motor_name])

        if (
            self.motors[self.PITCH_MOTOR_NAME].calibration_time is not None
            and self.motors[self.YAW_MOTOR_NAME].calibration_time is not None
            and self.motors[self.PITCH_MOTOR_NAME].can_interface is not None
            and self.motors[self.YAW_MOTOR_NAME].can_interface is not None
        ):
            if self.power is not None:
                last_powered_up_time = self.power.last_powered_up_time()
                if last_powered_up_time > self.motors[self.PITCH_MOTOR_NAME].calibration_time or last_powered_up_time > self.motors[self.YAW_MOTOR_NAME].calibration_time:
                    self.healthy_state = False
                    print("Neck needs to be recalibrated")
                else:
                    for motor_name in self.motors.keys():
                        self.motors_manager.recover_from_power_cycle(motor_name)
                    self.healthy_state = self.motors_manager.check_motors_in_range([self.PITCH_MOTOR_NAME, self.YAW_MOTOR_NAME], raise_error=False)
                    self._wakeup()
            

    def home(self):
        """ Home the neck to the homing position. """

        # normalize to be within range of motor 
        target_pitch_pos = (self.motors[self.PITCH_MOTOR_NAME].homing_pos - self.motors[self.PITCH_MOTOR_NAME].upper_limit ) / math.pi * 180
        target_yaw_pos = (self.motors[self.YAW_MOTOR_NAME].homing_pos - self.motors[self.YAW_MOTOR_NAME].middle_pos) / math.pi * 180
       
        self.last_sent_pitch_in_degrees = None
        self.last_sent_yaw_in_degrees = None
        self.move(target_pitch_pos, target_yaw_pos)

    def _wakeup(self):
        print("Waking up neck")
        try:
            self.motors_manager.write_param(self.YAW_MOTOR_NAME, "loc_kp", self.default_loc_kp[self.YAW_MOTOR_NAME])
            self.motors_manager.write_param(self.PITCH_MOTOR_NAME, "loc_kp", self.default_loc_kp[self.PITCH_MOTOR_NAME])
            self.enable_motors()
            #wait for motors to enable
            for i in range(1000):
                if self.motors_manager.motors_in_mode(self.motors.keys(), MotorMode.Run):
                    break
                time.sleep(0.001)
                if i % 10 == 0:
                    self.enable_motors()

            self.home()
        except UnknownInterfaceError as e:
            print(f"CAN {e}, neck platform will be disabled")
            self.enabled = False
        except Exception as e:
            print(f"Error: Neck wakeup failed: {e}")
            self.enabled = False

    def enable_motors(self):
        for motor_name in self.motors:
            self.motors_manager.set_run_mode(motor_name, RunMode.Position)
            self.motors_manager.enable(motor_name)
        self.enabled = True

    def sleep_and_disable(self):
        # recalibrate with default vel_max and acc_set
        try:
            in_range = self.motors_manager.check_motors_in_range(self.motors.keys(), raise_error=False)
            if self.healthy_state and not self.recalibrating and self.enabled and in_range:

                #set back to default vel_max and acc_set
                for motor_name in self.motors.keys():
                    self.motors_manager.write_param(motor_name, "vel_max", self.default_vel_max[motor_name])
                    self.motors_manager.write_param(motor_name, "acc_set", self.default_acc_set[motor_name])

                self.motors_manager.set_target_position(
                    self.PITCH_MOTOR_NAME, self.motors[self.PITCH_MOTOR_NAME].upper_limit - SAFETY_MARGIN
                )
                self.motors_manager.set_target_position(
                    self.YAW_MOTOR_NAME, self.motors[self.YAW_MOTOR_NAME].middle_pos
                )
                time.sleep(1.0)
                # set back to what the user set
                for motor_name in self.motors.keys():
                    self.set_movement_profile(
                        motor_name,
                        self.motor_vel_max[motor_name],
                        self.motor_acc_set[motor_name],
                    )
                self.target_pitch_in_degrees = None
                self.target_yaw_in_degrees = None
                self.last_sent_pitch_in_degrees = None
                self.last_sent_yaw_in_degrees = None
            else:
                print("Motor does not meet sleep and disable conditions, disabling motor")
        except Exception as e:
            #called on on abort, not best to raise an error here
            print(f"Unexpected Error: Neck sleep and disable failed: {e}")
            raise
        finally:
            self.disable_motors()
            self.enabled = False

    def disable_motors(self):
        for motor_name in self.motors:
            self.motors_manager.disable(motor_name)
        self.enabled = False

    def get_system_state(self):
        state = {}
        for motor_name in self.motors:
            motor = self.motors_manager.get_motor(motor_name)
            state[f"{motor_name}_angle"] = motor.calibrated_angle.value
        return state

    def _step(self):
        # We might have to move this into a background thread because _move is blocking 0.001s to execute
        # which means it delays the step loops of all systems by 0.05s assuming a move command is always
        # being sent.        
        self._move(self.target_pitch_in_degrees, self.target_yaw_in_degrees)

    def set_movement_profile(
        self,
        motor_name: str,
        max_velocity: float,
        max_acceleration: float,
        max_jerk=None,
    ):
        # raise an error it not in range [0, MAX_POS_VELOCITY] or [0, MAX_POS_ACCELERATION]
        if max_velocity > MAX_POSITION_VELOCITY or max_velocity < 0.1:
            raise ValueError(f"Error: Max velocity must be between 0.1 and {MAX_POSITION_VELOCITY} rad/s")
        if max_acceleration > MAX_POSITION_ACCELERATION or max_acceleration < 0.1:
            raise ValueError(f"Error: Max acceleration must be between 0.1 and {MAX_POSITION_ACCELERATION} rad/s^2")
        if max_jerk is not None:
            raise ValueError(f"Max Jerk is not supported")

        # Update the stored values for this motor
        if motor_name in self.motors:
            self.motor_vel_max[motor_name] = max_velocity
            self.motor_acc_set[motor_name] = max_acceleration
        else:
            raise ValueError(f"Motor {motor_name} is not a valid neck motor. Valid motors: {list(self.motors.keys())}")

        # Write the parameters to the motor
        self.motors_manager.write_param(motor_name, "vel_max", max_velocity)
        self.motors_manager.write_param(motor_name, "acc_set", max_acceleration)

    def _move(self, pitch_in_degrees: float = None, yaw_in_degrees: float = None, verbose: bool = False):
        # Move without safety checks
        # only waits for movement to finish if verbose is True, otherwise will move to latest command

        try:
            start_time = time.time()
            if pitch_in_degrees is not None:
                pitch_in_radians = (pitch_in_degrees * math.pi / 180) + PITCH_OFFSET
                if verbose:
                    print("trying to go to pitch: ", self.motors[self.PITCH_MOTOR_NAME].upper_limit + pitch_in_radians)

                if self.last_sent_pitch_in_degrees != pitch_in_degrees:
                    self.motors_manager.set_target_position(
                        self.PITCH_MOTOR_NAME, self.motors[self.PITCH_MOTOR_NAME].upper_limit + pitch_in_radians
                    )
                    self.last_sent_pitch_in_degrees = pitch_in_degrees

            if yaw_in_degrees is not None:
                yaw_in_radians = yaw_in_degrees * math.pi / 180
                if verbose:
                    print("trying to go to yaw: ", self.motors[self.YAW_MOTOR_NAME].middle_pos + yaw_in_radians)
                
                if self.last_sent_yaw_in_degrees != yaw_in_degrees:
                    self.motors_manager.set_target_position(
                        self.YAW_MOTOR_NAME, self.motors[self.YAW_MOTOR_NAME].middle_pos + yaw_in_radians
                    )
                    self.last_sent_yaw_in_degrees = yaw_in_degrees

            # makes the code wait for the movement to finish by printing torque and angle of pitch motor until complete
            while True and verbose:
                self.motors_manager.enable(self.PITCH_MOTOR_NAME)
                self.motors_manager.enable(self.YAW_MOTOR_NAME)
                time.sleep(0.05)
                curr_pitch_pos = self.motors[self.PITCH_MOTOR_NAME].angle[0]
                curr_yaw_pos = self.motors[self.YAW_MOTOR_NAME].angle[0]
                print(
                    f"Pitch torque: {self.motors[self.PITCH_MOTOR_NAME].torque[0]}, Pitch angle: {self.motors[self.PITCH_MOTOR_NAME].angle[0]}, velocity: {self.motors[self.PITCH_MOTOR_NAME].velocity[0]}\n"
                    f"Yaw torque: {self.motors[self.YAW_MOTOR_NAME].torque[0]}, Yaw angle: {self.motors[self.YAW_MOTOR_NAME].angle[0]}, velocity: {self.motors[self.YAW_MOTOR_NAME].velocity[0]}"
                )
                if (
                    abs(self.motors[self.PITCH_MOTOR_NAME].upper_limit + pitch_in_radians - curr_pitch_pos) < 0.02
                    and abs(self.motors[self.YAW_MOTOR_NAME].middle_pos + yaw_in_radians - curr_yaw_pos) < 0.02
                ):
                    print(f"Final Pitch Position: {curr_pitch_pos}, Final Yaw Position: {curr_yaw_pos}")
                    print(f"Time taken to complete: {time.time() - start_time}")
                    break
        except Exception as e:
            raise Exception(f"Error: Neck movement failed: {e}")

    def move(self, pitch_in_degrees: float = None, yaw_in_degrees: float = None):
        # Step will read the target_pitch and yaw at operation frequency and call the _move method
        # to prevent overloading the CAN bus with too many commands.
        if not self.enabled:
            raise Exception("Error: Neck must be enabled. Enable with enable_motors() method.")
        if not self.healthy_state:
            raise Exception("Error: Neck must be recalibrated. Recalibrate with recalibrate() method.")
        if self.recalibrating:
            raise Exception("Error: Neck is recalibrating, please wait for calibration to complete.")
        # if pitch in degrees not in range [-120, 0], raise error
        if pitch_in_degrees is not None and (pitch_in_degrees < -120 or pitch_in_degrees > 0):
            raise ValueError(f"Pitch in degrees must be between -120 and 0. Got {pitch_in_degrees}")
        # if yaw in degrees not in range [-90, 90], raise error
        if yaw_in_degrees is not None and (yaw_in_degrees < -90 or yaw_in_degrees > 90):
            raise ValueError(f"Yaw in degrees must be between -90 and 90. Got {yaw_in_degrees}")
        self.target_pitch_in_degrees = pitch_in_degrees
        self.target_yaw_in_degrees = yaw_in_degrees

    def recalibrate(self, verbose: bool = False):

        if self.recalibrating:
            raise Exception("Error: Neck is already recalibrating, please wait for calibration to complete.")
        
        try:
            self.recalibrating = True
            for motor_name in self.motors.keys():
                # recalibrate with default vel_max and acc_set
                self.motors_manager.write_param(motor_name, "vel_max", self.default_vel_max[motor_name])
                self.motors_manager.write_param(motor_name, "acc_set", self.default_acc_set[motor_name])
                motor = self.motors[motor_name]
                lower_limit, upper_limit, middle_pos, total_range = self.motors_manager.get_range(
                    motor_name, max_torque=1.5, step_time=0.05, verbose=verbose
                )
                if motor_name == self.YAW_MOTOR_NAME:
                    self.motors_manager.disable(motor_name)
                    # higher accuracy by zeroing twice
                    self.motors_manager.zero_position(motor_name)
                    time.sleep(0.2)
                    self.motors_manager.zero_position(motor_name)
                    time.sleep(0.2)

                else:
                    self.motors_manager.set_target_position(motor_name, upper_limit)
                    time.sleep(2.0)
                    self.motors_manager.disable(motor_name)
                    self.motors_manager.zero_position(motor_name)
                    time.sleep(0.2)
                    self.motors_manager.zero_position(motor_name)
                    time.sleep(0.2)

                motor_lower_limit, motor_upper_limit, motor_middle_pos, motor_total_range = (
                    self.motors_manager.get_range(
                        motor_name, max_torque=1.5, step_time=0.05, verbose=verbose
                    )
                )
                motor.set_calibration(motor_lower_limit, motor_upper_limit, motor_middle_pos, motor_total_range)

                if motor_name == self.PITCH_MOTOR_NAME:
                    self.motors_manager.set_target_position(
                        motor_name, motor_upper_limit - (math.pi / 2) + PITCH_OFFSET
                    )
                elif motor_name == self.YAW_MOTOR_NAME:
                    self.motors_manager.set_target_position(motor_name, motor_middle_pos)

            # set back to what the user set
            self.set_movement_profile(
                self.PITCH_MOTOR_NAME,
                self.motor_vel_max[self.PITCH_MOTOR_NAME],
                self.motor_acc_set[self.PITCH_MOTOR_NAME],
            )
            self.set_movement_profile(
                self.YAW_MOTOR_NAME, self.motor_vel_max[self.YAW_MOTOR_NAME], self.motor_acc_set[self.YAW_MOTOR_NAME]
            )
        except Exception as e:
            self.recalibrating = False
            self.enabled = True
            self.healthy_state = False
            raise Exception(f"Error: Neck recalibration failed: {e}")

        self.healthy_state = True
        self.recalibrating = False
        self.enabled = True
        self.target_pitch_in_degrees = self.motors[self.PITCH_MOTOR_NAME].homing_pos / math.pi * 180
        self.target_yaw_in_degrees = self.motors[self.YAW_MOTOR_NAME].homing_pos / math.pi * 180
        self.last_sent_pitch_in_degrees = None
        self.last_sent_yaw_in_degrees = None

    async def get_position(self, force_update: bool = False) -> dict[str, float]:
        # to get angle asyncronously from feedback frame need to ping motor for (feedback frame (not async))
        # or enable active reporting (continous polling), so using async mechpos instead
        positions = {}
        for motor_name in self.motors:
            if motor_name == self.PITCH_MOTOR_NAME:
                result = await self.motors_manager.read_param_async(motor_name, "mechpos") + PITCH_OFFSET
            else:
                result = await self.motors_manager.read_param_async(motor_name, "mechpos")
            positions[motor_name] = result
        return positions

    async def get_state(self, motor_name: str) -> dict[str, TimestampedValue]:
        # get temp, torque, angle, velocity from motor feedback frame
        state = {}
        await self.motors_manager.read_current_state_async(motor_name)
        motor = self.motors_manager.motors[motor_name]
        state["temp"] = motor.temp
        state["torque"] = motor.torque
        state["angle"] = motor.angle
        state["velocity"] = motor.velocity
        return state

    async def health_check(self) -> dict[str, dict[str, float]]:
        # call motors_manager.read_param_async for each motor and return the (mechpos, loc_ref, velocity, iqf, vel_max, acc_set, loc_kp, spd_kp, spd_ki, spd_filt_gain)
        states = {}
        for motor_name in self.motors:
            result = {
                "mechpos": await self.motors_manager.read_param_async(motor_name, "mechpos"),
                "loc_ref": await self.motors_manager.read_param_async(motor_name, "loc_ref"),
                "velocity": await self.motors_manager.read_param_async(motor_name, "mechvel"),
                "iqf": await self.motors_manager.read_param_async(motor_name, "iqf"),
                "vel_max": self.motor_vel_max[motor_name],
                "acc_set": self.motor_acc_set[motor_name],
                "loc_kp": await self.motors_manager.read_param_async(motor_name, "loc_kp"),
            }
            states[motor_name] = result
        return states

    def on_abort(self):
        self.sleep_and_disable()

    def on_power_event(self, event: PowerEvent):
        if event == PowerEvent.POWER_OFF:
            self.healthy_state = False
        elif event == PowerEvent.POWER_RESTORED:
            self.healthy_state = False