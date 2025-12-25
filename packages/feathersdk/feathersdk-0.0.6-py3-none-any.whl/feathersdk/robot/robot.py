import time
from .motors.motors_manager import MotorsManager
from .steppable_system import SteppableSystem
from .navigation_platform import ThreeWheelServeDrivePlatform
from .manipulation_platform import BimanualManipulationPlatform
from .battery_system import DualBatterySystem
from .robstride_neck_platform import RobstrideNeckPlatform
from .torso_platform import EZMotionTorsoPlatform
from .test_system import TestSystem
from ..comms import CommsManager
from ..comms.system import get_all_physical_can_interfaces
import threading
import atexit, signal, sys
from .instance_lock import get_robot_instance_lock


class Robot(SteppableSystem):
    def __init__(self, robot_name: str):
        get_robot_instance_lock(override_lock=False, strict=False)
        
        self.robot_name = robot_name
        # 10000 Hz
        self.operating_frequency = 10000
        self.systems = {}
        self.should_continue = True
        atexit.register(self.on_abort)
        signal.signal(signal.SIGTERM, self._handle_exit)
        signal.signal(signal.SIGINT, self._handle_exit)

    def start(self):
        super().start(is_root_step=True)
        for system in self.systems.values():
            if system:
                system.start()

    def _after_step(self):
        current_time = time.time()
        for system in self.systems.values():
            if system and system.get_next_step_start_time() <= current_time:
                system.step()
        
        super()._after_step()

    def _handle_exit(self, signum, frame):
        self.on_abort()
        sys.exit(0)

    def on_abort(self):
        self.should_continue = False

        for system in self.systems.values():
            if system:
                try:
                    system.on_abort()
                except Exception as e:
                    print(f"Uncaught Error in on_abort for {system}: {e}")

    def robot_loop(self):
        self.start()
        while self.should_continue:
            self.step()
        # Give time for abort to complete
        time.sleep(0.1)

    def start_loop_in_background(self):
        robot_thread = threading.Thread(target=self.robot_loop)

        robot_thread.daemon = True
        robot_thread.start()


class FeatherRobot(Robot):
    def __init__(self, robot_name: str, config: dict = {}):
        super().__init__(robot_name)
        
        self.cfg = config

        self.comms = CommsManager()
        self.comms.start(get_all_physical_can_interfaces(), enable_cans=False, allow_no_enable_can=True)

        self.torso = None
        self.navigation_platform = None

        if "power" in self.cfg:
            self.power = DualBatterySystem(self.cfg["power"])
            if self.power.is_estop_pressed():
                raise Exception("E-stop is pressed.")
        else:
            self.power = None

        self.motors_manager = MotorsManager()
        try:
            if "navigation_platform" in self.cfg:
                self.navigation_platform = ThreeWheelServeDrivePlatform(self.motors_manager, self.cfg["navigation_platform"])
                # Find the base motor can interface to use for EZMotion motors. Assume same for all base motors 
                base_can_iface = self.motors_manager.motors["BwC"].can_interface
            
                # Initialize the torso platform, bug requires base can interface.
                if "torso" in self.cfg:
                    self.torso = EZMotionTorsoPlatform(self.motors_manager, self.power, base_can_iface, self.cfg["torso"])
        except Exception:
            if not config.get("testing", False):
                raise

        # self.manipulation_platform = BimanualManipulationPlatform(self.motors_manager)
        self.manipulation_platform = None
        
        if "neck" in self.cfg:
            self.neck = RobstrideNeckPlatform(self.motors_manager, self.power, self.cfg["neck"])
        else:
            self.neck = None

        self.vision_system = None
        self.audio_system = None
        self.listening_system = None
        self.visual_system = None

        if config.get("testing", False):
            pass
            #self.test_system = TestSystem(self.motors_manager)

        self.systems = {
            "navigation_platform": self.navigation_platform,
            "manipulation_platform": self.manipulation_platform,
            "power": self.power,
            "torso": self.torso,
            "vision_system": self.vision_system,
            "audio_system": self.audio_system,
            "listening_system": self.listening_system,
            "visual_system": self.visual_system,
            "neck": self.neck,
        }

        # Automatically register systems with on_power_event method to BatterySystem
        if self.power:
            for system_name, system in self.systems.items():
                # Skip the power system itself to avoid self-registration
                if system_name != "power" and system and hasattr(system, 'on_power_event') and callable(getattr(system, 'on_power_event')):
                    self.power.add_power_event_listener(system)

    def get_battery_voltage(self):
        return 0

    def _step(self):
        pass

    def on_abort(self):
        super().on_abort()


