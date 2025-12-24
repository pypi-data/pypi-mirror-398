"""
RC Receiver Example

This example shows how to receive RC control signals.

Hardware Requirements:
- ESP32 board or LEGO SPIKE/MINDSTORMS hub
- Motors or other actuators on the device ports
- A device running rc_transmitter_example.py

Setup:
1. Flash MicroPython on your receiver device
2. Install btbricks: micropip install btbricks
3. Connect motors to ports
4. Run this code on the receiver
5. Run rc_transmitter_example.py on the transmitter

The receiver will listen for control signals and you can use them
to control motors, servos, or other outputs.
"""

from btbricks import RCReceiver, L_STICK_HOR, R_STICK_VER, L_TRIGGER, R_TRIGGER
from time import sleep_ms

# Create RC receiver with a name that matches what the transmitter connects to
rcv = RCReceiver(name="robot")

print("Waiting for RC transmitter to connect...")

try:
    while True:
        if rcv.is_connected():
            print("RC Transmitter connected!")

            # Get control values from transmitter
            # These are in range [-100, 100]
            steering = rcv.get_value(L_STICK_HOR)  # Left stick horizontal
            throttle = rcv.get_value(R_STICK_VER)  # Right stick vertical
            aux1 = rcv.get_value(L_TRIGGER)  # Left trigger
            aux2 = rcv.get_value(R_TRIGGER)  # Right trigger

            print(
                f"Steering: {steering:4d} | Throttle: {throttle:4d} | Aux1: {aux1:4d} | Aux2: {aux2:4d}"
            )

            # Example: Use these values to control motors
            # motor_left_power = throttle - steering
            # motor_right_power = throttle + steering
            # motor_left.dc(motor_left_power)
            # motor_right.dc(motor_right_power)

            sleep_ms(100)
        else:
            print("Waiting for transmitter connection...")
            sleep_ms(500)

except KeyboardInterrupt:
    print("Stopping receiver...")
    rcv.disconnect()

print("Done")
