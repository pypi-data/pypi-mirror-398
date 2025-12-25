from abc import ABC, abstractmethod
import enum
import math
import time

import numpy as np

from ..comms.comms_manager import UnknownInterfaceError
from ..utils.trajectory import change_in_vel
from .motors.motors_manager import (
    Motor, MotorMap, MotorMode, MotorsManager, RunMode, MotorError,
    MotorNotFoundError, MotorModeInconsistentError, MotorDisabledError
)
from .steppable_system import SteppableSystem
from .battery_system import PowerEvent



class NavigationMotorError(Exception):
    """Exception raised when motor errors are detected during navigation commands."""
    pass


# TODO: This might be helpful for other systems as well?
class CalibrationState(enum.Enum):
    """Represents the calibration and health state of the navigation platform."""
    
    UNINITIALIZED = "uninitialized"  # Before any checks are performed
    UNCALIBRATED = "uncalibrated"    # No calibration data exists
    OUT_OF_RANGE = "out_of_range"    # Has calibration but motors are outside valid range
    HEALTHY = "healthy"              # Calibrated and in range, ready to use
    RECALIBRATING = "recalibrating"  # Currently in the process of recalibration
    CALIBRATION_FAILED = "calibration_failed"  # Recalibration attempt failed


class NavigationPlanner(ABC):

    def __init__(self):
        self.x = 0
        self.y = 0
        self.theta = 0
        self.target_x = 0
        self.target_y = 0
        self.target_theta = 0

    def reset(self):
        self.x = 0
        self.y = 0
        self.theta = 0

    @abstractmethod
    def is_at_target_position(self):
        return (
            math.isclose(self.x, self.target_x, abs_tol=0.001)
            and math.isclose(self.y, self.target_y, abs_tol=0.001)
            and math.isclose(self.theta, self.target_theta, abs_tol=0.001)
        )


class NaiveNavigationPlanner(NavigationPlanner):

    @staticmethod
    def generate_s_curve_trajectory(T, dt, jerk, a_max, v_max, v0=0.0, a0=0.0):
        """
        Generate a jerk-limited (S-curve) trajectory.

        Parameters:
            T (float): Total trajectory time (s).
            dt (float): Time step (s).
            jerk (float): Constant jerk (m/s^3).
            a_max (float): Maximum acceleration (m/s^2).
            v_max (float): Maximum velocity (m/s).
            v0 (float): Starting velocity (m/s). Default is 0.
            a0 (float): Starting acceleration (m/s^2). Default is 0.

        Returns:
            t_arr (np.array): Array of time values.
            a_arr (np.array): Acceleration profile.
            v_arr (np.array): Velocity profile.
            x_arr (np.array): Position (displacement) profile.

        Assumes a symmetric S-curve profile where the deceleration phase is the mirror of acceleration.
        """
        # Time to ramp from a0 to a_max
        t_ramp = (a_max - a0) / jerk  # typically, a0 is 0

        # Velocity gained during one ramp (integrating acceleration from 0 to a_max)
        # For a ramp starting at 0: Δv_ramp = 0.5 * a_max * t_ramp.
        delta_v_ramp = 0.5 * a_max * t_ramp

        # Determine constant acceleration duration needed to reach v_max:
        # Total increase during acceleration phase = ramp-up + constant acceleration + ramp-down
        # = delta_v_ramp + (a_max * T_const_acc) + delta_v_ramp = a_max*T_const_acc + 2*delta_v_ramp.
        T_const_acc = (v_max - 2 * delta_v_ramp) / a_max

        # Total time for the full acceleration phase (acceleration ramp-up, constant acceleration, ramp-down)
        t_acc_phase = t_ramp + T_const_acc + t_ramp  # = T_const_acc + 2*t_ramp

        # For symmetric deceleration, deceleration phase takes the same time.
        # The remaining time is the cruise period at constant v_max.
        cruise_time = T - 2 * t_acc_phase
        if cruise_time < 0:
            raise ValueError("Total time T is too short for the given constraints.")

        # Define key time nodes:
        t1 = t_ramp  # End of acceleration ramp-up
        t2 = t1 + T_const_acc  # End of constant acceleration segment
        t3 = t2 + t_ramp  # End of acceleration ramp-down (v_max reached)
        t4 = t3 + cruise_time  # End of cruise at v_max
        t5 = t4 + t_ramp  # End of deceleration ramp-down start (acceleration = -a_max)
        t6 = t5 + T_const_acc  # End of constant deceleration segment
        t7 = t6 + t_ramp  # End of deceleration ramp-up back to 0

        # Create the time array.
        t_arr = np.arange(0, T + dt, dt)
        a_arr = np.zeros_like(t_arr)

        # Define the piecewise acceleration profile:
        # Segment 1: [0, t1]: ramp-up (a = a0 + jerk*t)
        seg1 = (t_arr >= 0) & (t_arr < t1)
        a_arr[seg1] = a0 + jerk * (t_arr[seg1])

        # Segment 2: [t1, t2]: constant acceleration (a = a_max)
        seg2 = (t_arr >= t1) & (t_arr < t2)
        a_arr[seg2] = a_max

        # Segment 3: [t2, t3]: ramp-down (a = a_max - jerk*(t - t2))
        seg3 = (t_arr >= t2) & (t_arr < t3)
        a_arr[seg3] = a_max - jerk * (t_arr[seg3] - t2)

        # Segment 4: [t3, t4]: cruise at constant velocity (a = 0)
        seg4 = (t_arr >= t3) & (t_arr < t4)
        a_arr[seg4] = 0.0

        # Segment 5: [t4, t5]: deceleration ramp (a = 0 - jerk*(t - t4))
        seg5 = (t_arr >= t4) & (t_arr < t5)
        a_arr[seg5] = -jerk * (t_arr[seg5] - t4)

        # Segment 6: [t5, t6]: constant deceleration (a = -a_max)
        seg6 = (t_arr >= t5) & (t_arr < t6)
        a_arr[seg6] = -a_max

        # Segment 7: [t6, t7]: ramp-up from deceleration (a = -a_max + jerk*(t - t6))
        seg7 = (t_arr >= t6) & (t_arr <= t7)
        a_arr[seg7] = -a_max + jerk * (t_arr[seg7] - t6)

        # Integrate acceleration to get velocity and position.
        # Using cumulative sum for a simple Euler integration.
        v_arr = np.cumsum(a_arr) * dt + v0
        x_arr = np.cumsum(v_arr) * dt

        return t_arr, a_arr, v_arr, x_arr

    @staticmethod
    def generate_s_curve_trajectory_by_displacement_math(S, dt, jerk, a_max, v_max, v0=0.0, a0=0.0):
        """
        Generate a jerk-limited (S-curve) trajectory for a given displacement S,
        handling three regimes:
        • Regime 1 (Long distance): trajectory reaches v_max.
        • Regime 2 (Intermediate): trajectory reaches a_max but not v_max.
        • Regime 3 (Short distance): trajectory is fully jerk-limited (a_max not reached).

        Parameters:
        S      : desired total displacement (m)
        dt     : time step (s)
        jerk   : constant jerk (m/s^3)
        a_max  : maximum acceleration (m/s^2)
        v_max  : maximum velocity (m/s)
        v0, a0 : initial velocity and acceleration (assumed 0)

        Returns:
        t_arr, a_arr, v_arr, x_arr : arrays of time, acceleration, velocity, and displacement.
        """
        # Threshold displacement for reaching a_max:
        S_thr = 2 * a_max**3 / jerk**2
        # Displacement required for a full profile (reaching v_max) in the acceleration phase:
        S_full = (v_max**2) / a_max + (v_max * a_max) / jerk  # note: this is the displacement in both accel+decel

        if S >= S_full:
            # Regime 1: v_max is reached.
            T_total = 2 * (v_max / a_max + a_max / jerk) + (S - S_full) / v_max
            return NaiveNavigationPlanner.generate_s_curve_trajectory(T_total, dt, jerk, a_max, v_max, v0, a0)
        elif S >= S_thr:
            # Regime 2: a_max is reached, but v_max is not.
            # In a profile that attains a_max (with no cruise), the displacement in the acceleration phase is:
            #    S_acc = a_max^3/jerk^2 + (a_max^2/jerk)*T_const + 0.5*a_max*T_const^2.
            # Setting 2*S_acc = S and solving for T_const yields:
            T_const = math.sqrt((S - a_max**3 / jerk**2) / a_max) - a_max / jerk
            # Total time:
            T_total = 4 * a_max / jerk + 2 * T_const
            # Define key time nodes:
            t1 = a_max / jerk
            t2 = t1 + T_const
            t3 = t2 + a_max / jerk  # end of acceleration phase
            t4 = t3 + a_max / jerk  # deceleration phase, first ramp
            t5 = t4 + T_const
            t6 = t5 + a_max / jerk  # end of deceleration phase

            t_arr = np.arange(0, T_total + dt, dt)
            a_arr = np.zeros_like(t_arr)
            # Acceleration phase:
            a_arr[(t_arr >= 0) & (t_arr < t1)] = jerk * t_arr[(t_arr >= 0) & (t_arr < t1)]
            a_arr[(t_arr >= t1) & (t_arr < t2)] = a_max
            a_arr[(t_arr >= t2) & (t_arr < t3)] = a_max - jerk * (t_arr[(t_arr >= t2) & (t_arr < t3)] - t2)
            # Deceleration phase (mirror the acceleration phase):
            a_arr[(t_arr >= t3) & (t_arr < t4)] = -jerk * (t_arr[(t_arr >= t3) & (t_arr < t4)] - t3)
            a_arr[(t_arr >= t4) & (t_arr < t5)] = -a_max
            a_arr[(t_arr >= t5) & (t_arr <= t6)] = -a_max + jerk * (t_arr[(t_arr >= t5) & (t_arr <= t6)] - t5)

            v_arr = np.cumsum(a_arr) * dt + v0
            x_arr = np.cumsum(v_arr) * dt
            return t_arr, a_arr, v_arr, x_arr
        else:
            # Regime 3: The distance is too short to reach a_max.
            # In a fully jerk-limit3ed (no saturation) profile the acceleration phase is composed of two segments,
            # and by symmetry the total time is T_total = 4*t_j, where:
            t_j = (S / (2 * jerk)) ** (1 / 3)
            T_total = 4 * t_j
            t1 = t_j
            t2 = 2 * t_j
            t3 = 3 * t_j
            t4 = 4 * t_j

            t_arr = np.arange(0, T_total + dt, dt)
            a_arr = np.zeros_like(t_arr)
            a_arr[(t_arr >= 0) & (t_arr < t1)] = jerk * t_arr[(t_arr >= 0) & (t_arr < t1)]
            a_arr[(t_arr >= t1) & (t_arr < t2)] = jerk * (2 * t_j - t_arr[(t_arr >= t1) & (t_arr < t2)])
            a_arr[(t_arr >= t2) & (t_arr < t3)] = -jerk * (t_arr[(t_arr >= t2) & (t_arr < t3)] - 2 * t_j)
            a_arr[(t_arr >= t3) & (t_arr <= t4)] = -jerk * (4 * t_j - t_arr[(t_arr >= t3) & (t_arr <= t4)])

            v_arr = np.cumsum(a_arr) * dt + v0
            x_arr = np.cumsum(v_arr) * dt
            return t_arr, a_arr, v_arr, x_arr

    def __init__(
        self, operating_frequency, max_velocity, max_acceleration, max_jerk, dtheta, dtheta_accel, dtheta_jerk
    ):
        super().__init__()
        self.operating_frequency = operating_frequency
        self.max_velocity = max_velocity
        self.max_acceleration = max_acceleration
        self.current_wheel_angle = 0
        self.max_jerk = max_jerk

        # Currently not supported.
        self.dtheta = dtheta
        self.dtheta_accel = dtheta_accel
        self.dtheta_jerk = dtheta_jerk

        self.curr_index = 0

    def update_trajectory_planner(self):

        target_wheel_angle = math.atan2(self.target_y, self.target_x)
        # calculate the distance to the target position
        distance = math.sqrt(self.target_x**2 + self.target_y**2)
        # calculate the time to reach the target position
        time = distance / self.target_velocity

        t_arr, a_arr, v_arr, x_arr = NaiveNavigationPlanner.generate_s_curve_trajectory_by_displacement_math(
            self.dtheta, self.operating_frequency, self.max_jerk, self.max_acceleration, self.max_velocity
        )


class VelocityNavigationPlanner(NavigationPlanner):
    """Allows the robot to be controlled by a specified velocity.
    TODO: The name of this class is misleading. A Planner builds a plan but does not control the robot in pure terms.
    This should be called VelocityController to better represent its purpose. Leaving for now for backward compatibility.
    
    Developer Notes: Any public methods of this class should
    follow _validate_and_accept_command() pattern in existing methods to ensure safety and error handling.
    """

    _BwC_MOTOR_DIRECTION = -1
    # Wheel circumference in meters, derived from wheel diameter: 0.12 m * π ≈ 0.376991 m
    _WHEEL_CIRCUMFERENCE_M = 0.12 * math.pi
    _SMALL_DELAY_SECONDS = 0.1

    def __init__(
        self, nav_platform, config: dict
    ):
        super().__init__()
        self.cfg = config
        self._current_wheel_angle = 0
        self._nav_platform : ThreeWheelServeDrivePlatform = nav_platform
        self._motor_manager = self._nav_platform.motors_manager
        self._max_velocity = config["max_velocity"]
        self._max_acceleration = config["max_acceleration"]
        # rad/s and rad/s2
        self._max_rotation_velocity = config["max_rotation_velocity"]
        self._max_rotation_acceleration = config["max_rotation_acceleration"]
        self._acceleration_ramp_time = self._max_acceleration / config["max_jerk"]
        self._acceleration_ramp_delta_velocity = change_in_vel(0, config["max_jerk"], 0, self._acceleration_ramp_time)
        self._max_jerk = config["max_jerk"]
        self.current_spd_ref = {"BpC": 0, "BpR": 0, "BpL": 0}
        self.current_acceleration = 0
        self._last_drive_key = time.time()
        self._last_turn_key = time.time()
        self._is_rotating = False
        self._last_rotate_key = time.time()
        self._rotate_key_start_time = -1
        self._rotation_target_angles = self.cfg["rotation_target_angles"]
        self._rotation_velocity = 0
        self._rotation_acceleration = 0
        self._motor_shutdown_on_abort = True
        self._enabled = False
        
        # Command state variables - these are set by command methods and read by _step()
        self._target_turning_angle_rad = None  # Dictionary: {motor_name: target_angle_rad} or None
        self._set_target_spinning_velocity_to_zero()  # Dictionary: {motor_name: target_velocity_rad_s} or None
        
        # Track last sent commands to avoid redundant CAN messages
        self._last_sent_turning_angles = {}  # {motor_name: last_sent_angle_rad}
        self._last_sent_spinning_velocities = {}  # {motor_name: last_sent_velocity_rad_s}
        self._last_command_time = 0
        self._last_command_time_per_motor = {motor_name: 0 for motor_name in self._nav_platform.ALL_MOTORS}
        self._COMMAND_REFRESH_INTERVAL = 0.1  # Refresh commands every 100ms for reliability
        
        # Feedback delay detection - threshold in seconds for detecting stale feedback
        self._feedback_delay_tolerance_seconds = config.get("feedback_delay_tolerance_seconds", 1.0)  # 1 second
        
        # Feedback delay state - tracks delay per motor in seconds (readable for monitoring)
        self._feedback_delay_per_motor = {motor_name: 0.0 for motor_name in self._nav_platform.ALL_MOTORS}
        
        # Error tracking - stores the last error that occurred during step() execution
        self._last_error = None  # Exception object or None

    def _validate_and_accept_command(self, command):
        """
        Validate system state and accept a command for later execution in the step loop.
        The command function sets state variables that will be executed by step().
        
        Args:
            command: A callable that sets navigation command state variables
            
        Raises:
            Exception: If the navigation platform is not in a healthy state (turning motors need recalibration)
            NavigationMotorError: If motor-related errors occur, with a detailed error message

        Developer Notes:
            I considered an alternate name ```_validate_and_queue_command```, however since we are
            only maintaining the last sent command (queue size 1), I chose the current name.
        """
        # Check for errors from previous step() execution
        if self._last_error is not None:
            e = self._last_error
            if isinstance(e, MotorNotFoundError):
                raise NavigationMotorError(
                    f"Motor {e.motor_name_or_id} not found during navigation command: {str(e)}."
                ) from e
            elif isinstance(e, MotorModeInconsistentError):
                raise NavigationMotorError(
                    f"Motor {e.motor_name} is not in compatible mode for the command attempted. "
                    f"Current mode: {e.current_mode.name}, Expected mode: {e.expected_mode.name}"
                ) from e
            elif isinstance(e, MotorDisabledError):
                raise NavigationMotorError(
                    f"Motor {e.motor_name} is in disabled state during navigation command. Try restarting the power cycle for Robot base."
                ) from e
            else:
                # General exception - include exception in message
                raise NavigationMotorError(
                    f"Unexpected error during navigation command execution: {str(e)}"
                ) from e
        
        if not self._enabled:
            raise Exception("Error: Navigation platform is not enabled. Try calling enable_motors method on NavigationPlanner/Platform to start the navigation system.")

        state = self._nav_platform.calibration_state
        
        if state.value == CalibrationState.RECALIBRATING.value:
            raise Exception("Error: Cannot execute navigation commands while recalibration is in progress. Please wait for calibration to complete.")
        
        if state.value != CalibrationState.HEALTHY.value:
            if state.value == CalibrationState.UNCALIBRATED.value:
                raise Exception("Error: Turning motors are not calibrated. Please use load_calibration_state() method on NavigationPlatform and follow the recommended actions.")
            elif state.value == CalibrationState.OUT_OF_RANGE.value:
                raise Exception("Error: Turning motors are out of valid range. Please use load_calibration_state() method on NavigationPlatform and follow the recommended actions.")
            elif state.value == CalibrationState.CALIBRATION_FAILED.value:
                raise Exception("Error: Previous calibration attempt failed. Please use load_calibration_state() method on NavigationPlatform and follow the recommended actions.")
            else:
                raise Exception(f"Error: Navigation platform is not ready (state: {state.value}). Please use load_calibration_state() method on NavigationPlatform and follow the recommended actions.")
        
        command()

    def _set_run_mode(self):
        try:
            for motor_name in self._nav_platform.TURNING_MOTORS:
                self._motor_manager.disable(motor_name)
                self._motor_manager.set_run_mode(motor_name, RunMode.Position)
                self._motor_manager.write_param(motor_name, "limit_spd", math.pi / 2) # for safety right now.
            for motor_name in self._nav_platform.SPINNING_MOTORS:
                self._motor_manager.disable(motor_name)
                self._motor_manager.set_run_mode(motor_name, RunMode.Speed)
                self._motor_manager.write_param(motor_name, "limit_spd", 4 * math.pi) # for safety right now.
                self._motor_manager.zero_position(motor_name) # spinning motors don't need calibration and are in velocity mode, so we zero position the motors at the time we initialize.
        except UnknownInterfaceError as e:
            print(f"Could not find interface for motors: {e}, navigation platform will be disabled")
        except Exception as e:
            print(f"Error: Enabling Navigation platform failed: {e}, commands to move the robot will not work correctly")

    def _enable_on_start_if_needed(self):
        if self.cfg.get("enable_motors_on_startup", False):
            self.enable_motors()

    def enable_motors(self):
        try:
            for motor_name in self._nav_platform.ALL_MOTORS:
                self._motor_manager.enable(motor_name)
            time.sleep(self._SMALL_DELAY_SECONDS)
            found_disabled_motors = False
            for motor_name in self._nav_platform.ALL_MOTORS:
                if self._motor_manager.motors[motor_name].mode[0] != MotorMode.Run:
                    found_disabled_motors = True
                    print (f"Motor {motor_name} is not in run mode after waiting for {self._SMALL_DELAY_SECONDS} seconds, navigation platform will be disabled, try calling enable_motors method on NavigationPlanner again or try a power cycle on the Robot")
            self._enabled = not found_disabled_motors
        except UnknownInterfaceError as e:
            print(f"Could not find interface for motors: {e}, navigation platform will be disabled")
            self._enabled = False
        except Exception as e:
            print(f"Error: Enabling motors failed: {e}, navigation platform will be disabled")
            self._enabled = False

    def set_motor_shutdown_on_abort(self, shutdown_on_abort: bool):
        self._motor_shutdown_on_abort = shutdown_on_abort

    def disable_motors(self, is_power_off: bool = False):
        # Clear command state when disabling motors
        self._target_turning_angle_rad = None
        self._set_target_spinning_velocity_to_zero()
        # Clear tracking to ensure fresh state when re-enabled
        self._last_sent_turning_angles.clear()
        self._last_sent_spinning_velocities.clear()
        # Clear command time tracking so step() won't recalculate delays
        self._last_command_time = 0
        self._last_command_time_per_motor = {motor_name: 0 for motor_name in self._nav_platform.ALL_MOTORS}
        # Clear feedback delay state when disabling motors
        self._feedback_delay_per_motor = {motor_name: 0.0 for motor_name in self._nav_platform.ALL_MOTORS}
        # Clear errors when disabling motors
        self._last_error = None
        # TODO: This is important to call step() to clear the target spinning velocity to 0.0 for the spinning motors.
        # If we don't do this, the spinning motors will continue to rotate at the last commanded velocity.
        # So the robot keeps moving even after we destroyed the instance!
        # Another approach might be to ignore _enabled flag in the step() method and continue executing the loop - but need to think about the implications.
        self.step(last_step_before_abort=True)
        if self._motor_shutdown_on_abort:
            if not is_power_off:
                for motor_name in self._nav_platform.ALL_MOTORS:
                    self._motor_manager.disable(motor_name)
        self._enabled = False

    def _set_target_spinning_velocity_to_zero(self):
        self._target_spinning_velocity_rad_s = {motor_name: 0.0 for motor_name in self._nav_platform.SPINNING_MOTORS}

    def step(self, last_step_before_abort: bool = False):
        """Execute pending commands at the operating frequency."""
        # Stop execution if disabled (e.g., due to previous errors)
        if not self._enabled:
            if last_step_before_abort:
                print (f"Enabled is False before last step before abort, skipping step")
            return
        
        # Check calibration state - don't send commands if not healthy
        state = self._nav_platform.calibration_state
        if state.value != CalibrationState.HEALTHY.value:
            if last_step_before_abort:
                print (f"Calibration state is not healthy before last step before abort, skipping step")
            return
        
        current_time = time.time()
        force_refresh = (current_time - self._last_command_time) >= self._COMMAND_REFRESH_INTERVAL
        command_sent = False
        
        try:
            delayed_motors = []
            # Calculate and store feedback delay for all motors (state variable for monitoring)
            for motor_name in self._nav_platform.ALL_MOTORS:
                motor = self._motor_manager.motors[motor_name]
                last_command_time = self._last_command_time_per_motor[motor_name]
                
                # Only calculate delay if we have both valid feedback timestamp and a command was sent
                if motor.temp.timestamp >= 0 and last_command_time > 0:
                    # We want to use the last commanded time on the motor as that is when
                    # a feedback is expected to be received. If we haven't received a feedback
                    # with the threshold time of last we commanded the motor, the motor is not 
                    # getting any feedback messages.
                    feedback_delay = last_command_time - motor.temp.timestamp
                    # Store feedback delay as state variable (readable for monitoring)
                    self._feedback_delay_per_motor[motor_name] = feedback_delay
                    if feedback_delay > self._feedback_delay_tolerance_seconds:
                        delayed_motors.append((motor_name, feedback_delay))
                else:
                    # No valid feedback or no command sent yet - set delay to 0
                    self._feedback_delay_per_motor[motor_name] = 0.0

            if any(delayed_motors):
                # If some motors are delayed, we want to stop the robot immediately.
                self._set_target_spinning_velocity_to_zero()
                
            # Handle turning motor angle command
            if self._target_turning_angle_rad is not None:
                for motor_name, target_angle in self._target_turning_angle_rad.items():
                    last_angle = self._last_sent_turning_angles.get(motor_name)
                    if force_refresh or last_angle != target_angle:
                        motor = self._motor_manager.motors[motor_name]
                        self._motor_manager.set_target_position(
                            motor_name, motor.middle_pos + target_angle
                        )
                        self._last_sent_turning_angles[motor_name] = target_angle
                        self._last_command_time_per_motor[motor_name] = current_time
                        command_sent = True
            else:
                # Clear tracking when target is None
                self._last_sent_turning_angles.clear()
            
            # Handle spinning motor velocity command
            if self._target_spinning_velocity_rad_s is not None:
                for motor_name, target_velocity in self._target_spinning_velocity_rad_s.items():
                    last_velocity = self._last_sent_spinning_velocities.get(motor_name)
                    if force_refresh or last_velocity != target_velocity:
                        if last_step_before_abort:
                            print (f"Setting target spinning velocity for {motor_name} to {target_velocity}")
                        self._motor_manager.set_target_velocity(motor_name, target_velocity)
                        self._last_sent_spinning_velocities[motor_name] = target_velocity
                        self._last_command_time_per_motor[motor_name] = current_time
                        command_sent = True
                    else:
                        if last_step_before_abort:
                            print (f"Target spinning velocity is the same as the last sent velocity for {motor_name}, skipping step")
            else:
                if last_step_before_abort:
                    print (f"Target spinning velocity is None before last step before abort, skipping step")
                # Clear tracking when target is None
                self._last_sent_spinning_velocities.clear()

            if any(delayed_motors):
                raise NavigationMotorError(f"Error: Feedback delay detected on motors: {delayed_motors}. Navigation system will be disabled.")
            
            # Update command time whenever a command is sent (state change or periodic refresh)
            if command_sent:
                self._last_command_time = current_time
                # Clear error on successful command execution
                self._last_error = None
        except Exception as e:
            self._last_error = e
            self._enabled = False

    # TODO: Do we really need to call this every time we want to execute a command?
    # This was done during an older pattern of keeping the constructor of the class
    # putting the motors in disabled state but doing lazy enabling of the motors on the
    # first time we execute a command. We changed the code since then to enable the motors
    # during the initialization of the NavigationPlanner.
    def _ensure_motors_enabled(self, motor_names):
        found_disabled_motors = False
        for motor_name in motor_names:
            if self._motor_manager.motors[motor_name].mode[0] != MotorMode.Run:
                found_disabled_motors = True
                self._motor_manager.enable(motor_name)
        if found_disabled_motors:
            time.sleep(self._SMALL_DELAY_SECONDS)
            found_disabled_motors = False
            for motor_name in motor_names:
                if self._motor_manager.motors[motor_name].mode[0] != MotorMode.Run:
                    found_disabled_motors = True
                    break
            if found_disabled_motors:
                self._enabled = False
                raise Exception("Error: Some motors are not in run mode. Try calling enable_motors method on NavigationPlanner again or try a power cycle on the Robot.")

    def orient_rotate(self):
        def _execute_orient_rotate():
            self._ensure_motors_enabled(self._nav_platform.TURNING_MOTORS)
            # Set state to orient wheels for rotation: each motor gets its specific angle from config
            self._target_turning_angle_rad = self._rotation_target_angles.copy()
            self._set_target_spinning_velocity_to_zero()
        
        self._validate_and_accept_command(_execute_orient_rotate)

    def rotate_in_place(self, speed):
        '''
        Rotate the robot in place by setting the speed of the spinning motors.
        Note that the speed is in degrees/s and also not the speed at which the robot turns.
        Args:
            speed (float): The speed in degrees/second at which all the spinning motors will rotate.
        '''
        def _execute_rotate():
            self._target_turning_angle_rad = self._rotation_target_angles.copy()
            self._ensure_motors_enabled(self._nav_platform.SPINNING_MOTORS)
            target_velocity_rad_s = self.degrees_to_radians(speed)
            self._target_spinning_velocity_rad_s = {
                motor_name: target_velocity_rad_s
                for motor_name in self._nav_platform.SPINNING_MOTORS
            }
        
        self._validate_and_accept_command(_execute_rotate)

    def _orient_angle(self, degrees):
        """Internal method to set target angle state. Actual execution happens in _step()."""
        target_angle_rad = self.degrees_to_radians(-1 * degrees)
        self._target_turning_angle_rad = {
            motor_name: target_angle_rad
            for motor_name in self._nav_platform.TURNING_MOTORS
        }

    def _set_speed(self, speed):
        """Internal method to set target speed state. Actual execution happens in _step()."""
        degrees_per_second = speed / self._WHEEL_CIRCUMFERENCE_M * 360
        base_velocity_rad_s = self.degrees_to_radians(degrees_per_second)
        self._target_spinning_velocity_rad_s = {
            motor_name: base_velocity_rad_s * self._motor_manager.motors[motor_name].direction
            for motor_name in self._nav_platform.SPINNING_MOTORS
        }

    def go_to(self, degrees, speed, motors_is_on=False):
        """
        Go to a target position and speed.
        Args:
            degrees (float): The target angle in degrees from -90 to 90 degrees. 0 represents the center. All the wheels will be turned to this angle.
            speed (float): The target speed in m/s, with valid range between -1.3 to 1.3 m/s
            motors_is_on (bool): If True, the motors will be enabled. If False, the motors will be disabled.
        """
        # TODO: The -90 and +90 values are not an immediate problem now 
        # given our expected range is 220 degrees for turning motors.
        # However, to be quite reliable, the -90 and +90 shouldn't be
        # hardcoded but they should be calculated as min(90, minimum_value_among_all_turning_motors_range / 2) 
        def _execute_go_to():
            if degrees < -90 or degrees > 90:
                raise ValueError("Degrees must be between -90 and 90 degrees")
            if speed < -1.3 or speed > 1.3:
                raise ValueError(f"Speed must be between -1.3 and 1.3 m/s, got {speed} m/s")
            if not motors_is_on:
                self._ensure_motors_enabled(self._nav_platform.TURNING_MOTORS)
                self._ensure_motors_enabled(self._nav_platform.SPINNING_MOTORS)
            self._orient_angle(degrees)
            self._set_speed(speed)
        
        self._validate_and_accept_command(_execute_go_to)

    def orient_angle(self, degrees):
        def _execute_orient():
            self._ensure_motors_enabled(self._nav_platform.TURNING_MOTORS)
            self._orient_angle(degrees)

        self._validate_and_accept_command(_execute_orient)
        # angle should be in degrees from -90 to 90 degrees. 0 represents the center. All the wheels will be turned to this angle.
        # clockwise convention. clockwise is positive.

    def set_speed(self, speed):
        # speed should be in m/s, with valid range between -1.3 to 1.3 m/s
        if speed < -1.3 or speed > 1.3:
            raise ValueError(f"Speed must be between -1.3 and 1.3 m/s, got {speed} m/s")
        def _execute_set_speed():
            self._ensure_motors_enabled(self._nav_platform.SPINNING_MOTORS)
            self._set_speed(speed)
        
        self._validate_and_accept_command(_execute_set_speed)

    def degrees_to_radians(self, degrees: float) -> float:
        """
        Convert an angle from degrees to radians.

        Args:
            degrees (float): Angle in degrees.

        Returns:
            float: Angle in radians.
        """
        return degrees * (math.pi / 180)

    def is_at_target_position(self):
        return True
    
    def get_last_error(self):
        """Get the last error that occurred during command execution in the step loop.
        
        Returns:
            Exception: The exception object or None if no errors
        """
        return self._last_error
    
    def clear_errors(self):
        """Clear the tracked error. Useful for recovery after fixing issues."""
        self._last_error = None
    
    def get_feedback_delay(self, motor_name=None):
        """Get feedback delay for motors.
        
        Args:
            motor_name (str, optional): If provided, returns delay for that specific motor.
                                      If None, returns delay for all motors as a dictionary.
        
        Returns:
            float or dict: If motor_name is provided, returns delay in seconds for that motor.
                         If motor_name is None, returns dict mapping motor_name -> delay in seconds.
                         Returns 0.0 if motor has no valid feedback or hasn't received commands yet.
        """
        if motor_name is not None:
            if motor_name not in self._nav_platform.ALL_MOTORS:
                raise ValueError(f"Motor {motor_name} is not a valid motor name. Valid motors: {self._nav_platform.ALL_MOTORS}")
            return self._feedback_delay_per_motor.get(motor_name, 0.0)
        else:
            return self._feedback_delay_per_motor.copy()


class ThreeWheelServeDrivePlatform(SteppableSystem):

    TURNING_MOTORS = ["BwC", "BwR", "BwL"]
    SPINNING_MOTORS = ["BpC", "BpR", "BpL"]
    ALL_MOTORS = TURNING_MOTORS + SPINNING_MOTORS

    def __init__(self, motors_manager: MotorsManager, config: dict):
        self.cfg = config
        self.motors_map = {}
        
        for motor_name, motor_dict in self.cfg["motors"].items():
            self.motors_map[motor_name] = Motor(int(motor_dict["id"], 16), motor_name, motor_dict["motor_config"])
        self.motors_manager = motors_manager
        self.motors_manager.add_motors(self.motors_map, family_name="wheels")
        self.motors_manager.find_motors(list(self.motors_map.keys()))

        for motor_name in self.ALL_MOTORS:
            assert motor_name in self.motors_map, f"Motor {motor_name} is expected to be in the config for navigation platform, without it, the navigation platform will not work correctly"

        # Initialize calibration state
        self.calibration_state = CalibrationState.UNINITIALIZED

        self.operating_frequency = 100
        assert "nav_planner" in self.cfg, "nav_planner configuration is required"
        self.nav_planner = VelocityNavigationPlanner(
            nav_platform=self,
            config=self.cfg["nav_planner"]["config"]
        )

        self._on_start()

    def _on_start(self):
        self.load_calibration_data()
        self.nav_planner._set_run_mode()
        self.nav_planner._enable_on_start_if_needed()

    def on_abort(self):
        self.nav_planner.disable_motors()

    def on_power_event(self, event: PowerEvent):
        """
        Handle power events from the BatterySystem.
        
        Args:
            event (PowerEvent): The power event (POWER_OFF or POWER_RESTORED)
        """
        if event == PowerEvent.POWER_OFF:
            self.nav_planner.disable_motors(is_power_off=True)
        elif event == PowerEvent.POWER_RESTORED:
            try:
                self._on_start()
            except Exception as e:
                print(f"Warning: Failed to re-enable navigation platform after power restore: {e}, Navigation system will not work, try recreating the Robot instance.")

    def _is_at_target_position(self):
        return (
            math.isclose(self.x, self.target_x, abs_tol=0.001)
            and math.isclose(self.y, self.target_y, abs_tol=0.001)
            and math.isclose(self.theta, self.target_theta, abs_tol=0.001)
        )

    def is_motors_enabled(self):
        for motor in self.motors_map.values():
            if not motor.mode[0] == MotorMode.Run:
                return False
        return True

    def _step(self):
        """
        Execute navigation commands at the operating frequency.
        Delegates to the navigation planner's step method.
        """
        self.nav_planner.step()

    def _reset_global_origin(self):
        self.x = 0
        self.y = 0
        self.theta = 0

    def _update_trajectory_plan(self):
        # x is forward, y is left, wheel_angle starts at 0 and is CCW
        # calculate the wheel angle to reach the target position
        target_wheel_angle = math.atan2(self.target_y, self.target_x)
        # calculate the distance to the target position
        distance = math.sqrt(self.target_x**2 + self.target_y**2)
        # calculate the time to reach the target position
        time = distance / self.target_velocity

    def _set_target_position(self, x=None, y=None, theta=None):
        if x is not None:
            self.target_x = x
        if y is not None:
            self.target_y = y
        if x is not None or y is not None:
            self._update_trajectory_plan()
        if theta is not None:
            self.target_theta = theta

    def _set_target_velocity(self, velocity=None, dtheta=None):
        if velocity is not None:
            self.target_velocity = velocity
        if dtheta is not None:
            self.target_dtheta = dtheta

    def _set_target_acceleration(self, acceleration=None, dtheta_accel=None):
        if acceleration is not None:
            self.target_accel = acceleration
        if dtheta_accel is not None:
            self.target_dtheta_accel = dtheta_accel

    def _set_target_jerk(self, jerk=None, dtheta_jerk=None):
        if jerk is not None:
            self.target_jerk = jerk
        if dtheta_jerk is not None:
            self.target_dtheta_jerk = dtheta_jerk

    def _set_target_state(
        self,
        x=None,
        y=None,
        theta=None,
        velocity=None,
        dtheta=None,
        acceleration=None,
        dtheta_accel=None,
        jerk=None,
        dtheta_jerk=None,
    ):
        self._set_target_position(x, y, theta)
        self._set_target_velocity(velocity, dtheta)
        self._set_target_acceleration(acceleration, dtheta_accel)
        self._set_target_jerk(jerk, dtheta_jerk)

    def _is_valid_range(self, total_range, expected_range=math.pi, tolerance=0.005):
        return total_range >= expected_range * (1.0 - tolerance) and total_range <= expected_range * (1 + tolerance)

    def _set_zero_position(self, motor_name):
        self.motors_manager.disable(motor_name)
        trials = 2
        for i in range(trials):
            self.motors_manager.zero_position(motor_name)
            time.sleep(0.1)

    def _calibrate_motor(self, motor_name, verbose=False):
        motor = self.motors_manager.motors[motor_name]
        lower_limit, upper_limit, middle_pos, total_range = self.motors_manager.get_range(motor_name, verbose=verbose)
        print(f"after first attempt to find the range before setting zero positions: {lower_limit=}, {upper_limit=}, {middle_pos=}, {total_range=}")

        # One reason the range of motion from the first attempt is not a valid range is if the Robot config does not match the 
        # range of possible motion for the motor. If that is the reason, we should fix the Robot config to match the hardware range
        # (use the range outputs from this method as a hint for config fixes).
        # There are in theory other possible mechanical / phyical reasons (for example, the motor is on a rough surface or hit something on the floor etc) 
        # that can cause this. So we retry for a few times to get the motion to reach the expected range again.
        retries = 0
        max_retries = 2
        while not self._is_valid_range(total_range, expected_range=motor.expected_range) and retries < max_retries:
            print(f"Warning: Range {total_range} is not close to {motor.expected_range} radians. Trying again to double check.")
            self._set_zero_position(motor_name)
            lower_limit, upper_limit, middle_pos, total_range = self.motors_manager.get_range(motor_name, verbose=verbose)
            print(f"Range after zeroing positions (retry attempt: {retries + 1}): {lower_limit=}, {upper_limit=}, {middle_pos=}, {total_range=}")
            time.sleep(0.1)
            retries += 1
        if retries >= max_retries:
            raise Exception(f"Error: Failed to find the range for motor {motor_name} after {max_retries} attempts. Please check the Robot config and the range of possible motion for the motor.")
        
        # At this point, we found a valid range for the motor. And the previous get_range should have moved the motor to the middle position.
        # So we set the zero position of motor to the middle position. However, sometimes setting the zero position has some drift or error.
        # To avoid any errors because of this drift, we find the range again with the zero position set to the middle position.
        # After that attempt, whatever positions we find for the range and middle position, we return them as the calibration state of the motor.
        self._set_zero_position(motor_name)
        lower_limit, upper_limit, middle_pos, total_range = self.motors_manager.get_range(motor_name, verbose=verbose)
        print(f"After final attempt to find the range after setting zero positions: {lower_limit=}, {upper_limit=}, {middle_pos=}, {total_range=}")
        return lower_limit, upper_limit, middle_pos, total_range

    def disable_motors(self):
        self.nav_planner.disable_motors()
    
    def enable_motors(self):
        self.nav_planner.enable_motors()

    def get_system_state(self):
        state = {}
        for motor_name in self.TURNING_MOTORS:
            motor = self.motors_manager.get_motor(motor_name)
            state[f"{motor_name}_angle"] = motor.calibrated_angle.value
        for motor_name in self.SPINNING_MOTORS:
            motor = self.motors_manager.get_motor(motor_name)
            state[f"{motor_name}_velocity"] = motor.velocity.value
        return state

    def load_calibration_data(self):
        """Load calibration data for all turning motors.
        
        Args:
            calibrate_if_not_found (bool): If True, calibrate only the motors that don't have calibration data saved.
            This was introduced to ease testing and development.
        """
        self.calibration_state = CalibrationState.UNINITIALIZED
        try:
            for motor_name in self.TURNING_MOTORS:
                motor = self.motors_manager.get_motor(motor_name)
                if not motor.load_calibration_state():
                    self.calibration_state = CalibrationState.UNCALIBRATED
                elif motor.dual_encoder and motor.can_interface is not None:
                    self.motors_manager.recover_from_power_cycle(motor_name)

            # Check if motors are in valid range
            if self.calibration_state.value != CalibrationState.UNCALIBRATED.value:
                if self.motors_manager.check_motors_in_range(self.TURNING_MOTORS):
                    self.calibration_state = CalibrationState.HEALTHY
                else:
                    self.calibration_state = CalibrationState.OUT_OF_RANGE
                    
            if self.calibration_state.value != CalibrationState.HEALTHY.value:
                print(f"Navigation requires recalibration. Use recalibrate() method on Robot's Navigation Platform to recalibrate the motors. Calibration state: {self.calibration_state.name}")
            else:
                print(f"Navigation platform calibration state restored successfully and the system is ready to use!")
        except Exception as e:
            print(f"Warning: Could not check turning motors health: {e}, the calibration state is left as UNCALIBRATED, try calling load_calibration_data() again and follow the recommended actions.")
            self.calibration_state = CalibrationState.UNCALIBRATED

    def recalibrate(self):
        self._recalibrate_private()

    def _recalibrate_private(self, motor_name=None, verbose=False):
        """
        Recalibrate the motors. If a motor name is provided, only recalibrate that motor.
        Else recalibrate all the motors. This private method can be used
        if we want to calibrate only one motor at a time.
        """
        if self.calibration_state.value == CalibrationState.RECALIBRATING.value:
            raise Exception("Error: Navigation platform is already recalibrating, please wait for calibration to complete.")
        
        try:
            self.calibration_state = CalibrationState.RECALIBRATING
            if motor_name is not None:
                if motor_name not in self.TURNING_MOTORS:
                    raise ValueError(f"Motor {motor_name} is not a turning motor")
                motor_names = [motor_name]
            else:
                motor_names = self.TURNING_MOTORS
            for motor_name in motor_names:
                print(f"Recalibrating {motor_name}")
                motor = self.motors_manager.get_motor(motor_name)
                total_range = 0
                middle_pos = 0
                while not self._is_valid_range(total_range, expected_range=motor.expected_range) and abs(middle_pos) < 0.15:
                    lower_limit, upper_limit, middle_pos, total_range = self._calibrate_motor(motor_name, verbose)
                motor.set_calibration(lower_limit, upper_limit, middle_pos, total_range)
                time.sleep(0.02)
            
            if motor_name is None:
                self.calibration_state = CalibrationState.HEALTHY
            else:
                range_check_for_all_motors = self.motors_manager.check_motors_in_range(self.TURNING_MOTORS, raise_error=False)
                if range_check_for_all_motors:
                    self.calibration_state = CalibrationState.HEALTHY
                else:
                    self.calibration_state = CalibrationState.OUT_OF_RANGE
                    print(f"Navigation platform calibration partial: You may need to calibrate other turning motors. Calibration state: {self.calibration_state.name}")
            
            if self.calibration_state.value == CalibrationState.HEALTHY.value:
                print(f"Navigation platform calibration completed successfully!")
        except Exception as e:
            self.calibration_state = CalibrationState.CALIBRATION_FAILED
            raise Exception(f"Error: Navigation platform recalibration failed: {e}")

    async def health_check(self):
        """
        Perform a health check on all motors and update calibration state based on motor positions.
        Returns motor states and updates calibration_state if motors are out of range.
        """
        states = {"calibration_state": self.calibration_state.name}
        states["enabled"] = self.nav_planner._enabled # TODO: Fix this private variable access.
        for motor_name in self.motors_map.keys():
            # Trigger feedback frame and wait for fresh feedback data (preserves enabled/disabled state)
            await self.motors_manager.read_current_state_async(motor_name)
            motor = self.motors_manager.motors[motor_name]
            result = {
                "mechpos": await self.motors_manager.read_param_async(motor_name, "mechpos"),
                "loc_ref": await self.motors_manager.read_param_async(motor_name, "loc_ref"),
                "mechvel": await self.motors_manager.read_param_async(motor_name, "mechvel"),
                "iqf": await self.motors_manager.read_param_async(motor_name, "iqf"),
                "loc_kp": await self.motors_manager.read_param_async(motor_name, "loc_kp"),
                "temp": motor.temp,
                "torque": motor.torque,
                "angle_internal": motor.angle,
                "angle": motor.calibrated_angle,
                "velocity": motor.velocity,
            }
            states[motor_name] = result
        return states
