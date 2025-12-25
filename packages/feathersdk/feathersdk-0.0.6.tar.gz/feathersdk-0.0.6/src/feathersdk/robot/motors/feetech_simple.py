import scservo_sdk as scs
import time

YAW_ID = 2
PITCH_ID = 1

HEAD_PITCH_CENTER_DEGREES = -55.6
HEAD_YAW_CENTER_DEGREES = -90

# To Flash the motors, use: https://github.com/huggingface/lerobot/blob/main/lerobot/scripts/configure_motor.py
# Currently installed on the jetson on the lerobot env.
class FeetechMotor:
    """A simple class to control Feetech servo motors."""
    
    def __init__(self, port, baudrate=1000000, protocol=0):
        """Initialize the Feetech motor controller.
        
        Args:
            port (str): Serial port (e.g., '/dev/ttyUSB0' or 'COM1')
            baudrate (int): Communication speed (default: 1000000)
            protocol (int): Protocol version (default: 0)
        """
        # Initialize handlers
        self.port_handler = scs.PortHandler(port)
        self.packet_handler = scs.PacketHandler(protocol)
        
        # Open port
        if not self.port_handler.openPort():
            raise Exception(f"Failed to open port {port}")
            
        # Set baudrate
        if not self.port_handler.setBaudRate(baudrate):
            raise Exception(f"Failed to set baudrate to {baudrate}")
            
        # Set timeout
        self.port_handler.setPacketTimeoutMillis(1000)  # 1 second timeout
        
    def go_to_angle(self, device_id, angle):
        """Move the motor to a specific angle.
        
        Args:
            device_id (int): ID of the motor (typically 1-252)
            angle (float): Target angle in degrees (-180 to +180)
        """
        # Convert angle to motor position (4096 steps per 360 degrees)
        steps_per_rotation = 4096
        steps_per_degree = steps_per_rotation / 360.0
        
        # Convert angle to steps (centered around 2048 which is the middle position)
        position = int(2048 + (angle * steps_per_degree))
        
        # Ensure position is within valid range (0-4095)
        position = max(0, min(4095, position))
        
        # Write the position to the motor
        result, error = self.packet_handler.write2ByteTxRx(
            self.port_handler, 
            device_id, 
            42,  # Address for Goal_Position
            position
        )
        
        if result != scs.COMM_SUCCESS:
            raise Exception(f"Failed to write position: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            raise Exception(f"Motor error: {self.packet_handler.getRxPacketError(error)}")
            
    def read_current_angle(self, device_id):
        """Read the current angle of the motor.
        
        Args:
            device_id (int): ID of the motor
            
        Returns:
            float: Current angle in degrees
        """
        # Read the current position
        position, result, error = self.packet_handler.read2ByteTxRx(
            self.port_handler,
            device_id,
            56  # Address for Present_Position
        )
        
        if result != scs.COMM_SUCCESS:
            raise Exception(f"Failed to read position: {self.packet_handler.getTxRxResult(result)}")
        elif error != 0:
            raise Exception(f"Motor error: {self.packet_handler.getRxPacketError(error)}")
            
        # Convert position to angle
        steps_per_rotation = 4096
        steps_per_degree = steps_per_rotation / 360.0
        angle = (position - 2048) / steps_per_degree
        
        return angle
    
    def smooth_move(self, device_id, angle, duration):
        """Smoothly move the motor to a specific angle.
        
        Args:
            device_id (int): ID of the motor
            angle (float): Target angle in degrees
            duration (float): Duration of the movement in seconds
        """
        start_angle = self.read_current_angle(device_id)
        total_steps = int(duration * 100)  # 100 steps per second
        step_delay = duration / total_steps
        
        for step in range(total_steps + 1):
            # Calculate intermediate angle using linear interpolation
            progress = step / total_steps
            current_angle = start_angle + (angle - start_angle) * progress
            
            # Move to intermediate position
            self.go_to_angle(device_id, current_angle)
            
            # Wait for next step
            time.sleep(step_delay)
        
        # Ensure we reach the final position exactly
        self.go_to_angle(device_id, angle)
    
    def close(self):
        """Close the serial port."""
        self.port_handler.closePort()

# Example usage:
if __name__ == "__main__":
    # Create motor controller
    motor = FeetechMotor("/dev/ttyUSB0")  # Adjust port as needed
    
    try:
        # Currently pitch
        # Move motor with ID 1 to 45 degrees (-135 (facing down) to -25 (facing up))
        # motor.go_to_angle(1,  -50) # Supported angles are -180 to 180
        
        # # Wait a moment
        # time.sleep(1)

        # for i in range(100):
        #     motor.go_to_angle(1,  -50 - (i / 2.0))
        #     motor.go_to_angle(2,  -30 - (i / 0.5))
        #     time.sleep(0.005)

        
        
        # Read current angle
        current_angle = motor.read_current_angle(PITCH_ID)
        print(f"Current angle pitch: {current_angle:.1f} degrees")

        # Currently
        # Move motor with ID 1 to 45 degrees
        # roll motor [positive is looking ~60, negative is looking left -120]
        # motor.go_to_angle(2, -30) # Supported angles are -180 to 180

        # for i in range(100):
        #     motor.go_to_angle(YAW_ID,  HEAD_YAW_CENTER_DEGREES - (i / 0.5))
        #     time.sleep(0.01)
        
        # # # Wait a moment
        # time.sleep(1)

        # motor.go_to_angle(PITCH_ID, HEAD_PITCH_CENTER_DEGREES)
        # motor.go_to_angle(YAW_ID, HEAD_YAW_CENTER_DEGREES)
        
        # Read current angle
        current_angle = motor.read_current_angle(YAW_ID)
        print(f"Current angle yaw: {current_angle:.1f} degrees")

        motor.go_to_angle(YAW_ID,  HEAD_YAW_CENTER_DEGREES)
        motor.go_to_angle(PITCH_ID,  HEAD_PITCH_CENTER_DEGREES)

        
    finally:
        # Always close the port when done
        motor.close() 