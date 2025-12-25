
import math
from .steppable_system import SteppableSystem
from .motors.motors_manager import MotorsManager, Motor, INSPIRE_RIGHT_FINGER_JOINTS_MAP, INSPIRE_LEFT_FINGER_JOINTS_MAP, RunMode, SafeStopPolicy
import time

class TestSystem(SteppableSystem):
    def __init__(self, motors_manager: MotorsManager):
        motors_map = {
            "test_motor_1": Motor("01", "test_motor_1", {
                # "joint_limits": [-3.14, 3.14],
                "max_torque": 0.75,
                "max_velocity": 3.14,
                # "max_position_dx": 0.9
            })
        }
        self.motors_manager = motors_manager
        self.motors_manager.add_motors(motors_map, "test", {"safe_stop_policy": SafeStopPolicy.COMPLIANCE_MODE})
        self.motors_manager.find_motors()
        self.motors = motors_map

    def _step(self):
        pass
