<div align="center">
<img alt="rcservo logo" src="https://raw.githubusercontent.com/antonvh/rcservo/master/img/rcservo.png" width="200">

# rcservo

[![PyPI version](https://badge.fury.io/py/rcservo.svg)](https://badge.fury.io/py/rcservo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MicroPython Compatible](https://img.shields.io/badge/MicroPython-Compatible-brightgreen.svg)](https://micropython.org/)

A lightweight, zero-dependency Python library for controlling **hobby servo motors** and **RC servos** with PWM (Pulse Width Modulation). Works seamlessly on CPython and **MicroPython** platforms.

**Keywords:** `micropython rc servo`, `micropython hobby servo`, `servo control`, `PWM`, `robotics`

</div>

## Features

- ✨ Simple, intuitive API for servo control
- 🎯 Angle-based and PWM pulse-width control
- 🔧 Flexible configuration for different servo types and ranges
- 🐍 Works on both **standard Python** and **MicroPython** (Raspberry Pi Pico, ESP32, etc.)
- 📦 Zero external dependencies
- ⚡ Lightweight and efficient

## Installation

Install from PyPI:

```bash
pip install rcservo
```

### For MicroPython

Copy `rcservo.py` to your MicroPython device:

```bash
# Using mpremote (Raspberry Pi Pico, etc.)
mpremote cp rcservo.py :

# Or using ampy (ESP32, ESP8266, etc.)
ampy --port /dev/ttyUSB0 put rcservo.py
```

## Quick Start

```python
from rcservo import Servo

# Create a servo instance on GPIO pin 12
servo = Servo(pin=12)

# Set servo angle (-90 to +90 degrees)
servo.angle(45)

# Set servo angle to neutral (0 degrees)
servo.angle(0)

# Set servo angle to far left (-90 degrees)
servo.angle(-90)
```

## Usage

### Basic Initialization

```python
from rcservo import Servo

# Default configuration (1000-2000 µs pulse width, -90 to +90 degrees)
servo = Servo(pin=12)
```

### Custom Configuration

```python
# Custom servo with different pulse width ranges
servo = Servo(
    pin=12,
    min_pulse=800,      # Minimum pulse width in microseconds
    max_pulse=2200,     # Maximum pulse width in microseconds
    min_angle=-120,     # Minimum angle
    max_angle=120       # Maximum angle
)
```

### Control Methods

```python
# Set servo angle
servo.angle(45)  # Move to 45 degrees

# Set servo PWM pulse width directly (in microseconds)
servo.pwm(1500)  # Set to 1500 µs pulse
```

## Hardware Requirements

- **Servo motor:** Standard hobby servo or RC servo with PWM control
- **Microcontroller:** Any board with PWM GPIO output capability:
  - Raspberry Pi Pico (MicroPython)
  - ESP32 / ESP8266 (MicroPython)
  - Arduino (with Python via Micropython)
  - Raspberry Pi / BeagleBone (standard Python)
  - Any board supported by CPython or MicroPython
- **Power supply:** Appropriate for your servo (typically 4.8–6V for hobby servos)

## API Reference

### Servo Class

#### `__init__(pin, min_pulse=1000, max_pulse=2000, min_angle=-90, max_angle=90)`

Initialize a servo on the specified pin.

**Parameters:**
- `pin` (int): GPIO pin number
- `min_pulse` (int): Minimum pulse width in microseconds. Default: 1000
- `max_pulse` (int): Maximum pulse width in microseconds. Default: 2000
- `min_angle` (int): Minimum angle. Default: -90
- `max_angle` (int): Maximum angle. Default: 90

#### `angle(angle)`

Set the servo to a specific angle.

**Parameters:**
- `angle` (float or int): Target angle. Will be clamped between min_angle and max_angle.

#### `pwm(pwm)`

Set the servo pulse width directly.

**Parameters:**
- `pwm` (int or float): Pulse width in microseconds. Will be clamped between min_pulse and max_pulse.

## Notes

- Angles are clamped to the configured min/max range
- Pulse widths are clamped to the configured min/max range
- Standard hobby servo pulse: 1000–2000 µs for −90 to +90 degrees
- 1500 µs corresponds to neutral (0 degrees) by default
- MicroPython implementation is memory-efficient and suitable for embedded devices

## Use Cases

- **Robotics:** Pan-tilt camera mounts, robot arms, legs
- **RC Projects:** Model airplanes, cars, boats with servo control
- **IoT:** Home automation with servo-controlled blinds, doors, valves
- **Education:** Teaching microcontroller PWM and servo control concepts
- **Hobbyist Projects:** Camera sliders, gimbal systems, mechanical displays

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License — See [LICENSE](LICENSE) file for details.

## Author

**Anton Vanhoucke**
