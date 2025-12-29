"""
Simple UART Peripheral (Server) Example

This example shows how to set up a UART Peripheral and accept connections.

Hardware Requirements:
- ESP32 board with MicroPython, OR
- LEGO SPIKE/MINDSTORMS hub
- Another MicroPython device running uart_central_example.py

Setup:
1. Flash MicroPython on your ESP32 board
2. Install btbricks: micropip install btbricks (or copy btbricks folder)
3. Run this code on the server/peripheral device
4. Run uart_central_example.py on the client/central device
"""

from btbricks import UARTPeripheral
from time import sleep_ms

# Create a UART peripheral (server) with a name
server = UARTPeripheral(name="server")
print("Waiting for connection...")

try:
    while True:
        if server.is_connected():
            print("Client connected!")

            # Try to read data from client
            data = server.readline()
            if data:
                print(f"Received: {data.decode().strip()}")

                # Echo the data back with a suffix
                response = data + b" [echo]\n"
                server.write(response)
                print(f"Sent: {response.decode().strip()}")
        else:
            print("Waiting for client...")
            sleep_ms(500)

except KeyboardInterrupt:
    print("Shutting down...")
    server.disconnect()
