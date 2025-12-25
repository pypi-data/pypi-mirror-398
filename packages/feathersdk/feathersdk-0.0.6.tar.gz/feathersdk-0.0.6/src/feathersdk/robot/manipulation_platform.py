
from .steppable_system import SteppableSystem
from .motors.motors_manager import MotorsManager, Motor, INSPIRE_RIGHT_FINGER_JOINTS_MAP, \
    INSPIRE_LEFT_FINGER_JOINTS_MAP, MotorMap

MAX_VELOCITY = 4.71

class ArmSystem(SteppableSystem):
    def __init__(self, motors_manager: MotorsManager, motors_map: MotorMap, name: str):
        self.motors_manager = motors_manager
        self.motors_manager.add_motors(motors_map, family_name=name)
        self.motors_manager.find_motors(list(motors_map.keys()))
        self.motors = motors_map

    def _step(self):
        pass

class HandSystem(SteppableSystem):
    def __init__(self, motors_manager: MotorsManager, motors_map: MotorMap, name: str):
        self.motors_manager = motors_manager
        self.motors_manager.add_motors(motors_map, family_name=name)
        self.motors = motors_map

    def _step(self):
        pass

class BimanualManipulationPlatform(SteppableSystem):
    def __init__(self, motors_manager: MotorsManager):
        # Initialize hands with the predefined INSPIRE finger motor maps
        self.right_hand = HandSystem(motors_manager, INSPIRE_RIGHT_FINGER_JOINTS_MAP, "right_hand")
        self.left_hand = HandSystem(motors_manager, INSPIRE_LEFT_FINGER_JOINTS_MAP, "left_hand")
        self.operating_frequency = 100
        
        # Initialize arms (assuming arm motor maps will be defined later)
        self.right_arm = ArmSystem(motors_manager, {
            "SpR": Motor(0x10, "SpR", {
                "joint_limits": [-1.570796, 0.117453],
                "max_torque": 10.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 3.0,
                "compliance_mode_dx": 0.001,
                "direction": -1,
            }),
            "SrR": Motor(0x11, "SrR", {
                "joint_limits": [-0.610865, 0.087266],
                "max_torque": 5.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 2.0,
                "compliance_mode_dx": 0.001,
                "direction": -1,
            }),
            "SwR": Motor(0x12, "SwR", {
                "joint_limits": [-1.570796, 0.317453],
                "max_torque": 5.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 1.0,
                "compliance_mode_dx": 0.001,    
                "direction": -1,
            }), 
            "EpR": Motor(0x13, "EpR", {
                "joint_limits": [-0.117453, 2.094395],
                "max_torque": 8.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 3.0,
                "compliance_mode_dx": 0.001,
                "direction": -1,
            }),
            "WwR": Motor(0x14, "WwR", {
                "joint_limits": [-2.356194, 0.785398],
                "max_torque": 4.0,
                "max_velocity": MAX_VELOCITY,
                "direction": -1,
            }),
            "WpR": Motor(0x15, "WpR", {
                "joint_limits": [-1.57, 1.57],
                "max_torque": 4.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 4.0,
                "compliance_mode_dx": 0.001,
                "direction": -1,
            }),
            "WrR": Motor(0x16, "WrR", {
                "joint_limits": [-1.57, 1.57], # todo, get values from joint limits using pinnochio
                "max_torque": 4.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 2.0,
                "compliance_mode_dx": 0.001,
                "direction": -1,
            })
        }, "right_arm")

        self.left_arm = ArmSystem(motors_manager, {
            "SpL": Motor(0x20, "SpL", { # likely inverted
                "joint_limits": [-0.117453, 1.570796],
                "max_torque": 10.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 3.0,
                "compliance_mode_dx": 0.001,
            }),
            "SrL": Motor(0x21, "SrL", { # likely inverted
                "joint_limits": [-0.087266, 0.610865],
                "max_torque": 5.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 2.0,
                "compliance_mode_dx": 0.001,
            }),
            "SwL": Motor(0x22, "SwL", { # likely inverted
                "joint_limits": [-0.317453, 1.570796],
                "max_torque": 5.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 1.0,
                "compliance_mode_dx": 0.001,
            }),
            "EpL": Motor(0x23, "EpL", { # likely inverted
                "joint_limits": [-2.094395, 0.117453],
                "max_torque": 8.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 3.0,
                "compliance_mode_dx": 0.001,
            }),
            "WwL": Motor(0x24, "WwL", { # likely inverted
                "joint_limits": [-0.785398, 2.356194],
                "max_torque": 4.0,
                "max_velocity": 1.5
            }),
            "WpL": Motor(0x25, "WpL", { # likely inverted
                "joint_limits": [-1.57, 1.57],
                "max_torque": 4.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 4.0,
                "compliance_mode_dx": 0.001,
            }),
            "WrL": Motor(0x26, "WrL", { # likely inverted
                "joint_limits": [-1.57, 1.57],
                "max_torque": 4.0,
                "max_velocity": MAX_VELOCITY,
                "compliance_mode_torque_threshold": 2.0,
                "compliance_mode_dx": 0.001,
            })
        }, "left_arm")

    def _step(self):
        pass

