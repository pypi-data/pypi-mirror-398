


class TwoDOFNeckVisionSystem(SteppableSystem):

    
    
    def __init__(self, motors_manager: MotorsManager):
        self.motors_map = {
            "BwC": Motor("70", WHEELS_CAN_INTERFACE, "BwC"),
            "BwR": Motor("71", WHEELS_CAN_INTERFACE, "BwR"),
            "BwL": Motor("72", WHEELS_CAN_INTERFACE, "BwL"),
            "BpC": Motor("73", WHEELS_CAN_INTERFACE, "BpC"),
            "BpR": Motor("74", WHEELS_CAN_INTERFACE, "BpR"),
            "BpL": Motor("75", WHEELS_CAN_INTERFACE, "BpL")
        }
        self.motors_manager = motors_manager
        self.motors_manager.add_motors(self.motors_map)

        self.operating_frequency = 100
        self.nav_planner = RemoteNavigationPlanner(
            nav_platform=self,
            max_velocity=0.1,
            max_acceleration=0.1,
            max_jerk=1.0,
            max_rotation_velocity=0.075,
            max_rotation_acceleration=0.15)
        # self.nav_planner = NaiveNavigationPlanner(
        #     operating_frequency=self.operating_frequency,
        #     max_velocity=0.5,
        #     max_acceleration=0.5,
        #     max_jerk=1.0, # 2x max acceleration
        #     dtheta=math.pi/2,
        #     dtheta_accel=math.pi/2,
        #     dtheta_jerk=math.pi/2)

        self.reset()

    def reset(self):
        # Reset to a safe state
        for motor_name in self.SPINNING_MOTORS:
            self.motors_manager.disable(motor_name)
            self.motors_manager.write_param(motor_name, "run_mode", 1)
            self.motors_manager.write_param(motor_name, "limit_spd", 4 * math.pi) # for safety right now.
            self.motors_manager.zero_position(motor_name)

    def on_abort(self):
        for motor_name in self.SPINNING_MOTORS:
            self.motors_manager.disable(motor_name)
        for motor_name in self.TURNING_MOTORS:
            self.motors_manager.disable(motor_name)

    def is_at_target_position(self):
        return (math.isclose(self.x, self.target_x, abs_tol=0.001) and math.isclose(self.y, self.target_y, abs_tol=0.001) and math.isclose(self.theta, self.target_theta, abs_tol=0.001))
    
    def is_motors_enabled(self):
        for motor in self.motors_map.values():
            if not motor.mode[0] == MotorMode.Run:
                return False
        return True

    def _step(self):
        self.nav_planner.step()

        # Move to target position

        # TODO: If the motor is at the right angle:

    def reset_global_origin(self):
        self.x = 0
        self.y = 0
        self.theta = 0

    def update_trajectory_plan(self):
        # x is forward, y is left, wheel_angle starts at 0 and is CCW
        # calculate the wheel angle to reach the target position
        target_wheel_angle = math.atan2(self.target_y, self.target_x)
        # calculate the distance to the target position
        distance = math.sqrt(self.target_x**2 + self.target_y**2)
        # calculate the time to reach the target position
        time = distance / self.target_velocity
        
        

    def set_target_position(self, x=None, y=None, theta=None):
        if x is not None:
            self.target_x = x
        if y is not None:
            self.target_y = y
        if x is not None or y is not None:
            self.update_trajectory_plan()
        if theta is not None:
            self.target_theta = theta

    def set_target_velocity(self, velocity=None, dtheta=None):
        if velocity is not None:
            self.target_velocity = velocity
        if dtheta is not None:
            self.target_dtheta = dtheta

    def set_target_acceleration(self, acceleration=None, dtheta_accel=None):
        if acceleration is not None:
            self.target_accel = acceleration
        if dtheta_accel is not None:
            self.target_dtheta_accel = dtheta_accel

    def set_target_jerk(self, jerk=None, dtheta_jerk=None):
        if jerk is not None:
            self.target_jerk = jerk
        if dtheta_jerk is not None:
            self.target_dtheta_jerk = dtheta_jerk

    def set_target_state(self, x=None, y=None, theta=None, velocity=None, dtheta=None, acceleration=None, dtheta_accel=None, jerk=None, dtheta_jerk=None):
        self.set_target_position(x, y, theta)
        self.set_target_velocity(velocity, dtheta)
        self.set_target_acceleration(acceleration, dtheta_accel)
        self.set_target_jerk(jerk, dtheta_jerk)
