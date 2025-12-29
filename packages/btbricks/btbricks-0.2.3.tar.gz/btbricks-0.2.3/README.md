<div align="center">
<img alt="btbricks logo" src="https://raw.githubusercontent.com/antonvh/btbricks/master/img/btbricks.png" width="200">

# btbricks

[![PyPI Version](https://img.shields.io/pypi/v/btbricks.svg)](https://pypi.org/project/btbricks/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MicroPython](https://img.shields.io/badge/MicroPython-compatible-orange.svg)](https://micropython.org/)

btbricks is MicroPython Bluetooth library. It implements **BLE** (Bluetooth 5, Bluetooth Low Energy). Of the know BLE services, this library implements **Nordic Uart Service** (NUS), **LEGO Service** and **MIDI service**. The library contains both the BLE Central (client) and BLE Peripheral (server) classes.

</div>

The BLE services allow controlling LEGO hubs running official firmware. You can
also create custom Bluetooth peripherals: RC controllers, MIDI devices, and more.
For LEGO hub control, a
[hub expansion board like the LMS-ESP32](https://www.antonsmindstorms.com/product/wifi-python-esp32-board-for-mindstorms/)
is recommended.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Documentation](#documentation-and-api-reference)
- [Supported Platforms](#supported-platforms)
- [License](#license)
- [Author](#author)

## Features

- 🔌 **BLE Communication**: Comprehensive Bluetooth Low Energy support via
  MicroPython's `ubluetooth`
- 🎮 **Hub Control**: Control LEGO MINDSTORMS hubs, SPIKE sets, and smart hubs
  over Bluetooth
- 📱 **Custom Peripherals**: Create RC controllers, MIDI controllers, and other
  BLE peripherals compatible with LEGO hubs
- 🚀 **MicroPython Ready**: Optimized for MicroPython on ESP32, LEGO SPIKE, and
  other platforms
- 📡 **LEGO Protocol**: Full support for LEGO Bluetooth protocols (LPF2, LPUP,
  CTRL+)
- 🎛️ **Multiple Interfaces**: Nordic UART, MIDI, RC control, and native LEGO hub
  communication
- ⚙️ **Advanced BLE**: Automatic MTU negotiation, descriptor handling, and
  efficient payload management

## Installation

### Using ViperIDE Package Manager (Recommended)

1. Open **ViperIDE** on your device
2. Go to **Tools** → **Package Manager**
3. Select **Install Package via Link**
4. Enter the package link: `https://github.com/antonvh/btbricks.git`
5. Follow the on-screen prompts to complete installation

### On LMS-ESP32

The module should be included in the latest Micropython firmware from <https:/firmware.antonsmindstorms.com>. If not, use ViperIDE as described above.

### On SPIKE Legacy or MINDSTORMS Robot Inventor

Use the installer script in mpy-robot-tools: <https://github.com/antonvh/mpy-robot-tools/blob/master/Installer/install_mpy_robot_tools.py>

### Deprecated: using `micropip` from PyPI

```python
import micropip
await micropip.install("btbricks")
```

Note: `micropip` must be available on the target board and may require an internet connection from the device.

## Quick Start

### Connect to a LEGO Hub

```python
from btbricks import BtHub

# Create hub instance
hub = BtHub()

# Connect to a nearby hub
hub.connect()

if hub.is_connected():
    # Set hub LED to green
    hub.set_led_color(6)  # GREEN constant
    
    # Read accelerometer data
    acc = hub.acc()
    if acc:
        print(f"Accelerometer: {acc}")
    
    # Control motor on port A with 50% power
    hub.dc("A", 50)
    
    hub.disconnect()
```

### Create an RC Receiver (Hub-side)

Use the examples in the `examples/` folder for full, runnable code. Minimal
receiver/transmitter snippets:

```python
from btbricks import RCReceiver, R_STICK_HOR, R_STICK_VER
from time import sleep_ms

# Create RC receiver (advertises as "robot" by default)
rcv = RCReceiver(name="robot")

print("Waiting for RC transmitter to connect...")
try:
    while True:
        if rcv.is_connected():
            steering = rcv.controller_state(R_STICK_HOR)
            throttle = rcv.controller_state(R_STICK_VER)
            print(f"Steering: {steering}, Throttle: {throttle}")
            sleep_ms(100)
        else:
            sleep_ms(500)
except KeyboardInterrupt:
    rcv.disconnect()
```

```python
from btbricks import RCTransmitter, L_STICK_HOR, R_STICK_VER
from time import sleep

# Create RC transmitter (central)
tx = RCTransmitter()

if tx.connect(name="robot"):
    try:
        while tx.is_connected():
            # Set stick values in range [-100, 100]
            tx.set_stick(L_STICK_HOR, 0)
            tx.set_stick(R_STICK_VER, 50)
            tx.transmit()
            sleep(0.1)
    except KeyboardInterrupt:
        tx.disconnect()
```

### Create a MIDI Controller

```python
from btbricks import MidiController
from time import sleep

# Create MIDI controller (advertises as "amh-midi" by default)
midi = MidiController(name="amh-midi")

print("MIDI controller started, connect from your DAW...")

try:
    while True:
        # Send MIDI note on: middle C (note 60), velocity 100
        midi.note_on(60, 100)
        sleep(0.5)
        
        # Send MIDI note off
        midi.note_off(60)
        sleep(0.5)
        
        # Or send a chord
        midi.chord_on("C4", velocity=100, style="M")  # C major chord
        sleep(1)
        midi.note_off(60)  # Stop the chord
        
except KeyboardInterrupt:
    print("MIDI controller stopped")
```

## Documentation and API reference

See the full documentation and API reference at:

[docs.antonsmindstorms.com](https://docs.antonsmindstorms.com/en/latest/Software/btbricks/docs/index.html)

### Core Classes

- `BLEHandler`: Low-level Bluetooth communication
- `UARTCentral`: Nordic UART client mode
- `UARTPeripheral`: Nordic UART server mode
- `RCReceiver`: Receive RC control signals
- `RCTransmitter`: Send RC control signals
- `MidiController`: Send MIDI commands over BLE
- `BtHub`: High-level hub communication interface

### Control Constants

- Sticks: `L_STICK_HOR`, `L_STICK_VER`, `R_STICK_HOR`, `R_STICK_VER`
- Triggers: `L_TRIGGER`, `R_TRIGGER`
- Buttons: `BUTTONS`
- Settings: `SETTING1`, `SETTING2`

## Supported Platforms

- **LEGO MINDSTORMS EV3** (with MicroPython firmware)
- **LEGO SPIKE Prime/Prime Essential** (with MINDSTORMS firmware)
- **LEGO SPIKE Robot Inventor**
- **ESP32** with MicroPython
- Other MicroPython boards with `ubluetooth` support

## License

MIT License

## Author

Anton Vanhoucke
