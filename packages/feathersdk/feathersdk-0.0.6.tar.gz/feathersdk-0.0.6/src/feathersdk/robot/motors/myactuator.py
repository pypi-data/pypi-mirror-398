import can
import time
import struct
 
# Adjust these values as needed
CAN_INTERFACE = 'can4'
MOTOR_ID = 0x141  # Example motor CAN ID
 
def send_can_message(bus, arbitration_id, data):
    msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
    bus.send(msg)
    # print(f"Sent: {msg}")
 
def enable_motor(bus):
    # Motor enable is typically handled by Function Control Command (0x20 + enable index)
    # Example: enabling motor (function index 1)
    data = [0x20, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    send_can_message(bus, MOTOR_ID, data)

def zero_motor(bus):
    data = [0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    send_can_message(bus, MOTOR_ID, data)
    time.sleep(0.1)
    data2 = [0x76, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    send_can_message(bus, MOTOR_ID, data2)
    time.sleep(1)

 
def move_to_position(bus, angle_deg, speed_dps, direction=0x00):
    # Command: Single-turn position control (0xA6)
    # angle: 0.01 degree/LSB
    if direction == 0x01:
        angle_deg = 360 - angle_deg
    angle = int(angle_deg * 100)
    
    speed = int(speed_dps * 100)
    data = [
        0xA6,
        direction,
        speed & 0xFF,
        (speed >> 8) & 0xFF,
        angle & 0xFF,
        (angle >> 8) & 0xFF,
        (angle >> 16) & 0xFF,
        (angle >> 24) & 0xFF
    ]
    send_can_message(bus, MOTOR_ID, data)
 
def read_status(bus):
    # Command: Read motor status 2 (0x9C)
    data = [0x9C] + [0x00]*7
    send_can_message(bus, MOTOR_ID, data)
    msg = bus.recv(timeout=1.0)
    print('msg', msg)
    
    if msg and msg.data and msg.data[0] == 0x9c:
        temperature = msg.data[1]
        
        current = struct.unpack('<h', bytes(msg.data[2:4]))[0] * 0.01
        print(f"Temperature: {temperature}°C, Current: {current}A")
    # else:
        #print("No response received.")
 
def disable_motor(bus):
    # Command: Motor shutdown (0x80)
    data = [0x80] + [0x00]*7
    send_can_message(bus, MOTOR_ID, data)
 
def main():
    bus = can.interface.Bus(channel=CAN_INTERFACE, bustype='socketcan')
 
    enable_motor(bus)
    zero_motor(bus)
    move_to_position(bus, angle_deg=10, speed_dps=5, direction=0x01)
    for i in range(100):
        read_status(bus)
        time.sleep(.10)
    # move_to_position(bus, angle_deg=-90.0, speed_dps=15, direction=0x01)
    # time.sleep(5)
    disable_motor(bus)
    bus.shutdown()
 
if __name__ == "__main__":
    main()