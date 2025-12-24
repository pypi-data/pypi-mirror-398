"""
Simple UART Central (Client) Example

This example shows how to connect to a UART Peripheral and send/receive data.

Hardware Requirements:
- Two ESP32 boards with MicroPython, OR
- One LEGO SPIKE/MINDSTORMS hub acting as peripheral
- Another MicroPython device running this code

Setup:
1. Flash MicroPython on your ESP32 board
2. Install btbricks: micropip install btbricks (or copy btbricks folder)
3. Run this code on the client/central device
4. Run ble_uart_simple_peripheral.py on the server/peripheral device
"""

from btbricks import UARTCentral
from time import sleep

# Create a UART central (client) connection
client = UARTCentral()

# Try to connect to a device named "server"
# Adjust the name based on what your peripheral is advertising
print("Connecting to server...")
if client.connect(name="server"):
    print("Connected! Sending messages...")

    # Send some test messages
    for i in range(1, 5):
        msg = f"Hello {i}!"
        print(f"Sending: {msg}")
        client.write(msg.encode() + b"\n")
        sleep(0.5)

        # Try to read response
        try:
            response = client.readline()
            if response:
                print(f"Received: {response.decode().strip()}")
        except:
            pass

        sleep(0.5)

    print("Disconnecting...")
    client.disconnect()
else:
    print("Failed to connect. Make sure peripheral is running and advertising as 'server'")

print("Done")
