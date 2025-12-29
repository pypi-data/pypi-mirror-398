"""
RC Transmitter Example

This example shows how to send RC control signals.

Hardware Requirements:
- ESP32 board with analog joysticks/potentiometers, OR
- LEGO MINDSTORMS Robot Inventor with motors as analog inputs
- A device running rc_receiver_example.py

Setup:
1. Flash MicroPython on your transmitter device
2. Install btbricks: micropip install btbricks
3. Connect analog inputs (joysticks, potentiometers, buttons)
4. Run this code on the transmitter

Expected Hardware:
- Analog input on pin for left stick horizontal (L_STICK_HOR = 0)
- Analog input on pin for right stick vertical (R_STICK_VER = 3)
- Analog input on pin for triggers (L_TRIGGER = 4, R_TRIGGER = 5)
"""

from btbricks import RCTransmitter, L_STICK_HOR, R_STICK_VER, L_TRIGGER, R_TRIGGER
from time import sleep

# Create RC transmitter
tx = RCTransmitter()

# Connect to a receiver (adjust name as needed)
print("Connecting to receiver...")
if tx.connect(name="robot"):
    print("Connected! Sending RC commands...")

    try:
        while True:
            # Example: Send fixed control values
            # In a real application, you would read from joysticks/analog inputs

            # Set left stick horizontal (steering)
            tx.set_stick(L_STICK_HOR, 0)

            # Set right stick vertical (throttle)
            tx.set_stick(R_STICK_VER, 50)  # 50% forward

            # Set left trigger (auxiliary control)
            tx.set_stick(L_TRIGGER, 25)

            # Set right trigger (auxiliary control)
            tx.set_stick(R_TRIGGER, 0)

            # Send all stick values to receiver
            tx.transmit()

            print("Sent RC command")
            sleep(0.1)

    except KeyboardInterrupt:
        print("Stopping transmitter...")
        tx.disconnect()
else:
    print("Failed to connect to receiver")

print("Done")
