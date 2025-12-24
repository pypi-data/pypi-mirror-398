"""
MIDI Controller Example

This example shows how to send MIDI commands over Bluetooth.

Hardware Requirements:
- ESP32 board with MicroPython
- A MIDI-compatible device (synthesizer, DAW, etc.)
- Bluetooth connectivity on both devices

Setup:
1. Flash MicroPython on your ESP32
2. Install btbricks: micropip install btbricks
3. Run this code
4. Connect your device via Bluetooth to the ESP32

This example sends some example MIDI notes.
"""

from btbricks import MidiController
from time import sleep

# Create MIDI controller
midi = MidiController()

# Try to connect to a MIDI device
print("Initializing MIDI controller...")

try:
    # Example MIDI notes (C, D, E, F notes)
    notes = [60, 62, 64, 65]  # Middle C and surrounding notes

    print("Playing notes...")
    for note in notes:
        print(f"Sending MIDI note {note}")
        midi.send_note_on(note, velocity=100)
        sleep(0.5)
        midi.send_note_off(note)
        sleep(0.2)

    # Play a simple chord (C major: C, E, G)
    print("Playing C major chord...")
    for note in [60, 64, 67]:
        midi.send_note_on(note, velocity=80)

    sleep(1.0)

    for note in [60, 64, 67]:
        midi.send_note_off(note)

    print("Done")

except Exception as e:
    print(f"Error: {e}")

print("MIDI controller shutdown")
