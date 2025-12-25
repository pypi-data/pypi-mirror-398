Introduction
=============

BLE2WLED bridges the gap between Bluetooth Low Energy beacon detection and visual LED effects. It processes beacon data from MQTT and renders dynamic, real-time visualizations on WLED LED strips.

Overview
--------

BLE2WLED is a Python package that:

1. **Receives BLE beacon data** via MQTT (beacon ID and signal strength/RSSI)
2. **Converts signal strength to distance** using RF propagation modeling
3. **Maps distance to colors** on a gradient (yellow when near → red when far)
4. **Adds visual identity** with hash-based hue shifts for each beacon
5. **Implements graceful fade-out** for beacons that disappear
6. **Renders motion trails** as beacons move along the LED strip
7. **Outputs to WLED** via HTTP or UDP (DRGB protocol) for smooth real-time animation

Key Features
------------

- **Real-time beacon visualization** with distance-based coloring
- **Motion trails** showing beacon movement across LED strips
- **Graceful fade-out** when beacons disappear
- **Multiple output protocols** (HTTP and UDP/DRGB)
- **MQTT authentication** support for secured brokers
- **HTTP retry logic** with automatic timeout recovery
- **CLI simulator** for testing without hardware
- **Real-time statistics** showing message rates and active beacons
- **Fully configurable** via environment variables or code

Use Cases
---------

- **Presence visualization** in smart homes or offices
- **Occupancy detection** showing active beacons in rooms
- **Proximity-based effects** with beacons triggering LED changes
- **Development and testing** of beacon detection logic
- **Interactive installations** with real-time beacon feedback

Prerequisites
-------------

You need a working MQTT broker that receives BLE beacon data in JSON format. Each message should contain a unique beacon ID and its RSSI value.  
Ideally use `ESPresense`<https://espresense.com/> firmware on ESP32 devices for BLE scanning and MQTT publishing to a mosquito broker (running on `HomeAssistant`<https://www.home-assistant.io/> for example).

On the output side, you need a `LED`<https://kno.wled.ge/> controlled LED strip. Use an ESP8266 or ESP32 running the WLED firmware.

Architecture
------------

The system follows a modular architecture:

::

    MQTT Broker
        ↓
    EspresenseBeaconListener
        ↓
    BeaconState (tracks active beacons)
        ↓
    Animation Engine (processes visual effects)
        ↓
    WLED Controller (HTTP or UDP)
        ↓
    Physical LED Strip

Data Flow
---------

1. **MQTT Reception**: Beacon data arrives via MQTT from espresense devices
2. **State Management**: Beacon state tracks each beacon's position, signal strength, and lifecycle
3. **Distance Calculation**: RSSI is converted to distance using RF propagation modeling
4. **Color Mapping**: Distance is mapped to colors (distance → hue, strength → brightness)
5. **Trail Rendering**: Motion trails are rendered showing recent beacon positions
6. **LED Update**: Calculated LED values are sent to WLED via HTTP or UDP
7. **Animation Loop**: This cycle repeats at configurable intervals (typically 5-50ms)

Signal Strength to Distance Conversion
---------------------------------------

The system uses Friis path loss model to convert RSSI (Received Signal Strength Indicator) to distance:

.. math::

    d = 10^{\frac{TXP - RSSI - A}{20n}}

Where:
- ``TXP`` = Transmit Power (typically -59 dBm for BLE)
- ``RSSI`` = Received Signal Strength Indicator (in dBm)
- ``A`` = Environmental factor (typically 2.0 for line-of-sight)
- ``n`` = Path loss exponent (typically 2.0)

Color Mapping Strategy
----------------------

The system uses a sophisticated color mapping strategy:

1. **Hue Assignment**: Each beacon gets a unique hue based on its ID (hash-based)
2. **Distance-based Saturation**: Closer beacons are more saturated (yellow), farther are less (red)
3. **Signal-based Brightness**: Stronger signal = brighter LED, weaker = dimmer
4. **Motion Trails**: Recent positions are brightest, fade out over time

This creates a visually distinctive and informative display where you can:
- Identify individual beacons by color
- Gauge distance by color intensity
- See movement patterns with trails

Next Steps
----------

- :doc:`installation` - Get started with installation
- :doc:`quickstart` - Five-minute quick start guide
- :doc:`guides/configuration` - Configuration options
- :doc:`guides/cli_simulator` - Testing with the CLI simulator
